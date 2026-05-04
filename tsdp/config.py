"""
Configuration dataclass for TSDP.

All hyper-parameters used in the paper are collected here so that
experiments can override them via CLI without touching the algorithm.
The default values reproduce the configuration reported in
"TSDP configuration" of the Methods section.
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TSDPConfig:
    # --- Subdivision threshold (Eq. 1) ---
    alpha: float = 0.6        # weight of terrain roughness term
    beta: float = 0.3         # weight of semantic importance term
    gamma: float = 0.1        # depth penalty weight (alpha + beta + gamma == 1)
    tau: float = 0.35         # subdivision threshold; subdivide when phi(V) > tau
    tau_merge: float = 0.20   # merge threshold; merge siblings when all phi < tau_merge

    # --- Level bounds ---
    L0: int = 5               # base GeoSOT-3D level (uniform grid before refinement)
    L_max: int = 9            # maximum recursion depth

    # --- Terrain roughness sub-weights (Eq. 2) ---
    w1: float = 0.7           # normalised elevation range
    w2: float = 0.2           # least-squares gradient magnitude
    w3: float = 0.1           # absolute mean curvature

    # --- Semantic importance (Eq. 3) ---
    lam: float = 0.3          # variance regulariser

    # --- Path-planning cost (Eq. 4) ---
    mu: float = 5.0           # risk multiplier
    no_fly_sentinel: float = 1e9  # cost assigned to no-fly voxels

    # --- KD-Tree adjacency ---
    adjacency_radius_factor: float = 1.6  # search radius = factor * cell diagonal

    # --- Reproducibility ---
    seed: int = 42
    n_repetitions: int = 30

    # --- Validation ---
    def __post_init__(self) -> None:
        total = self.alpha + self.beta + self.gamma
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"alpha + beta + gamma must equal 1.0; got {total:.6f}. "
                "Check Eq. (1) constraint."
            )
        if not 0.0 <= self.tau_merge < self.tau <= 1.0:
            raise ValueError(
                f"Require 0 <= tau_merge < tau <= 1; got "
                f"tau={self.tau}, tau_merge={self.tau_merge}."
            )
        if self.L_max < self.L0:
            raise ValueError(f"L_max ({self.L_max}) must be >= L0 ({self.L0}).")


# Convenience: the exact configuration reported in the paper.
PAPER_DEFAULT = TSDPConfig()


# Configurations used as baselines in the ablation
TERRAIN_AMR_BASELINE = TSDPConfig(alpha=0.9, beta=0.0, gamma=0.1)
SEMANTIC_ONLY_BASELINE = TSDPConfig(alpha=0.0, beta=0.9, gamma=0.1)
