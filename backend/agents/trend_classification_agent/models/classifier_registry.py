"""
Classifier Registry for Trend Classification Agent.

Provides model versioning and storage for classifiers.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class ClassifierRegistry:
    """
    Registry for trend classification models.

    Features:
    - Save trained classifiers with metadata
    - Load latest or specific version
    - Track model performance
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize Classifier Registry.

        Args:
            base_path: Base directory for model storage
        """
        if base_path is None:
            base_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "saved_models"
            )

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.index_file = self.base_path / "classifier_index.json"
        self._load_index()

    def _load_index(self) -> None:
        """Load or create registry index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    self.index = json.load(f)
            except Exception:
                self.index = {}
        else:
            self.index = {}

    def _save_index(self) -> None:
        """Save registry index."""
        try:
            with open(self.index_file, "w") as f:
                json.dump(self.index, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def _get_next_version(self, model_key: str) -> str:
        """Get next version number."""
        if model_key not in self.index:
            return "1.0.0"

        versions = self.index[model_key].get("versions", [])
        if not versions:
            return "1.0.0"

        latest = versions[-1]["version"]
        parts = latest.split(".")
        try:
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{major}.{minor}.{patch + 1}"
        except (ValueError, IndexError):
            return f"{len(versions) + 1}.0.0"

    def save_model(
        self,
        model: Any,
        name: str,
        symbol: str,
        timeframe: str,
        model_type: str,
        metrics: Dict[str, float],
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save a trained classifier to the registry.

        Args:
            model: Classifier object with save() method
            name: Model name (e.g., "lightgbm", "xgboost")
            symbol: Stock symbol
            timeframe: Timeframe ("1h" or "1d")
            model_type: Type of classifier
            metrics: Training/validation metrics
            version: Optional specific version

        Returns:
            Save result with version info
        """
        try:
            model_key = f"{name}_{symbol}_{timeframe}"

            if version is None:
                version = self._get_next_version(model_key)

            model_dir = self.base_path / model_key / version
            model_dir.mkdir(parents=True, exist_ok=True)

            model_file = model_dir / "model"
            if hasattr(model, "save"):
                model.save(str(model_file))
            else:
                import joblib
                joblib.dump(model, str(model_file) + ".joblib")

            metadata = {
                "name": name,
                "symbol": symbol,
                "timeframe": timeframe,
                "model_type": model_type,
                "version": version,
                "metrics": metrics,
                "created_at": datetime.now().isoformat(),
            }

            with open(model_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

            if model_key not in self.index:
                self.index[model_key] = {
                    "name": name,
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "model_type": model_type,
                    "versions": [],
                    "latest": None,
                }

            self.index[model_key]["versions"].append({
                "version": version,
                "metrics": metrics,
                "created_at": datetime.now().isoformat(),
            })
            self.index[model_key]["latest"] = version
            self._save_index()

            logger.info(f"Saved classifier {model_key} v{version}")

            return {
                "success": True,
                "model_key": model_key,
                "version": version,
                "path": str(model_dir),
            }

        except Exception as e:
            logger.error(f"Failed to save classifier: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def load_model(
        self,
        name: str,
        symbol: str,
        timeframe: str,
        model_class: type,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Load a classifier from the registry.

        Args:
            name: Model name
            symbol: Stock symbol
            timeframe: Timeframe
            model_class: Class to instantiate
            version: Version to load

        Returns:
            Dict with loaded model and metadata
        """
        try:
            model_key = f"{name}_{symbol}_{timeframe}"

            if model_key not in self.index:
                return {
                    "success": False,
                    "error": f"Model {model_key} not found"
                }

            if version == "latest":
                version = self.index[model_key].get("latest")
                if not version:
                    return {
                        "success": False,
                        "error": "No versions available"
                    }

            model_dir = self.base_path / model_key / version
            if not model_dir.exists():
                return {
                    "success": False,
                    "error": f"Version {version} not found"
                }

            with open(model_dir / "metadata.json", "r") as f:
                metadata = json.load(f)

            model = model_class()
            model_file = model_dir / "model"
            model.load(str(model_file))

            logger.info(f"Loaded classifier {model_key} v{version}")

            return {
                "success": True,
                "model": model,
                "metadata": metadata,
                "version": version,
            }

        except Exception as e:
            logger.error(f"Failed to load classifier: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_info(self, name: str, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Get information about a registered classifier."""
        model_key = f"{name}_{symbol}_{timeframe}"

        if model_key not in self.index:
            return {
                "success": False,
                "error": f"Model {model_key} not found"
            }

        return {
            "success": True,
            "model_key": model_key,
            **self.index[model_key]
        }

    def list_models(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all registered classifiers."""
        models = []

        for model_key, info in self.index.items():
            if symbol and info.get("symbol") != symbol:
                continue
            if timeframe and info.get("timeframe") != timeframe:
                continue

            models.append({
                "model_key": model_key,
                "name": info.get("name"),
                "symbol": info.get("symbol"),
                "timeframe": info.get("timeframe"),
                "latest_version": info.get("latest"),
                "version_count": len(info.get("versions", [])),
            })

        return models

    def get_best_model(
        self,
        name: str,
        symbol: str,
        timeframe: str,
        metric: str = "accuracy"
    ) -> Optional[str]:
        """Get version with best performance on a metric."""
        model_key = f"{name}_{symbol}_{timeframe}"

        if model_key not in self.index:
            return None

        versions = self.index[model_key].get("versions", [])
        if not versions:
            return None

        valid_versions = [
            v for v in versions
            if metric in v.get("metrics", {})
        ]

        if not valid_versions:
            return versions[-1]["version"]

        sorted_versions = sorted(
            valid_versions,
            key=lambda v: v["metrics"][metric],
            reverse=True  # Higher is better for accuracy
        )

        return sorted_versions[0]["version"]
