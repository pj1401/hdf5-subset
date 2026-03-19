import h5py
import random
import pandas as pd


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
        analysis_data = f["analysis"]["songs"][:]
        track_ids = [
            tid.decode("utf-8").strip().upper() for tid in analysis_data["track_id"]
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

    # Step 5: Write the subset to a new HDF5 file
    with h5py.File(output_hdf5_path, "w") as f_out:
        for group_name, datasets in subset_data.items():
            group = f_out.create_group(group_name)
            for dataset_name, data in datasets.items():
                group.create_dataset(dataset_name, data=data)

    print(f"Subset HDF5 file saved to: {output_hdf5_path}")


if __name__ == "__main__":
    original_hdf5_path = "data/msd_summary_file.h5"
    csv_path = "data/Music Info.csv"
    output_hdf5_path = "output/msd-summary-subset.h5"

    create_subset_hdf5(
        original_hdf5_path,
        csv_path,
        output_hdf5_path,
        num_csv_tracks=10,
        num_extra_tracks=5,
    )
