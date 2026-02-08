"""
Trend Classification Agent Models.

This module provides:
- LightGBMClassifier: Gradient boosting classifier
- XGBoostClassifier: Alternative gradient boosting
- ClassifierRegistry: Model versioning
"""

from .lightgbm_classifier import LightGBMClassifier
from .xgboost_classifier import XGBoostClassifier
from .classifier_registry import ClassifierRegistry

__all__ = [
    "LightGBMClassifier",
    "XGBoostClassifier",
    "ClassifierRegistry",
]
