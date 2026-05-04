"""
TS-AdaptiveSubdivide algorithm — top-down subdivision + bottom-up merging.

Faithful translation of Fig. 1 of the paper. Uses the symbols introduced
in the Methods/TS-AdaptiveSubdivide algorithm subsection:

    Q : working queue of voxels awaiting evaluation
    C : candidate terminal-voxel set accumulated during top-down pass
    G* : final dynamic subdivision grid (the algorithm output)
    Phi(V) : decision function (Eq. 1)
    GeoSOT_Subdivide(V) : split operation (geosot3d.subdivide)
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Set, Tuple

import numpy as np

from .config import TSDPConfig
from .decision_function import phi
from .feature_metrics import terrain_roughness, semantic_importance
from .geosot3d import Voxel, subdivide, parent, siblings, cell_diagonal_metres


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class TSDPResult:
    """Output of `ts_adaptive_subdivide`."""
    terminals: List[Voxel]               # G*: final terminal voxels
    phi_values: Dict[Voxel, float]       # Phi(V) computed during top-down
    levels_histogram: Dict[int, int]     # count per level
    n_subdivisions: int                  # number of GeoSOT_Subdivide calls
    n_merges: int                        # number of successful merges


# Type alias for environment-query callbacks. Caller supplies these:
ElevationQuery = Callable[[Voxel], np.ndarray]                # voxel -> DEM patch
SemanticQuery  = Callable[[Voxel], Tuple[List[int], List[float]]]  # -> (occupancy, weights)
LabelQuery     = Callable[[Voxel], int]                       # voxel -> dominant class id


def ts_adaptive_subdivide(
    initial_grid: Iterable[Voxel],
    *,
    elevation_query: ElevationQuery,
    semantic_query: SemanticQuery,
    label_query: LabelQuery,
    config: TSDPConfig,
) -> TSDPResult:
    """
    Run the full TS-AdaptiveSubdivide algorithm (Fig. 1).

    Parameters
    ----------
    initial_grid : iterable of Voxel
        G_0: the uniform base grid at level config.L0 covering the study area.
    elevation_query : callable
        Maps a voxel to its elevation patch from the DEM.
    semantic_query : callable
        Maps a voxel to (occupancy, weights) lists for Eq. (3).
    label_query : callable
        Maps a voxel to its dominant semantic class id (used for merge consistency).
    config : TSDPConfig
        Hyper-parameters.

    Returns
    -------
    result : TSDPResult
    """
    G0 = list(initial_grid)
    if not G0:
        raise ValueError("initial_grid is empty.")

    # Step (i): compute R_max, S_max as 95th-percentile across G_0.
    R_max, S_max = _compute_normalisation_constants(
        G0, elevation_query, semantic_query, config
    )

    # ---- Top-down phase ----
    Q: deque[Voxel] = deque(G0)
    C: List[Voxel] = []
    phi_cache: Dict[Voxel, float] = {}
    n_subdivisions = 0

    while Q:
        V = Q.popleft()

        elev = elevation_query(V)
        occ, w = semantic_query(V)
        R = terrain_roughness(elev, cell_diagonal_metres(V), config)
        S = semantic_importance(occ, w, config)
        phi_V = phi(R, S, V.level, R_max, S_max, config)
        phi_cache[V] = phi_V

        if phi_V > config.tau and V.level < config.L_max:
            for child in subdivide(V):
                Q.append(child)
            n_subdivisions += 1
        else:
            # Mark V as a terminal-state element
            C.append(V)

    # ---- Bottom-up merge phase ----
    # Process C from deepest level upwards; merge a sibling group of 4 if all
    # of them satisfy phi < tau_merge AND share the same dominant label.
    n_merges = 0
    C_set: Set[Voxel] = set(C)

    # Group voxels by level; iterate from deepest to shallowest
    by_level: Dict[int, List[Voxel]] = {}
    for v in C:
        by_level.setdefault(v.level, []).append(v)

    for level in sorted(by_level.keys(), reverse=True):
        if level == config.L0:
            break  # cannot merge above L0

        # Group by parent
        candidates_by_parent: Dict[Voxel, List[Voxel]] = {}
        for v in list(C_set):
            if v.level != level:
                continue
            p = parent(v)
            candidates_by_parent.setdefault(p, []).append(v)

        for p, sibs in candidates_by_parent.items():
            full_siblings = set(siblings(sibs[0]))
            if not full_siblings.issubset(C_set):
                continue  # not all four siblings are terminal yet
            # Check phi < tau_merge for all
            if not all(phi_cache.get(s, float("inf")) < config.tau_merge
                       for s in full_siblings):
                continue
            # Check label consistency
            labels = {label_query(s) for s in full_siblings}
            if len(labels) != 1:
                continue
            # Merge: remove siblings from C_set, add parent
            for s in full_siblings:
                C_set.discard(s)
            C_set.add(p)
            phi_cache[p] = max(phi_cache[s] for s in full_siblings)
            n_merges += 1

    terminals = sorted(C_set, key=lambda v: (v.level, v.lon_idx, v.lat_idx))
    levels_histogram: Dict[int, int] = {}
    for v in terminals:
        levels_histogram[v.level] = levels_histogram.get(v.level, 0) + 1

    return TSDPResult(
        terminals=terminals,
        phi_values=phi_cache,
        levels_histogram=levels_histogram,
        n_subdivisions=n_subdivisions,
        n_merges=n_merges,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_normalisation_constants(
    G0: List[Voxel],
    elevation_query: ElevationQuery,
    semantic_query: SemanticQuery,
    config: TSDPConfig,
) -> Tuple[float, float]:
    """
    Compute R_max and S_max as 95th-percentile values across G_0.

    Held constant during the top-down phase (see `phi` docstring for rationale).
    """
    R_values = np.empty(len(G0))
    S_values = np.empty(len(G0))
    for i, v in enumerate(G0):
        elev = elevation_query(v)
        occ, w = semantic_query(v)
        R_values[i] = terrain_roughness(elev, cell_diagonal_metres(v), config)
        S_values[i] = semantic_importance(occ, w, config)
    R_max = float(np.percentile(R_values, 95)) if R_values.size else 1.0
    S_max = float(np.percentile(S_values, 95)) if S_values.size else 1.0
    # Guard against degenerate (all-zero) cases
    return max(R_max, 1e-9), max(S_max, 1e-9)
