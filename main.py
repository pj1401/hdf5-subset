"""
Script that creates a subset of the msd_summary_file.
module: main
"""

from collections.abc import Iterator
import h5py
import random
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.getenv("CSV_PATH")
HDF5_PATH = os.getenv("HDF5_PATH")
OUTPUT_PATH = os.getenv("OUTPUT_PATH")
NUM_CSV_TRACKS = int(os.getenv("NUM_CSV_TRACKS"))
NUM_EXTRA_TRACKS = int(os.getenv("NUM_EXTRA_TRACKS"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 5000))

# Only copy data that is needed for the seed script.
DATASETS_TO_COPY = {
    "analysis": ["songs"],
    "metadata": ["songs"],
}

ANALYSIS_FIELDS = ["track_id"]
METADATA_FIELDS = ["release", "release_7digitalid"]


def _filter_structured_array(
    arr: np.ndarray,
    fields: list[str],
    indices: list[int],
) -> np.ndarray:
    """Return a new structured array containing only `fields` at `indices`."""
    import numpy as np

    sub = arr[indices]
    dtype = [(f, sub.dtype[f]) for f in fields if f in sub.dtype.names]
    out = np.empty(len(sub), dtype=dtype)
    for f, _ in dtype:
        out[f] = sub[f]
    return out


def create_subset_hdf5(
    original_hdf5_path: str,
    csv_path: str,
    output_hdf5_path: str,
    num_csv_tracks: int = 10,
    num_extra_tracks: int = 10,
):
    """
    Create a subset HDF5 file containing the first n tracks from the CSV and a random sample of additional tracks.

    Args:
        original_hdf5_path: Path to the original HDF5 file.
        csv_path: Path to the CSV file.
        output_hdf5_path: Path to save the subset HDF5 file.
        num_csv_tracks: Number of tracks from the CSV file
        num_extra_tracks: Number of additional random tracks to include.
    """
    # Step 1: Get the first n track_ids from the CSV
    csv_chunks = read_csv_music_info(csv_path, num_csv_tracks, CHUNK_SIZE)
    csv_track_ids = get_csv_track_ids(csv_chunks)
    print(f"Read {len(csv_track_ids)} track_ids from CSV.")

    # Step 2: Open the original HDF5 file and find the indices of the CSV tracks
    with h5py.File(original_hdf5_path, "r") as f:
        # Read track_ids from the analysis/songs dataset
        analysis_songs: h5py.Dataset = f["analysis"]["songs"]
        track_ids = [
            tid.decode("utf-8").strip().upper() for tid in analysis_songs["track_id"]
        ]
        total_tracks = len(track_ids)

        # Step 3: Find the indices of the CSV tracks
        csv_indices = []
        for track_id in csv_track_ids:
            try:
                index = track_ids.index(track_id)
                csv_indices.append(index)
            except ValueError:
                print(f"Warning: Track ID {track_id} not found in the HDF5 file.")

        if not csv_indices:
            raise ValueError(
                f"None of the first {num_csv_tracks} track IDs from the CSV were found in the HDF5 file."
            )

        print(f"Found {len(csv_indices)} CSV track IDs in HDF5 data.")

        # Step 4: Randomly sample additional track indices
        subset_indices = get_subset_indices(csv_indices, total_tracks, num_extra_tracks)

        # Step 5: Extract only the needed fields for each group.
        analysis_subset = _filter_structured_array(
            analysis_songs[:], ANALYSIS_FIELDS, subset_indices
        )

        metadata_songs: h5py.Dataset = f["metadata"]["songs"]
        metadata_subset = _filter_structured_array(
            metadata_songs[:], METADATA_FIELDS, subset_indices
        )

    # Step 6: Write the subset to a new HDF5 file
    with h5py.File(output_hdf5_path, "w") as f_out:
        analysis_group = f_out.create_group("analysis")
        analysis_group.create_dataset("songs", data=analysis_subset)

        metadata_group = f_out.create_group("metadata")
        metadata_group.create_dataset("songs", data=metadata_subset)

    print(f"Subset HDF5 file saved to: {output_hdf5_path}")


def read_csv_music_info(
    file_path: str, nrows: int, chunk_size: int
) -> Iterator[pd.DataFrame]:
    """
    Read the CSV music info file.

    :param file_path: Path to the CSV file.
    :type file_path: str
    :param nrows: Number of tracks from the CSV file.
    :type nrows: int
    :param chunk_size: The number of rows in each chunk.
    :type chunk_size: int
    :return: An Iterator with the music info chunks.
    :rtype: Iterator[DataFrame]
    """
    return pd.read_csv(
        file_path, nrows=nrows, chunksize=chunk_size, usecols=["track_id"]
    )


def get_csv_track_ids(chunks: Iterator[pd.DataFrame]) -> list[str]:
    """
    Get a list of track IDs from the music info chunks.

    :param chunks: An Iterator with the music info chunks.
    :type chunks: Iterator[pd.DataFrame]
    :return: A list of track IDs.
    :rtype: list[str]
    """
    track_ids = set()
    for chunk in chunks:
        chunk["track_id"] = chunk["track_id"].astype("str").str.strip().str.upper()
        track_ids.update(chunk["track_id"].to_numpy())
    return list(track_ids)


def get_subset_indices(
    csv_indices: list[int], total_tracks: int, num_extra_tracks: int
):
    """
    Get the indices for the subset.
    """
    csv_set = set(csv_indices)

    # List of indexes that are not listed in the CSV file.
    remaining = [i for i in range(total_tracks) if i not in csv_set]

    # Randomise extra indices.
    extra_indices = random.sample(remaining, min(num_extra_tracks, len(remaining)))

    # Join sets and sort.
    subset_indices = sorted(csv_set | set(extra_indices))

    print(
        f"Selected {len(subset_indices)} tracks for subset "
        f"({len(csv_indices)} from CSV, {len(extra_indices)} random)."
    )
    return subset_indices


if __name__ == "__main__":
    create_subset_hdf5(
        HDF5_PATH, CSV_PATH, OUTPUT_PATH, NUM_CSV_TRACKS, NUM_EXTRA_TRACKS
    )
