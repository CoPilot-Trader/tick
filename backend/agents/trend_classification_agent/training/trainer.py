"""
Classifier Trainer for Trend Classification Agent.

Provides:
- Training pipeline for LightGBM and XGBoost
- Time-series cross-validation
- Model comparison and selection
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np
import pandas as pd

from ..models.lightgbm_classifier import LightGBMClassifier
from ..models.xgboost_classifier import XGBoostClassifier
from ..models.classifier_registry import ClassifierRegistry
from ..features.feature_builder import FeatureBuilder

logger = logging.getLogger(__name__)


class ClassifierTrainer:
    """
    Training pipeline for trend classifiers.

    Features:
    - Train LightGBM and XGBoost classifiers
    - Time-series cross-validation
    - Model comparison
    - Automatic model registration
    """

    def __init__(
        self,
        registry: Optional[ClassifierRegistry] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Classifier Trainer.

        Args:
            registry: Classifier registry for saving models
            config: Training configuration
        """
        self.registry = registry or ClassifierRegistry()
        self.config = config or {}
        self.feature_builder = FeatureBuilder()

        self.lightgbm_config = self.config.get("lightgbm", {})
        self.xgboost_config = self.config.get("xgboost", {})

    def train_lightgbm(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "1d",
        horizon: int = 1,
        save_model: bool = True
    ) -> Dict[str, Any]:
        """
        Train LightGBM classifier.

        Args:
            df: Historical data with features
            symbol: Stock symbol
            timeframe: Timeframe ("1h" or "1d")
            horizon: Prediction horizon
            save_model: Save to registry

        Returns:
            Training results
        """
        logger.info(f"Training LightGBM classifier for {symbol} ({timeframe})")

        # Build features
        df_feat = self.feature_builder.build_features(df)

        # Train
        classifier = LightGBMClassifier(config=self.lightgbm_config)
        result = classifier.train(df_feat, horizon=horizon)

        if result.get("success") and save_model:
            save_result = self.registry.save_model(
                model=classifier,
                name="lightgbm",
                symbol=symbol,
                timeframe=timeframe,
                model_type="lightgbm",
                metrics=result.get("metrics", {}),
            )
            result["saved"] = save_result.get("success", False)
            result["version"] = save_result.get("version")

        return result

    def train_xgboost(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "1d",
        horizon: int = 1,
        save_model: bool = True
    ) -> Dict[str, Any]:
        """
        Train XGBoost classifier.

        Args:
            df: Historical data with features
            symbol: Stock symbol
            timeframe: Timeframe
            horizon: Prediction horizon
            save_model: Save to registry

        Returns:
            Training results
        """
        logger.info(f"Training XGBoost classifier for {symbol} ({timeframe})")

        df_feat = self.feature_builder.build_features(df)

        classifier = XGBoostClassifier(config=self.xgboost_config)
        result = classifier.train(df_feat, horizon=horizon)

        if result.get("success") and save_model:
            save_result = self.registry.save_model(
                model=classifier,
                name="xgboost",
                symbol=symbol,
                timeframe=timeframe,
                model_type="xgboost",
                metrics=result.get("metrics", {}),
            )
            result["saved"] = save_result.get("success", False)
            result["version"] = save_result.get("version")

        return result

    def train_all(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "1d",
        horizon: int = 1,
        save_models: bool = True
    ) -> Dict[str, Any]:
        """
        Train all classifier types.

        Args:
            df: Historical data
            symbol: Stock symbol
            timeframe: Timeframe
            horizon: Prediction horizon
            save_models: Save to registry

        Returns:
            Training results for all classifiers
        """
        results = {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": datetime.now().isoformat(),
            "models": {},
        }

        # Train LightGBM
        lgb_result = self.train_lightgbm(
            df, symbol, timeframe, horizon, save_models
        )
        results["models"]["lightgbm"] = lgb_result

        # Train XGBoost
        xgb_result = self.train_xgboost(
            df, symbol, timeframe, horizon, save_models
        )
        results["models"]["xgboost"] = xgb_result

        # Summary
        results["summary"] = {
            "lightgbm_success": lgb_result.get("success", False),
            "xgboost_success": xgb_result.get("success", False),
            "best_model": self._determine_best(lgb_result, xgb_result),
        }

        return results

    def _determine_best(
        self,
        lgb_result: Dict[str, Any],
        xgb_result: Dict[str, Any]
    ) -> Optional[str]:
        """Determine best model based on metrics."""
        lgb_success = lgb_result.get("success", False)
        xgb_success = xgb_result.get("success", False)

        if lgb_success and xgb_success:
            lgb_acc = lgb_result.get("metrics", {}).get("accuracy", 0)
            xgb_acc = xgb_result.get("metrics", {}).get("accuracy", 0)
            return "lightgbm" if lgb_acc >= xgb_acc else "xgboost"
        elif lgb_success:
            return "lightgbm"
        elif xgb_success:
            return "xgboost"
        return None

    def cross_validate(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "1d",
        n_splits: int = 5,
        model_type: str = "lightgbm"
    ) -> Dict[str, Any]:
        """
        Perform time-series cross-validation.

        Args:
            df: Historical data
            symbol: Stock symbol
            timeframe: Timeframe
            n_splits: Number of CV splits
            model_type: "lightgbm" or "xgboost"

        Returns:
            Cross-validation results
        """
        logger.info(f"Cross-validating {model_type} for {symbol}")

        df_feat = self.feature_builder.build_features(df)

        # Time-series split
        n_samples = len(df_feat)
        test_size = n_samples // (n_splits + 1)

        fold_results = []

        for fold in range(n_splits):
            test_end = n_samples - fold * test_size
            test_start = test_end - test_size
            train_end = test_start

            if train_end < 100:
                break

            train_df = df_feat.iloc[:train_end]
            test_df = df_feat.iloc[test_start:test_end]

            # Train model
            if model_type == "lightgbm":
                classifier = LightGBMClassifier(config=self.lightgbm_config)
            else:
                classifier = XGBoostClassifier(config=self.xgboost_config)

            train_result = classifier.train(train_df, validation_split=0)

            if not train_result.get("success"):
                continue

            # Evaluate on test set
            predictions = classifier.predict_batch(test_df)

            if predictions.get("success"):
                # Calculate accuracy
                signals = predictions.get("signals", [])
                # Get actual labels for test set
                classifier_temp = LightGBMClassifier() if model_type == "lightgbm" else XGBoostClassifier()
                actual_labels = classifier_temp._create_labels(test_df)

                valid_mask = ~np.isnan(actual_labels)
                if np.sum(valid_mask) > 0:
                    pred_array = np.array([classifier.LABEL_TO_INT[s] for s in signals])
                    pred_valid = pred_array[valid_mask[:len(pred_array)]]
                    actual_valid = actual_labels[valid_mask][:len(pred_valid)]

                    if len(pred_valid) > 0 and len(actual_valid) > 0:
                        accuracy = np.mean(pred_valid == actual_valid.astype(int)) * 100

                        fold_results.append({
                            "fold": fold + 1,
                            "train_size": len(train_df),
                            "test_size": len(test_df),
                            "accuracy": round(accuracy, 2),
                        })

        if not fold_results:
            return {
                "success": False,
                "error": "All folds failed"
            }

        avg_accuracy = np.mean([f["accuracy"] for f in fold_results])

        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "model_type": model_type,
            "n_folds": len(fold_results),
            "fold_results": fold_results,
            "average_accuracy": round(avg_accuracy, 2),
        }

    def compare_models(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "1d",
        validation_days: int = 30
    ) -> Dict[str, Any]:
        """
        Compare LightGBM vs XGBoost.

        Args:
            df: Historical data
            symbol: Stock symbol
            timeframe: Timeframe
            validation_days: Days for validation

        Returns:
            Comparison results with recommendation
        """
        logger.info(f"Comparing classifiers for {symbol}")

        df_feat = self.feature_builder.build_features(df)

        train_df = df_feat.iloc[:-validation_days]
        val_df = df_feat.iloc[-validation_days:]

        results = {
            "symbol": symbol,
            "timeframe": timeframe,
            "validation_days": validation_days,
            "models": {},
        }

        # Train and evaluate LightGBM
        lgb = LightGBMClassifier(config=self.lightgbm_config)
        lgb_train = lgb.train(train_df, validation_split=0)

        if lgb_train.get("success"):
            lgb_pred = lgb.predict_batch(val_df)
            if lgb_pred.get("success"):
                results["models"]["lightgbm"] = {
                    "trained": True,
                    "training_accuracy": lgb_train.get("metrics", {}).get("accuracy", 0),
                    "signal_distribution": lgb_pred.get("signal_distribution", {}),
                }
        else:
            results["models"]["lightgbm"] = {
                "trained": False,
                "error": lgb_train.get("error"),
            }

        # Train and evaluate XGBoost
        xgb = XGBoostClassifier(config=self.xgboost_config)
        xgb_train = xgb.train(train_df, validation_split=0)

        if xgb_train.get("success"):
            xgb_pred = xgb.predict_batch(val_df)
            if xgb_pred.get("success"):
                results["models"]["xgboost"] = {
                    "trained": True,
                    "training_accuracy": xgb_train.get("metrics", {}).get("accuracy", 0),
                    "signal_distribution": xgb_pred.get("signal_distribution", {}),
                }
        else:
            results["models"]["xgboost"] = {
                "trained": False,
                "error": xgb_train.get("error"),
            }

        # Recommendation
        lgb_ok = results["models"].get("lightgbm", {}).get("trained", False)
        xgb_ok = results["models"].get("xgboost", {}).get("trained", False)

        if lgb_ok and xgb_ok:
            lgb_acc = results["models"]["lightgbm"].get("training_accuracy", 0)
            xgb_acc = results["models"]["xgboost"].get("training_accuracy", 0)

            if lgb_acc >= xgb_acc:
                recommendation = "lightgbm"
                reason = f"LightGBM had higher accuracy ({lgb_acc:.1f}% vs {xgb_acc:.1f}%)"
            else:
                recommendation = "xgboost"
                reason = f"XGBoost had higher accuracy ({xgb_acc:.1f}% vs {lgb_acc:.1f}%)"
        elif lgb_ok:
            recommendation = "lightgbm"
            reason = "Only LightGBM trained successfully"
        elif xgb_ok:
            recommendation = "xgboost"
            reason = "Only XGBoost trained successfully"
        else:
            recommendation = None
            reason = "Neither model trained successfully"

        results["recommendation"] = {
            "model": recommendation,
            "reason": reason,
        }

        return results
