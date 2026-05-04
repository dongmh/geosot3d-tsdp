"""
Feature metrics: terrain roughness R(V) and semantic importance S(V).

Implements equations (2) and (3) of the paper.

    R(V) = w1 * (Delta H / D) + w2 * ||grad H|| + w3 * |kappa|       (Eq. 2)
    S(V) = max_k (O_k * W_k) + lambda * sqrt[ (1/M) * sum_k (O_k * (W_k - W_bar))^2 ]   (Eq. 3)
"""
from __future__ import annotations
from typing import Dict, Sequence
import numpy as np
from .config import TSDPConfig


# ---------------------------------------------------------------------------
# Equation (2): terrain roughness
# ---------------------------------------------------------------------------

def terrain_roughness(
    elevation_patch: np.ndarray,
    cell_diagonal_m: float,
    config: TSDPConfig,
) -> float:
    """
    Compute R(V) for a single voxel from its DEM elevation patch.

    Parameters
    ----------
    elevation_patch : np.ndarray, shape (H, W)
        Elevation samples of GDEM (or equivalent) within the voxel footprint,
        in metres. Must contain at least 3x3 samples for curvature fitting.
    cell_diagonal_m : float
        Length D of the voxel's horizontal diagonal, in metres.
    config : TSDPConfig
        Provides w1, w2, w3.

    Returns
    -------
    R : float
        Terrain-roughness score (non-negative, unitless after w-weighting).

    Implementation notes
    --------------------
    - Delta H: max - min over the patch
    - ||grad H||: magnitude of least-squares-fit gradient (single scalar)
    - |kappa|: absolute mean curvature from a quadric surface fit
    """
    if elevation_patch.size < 9:
        # Degenerate (sub-3x3) patch; treat as flat
        return 0.0

    # Term 1: normalised elevation range
    delta_H = float(np.nanmax(elevation_patch) - np.nanmin(elevation_patch))
    term1 = delta_H / cell_diagonal_m if cell_diagonal_m > 0 else 0.0

    # Term 2: least-squares gradient magnitude
    grad_norm = _gradient_magnitude_lsq(elevation_patch, cell_diagonal_m)

    # Term 3: absolute mean curvature from quadric fit
    abs_curvature = _abs_mean_curvature_quadric(elevation_patch, cell_diagonal_m)

    return (
        config.w1 * term1
        + config.w2 * grad_norm
        + config.w3 * abs_curvature
    )


def _gradient_magnitude_lsq(
    elevation: np.ndarray, cell_diagonal_m: float
) -> float:
    """
    Fit a plane H = a*x + b*y + c via least squares and return ||(a, b)||.

    The grid is assumed to be regularly sampled along the voxel footprint.
    """
    # TODO: implement using np.linalg.lstsq on a flattened (x, y, H) design matrix.
    # Reference implementation (replace stub when validating against paper data):
    raise NotImplementedError(
        "Implement least-squares plane fit. See Methods/Feature metrics."
    )


def _abs_mean_curvature_quadric(
    elevation: np.ndarray, cell_diagonal_m: float
) -> float:
    """
    Fit a quadric H = a*x^2 + b*y^2 + c*xy + d*x + e*y + f and return
    |mean curvature| = |(a + b)| / 2 (under the small-slope approximation).
    """
    # TODO: implement quadric LSQ fit; return |a + b| / 2.
    raise NotImplementedError(
        "Implement quadric surface fit for curvature; see Methods/Feature metrics."
    )


# ---------------------------------------------------------------------------
# Equation (3): semantic importance
# ---------------------------------------------------------------------------

def semantic_importance(
    occupancy: Sequence[int],
    weights: Sequence[float],
    config: TSDPConfig,
) -> float:
    """
    Compute S(V) for a single voxel.

    Parameters
    ----------
    occupancy : sequence of {0, 1}, length M
        O_k indicators: whether class k is present in the voxel.
    weights : sequence of float, length M
        W_k domain weights (see Table 1 of the paper).
    config : TSDPConfig
        Provides lambda (lam).

    Returns
    -------
    S : float
        Semantic-importance score.

    Notes
    -----
    W_bar is computed as the unconditional mean of weights (over all M classes,
    not just occupied ones), as documented in the Methods.
    """
    O = np.asarray(occupancy, dtype=float)
    W = np.asarray(weights, dtype=float)
    if O.shape != W.shape:
        raise ValueError(
            f"occupancy and weights must have same length; got {O.shape} and {W.shape}"
        )
    if O.size == 0:
        return 0.0

    # First term: max_k (O_k * W_k)  --- the dominant occupied class
    max_term = float(np.max(O * W))

    # Second term: variance regulariser
    M = len(W)
    W_bar = float(np.mean(W))
    variance_term = float(np.sqrt(np.mean((O * (W - W_bar)) ** 2)))

    return max_term + config.lam * variance_term
