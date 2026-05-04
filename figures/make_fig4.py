"""
Figure 4: Real-world grid comparison on the Xi'an district (4 panels).

Panels: (a) Uniform, (b) Terrain-AMR, (c) Semantic-Only, (d) TSDP.
Each panel shows voxel boundaries coloured by GeoSOT-3D level (L5-L9).

Reads:  results/xian_partitions/{method}.npz  (one per method)
Writes: figures/output/figure4.jpeg
"""
from __future__ import annotations
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Rectangle


LEVEL_COLOURS = {
    5: "#2ecc71",   # green
    6: "#3498db",   # blue
    7: "#f1c40f",   # yellow
    8: "#e67e22",   # orange
    9: "#e91e63",   # pink
}


def plot_one_panel(ax, partition_npz: Path, title: str) -> None:
    data = np.load(partition_npz)
    bboxes = data["bboxes"]      # shape (N, 4): lon_min, lat_min, lon_max, lat_max
    levels = data["levels"]      # shape (N,)

    patches = []
    colours = []
    for (lon_min, lat_min, lon_max, lat_max), lvl in zip(bboxes, levels):
        patches.append(Rectangle(
            (lon_min, lat_min), lon_max - lon_min, lat_max - lat_min,
        ))
        colours.append(LEVEL_COLOURS.get(int(lvl), "#aaaaaa"))
    pc = PatchCollection(patches, facecolors=colours, edgecolors="black",
                         linewidths=0.1, alpha=0.6)
    ax.add_collection(pc)
    ax.autoscale_view()
    ax.set_xlabel("Longitude (deg E)")
    ax.set_ylabel("Latitude (deg N)")
    ax.set_title(f"{title}  (n = {len(levels):,})")
    ax.set_aspect("equal")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input-dir", type=Path,
                        default=Path("results/xian_partitions"))
    parser.add_argument("--output", type=Path,
                        default=Path("figures/output/figure4.jpeg"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    plot_one_panel(axes[0, 0], args.input_dir / "uniform.npz",       "(a) Uniform")
    plot_one_panel(axes[0, 1], args.input_dir / "terrain_amr.npz",   "(b) Terrain-AMR")
    plot_one_panel(axes[1, 0], args.input_dir / "semantic_only.npz", "(c) Semantic-Only")
    plot_one_panel(axes[1, 1], args.input_dir / "tsdp.npz",          "(d) TSDP")

    # Legend
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=c, label=f"L{l}")
        for l, c in LEVEL_COLOURS.items()
    ]
    fig.legend(handles=handles, loc="lower center", ncol=5,
               bbox_to_anchor=(0.5, -0.01))
    plt.tight_layout()
    plt.savefig(args.output, dpi=300, bbox_inches="tight")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
