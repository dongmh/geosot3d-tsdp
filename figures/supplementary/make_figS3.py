"""
Supplementary Figure S3: 3D terrain visualisation of the Xi'an study area.

Renders the cropped GDEM V3 elevation raster as a 3D surface plot,
with building footprints extruded as vertical bars (height = building
height + ground elevation).

Usage
-----
    python -m figures.supplementary.make_figS3

Inputs
------
    data/cache/gdem_xian.tif                (DEM, output of download_xian.sh)
    data/cache/osm_xian_buildings.geojson   (buildings, output of download_xian.sh)

Outputs
-------
    figures/output/figureS3.jpeg
"""
from __future__ import annotations
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dem", type=Path,
                        default=Path("data/cache/gdem_xian.tif"))
    parser.add_argument("--buildings", type=Path,
                        default=Path("data/cache/osm_xian_buildings.geojson"))
    parser.add_argument("--output", type=Path,
                        default=Path("figures/output/figureS3.jpeg"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    # TODO: implement using rasterio + matplotlib mplot3d:
    #   1. open DEM, downsample to ~200x200 for visualisation
    #   2. plot_surface with viridis colormap, alpha=0.85
    #   3. for each building: bar3d at building centroid with z=ground_elev,
    #      dz=building_height
    #   4. set view_init(elev=35, azim=-60) to match the paper
    raise NotImplementedError(
        "Implement Xi'an 3D terrain visualisation. "
        "Use rasterio.open + plt.subplots(subplot_kw={'projection': '3d'})."
    )


if __name__ == "__main__":
    main()
