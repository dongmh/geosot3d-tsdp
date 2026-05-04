"""
Synthetic 5x5 km benchmark — reproduces Table 2 and Fig. 2.

Usage
-----
    python -m experiments.synthetic --output results/synthetic.csv

What this script does
---------------------
1. Generates a fractal-noise terrain (175 m relief), 15 random buildings
   (20-80 m height), a no-fly zone, a restricted zone, and a river. Random
   placement is reseeded per repetition; terrain is held fixed.
2. Runs 4 partitioning methods (Uniform / Terrain-AMR / Semantic-Only / TSDP).
3. Performs A* path planning with randomised start-goal pairs.
4. Aggregates RMSE, max error, F1, voxel count, planning time, expanded
   nodes, path length, minimum obstacle clearance over 30 repetitions.
5. Writes the table and runs Wilcoxon signed-rank significance tests.

NOTE on this stub
-----------------
This module currently contains the experiment skeleton. The terrain and
building placement code, plus the metric aggregation, must be filled in
before a paper-faithful run is possible. Each TODO is marked below.
"""
from __future__ import annotations
import argparse
import csv
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import numpy as np
from tqdm import tqdm

from tsdp import TSDPConfig, ts_adaptive_subdivide
from tsdp.config import (
    PAPER_DEFAULT, TERRAIN_AMR_BASELINE, SEMANTIC_ONLY_BASELINE,
)
from tsdp.adjacency import build_adjacency
from tsdp.path_cost import (
    astar, path_length_metres, mean_safety_distance, min_clearance,
)


# ---------------------------------------------------------------------------
# Synthetic environment generation
# ---------------------------------------------------------------------------

def generate_synthetic_terrain(seed: int, side_km: float = 5.0,
                                relief_m: float = 175.0) -> np.ndarray:
    """
    Fractal-noise terrain on a regular grid.

    TODO: implement Perlin / diamond-square noise reaching the specified relief.
    Held fixed across repetitions (use a fixed seed independent of the
    repetition seed).
    """
    raise NotImplementedError("Implement fractal-noise terrain generator.")


def generate_random_buildings(rng: np.random.Generator,
                               n_buildings: int = 15,
                               height_range_m: Tuple[float, float] = (20.0, 80.0)
                               ) -> List[Dict]:
    """
    TODO: place n buildings at uniformly-random (x, y) within the scene with
    heights drawn from height_range. Return as a list of dicts with keys
    {centroid, footprint_polygon, height}.
    """
    raise NotImplementedError("Implement random building generator.")


# ---------------------------------------------------------------------------
# Per-method runner
# ---------------------------------------------------------------------------

def run_one_repetition(
    config: TSDPConfig,
    method_name: str,
    rep_seed: int,
) -> Dict[str, float]:
    """
    Build the scene, partition with the given config, plan a path, return
    a row of metrics.
    """
    rng = np.random.default_rng(rep_seed)

    # 1. Build the scene
    terrain = generate_synthetic_terrain(seed=20260101)  # fixed terrain
    buildings = generate_random_buildings(rng)
    no_fly_zones = []   # TODO: place 1 no-fly + 1 restricted + 1 river
    start_xy, goal_xy = _sample_start_goal(rng)

    # 2. Build the initial uniform grid G_0
    G0 = _build_initial_grid_for_synthetic_scene(config)

    # 3. Run partitioning
    elev_q, sem_q, label_q = _build_query_callbacks(
        terrain, buildings, no_fly_zones,
    )
    t0 = time.perf_counter()
    result = ts_adaptive_subdivide(
        G0,
        elevation_query=elev_q,
        semantic_query=sem_q,
        label_query=label_q,
        config=config,
    )
    partition_time = time.perf_counter() - t0

    # 4. Run path planning
    centroids, adj = build_adjacency(result.terminals, config)
    risks, no_fly_mask = _per_voxel_risks(result.terminals, buildings, no_fly_zones)
    start_idx = _nearest_voxel(centroids, start_xy)
    goal_idx = _nearest_voxel(centroids, goal_xy)

    t0 = time.perf_counter()
    path, n_expanded = astar(
        centroids, adj, risks, no_fly_mask, start_idx, goal_idx, config,
    )
    plan_time = time.perf_counter() - t0

    # 5. Compute metrics (see Table 2 columns)
    rmse, max_err = _terrain_rmse_and_max_error(result.terminals, terrain)
    building_f1, precision = _building_f1(result.terminals, buildings)
    obstacle_centroids = np.array([b["centroid"] for b in buildings])

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
        "min_clearance_m": min_clearance(centroids, path, obstacle_centroids) if path else float("nan"),
    }


# ---------------------------------------------------------------------------
# Stubs to be filled in
# ---------------------------------------------------------------------------
# These are kept thin so reviewers can locate and replace them.

def _sample_start_goal(rng): raise NotImplementedError
def _build_initial_grid_for_synthetic_scene(config): raise NotImplementedError
def _build_query_callbacks(terrain, buildings, no_fly_zones): raise NotImplementedError
def _per_voxel_risks(voxels, buildings, no_fly_zones): raise NotImplementedError
def _nearest_voxel(centroids, xy): raise NotImplementedError
def _terrain_rmse_and_max_error(voxels, terrain): raise NotImplementedError
def _building_f1(voxels, buildings): raise NotImplementedError


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

METHODS = {
    "Uniform": None,                             # special-cased below
    "Terrain-AMR": TERRAIN_AMR_BASELINE,
    "Semantic-Only": SEMANTIC_ONLY_BASELINE,
    "TSDP": PAPER_DEFAULT,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--seed", type=int, default=42,
                        help="Master seed; per-repetition seeds derived from it.")
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    rep_seeds = rng.integers(0, 2**31 - 1, size=args.repetitions).tolist()

    rows: List[Dict[str, float]] = []
    for method_name, config in METHODS.items():
        if config is None:
            # TODO: handle uniform-grid baseline (does not run TSDP)
            continue
        for rep_seed in tqdm(rep_seeds, desc=method_name):
            row = run_one_repetition(config, method_name, int(rep_seed))
            rows.append(row)

    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
