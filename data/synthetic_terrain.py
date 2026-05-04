"""
Deterministic fractal-noise terrain generator for the synthetic experiment.

The terrain is held fixed across the 30 repetitions (only building placement
and start-goal pairs are reseeded); see the *Synthetic scene* paragraph of
the Methods.

The generator uses the diamond-square algorithm with a fixed master seed so
that the resulting elevation field is bit-for-bit reproducible across
machines and Python versions.
"""
from __future__ import annotations
import argparse
from pathlib import Path

import numpy as np


def diamond_square(side: int, roughness: float, seed: int) -> np.ndarray:
    """
    Generate a (side+1) x (side+1) heightmap by the diamond-square algorithm.

    Parameters
    ----------
    side : int
        Power of 2 (e.g., 256, 512, 1024).
    roughness : float in [0, 1]
        Fractal exponent: smaller -> smoother terrain.
    seed : int
        Random seed; a fixed value gives bit-identical output.

    Returns
    -------
    grid : np.ndarray, shape (side + 1, side + 1)
    """
    if (side & (side - 1)) != 0:
        raise ValueError(f"side must be a power of 2; got {side}.")

    rng = np.random.default_rng(seed)
    grid = np.zeros((side + 1, side + 1), dtype=float)

    # Seed corners
    grid[0, 0] = grid[0, side] = grid[side, 0] = grid[side, side] = 0.0

    step = side
    scale = 1.0
    while step > 1:
        half = step // 2
        # Diamond step
        for x in range(0, side, step):
            for y in range(0, side, step):
                avg = (grid[x, y] + grid[x + step, y]
                       + grid[x, y + step] + grid[x + step, y + step]) / 4.0
                grid[x + half, y + half] = avg + rng.uniform(-scale, scale)
        # Square step
        for x in range(0, side + 1, half):
            for y in range((x + half) % step, side + 1, step):
                vals = []
                if x - half >= 0: vals.append(grid[x - half, y])
                if x + half <= side: vals.append(grid[x + half, y])
                if y - half >= 0: vals.append(grid[x, y - half])
                if y + half <= side: vals.append(grid[x, y + half])
                grid[x, y] = np.mean(vals) + rng.uniform(-scale, scale)
        step = half
        scale *= roughness
    return grid


def generate_synthetic_terrain(
    n_x: int = 512,
    n_y: int = 512,
    relief_m: float = 175.0,
    seed: int = 20260101,
) -> np.ndarray:
    """
    Convenience wrapper.

    Returns a (n_y, n_x) elevation field rescaled to span exactly relief_m.
    """
    side = max(n_x, n_y)
    side_pow2 = 1 << (side - 1).bit_length()
    raw = diamond_square(side_pow2, roughness=0.6, seed=seed)
    raw = raw[:n_y, :n_x]
    raw = raw - raw.min()
    raw = raw * (relief_m / max(raw.max(), 1e-9))
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--output", type=Path,
                        default=Path("data/cache/synthetic_terrain.npy"))
    parser.add_argument("--n-x", type=int, default=512)
    parser.add_argument("--n-y", type=int, default=512)
    parser.add_argument("--relief-m", type=float, default=175.0)
    parser.add_argument("--seed", type=int, default=20260101)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    grid = generate_synthetic_terrain(
        n_x=args.n_x, n_y=args.n_y,
        relief_m=args.relief_m, seed=args.seed,
    )
    np.save(args.output, grid)
    print(f"Wrote {grid.shape} terrain to {args.output} "
          f"(relief={grid.max()-grid.min():.1f} m)")


if __name__ == "__main__":
    main()
