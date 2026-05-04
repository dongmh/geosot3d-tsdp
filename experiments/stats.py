"""
Statistical tests used for significance reporting in Tables 2 and 3.

We use:
    1. Shapiro-Wilk to test per-metric normality across the 30 repetitions.
       Result: normality is rejected for all metrics (W < 0.95, p < 0.05),
       which motivates non-parametric tests.
    2. Wilcoxon signed-rank test for paired (per-seed) comparisons between
       methods. Reported p-values use this test throughout.

Usage
-----
    python -m experiments.stats --input results/xian.csv \
                                --reference TSDP \
                                --output results/xian_pvalues.csv
"""
from __future__ import annotations
import argparse
import csv
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy import stats


METRICS_TO_TEST = [
    "rmse_m", "building_f1", "n_voxels", "plan_time_s",
    "expanded_nodes", "mean_safety_m",
]


def load_results(path: Path) -> Dict[str, Dict[str, np.ndarray]]:
    """Read CSV and return {method: {metric: array of values}}."""
    out: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    with path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = row["method"]
            for metric in METRICS_TO_TEST:
                if metric in row:
                    try:
                        out[method][metric].append(float(row[metric]))
                    except (ValueError, TypeError):
                        out[method][metric].append(np.nan)
    return {m: {k: np.array(v) for k, v in d.items()} for m, d in out.items()}


def shapiro_wilk_per_metric(data: Dict[str, Dict[str, np.ndarray]]
                            ) -> List[Tuple[str, str, float, float]]:
    """For each (method, metric), run Shapiro-Wilk."""
    results = []
    for method, metric_dict in data.items():
        for metric, values in metric_dict.items():
            v = values[~np.isnan(values)]
            if len(v) < 3:
                continue
            W, p = stats.shapiro(v)
            results.append((method, metric, float(W), float(p)))
    return results


def wilcoxon_pairwise(
    data: Dict[str, Dict[str, np.ndarray]],
    reference: str,
) -> List[Tuple[str, str, str, float]]:
    """
    Wilcoxon signed-rank test of each method vs `reference`, per metric.

    Returns a list of (method, reference, metric, p_value).
    Pairs are matched by repetition order (assumes the CSV has identical
    rep_seed sequences across methods, which is true if the CSV was
    produced by `synthetic.py` or `xian.py` with the same --seed).
    """
    if reference not in data:
        raise KeyError(f"Reference method {reference!r} not in data.")

    out = []
    ref = data[reference]
    for method, metric_dict in data.items():
        if method == reference:
            continue
        for metric, values_method in metric_dict.items():
            values_ref = ref.get(metric)
            if values_ref is None or values_ref.size != values_method.size:
                continue
            # Drop pairs where either is NaN
            mask = ~(np.isnan(values_ref) | np.isnan(values_method))
            if mask.sum() < 5:
                continue
            try:
                _, p = stats.wilcoxon(values_method[mask], values_ref[mask])
            except ValueError:
                p = float("nan")
            out.append((method, reference, metric, float(p)))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--reference", type=str, default="TSDP")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    data = load_results(args.input)

    sw = shapiro_wilk_per_metric(data)
    wx = wilcoxon_pairwise(data, args.reference)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as f:
        f.write("# Shapiro-Wilk test (per method, per metric)\n")
        f.write("method,metric,W,p_shapiro\n")
        for row in sw:
            f.write(",".join(str(x) for x in row) + "\n")
        f.write("\n# Wilcoxon signed-rank test (method vs reference)\n")
        f.write("method,reference,metric,p_wilcoxon\n")
        for row in wx:
            f.write(",".join(str(x) for x in row) + "\n")

    print(f"Wrote statistical results to {args.output}")


if __name__ == "__main__":
    main()
