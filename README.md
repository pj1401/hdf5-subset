# HDF5 Subset

A script that creates a subset of the Million Song Dataset.

The CSV files can be downloaded here: [Million Song Dataset + Spotify + Last.fm](https://www.kaggle.com/datasets/undefinenull/million-song-dataset-spotify-lastfm)  
The HDF5 file can be found here: [http://millionsongdataset.com/pages/getting-dataset/, (Additional files, 7)](http://millionsongdataset.com/pages/getting-dataset/)

## Usage

**Requires:**
- uv, [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/)

Clone project:

```bash
# ssh
git clone git@github.com:pj1401/hdf5-subset.git

# change directory
cd hdf5-subset

# Copy from .example.env to .env
cp .example.env .env
```

Set .venv and install dependencies

```bash
uv sync --group dev
```

Run the script:

```bash
uv run main.py
```
