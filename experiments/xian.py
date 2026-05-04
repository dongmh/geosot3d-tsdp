"""
Real-world Xi'an benchmark — reproduces Table 3 and Figs. 4-5.

Usage
-----
    bash data/download_xian.sh            # one-time data download
    python -m experiments.xian --output results/xian.csv

Region of interest
------------------
    Bounding box: 108.85-109.00 E, 34.18-34.30 N (~13.8 x 13.3 km)
    Includes: Xi'an Bell Tower, Giant Wild Goose Pagoda district

Data sources
------------
    Elevation : ASTER GDEM V3 (NASA Earthdata)
    Buildings : OpenStreetMap (~4,200 footprints via Overpass API)
    Airspace  : eAIP / DJI FlySafe public sources (digitised manually)
    Waterways : OpenStreetMap

NOTE on this stub
-----------------
The data-loading paths assume the download script in `data/download_xian.sh`
has been run; the partitioning + path-planning loop is the same as the
synthetic experiment, so most of the work is in adapting the I/O.
"""
from __future__ import annotations
import argparse
import csv
import time
from pathlib import Path
from typing import Dict, List

import numpy as np
from tqdm import tqdm

from tsdp import TSDPConfig, ts_adaptive_subdivide
from tsdp.config import (
    PAPER_DEFAULT, TERRAIN_AMR_BASELINE, SEMANTIC_ONLY_BASELINE,
)
from tsdp.adjacency import build_adjacency
from tsdp.path_cost import (
    astar, path_length_metres, mean_safety_distance,
)


# Bounding box of the study area (lon_min, lat_min, lon_max, lat_max)
XIAN_BBOX = (108.85, 34.18, 109.00, 34.30)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_xian_dem(data_dir: Path) -> "rasterio.DatasetReader":
    """Open the cached ASTER GDEM V3 tile clipped to XIAN_BBOX."""
    raise NotImplementedError(
        "Use rasterio.open(data_dir / 'cache' / 'gdem_xian.tif'). "
        "See data/download_xian.sh."
    )


def load_xian_buildings(data_dir: Path) -> "geopandas.GeoDataFrame":
    """Load OSM buildings from the cached PBF or pre-extracted GeoJSON."""
    raise NotImplementedError("See data/download_xian.sh.")


def load_xian_airspace(data_dir: Path) -> "geopandas.GeoDataFrame":
    """Load no-fly and restricted-flight zones from data/airspace/."""
    raise NotImplementedError("See data/airspace/README.md for format.")


# ---------------------------------------------------------------------------
# Per-method runner
# ---------------------------------------------------------------------------

def run_one_repetition(
    config: TSDPConfig,
    method_name: str,
    rep_seed: int,
    data_dir: Path,
) -> Dict[str, float]:
    """
    Real-world variant of the synthetic runner.

    Compared to synthetic.py: the DEM, buildings, and airspace are held fixed
    across repetitions; only start-goal pairs are randomised.
    """
    rng = np.random.default_rng(rep_seed)

    # 1. Load fixed scene
    dem = load_xian_dem(data_dir)
    buildings = load_xian_buildings(data_dir)
    airspace = load_xian_airspace(data_dir)
    start_xy, goal_xy = _sample_start_goal_xian(rng, XIAN_BBOX)

    # 2. Build the initial grid covering the bbox at level config.L0
    G0 = _build_initial_grid_for_xian(config, XIAN_BBOX)

    # 3. Partition
    elev_q, sem_q, label_q = _build_xian_query_callbacks(dem, buildings, airspace)
    t0 = time.perf_counter()
    result = ts_adaptive_subdivide(
        G0,
        elevation_query=elev_q,
        semantic_query=sem_q,
        label_query=label_q,
        config=config,
    )
    partition_time = time.perf_counter() - t0

    # 4. Plan
    centroids, adj = build_adjacency(result.terminals, config)
    risks, no_fly_mask = _xian_per_voxel_risks(result.terminals, buildings, airspace)
    start_idx = _nearest_voxel(centroids, start_xy)
    goal_idx = _nearest_voxel(centroids, goal_xy)

    t0 = time.perf_counter()
    path, n_expanded = astar(
        centroids, adj, risks, no_fly_mask, start_idx, goal_idx, config,
    )
    plan_time = time.perf_counter() - t0

    # 5. Metrics (Table 3)
    rmse, max_err = _xian_terrain_metrics(result.terminals, dem)
    building_f1, precision = _xian_building_f1(result.terminals, buildings)
    obstacle_centroids = _xian_obstacle_centroids(buildings, airspace)

    return {
        "method": method_name,
        "rep_seed": rep_seed,
        "rmse_m": rmse,
        "max_error_m": max_err,
        "building_f1": building_f1,
        "building_precision": precision,
        "n_voxels": len(result.terminals),
        "compression_pct": 100.0 * (1.0 - len(result.terminals) / len(G0)),
        "partition_time_s": partition_time,
        "plan_time_s": plan_time,
        "expanded_nodes": n_expanded,
        "path_length_m": path_length_metres(centroids, path) if path else float("nan"),
        "mean_safety_m": mean_safety_distance(centroids, path, obstacle_centroids) if path else float("nan"),
    }


# Stubs
def _sample_start_goal_xian(rng, bbox): raise NotImplementedError
def _build_initial_grid_for_xian(config, bbox): raise NotImplementedError
def _build_xian_query_callbacks(dem, buildings, airspace): raise NotImplementedError
def _xian_per_voxel_risks(voxels, buildings, airspace): raise NotImplementedError
def _xian_terrain_metrics(voxels, dem): raise NotImplementedError
def _xian_building_f1(voxels, buildings): raise NotImplementedError
def _xian_obstacle_centroids(buildings, airspace): raise NotImplementedError
def _nearest_voxel(centroids, xy): raise NotImplementedError


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

METHODS = {
    "Terrain-AMR": TERRAIN_AMR_BASELINE,
    "Semantic-Only": SEMANTIC_ONLY_BASELINE,
    "TSDP": PAPER_DEFAULT,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    rep_seeds = rng.integers(0, 2**31 - 1, size=args.repetitions).tolist()

    rows: List[Dict[str, float]] = []
    for method_name, config in METHODS.items():
        for rep_seed in tqdm(rep_seeds, desc=method_name):
            row = run_one_repetition(config, method_name, int(rep_seed), args.data_dir)
            rows.append(row)

    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
