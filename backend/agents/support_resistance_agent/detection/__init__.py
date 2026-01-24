"""
Detection module for Support/Resistance Agent.

This module contains algorithms for:
- Extrema detection (finding peaks and valleys) - using scipy.signal.argrelextrema
- DBSCAN clustering (grouping similar price levels)
- Level validation (checking historical price reactions)
- Volume profile analysis (identifying high-volume price nodes)
"""

from .extrema_detection import ExtremaDetector
from .dbscan_clustering import DBSCANClusterer
from .level_validator import LevelValidator
from .volume_profile import VolumeProfileAnalyzer

__all__ = [
    "ExtremaDetector",
    "DBSCANClusterer",
    "LevelValidator",
    "VolumeProfileAnalyzer",
]
