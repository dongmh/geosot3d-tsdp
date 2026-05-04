"""
Decision function Phi(V) — Equation (1) of the paper.

    Phi(V) = alpha * R(V)/R_max + beta * S(V)/S_max + gamma * (1 - l/L_max)

This module is intentionally minimal: it implements only the local
greedy decision rule. The R(V) and S(V) values are computed elsewhere
(see feature_metrics.py).
"""
from __future__ import annotations
import numpy as np
from .config import TSDPConfig


def phi(
    R: float,
    S: float,
    level: int,
    R_max: float,
    S_max: float,
    config: TSDPConfig,
) -> float:
    """
    Evaluate Phi(V) for a single voxel.

    Parameters
    ----------
    R : float
        Terrain-roughness score for the voxel; output of `terrain_roughness`.
    S : float
        Semantic-importance score; output of `semantic_importance`.
    level : int
        Current GeoSOT-3D subdivision level l of the voxel.
    R_max : float
        95th-percentile R across G_0 (the base uniform grid).
    S_max : float
        95th-percentile S across G_0.
    config : TSDPConfig
        Hyper-parameter container; alpha, beta, gamma, L_max are read from here.

    Returns
    -------
    phi_value : float
        The decision value; voxel is subdivided when phi_value > config.tau.

    Notes
    -----
    The 95th-percentile normalisation (R_max, S_max) is computed once over
    G_0 and held constant during refinement. This avoids the chicken-and-egg
    problem of normalising against a moving distribution.

    The depth-penalty term (1 - l/L_max) is an empirical regulariser; see
    the "Approximation regime" paragraph of the Methods.
    """
    # Avoid division by zero on degenerate inputs (e.g., perfectly flat synthetic terrain)
    R_norm = R / R_max if R_max > 0 else 0.0
    S_norm = S / S_max if S_max > 0 else 0.0
    depth_term = 1.0 - level / config.L_max

    return (
        config.alpha * R_norm
        + config.beta * S_norm
        + config.gamma * depth_term
    )


def phi_batch(
    R: np.ndarray,
    S: np.ndarray,
    levels: np.ndarray,
    R_max: float,
    S_max: float,
    config: TSDPConfig,
) -> np.ndarray:
    """Vectorised version of `phi` for an entire G_0."""
    R_norm = np.where(R_max > 0, R / R_max, 0.0)
    S_norm = np.where(S_max > 0, S / S_max, 0.0)
    depth_term = 1.0 - levels / config.L_max
    return config.alpha * R_norm + config.beta * S_norm + config.gamma * depth_term
