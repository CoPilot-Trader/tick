"""
API Routes for TICK Backend.
"""

from .data import router as data_router
from .features import router as features_router

__all__ = ["data_router", "features_router"]




