"""
GeoSOT-3D TSDP — Terrain-Semantic Dual-driven Partitioning.

Reference implementation of the algorithm described in:
    Wang, Liu & Zhao (2026), "Adaptive spatial partitioning under the
    GeoSOT-3D global grid for efficient low-altitude environment modeling",
    Scientific Reports.

Public API
----------
TSDPConfig : dataclass holding all hyper-parameters
ts_adaptive_subdivide : main top-level entry point (Fig. 1 of the paper)
"""
from .config import TSDPConfig
from .adaptive_subdivide import ts_adaptive_subdivide
from .decision_function import phi
from .feature_metrics import terrain_roughness, semantic_importance

__version__ = "1.0.0"
__all__ = [
    "TSDPConfig",
    "ts_adaptive_subdivide",
    "phi",
    "terrain_roughness",
    "semantic_importance",
]
