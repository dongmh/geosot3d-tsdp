"""
Parameter sensitivity sweep — produces the data behind Fig. 3.

Two scans:
    1. tau scan: tau in {0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50},
       record voxel count and elevation RMSE. -> Fig. 3 panel (a).
    2. (alpha, beta) heatmap: 10x10 grid over the simplex alpha + beta <= 0.9
       (gamma fixed at 0.1), record compression rate and building F1.
       -> Fig. 3 panel (b).

Usage
-----
    python -m experiments.parameter_sweep --output results/sweep.npz
"""
from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np

from tsdp import TSDPConfig
# Note: we re-use the synthetic-scene runner because the sweep is performed
# on the synthetic environment; importing it lazily so the Xi'an scripts
# do not pull in the synthetic dependencies.


TAU_GRID = np.array([0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50])
ALPHA_GRID = np.linspace(0.0, 0.9, 10)
BETA_GRID = np.linspace(0.0, 0.9, 10)


def run_tau_sweep(seed: int) -> dict:
    """For each tau in TAU_GRID, build the partition and record (voxels, rmse)."""
    raise NotImplementedError(
        "Loop over TAU_GRID, calling experiments.synthetic.run_one_repetition "
        "with config.tau replaced; record n_voxels and rmse_m."
    )


def run_alpha_beta_sweep(seed: int) -> dict:
    """
    For each (alpha, beta) with alpha + beta <= 0.9, record (compression, F1).

    Uses gamma = 0.1 fixed (per paper). Cells where alpha + beta > 0.9 are
    filled with NaN (these are infeasible).
    """
    raise NotImplementedError(
        "Loop over ALPHA_GRID x BETA_GRID; skip cells where alpha + beta > 0.9."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    tau_results = run_tau_sweep(args.seed)
    ab_results = run_alpha_beta_sweep(args.seed)

    np.savez(args.output, **tau_results, **ab_results,
             tau_grid=TAU_GRID, alpha_grid=ALPHA_GRID, beta_grid=BETA_GRID)
    print(f"Wrote sweep results to {args.output}")


if __name__ == "__main__":
    main()
