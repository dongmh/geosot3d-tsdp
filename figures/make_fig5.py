"""
Figure 5: Path planning visualisation on the Xi'an scene (3 panels).

Panels: (a) Uniform, (b) Terrain-AMR, (c) TSDP.
Shows the planned A* path overlaid on each grid, with start/goal markers
and an inset summary of (planning time, expanded nodes, path length, mean safety).

Reads:  results/xian_paths/{method}.npz
Writes: figures/output/figure5.jpeg
"""
from __future__ import annotations
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_one_panel(ax, path_npz: Path, title: str) -> None:
    data = np.load(path_npz)
    background = data["background_image"]      # (H, W, 3) uint8 — terrain raster
    bbox = data["bbox"]                        # (4,) lon_min, lat_min, lon_max, lat_max
    path_xy = data["path_xy"]                  # (P, 2)
    start_xy = data["start_xy"]
    goal_xy = data["goal_xy"]
    metrics = data["metrics"].item()           # dict

    ax.imshow(
        background,
        extent=(bbox[0], bbox[2], bbox[1], bbox[3]),
        origin="lower",
    )
    ax.plot(path_xy[:, 0], path_xy[:, 1], "-", color="C0", linewidth=2)
    ax.plot(*start_xy, "o", color="green", markersize=10)
    ax.plot(*goal_xy,  "*", color="orange", markersize=14)

    # Inset summary
    summary = (
        f"Time: {metrics['plan_time_s']:.2f} s\n"
        f"Nodes: {metrics['expanded_nodes']:,}\n"
        f"Length: {metrics['path_length_m']:.0f} m\n"
        f"Safety: {metrics['mean_safety_m']:.1f} m"
    )
    ax.text(0.02, 0.98, summary, transform=ax.transAxes,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9))

    ax.set_xlabel("Longitude (deg E)")
    ax.set_ylabel("Latitude (deg N)")
    ax.set_title(title)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input-dir", type=Path,
                        default=Path("results/xian_paths"))
    parser.add_argument("--output", type=Path,
                        default=Path("figures/output/figure5.jpeg"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    plot_one_panel(axes[0], args.input_dir / "uniform.npz",     "(a) Uniform")
    plot_one_panel(axes[1], args.input_dir / "terrain_amr.npz", "(b) Terrain-AMR")
    plot_one_panel(axes[2], args.input_dir / "tsdp.npz",        "(c) TSDP (Ours)")

    plt.tight_layout()
    plt.savefig(args.output, dpi=300, bbox_inches="tight")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
