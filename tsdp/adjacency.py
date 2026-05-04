"""
Adjacency graph construction over terminal voxels.

Per the Methods section: adjacency uses a KD-Tree on terminal centroids
with search radius 1.6 * cell diagonal, followed by symmetrisation
(if A is in B's neighbour list, B is added to A's list).

The resulting undirected graph is the input to the A* path planner.
"""
from __future__ import annotations
from typing import Dict, List, Tuple

import numpy as np
from scipy.spatial import cKDTree

from .config import TSDPConfig
from .geosot3d import Voxel, cell_diagonal_metres


def build_adjacency(
    voxels: List[Voxel],
    config: TSDPConfig,
) -> Tuple[np.ndarray, Dict[int, List[int]]]:
    """
    Build a symmetric adjacency graph over the terminal voxels.

    Parameters
    ----------
    voxels : list of Voxel
        The terminal voxels of G* (output of `ts_adaptive_subdivide`).
    config : TSDPConfig
        Provides adjacency_radius_factor.

    Returns
    -------
    centroids : np.ndarray, shape (N, 2)
        Centroid coordinates in (lon, lat) degrees, indexed by voxel order.
    adjacency : dict mapping int -> list of int
        For each voxel index i, a list of neighbour indices j (i in adj[j] iff
        j in adj[i]). Self-loops are excluded.
    """
    N = len(voxels)
    if N == 0:
        return np.empty((0, 2)), {}

    # Convert each voxel to a centroid in metres for distance queries
    # (degree-space queries are anisotropic and would distort radii)
    centroids_deg = np.empty((N, 2))
    for i, v in enumerate(voxels):
        lon_min, lat_min, lon_max, lat_max = v.bbox_deg()
        centroids_deg[i] = ((lon_min + lon_max) / 2.0, (lat_min + lat_max) / 2.0)

    # Project to local metric tangent plane around the dataset centroid
    centroid_lat = float(np.mean(centroids_deg[:, 1]))
    centroids_m = _to_local_metres(centroids_deg, centroid_lat)

    # Per-voxel search radius (1.6 * cell diagonal)
    radii = np.array([
        config.adjacency_radius_factor * cell_diagonal_metres(v) for v in voxels
    ])

    # KD-Tree query (use the largest radius and filter per-voxel afterwards)
    tree = cKDTree(centroids_m)
    max_radius = float(np.max(radii))
    raw_neighbours = tree.query_ball_tree(tree, r=max_radius)

    # Filter by per-voxel radius (asymmetric pre-symmetrisation)
    adjacency: Dict[int, List[int]] = {}
    for i, candidates in enumerate(raw_neighbours):
        kept = [
            j for j in candidates
            if j != i
            and np.linalg.norm(centroids_m[i] - centroids_m[j]) <= radii[i]
        ]
        adjacency[i] = kept

    # Symmetrise: if j in adj[i] but i not in adj[j], add it.
    for i in range(N):
        for j in adjacency[i]:
            if i not in adjacency[j]:
                adjacency[j].append(i)

    return centroids_deg, adjacency


def _to_local_metres(coords_deg: np.ndarray, centre_lat_deg: float) -> np.ndarray:
    """
    Crude equirectangular projection around a centre latitude.

    Adequate for adjacency queries within a single city-scale study area
    (~14 km in our experiments). For continental-scale applications, switch
    to a proper UTM or LCC projection via pyproj.
    """
    R = 111_320.0
    centre_rad = np.radians(centre_lat_deg)
    out = np.empty_like(coords_deg)
    out[:, 0] = coords_deg[:, 0] * R * np.cos(centre_rad)
    out[:, 1] = coords_deg[:, 1] * R
    return out
