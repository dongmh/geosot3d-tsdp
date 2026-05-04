# Data sources and provenance

This directory contains scripts and metadata for the public datasets used in
the experiments. We deliberately do NOT redistribute any third-party data.
The download scripts fetch from the original providers; the synthetic data
is regenerated deterministically from a fixed seed.

## Contents

| Path                       | Description                                          |
| -------------------------- | ---------------------------------------------------- |
| `download_xian.sh`         | Fetches GDEM V3 + OSM buildings for the Xi'an scene  |
| `synthetic_terrain.py`     | Deterministic fractal-noise terrain generator        |
| `airspace/`                | Manually digitised no-fly / restricted-flight zones  |
| `cache/`                   | Empty; populated by `download_xian.sh`               |

## Required external accounts

To run `download_xian.sh` you will need:

1. **NASA Earthdata Login** (free): https://urs.earthdata.nasa.gov/users/new
2. A `~/.netrc` file with these credentials, formatted as:
   ```
   machine urs.earthdata.nasa.gov
       login YOUR_USERNAME
       password YOUR_PASSWORD
   ```
   Make sure permissions are `chmod 600 ~/.netrc`.

The OpenStreetMap query goes through Overpass API and does not require
authentication, but the public Overpass instance has rate limits (~10K
queries/day). For repeated experimentation, consider running a local
Overpass instance via Docker.

## Data versions used in the paper

| Source            | Version / date                  | License             |
| ----------------- | ------------------------------- | ------------------- |
| ASTER GDEM V3     | NASA/JPL/METI, released 2019    | NASA EOSDIS terms   |
| OpenStreetMap     | Snapshot of 2025-12-15          | ODbL 1.0            |
| eAIP airspace     | Manually transcribed from the   | Attribution required |
|                   | Civil Aviation Administration   |                     |
|                   | of China public AIP, accessed   |                     |
|                   | 2025-11-01                      |                     |
| DJI FlySafe zones | Cross-checked against the public| (Reference only)    |
|                   | DJI FlySafe map                 |                     |

If you want bit-for-bit reproducibility of our experiments, please use the
exact OpenStreetMap snapshot we archived on Zenodo together with the
software release; otherwise newer OSM data will produce slightly different
building counts.

## Synthetic data

`synthetic_terrain.py` produces the same elevation field on any machine
when called with the default seed (`20260101`). Verify by running:

```bash
python data/synthetic_terrain.py
python -c "import numpy as np; t = np.load('data/cache/synthetic_terrain.npy'); print(f'mean={t.mean():.4f}, std={t.std():.4f}')"
# Expected: mean=87.5xxx, std=27.2xxx (exact values depend on numpy version)
```
