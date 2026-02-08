"""
Model Registry for Price Forecast Agent.

Provides:
- Model versioning and storage
- Model metadata tracking
- Performance metrics history
- Model deployment management
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Simple model registry for versioning and deployment.

    Features:
    - Save trained models with metadata
    - Load latest or specific version
    - Track model performance over time
    - Manage model lifecycle
    """

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize Model Registry.

        Args:
            base_path: Base directory for model storage
        """
        if base_path is None:
            # Default to models directory in project
            base_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "saved_models"
            )

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        # Registry index file
        self.index_file = self.base_path / "registry_index.json"
        self._load_index()

    def _load_index(self) -> None:
        """Load or create registry index."""
        if self.index_file.exists():
            try:
                with open(self.index_file, "r") as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load index: {e}")
                self.index = {}
        else:
            self.index = {}

    def _save_index(self) -> None:
        """Save registry index to file."""
        try:
            with open(self.index_file, "w") as f:
                json.dump(self.index, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")

    def _get_next_version(self, model_name: str) -> str:
        """Get next version number for a model."""
        if model_name not in self.index:
            return "1.0.0"

        versions = self.index[model_name].get("versions", [])
        if not versions:
            return "1.0.0"

        # Parse latest version and increment
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
        model_type: str,
        metrics: Dict[str, float],
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save a trained model to the registry.

        Args:
            model: Model object with save() method
            name: Model name (e.g., "prophet", "lstm")
            symbol: Stock symbol the model is trained for
            model_type: Type of model ("prophet", "lstm")
            metrics: Training/validation metrics
            version: Optional specific version (auto-increments if None)
            metadata: Additional metadata to store

        Returns:
            Save result with version info
        """
        try:
            # Generate model key (name + symbol)
            model_key = f"{name}_{symbol}"

            # Get version
            if version is None:
                version = self._get_next_version(model_key)

            # Create model directory
            model_dir = self.base_path / model_key / version
            model_dir.mkdir(parents=True, exist_ok=True)

            # Save model file
            model_file = model_dir / "model"
            if hasattr(model, "save"):
                model.save(str(model_file))
            else:
                import joblib
                joblib.dump(model, str(model_file) + ".joblib")

            # Create metadata
            model_metadata = {
                "name": name,
                "symbol": symbol,
                "model_type": model_type,
                "version": version,
                "metrics": metrics,
                "created_at": datetime.now().isoformat(),
                "metadata": metadata or {},
            }

            # Save metadata
            with open(model_dir / "metadata.json", "w") as f:
                json.dump(model_metadata, f, indent=2, default=str)

            # Update index
            if model_key not in self.index:
                self.index[model_key] = {
                    "name": name,
                    "symbol": symbol,
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

            logger.info(f"Saved model {model_key} v{version}")

            return {
                "success": True,
                "model_key": model_key,
                "version": version,
                "path": str(model_dir),
            }

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def load_model(
        self,
        name: str,
        symbol: str,
        model_class: type,
        version: str = "latest"
    ) -> Dict[str, Any]:
        """
        Load a model from the registry.

        Args:
            name: Model name (e.g., "prophet", "lstm")
            symbol: Stock symbol
            model_class: Class to instantiate (with load() method)
            version: Version to load ("latest" or specific version)

        Returns:
            Dict with loaded model and metadata
        """
        try:
            model_key = f"{name}_{symbol}"

            if model_key not in self.index:
                return {
                    "success": False,
                    "error": f"Model {model_key} not found in registry"
                }

            # Get version
            if version == "latest":
                version = self.index[model_key].get("latest")
                if not version:
                    return {
                        "success": False,
                        "error": "No versions available"
                    }

            # Get model directory
            model_dir = self.base_path / model_key / version
            if not model_dir.exists():
                return {
                    "success": False,
                    "error": f"Version {version} not found"
                }

            # Load metadata
            metadata_file = model_dir / "metadata.json"
            with open(metadata_file, "r") as f:
                metadata = json.load(f)

            # Load model
            model = model_class()
            model_file = model_dir / "model"
            model.load(str(model_file))

            logger.info(f"Loaded model {model_key} v{version}")

            return {
                "success": True,
                "model": model,
                "metadata": metadata,
                "version": version,
            }

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_model_info(self, name: str, symbol: str) -> Dict[str, Any]:
        """
        Get information about a registered model.

        Args:
            name: Model name
            symbol: Stock symbol

        Returns:
            Model info including all versions and metrics
        """
        model_key = f"{name}_{symbol}"

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
        model_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all registered models.

        Args:
            symbol: Filter by symbol
            model_type: Filter by model type

        Returns:
            List of model summaries
        """
        models = []

        for model_key, info in self.index.items():
            # Apply filters
            if symbol and info.get("symbol") != symbol:
                continue
            if model_type and info.get("model_type") != model_type:
                continue

            models.append({
                "model_key": model_key,
                "name": info.get("name"),
                "symbol": info.get("symbol"),
                "model_type": info.get("model_type"),
                "latest_version": info.get("latest"),
                "version_count": len(info.get("versions", [])),
            })

        return models

    def delete_model(
        self,
        name: str,
        symbol: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete a model or specific version.

        Args:
            name: Model name
            symbol: Stock symbol
            version: Specific version to delete (None = all versions)

        Returns:
            Deletion result
        """
        try:
            model_key = f"{name}_{symbol}"

            if model_key not in self.index:
                return {
                    "success": False,
                    "error": f"Model {model_key} not found"
                }

            model_dir = self.base_path / model_key

            if version is None:
                # Delete all versions
                if model_dir.exists():
                    shutil.rmtree(model_dir)
                del self.index[model_key]
                self._save_index()
                logger.info(f"Deleted all versions of {model_key}")
                return {"success": True, "deleted": "all versions"}

            else:
                # Delete specific version
                version_dir = model_dir / version
                if version_dir.exists():
                    shutil.rmtree(version_dir)

                # Update index
                versions = self.index[model_key].get("versions", [])
                self.index[model_key]["versions"] = [
                    v for v in versions if v["version"] != version
                ]

                # Update latest if needed
                if self.index[model_key]["latest"] == version:
                    remaining = self.index[model_key]["versions"]
                    if remaining:
                        self.index[model_key]["latest"] = remaining[-1]["version"]
                    else:
                        self.index[model_key]["latest"] = None

                self._save_index()
                logger.info(f"Deleted {model_key} v{version}")
                return {"success": True, "deleted": version}

        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_best_model(
        self,
        name: str,
        symbol: str,
        metric: str = "mape",
        lower_is_better: bool = True
    ) -> Optional[str]:
        """
        Get the version with best performance on a metric.

        Args:
            name: Model name
            symbol: Stock symbol
            metric: Metric to compare
            lower_is_better: Whether lower values are better

        Returns:
            Best version string or None
        """
        model_key = f"{name}_{symbol}"

        if model_key not in self.index:
            return None

        versions = self.index[model_key].get("versions", [])
        if not versions:
            return None

        # Filter versions with the metric
        valid_versions = [
            v for v in versions
            if metric in v.get("metrics", {})
        ]

        if not valid_versions:
            return versions[-1]["version"]  # Return latest if no metrics

        # Sort by metric
        sorted_versions = sorted(
            valid_versions,
            key=lambda v: v["metrics"][metric],
            reverse=not lower_is_better
        )

        return sorted_versions[0]["version"]

    def compare_versions(
        self,
        name: str,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Compare all versions of a model.

        Args:
            name: Model name
            symbol: Stock symbol

        Returns:
            Comparison of all versions
        """
        model_key = f"{name}_{symbol}"

        if model_key not in self.index:
            return {
                "success": False,
                "error": f"Model {model_key} not found"
            }

        versions = self.index[model_key].get("versions", [])

        return {
            "success": True,
            "model_key": model_key,
            "total_versions": len(versions),
            "versions": versions,
            "best_mape": self.get_best_model(name, symbol, "mape", True),
            "best_direction_accuracy": self.get_best_model(
                name, symbol, "direction_accuracy", False
            ),
        }
