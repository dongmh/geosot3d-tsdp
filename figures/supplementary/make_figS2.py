"""
Supplementary Figure S2: Synthetic-scene layout.

Shows the synthetic 5x5 km test scene used to populate Table 2:
fractal-noise terrain (175 m relief), 15 random buildings (20-80 m
height), one no-fly zone, one restricted zone, one river.

This is generated from the same scene snapshot used in `experiments/synthetic.py`,
so a re-run of the synthetic experiment produces the data this script needs.

Usage
-----
    python -m figures.supplementary.make_figS2

Inputs
------
    results/synthetic_scene_snapshot.npz   (terrain, buildings, zones)

Outputs
-------
    figures/output/figureS2.jpeg
"""
from __future__ import annotations
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input", type=Path,
                        default=Path("results/synthetic_scene_snapshot.npz"))
    parser.add_argument("--output", type=Path,
                        default=Path("figures/output/figureS2.jpeg"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    # TODO: load the snapshot and plot:
    #   - terrain raster background (viridis colormap)
    #   - building footprints (orange polygons with height labels)
    #   - no-fly zone (red dashed polygon)
    #   - restricted zone (yellow dashed polygon)
    #   - river (blue polyline)
    raise NotImplementedError(
        "Implement the synthetic-scene visualisation. "
        "See `figures/output/figureS2.jpeg` (paper version) for the target layout."
    )


if __name__ == "__main__":
    main()
