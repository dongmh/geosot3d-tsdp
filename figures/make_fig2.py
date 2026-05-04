"""
Figure 2: TSDP subdivision result on the synthetic scene.

Reads:
    results/synthetic_scene_partition.npz  (terminals, levels, terrain, buildings)

Writes:
    figures/output/figure2.jpeg
"""
from __future__ import annotations
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input", type=Path,
                        default=Path("results/synthetic_scene_partition.npz"))
    parser.add_argument("--output", type=Path,
                        default=Path("figures/output/figure2.jpeg"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    # TODO: load partition data and plot:
    #   - terrain as a coloured raster background
    #   - voxel boundaries as line segments, coloured by level (L5 green -> L9 pink)
    #   - building footprints as orange polygons
    #   - no-fly / restricted zones as dashed red / yellow polygons
    #   - river as a blue polyline
    # Style: match Figure 2 in the published paper.
    raise NotImplementedError(
        "Implement the synthetic-scene partition visualisation. "
        "See `figures/output/figure2.jpeg` for the target layout in the paper."
    )


if __name__ == "__main__":
    main()
