"""
Script that creates a subset of the msd_summary_file.
module: main
"""

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
    csv_df = pd.read_csv(csv_path, nrows=num_csv_tracks)  # Read only the first n rows
    csv_track_ids = csv_df["track_id"].str.strip().str.upper().tolist()
    print(f"First {num_csv_tracks} track_ids in CSV: {csv_track_ids}")

    # Step 2: Open the original HDF5 file and find the indices of the CSV tracks
    with h5py.File(original_hdf5_path, "r") as f:
        # Read track_ids from the analysis/songs dataset
        analysis_songs: h5py.Dataset = f["analysis"]["songs"]
        track_ids = [
            tid.decode("utf-8").strip().upper() for tid in analysis_songs["track_id"]
        ]

        # Find the indices of the CSV tracks
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

        print(f"Found CSV tracks at indices: {csv_indices}")

        # Step 3: Randomly sample additional track indices
        all_indices = list(
            set(range(len(track_ids))) - set(csv_indices)
        )  # Exclude CSV tracks
        extra_indices = random.sample(
            all_indices, min(num_extra_tracks, len(all_indices))
        )

        # Combine the indices
        subset_indices = csv_indices + extra_indices
        subset_indices = sorted(set(subset_indices))  # Remove duplicates and sort

        print(
            f"Selected {len(subset_indices)} tracks for subset (including {len(csv_indices)} CSV tracks)."
        )

        # Step 4: Extract data for these indices from all groups
        subset_data = {}
        for group_name in f.keys():
            subset_data[group_name] = {}
            for dataset_name in f[group_name].keys():
                dataset = f[group_name][dataset_name]
                # Extract rows for the subset_indices
                subset_data[group_name][dataset_name] = dataset[subset_indices]

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


if __name__ == "__main__":
    create_subset_hdf5(
        HDF5_PATH, CSV_PATH, OUTPUT_PATH, NUM_CSV_TRACKS, NUM_EXTRA_TRACKS
    )
