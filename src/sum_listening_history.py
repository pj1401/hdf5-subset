"""
A script that sums the play count in the User Listening History file,
    to get a total play count for each track.
module: src.sum_listening_history
"""

from collections.abc import Iterator
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

CSV_LISTENING_HISTORY_PATH = os.getenv("CSV_LISTENING_HISTORY_PATH")
LISTENING_HISTORY_OUTPUT_PATH = os.getenv("LISTENING_HISTORY_OUTPUT_PATH")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 5000))


def read_listening_history_data(
    file_path: str, chunk_size: int
) -> Iterator[pd.DataFrame]:
    """
    Read listening data from the file, returns the data as an Iterator with chunks.

    :param file_path: The path to the listening history file.
    :type file_path: str
    :param chunk_size: The number of rows in each chunk.
    :type chunk_size: int
    :return: An Iterator with the listening history chunks.
    :rtype: Iterator[DataFrame]
    """
    return pd.read_csv(
        file_path,
        chunksize=chunk_size,
        usecols=[
            "track_id",
            "playcount",
        ],
    )


def transform_listening_history_data(chunks: Iterator[pd.DataFrame]) -> pd.DataFrame:
    """
    Sums the playcount column values for each track ID.

    :param chunks: The Iterator with the playcount chunks.
    :type chunks: Iterator[pd.DataFrame]
    :return: A DataFrame with the track_id and playcount columns,
        where playcount has the total play count for each track.
    :rtype: DataFrame
    """
    total_playcount = pd.DataFrame()
    for chunk in chunks:
        chunk["track_id"] = chunk["track_id"].astype("str").str.strip().str.upper()
        chunk = chunk.groupby("track_id")["playcount"].sum().reset_index()
        total_playcount = (
            pd.concat([total_playcount, chunk])
            .groupby("track_id")["playcount"]
            .sum()
            .reset_index()
        )
    return total_playcount


def main():
    """
    Starting point for writing a new listening history file.
    """
    print("Reading data...")
    listening_history_data = read_listening_history_data(
        CSV_LISTENING_HISTORY_PATH, CHUNK_SIZE
    )

    print("Transforming data...")
    total_playcount = transform_listening_history_data(listening_history_data)

    print("Writing data to file...")
    total_playcount.to_csv(LISTENING_HISTORY_OUTPUT_PATH, index=False)


if __name__ == "__main__":
    main()
