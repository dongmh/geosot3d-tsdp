"""
Path-planning cost function (Eq. 4) and A* search wrapper.

Equation (4):
    cost(V_i, V_j) = d * (1 + mu * risk(V_j))

where:
    d : Euclidean centroid distance
    risk(V_j) : maximum semantic weight of V_j
    mu : risk multiplier (config.mu, default 5.0)

No-fly voxels receive a sentinel cost (config.no_fly_sentinel = 1e9).
"""
from __future__ import annotations
from heapq import heappush, heappop
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .config import TSDPConfig


def edge_cost(
    centroid_i: Sequence[float],
    centroid_j: Sequence[float],
    risk_j: float,
    is_no_fly_j: bool,
    config: TSDPConfig,
) -> float:
    """
    Cost of traversing from voxel i to voxel j (Eq. 4).

    Parameters
    ----------
    centroid_i, centroid_j : 2-tuple
        (x, y) coordinates in any consistent metric space.
    risk_j : float
        risk(V_j) = max semantic weight in V_j (i.e., the weight of the
        dominant occupied class).
    is_no_fly_j : bool
        If True, the cost is replaced by config.no_fly_sentinel.
    config : TSDPConfig
        Provides mu and no_fly_sentinel.
    """
    if is_no_fly_j:
        return config.no_fly_sentinel
    d = float(np.hypot(
        centroid_j[0] - centroid_i[0],
        centroid_j[1] - centroid_i[1],
    ))
    return d * (1.0 + config.mu * risk_j)


# ---------------------------------------------------------------------------
# A* search
# ---------------------------------------------------------------------------

def astar(
    centroids: np.ndarray,                 # shape (N, 2)
    adjacency: Dict[int, List[int]],
    risks: np.ndarray,                     # shape (N,) -- risk(V) for each voxel
    no_fly_mask: np.ndarray,               # shape (N,) -- bool
    start_idx: int,
    goal_idx: int,
    config: TSDPConfig,
) -> Tuple[Optional[List[int]], int]:
    """
    Standard A* with Euclidean heuristic, returning (path, expanded_nodes).

    Parameters
    ----------
    centroids : np.ndarray, shape (N, 2)
        Voxel centroids in a metric coordinate system.
    adjacency : dict mapping int -> list of int
        Symmetric adjacency graph (output of `build_adjacency`).
    risks : np.ndarray, shape (N,)
        Per-voxel risk values (max occupied semantic weight).
    no_fly_mask : np.ndarray of bool
        True where the voxel intersects a permanent no-fly zone.
    start_idx, goal_idx : int
        Indices into the voxel list.
    config : TSDPConfig

    Returns
    -------
    path : list of int or None
        Sequence of voxel indices from start to goal. None if no path exists.
    n_expanded : int
        Number of nodes popped from the open set.
    """
    if start_idx == goal_idx:
        return [start_idx], 0
    if no_fly_mask[start_idx] or no_fly_mask[goal_idx]:
        return None, 0

    open_heap: list[Tuple[float, int]] = []
    heappush(open_heap, (0.0, start_idx))

    came_from: Dict[int, int] = {}
    g_score: Dict[int, float] = {start_idx: 0.0}
    n_expanded = 0
    goal_xy = centroids[goal_idx]

    while open_heap:
        _, current = heappop(open_heap)
        n_expanded += 1

        if current == goal_idx:
            return _reconstruct_path(came_from, current), n_expanded

        for neighbour in adjacency.get(current, []):
            cost = edge_cost(
                centroids[current],
                centroids[neighbour],
                float(risks[neighbour]),
                bool(no_fly_mask[neighbour]),
                config,
            )
            tentative_g = g_score[current] + cost
            if tentative_g < g_score.get(neighbour, float("inf")):
                came_from[neighbour] = current
                g_score[neighbour] = tentative_g
                # Heuristic: Euclidean distance to goal (admissible because
                # risk multiplier >= 0 makes true cost >= Euclidean distance)
                h = float(np.hypot(
                    goal_xy[0] - centroids[neighbour][0],
                    goal_xy[1] - centroids[neighbour][1],
                ))
                heappush(open_heap, (tentative_g + h, neighbour))

    return None, n_expanded


def _reconstruct_path(came_from: Dict[int, int], end: int) -> List[int]:
    path = [end]
    while path[-1] in came_from:
        path.append(came_from[path[-1]])
    path.reverse()
    return path


# ---------------------------------------------------------------------------
# Path metrics (used by experiments to populate Table 3 / Supp Table S3)
# ---------------------------------------------------------------------------

def path_length_metres(centroids: np.ndarray, path: List[int]) -> float:
    """Total Euclidean length of a path through voxel centroids."""
    if len(path) < 2:
        return 0.0
    pts = centroids[path]
    diffs = np.diff(pts, axis=0)
    return float(np.sum(np.hypot(diffs[:, 0], diffs[:, 1])))


def mean_safety_distance(
    centroids: np.ndarray,
    path: List[int],
    obstacle_centroids: np.ndarray,
) -> float:
    """
    Mean distance from each path point to the nearest obstacle centroid.

    Used in the real-world experiment (Table 3, Mean safety column).
    """
    if len(path) == 0 or len(obstacle_centroids) == 0:
        return float("nan")
    path_pts = centroids[path]
    # Nearest obstacle for each path point
    from scipy.spatial import cKDTree
    tree = cKDTree(obstacle_centroids)
    dists, _ = tree.query(path_pts, k=1)
    return float(np.mean(dists))


def min_clearance(
    centroids: np.ndarray,
    path: List[int],
    obstacle_centroids: np.ndarray,
) -> float:
    """
    Minimum distance from any path point to any obstacle centroid.

    Used in the synthetic experiment (Supp Table S3, Min. clearance column).
    """
    if len(path) == 0 or len(obstacle_centroids) == 0:
        return float("nan")
    path_pts = centroids[path]
    from scipy.spatial import cKDTree
    tree = cKDTree(obstacle_centroids)
    dists, _ = tree.query(path_pts, k=1)
    return float(np.min(dists))
