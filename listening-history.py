import pandas as pd


def create_listening_history_subset(
    original_csv_path: str, track_ids: list, output_csv_path: str
):
    """
    Create a subset of the listening history CSV file containing only the rows for the specified track IDs.

    Args:
        original_csv_path: Path to the original listening history CSV file.
        track_ids: List of track IDs to include in the subset.
        output_csv_path: Path to save the subset CSV file.
    """
    # Read the original listening history CSV
    listening_history = pd.read_csv(original_csv_path)

    # Filter rows for the specified track IDs
    subset = listening_history[listening_history["track_id"].isin(track_ids)]

    # Save the subset to a new CSV file
    subset.to_csv(output_csv_path, index=False)

    print(f"Listening history subset saved to: {output_csv_path}")
    print(f"Number of rows in subset: {len(subset)}")


if __name__ == "__main__":
    original_csv_path = "data/User Listening History.csv"
    output_csv_path = "output/listening-history-subset.csv"

    # Get the first 10 track IDs from the CSV
    csv_df = pd.read_csv("data/Music Info.csv", nrows=10)
    track_ids = csv_df["track_id"].str.strip().str.upper().tolist()

    create_listening_history_subset(original_csv_path, track_ids, output_csv_path)
