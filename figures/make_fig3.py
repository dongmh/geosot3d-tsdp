"""
Figure 3: Parameter sensitivity (2 panels).

Panel (a): tau scan with voxel count (left axis, blue) and elevation RMSE
           (right axis, orange). Optimal range tau in [0.30, 0.40] shaded.
Panel (b): (alpha, beta) joint heatmap, colour = compression rate, contours
           of building F1, working point (alpha=0.6, beta=0.3) marked with star.

Reads:  results/sweep.npz  (output of experiments/parameter_sweep.py)
Writes: figures/output/figure3.png
"""
from __future__ import annotations
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input", type=Path, default=Path("results/sweep.npz"))
    parser.add_argument("--output", type=Path,
                        default=Path("figures/output/figure3.png"))
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    data = np.load(args.input)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # --- Panel (a): tau scan ---
    ax_a = axes[0]
    tau_grid = data["tau_grid"]
    voxels = data["tau_n_voxels"]      # set by run_tau_sweep
    rmse = data["tau_rmse"]            # set by run_tau_sweep
    ax_a.plot(tau_grid, voxels, "o-", color="C0", label="Voxel count")
    ax_a.set_xlabel(r"Threshold $\tau$")
    ax_a.set_ylabel("Number of voxels", color="C0")
    ax_a.tick_params(axis="y", labelcolor="C0")
    ax_a.axvspan(0.30, 0.40, color="green", alpha=0.15)

    ax_a2 = ax_a.twinx()
    ax_a2.plot(tau_grid, rmse, "s-", color="C1", label="RMSE")
    ax_a2.set_ylabel("Elevation RMSE (m)", color="C1")
    ax_a2.tick_params(axis="y", labelcolor="C1")
    ax_a.set_title(r"(a) $\tau$ Sensitivity")

    # --- Panel (b): (alpha, beta) heatmap ---
    ax_b = axes[1]
    alpha_grid = data["alpha_grid"]
    beta_grid = data["beta_grid"]
    compression = data["ab_compression"]   # shape (len(alpha), len(beta))
    f1 = data["ab_f1"]
    im = ax_b.imshow(
        compression.T,
        origin="lower",
        extent=(alpha_grid.min(), alpha_grid.max(), beta_grid.min(), beta_grid.max()),
        aspect="auto",
        cmap="YlOrRd",
    )
    cs = ax_b.contour(
        alpha_grid, beta_grid, f1.T,
        levels=[0.60, 0.70, 0.80, 0.90], colors="k", linestyles="--",
    )
    ax_b.clabel(cs, inline=True, fmt="F1=%.2f", fontsize=9)
    ax_b.scatter([0.6], [0.3], marker="*", s=200, c="black",
                 label=r"Working point ($\alpha$=0.6, $\beta$=0.3)")
    ax_b.set_xlabel(r"$\alpha$ (Terrain weight)")
    ax_b.set_ylabel(r"$\beta$ (Semantic weight)")
    ax_b.legend(loc="upper right")
    ax_b.set_title(r"(b) ($\alpha$, $\beta$) Joint Sensitivity")
    plt.colorbar(im, ax=ax_b, label="Compression rate (%)")

    plt.tight_layout()
    plt.savefig(args.output, dpi=300, bbox_inches="tight")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
