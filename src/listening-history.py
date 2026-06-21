import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = os.getenv("CSV_PATH")
NUM_CSV_TRACKS = int(os.getenv("NUM_CSV_TRACKS"))
CSV_LISTENING_HISTORY_PATH = os.getenv("CSV_LISTENING_HISTORY_PATH")
LISTENING_HISTORY_OUTPUT_PATH = os.getenv("LISTENING_HISTORY_OUTPUT_PATH")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 5000))


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
    listening_history_chunks = pd.read_csv(
        original_csv_path,
        chunksize=CHUNK_SIZE,
    )

    for listening_history in listening_history_chunks:
        # Filter rows for the specified track IDs
        subset = listening_history[listening_history["track_id"].isin(track_ids)]

        # Save the subset to a new CSV file
        subset.to_csv(output_csv_path, index=False, mode="a", header=not os.path.exists(output_csv_path))

    print(f"Listening history subset saved to: {output_csv_path}")


if __name__ == "__main__":
    original_csv_path = CSV_LISTENING_HISTORY_PATH
    output_csv_path = LISTENING_HISTORY_OUTPUT_PATH

    # Get the first n track IDs from the CSV
    csv_df = pd.read_csv(CSV_PATH, nrows=NUM_CSV_TRACKS)
    track_ids = csv_df["track_id"].str.strip().str.upper().tolist()

    create_listening_history_subset(original_csv_path, track_ids, output_csv_path)
