"""
Supplementary Figure S1: GeoSOT-3D conceptual schematic.

This figure is a hand-drawn schematic, not generated from data.
The source SVG lives in `figures/static/figureS1.svg` and is exported
to JPEG via Inkscape.

Usage
-----
    python -m figures.supplementary.make_figS1

Inputs
------
    figures/static/figureS1.svg

Outputs
-------
    figures/output/figureS1.jpeg
"""
from __future__ import annotations
from pathlib import Path
import subprocess


def main() -> None:
    src = Path("figures/static/figureS1.svg")
    dst = Path("figures/output/figureS1.jpeg")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        raise FileNotFoundError(
            f"{src} not found. Add the SVG source for the DGGS schematic there."
        )
    # Inkscape 1.x CLI: --export-type=jpeg
    subprocess.run([
        "inkscape", str(src),
        "--export-type=jpeg",
        f"--export-filename={dst}",
        "--export-dpi=300",
    ], check=True)
    print(f"Wrote {dst}")


if __name__ == "__main__":
    main()
