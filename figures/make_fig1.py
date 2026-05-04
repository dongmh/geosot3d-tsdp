"""
Figure 1: TS-AdaptiveSubdivide algorithm flowchart.

This figure is a static schematic, not generated from experiment data.
Edit the source SVG/Graphviz file in `figures/static/figure1.gv` and
re-export to PNG with:
    dot -Tpng figures/static/figure1.gv -o figures/output/figure1.png
"""
from __future__ import annotations
from pathlib import Path
import subprocess


def main() -> None:
    src = Path("figures/static/figure1.gv")
    dst = Path("figures/output/figure1.png")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        raise FileNotFoundError(
            f"{src} not found. Add the Graphviz source for the flowchart there."
        )
    subprocess.run(["dot", "-Tpng", str(src), "-o", str(dst)], check=True)
    print(f"Wrote {dst}")


if __name__ == "__main__":
    main()
