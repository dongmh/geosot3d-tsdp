"""
Supplementary Figure S4: Local detail comparison (Uniform vs TSDP).

Zoomed-in view of a 0.025 deg x 0.015 deg sub-region of the Xi'an scene
(approximately 108.935-108.960 E, 34.255-34.270 N). Two panels:
    (a) Uniform grid voxels in the sub-region
    (b) TSDP voxels in the same sub-region, with merged coarse cells (yellow)
        highlighted to show the bottom-up merging effect in flat areas.

Usage
-----
    python -m figures.supplementary.make_figS4

Inputs
------
    results/xian_partitions/uniform.npz
    results/xian_partitions/tsdp.npz

Outputs
-------
    figures/output/figureS4.jpeg
"""
from __future__ import annotations
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


# Sub-region of interest (lon_min, lat_min, lon_max, lat_max), in degrees.
SUBREGION_BBOX = (108.935, 34.255, 108.960, 34.270)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input-dir", type=Path,
                        default=Path("results/xian_partitions"))
    parser.add_argument("--output", type=Path,
                        default=Path("figures/output/figureS4.jpeg"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    # TODO: implement the 2-panel local-detail comparison:
    #   1. load uniform.npz and tsdp.npz
    #   2. filter voxels whose centroid falls inside SUBREGION_BBOX
    #   3. plot rectangles (using PatchCollection) for each panel
    #   4. highlight TSDP voxels at level <= L7 (merged) in yellow,
    #      voxels at level >= L8 in grey
    #   5. annotate each panel with the local voxel count n
    raise NotImplementedError(
        "Implement local-detail comparison panel. "
        "See figures/make_fig4.py for the rectangle-plotting pattern."
    )


if __name__ == "__main__":
    main()
