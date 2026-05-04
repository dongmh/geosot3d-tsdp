"""
GeoSOT-3D encoding utilities.

The GeoSOT-3D scheme recursively subdivides longitude, latitude, and altitude
extents by 2 at each level. Cell identity is encoded as an integer Morton-style
interleaving of bit indices along each axis.

This module provides the minimum operations required by the partitioning
algorithm:
    - level_to_cell_size: side length at a given level
    - subdivide(V): split a voxel into 4 horizontal children at level l+1
    - encode / decode: integer code <-> (lon_idx, lat_idx, alt_idx, level)

References
----------
Song, S. et al. (2014). GeoSOT grid for global remote sensing data.
Acta Geod. Cartogr. Sin. 43, 869-876.

Notes
-----
This is a planar quadtree implementation (horizontal subdivision only).
Octree extension for full 3D partitioning is on the roadmap; see Issue #1.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import math


# --- Constants ---
# Level 0 covers a 512deg x 512deg pseudo-extent (the GeoSOT global frame is
# defined on a doubled domain to allow integer subdivision; physical extent
# is 0..180 lat, -180..180 lon). See Song et al. 2014.
GEOSOT_BASE_DEG = 512.0


@dataclass(frozen=True)
class Voxel:
    """
    A GeoSOT-3D voxel identified by (level, lon_idx, lat_idx).

    For the planar quadtree implementation we omit the alt_idx; elevation is
    stored as a per-voxel attribute, not as a 3rd axis of the index.

    Attributes
    ----------
    level : int
        Subdivision level l (>= 0).
    lon_idx : int
        Longitude bin index at this level. Range [0, 2**level).
    lat_idx : int
        Latitude bin index at this level. Range [0, 2**level).
    """
    level: int
    lon_idx: int
    lat_idx: int

    def cell_size_deg(self) -> float:
        """Side length of the voxel in degrees (longitude == latitude here)."""
        return GEOSOT_BASE_DEG / (2 ** self.level)

    def bbox_deg(self) -> Tuple[float, float, float, float]:
        """
        Geographic bounding box (lon_min, lat_min, lon_max, lat_max), in degrees.

        Origin convention: (lon_idx=0, lat_idx=0) is the south-west corner of
        the GeoSOT global frame.
        """
        size = self.cell_size_deg()
        # Map back to physical coordinates: longitude in [-180, 180), lat in [-90, 90)
        # The GeoSOT 512-deg domain places (0,0) at (-256, -256); the physical
        # grid is the central [-180, 180) x [-90, 90) sub-region.
        lon_min = -256.0 + self.lon_idx * size
        lat_min = -256.0 + self.lat_idx * size
        return (lon_min, lat_min, lon_min + size, lat_min + size)


def subdivide(v: Voxel) -> Tuple[Voxel, Voxel, Voxel, Voxel]:
    """
    Standard GeoSOT-3D split operation.

    Produces 4 children at level l+1 by halving the longitude and latitude
    extents. Children are returned in (SW, SE, NW, NE) order.

    Corresponds to GeoSOT_Subdivide(V) in Fig. 1 of the paper.
    """
    new_level = v.level + 1
    base_lon = v.lon_idx * 2
    base_lat = v.lat_idx * 2
    return (
        Voxel(new_level, base_lon,     base_lat),       # SW
        Voxel(new_level, base_lon + 1, base_lat),       # SE
        Voxel(new_level, base_lon,     base_lat + 1),   # NW
        Voxel(new_level, base_lon + 1, base_lat + 1),   # NE
    )


def parent(v: Voxel) -> Voxel:
    """Return the parent voxel at level l-1."""
    if v.level == 0:
        raise ValueError("Voxel at level 0 has no parent.")
    return Voxel(v.level - 1, v.lon_idx // 2, v.lat_idx // 2)


def siblings(v: Voxel) -> Tuple[Voxel, Voxel, Voxel, Voxel]:
    """Return the 4 children of v's parent (i.e., v and its 3 siblings)."""
    return subdivide(parent(v))


def cell_diagonal_metres(v: Voxel) -> float:
    """
    Approximate the voxel's horizontal diagonal in metres, evaluated at its
    centroid latitude. Used by terrain_roughness to normalise elevation range.

    Uses the small-cell approximation:
        1 deg latitude ~= 111_320 m
        1 deg longitude ~= 111_320 * cos(lat) m
    """
    lon_min, lat_min, lon_max, lat_max = v.bbox_deg()
    centroid_lat_rad = math.radians((lat_min + lat_max) / 2.0)
    dlat_m = (lat_max - lat_min) * 111_320.0
    dlon_m = (lon_max - lon_min) * 111_320.0 * math.cos(centroid_lat_rad)
    return math.hypot(dlon_m, dlat_m)


def encode(v: Voxel) -> int:
    """
    Encode (level, lon_idx, lat_idx) into a single integer code via bit
    interleaving (Morton order). Useful for hashing and storage.

    Bit layout (least to most significant):
        - 6 bits for level (supports up to L_max = 63)
        - alternating lon/lat bits, 2*level bits total
    """
    if v.level < 0 or v.level >= 64:
        raise ValueError(f"Level {v.level} out of supported range [0, 63].")
    code = v.level & 0x3F  # 6 bits for level
    for i in range(v.level):
        code |= ((v.lon_idx >> i) & 1) << (6 + 2 * i)
        code |= ((v.lat_idx >> i) & 1) << (6 + 2 * i + 1)
    return code


def decode(code: int) -> Voxel:
    """Inverse of `encode`."""
    level = code & 0x3F
    lon_idx = 0
    lat_idx = 0
    for i in range(level):
        lon_idx |= ((code >> (6 + 2 * i)) & 1) << i
        lat_idx |= ((code >> (6 + 2 * i + 1)) & 1) << i
    return Voxel(level, lon_idx, lat_idx)
