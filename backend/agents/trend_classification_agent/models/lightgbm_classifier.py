"""
LightGBM Classifier for Trend Classification.

Uses LightGBM for BUY/SELL/HOLD classification with:
- Multi-class classification
- Probability outputs
- Feature importance analysis
- Cross-validation
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Optional import - LightGBM may not be installed
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not installed. Use: pip install lightgbm")


class LightGBMClassifier:
    """
    LightGBM-based trend classifier.

    Classes:
    - 0 (SELL): Price decreases >1% in horizon
    - 1 (HOLD): Price changes <1% in horizon
    - 2 (BUY): Price increases >1% in horizon

    Features:
    - Multi-class classification
    - Probability scores for each class
    - Feature importance tracking
    - Time-series aware cross-validation
    """

    # Class labels
    LABELS = {0: "SELL", 1: "HOLD", 2: "BUY"}
    LABEL_TO_INT = {"SELL": 0, "HOLD": 1, "BUY": 2}

    # Default hyperparameters
    DEFAULT_PARAMS = {
        "objective": "multiclass",
        "num_class": 3,
        "metric": "multi_logloss",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.9,
        "bagging_fraction": 0.8,
        "bagging_freq": 5,
        "verbose": -1,
        "seed": 42,
    }

    # Threshold for classification (1% move)
    THRESHOLD = 0.01

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LightGBM Classifier.

        Args:
            config: Optional configuration dict
                - threshold: Price change threshold for BUY/SELL (default: 0.01)
                - num_boost_round: Number of boosting rounds
                - params: LightGBM parameters
        """
        self.config = config or {}
        self.model = None
        self.is_trained = False
        self.last_train_date: Optional[datetime] = None
        self.training_metrics: Dict[str, float] = {}

        # Configuration
        self.threshold = self.config.get("threshold", self.THRESHOLD)
        self.num_boost_round = self.config.get("num_boost_round", 100)
        self.params = {**self.DEFAULT_PARAMS, **self.config.get("params", {})}

        # Feature columns used in training
        self.feature_columns: List[str] = []
        self.feature_importance: Dict[str, float] = {}

    def _create_labels(
        self,
        df: pd.DataFrame,
        horizon: int = 1,
        target_col: str = "close"
    ) -> np.ndarray:
        """
        Create classification labels based on future returns.

        Args:
            df: DataFrame with price data
            horizon: Number of periods to look ahead
            target_col: Column to use for returns

        Returns:
            Array of labels (0=SELL, 1=HOLD, 2=BUY)
        """
        # Calculate future returns
        future_returns = df[target_col].pct_change(horizon).shift(-horizon)

        # Create labels
        labels = np.where(
            future_returns > self.threshold, 2,  # BUY
            np.where(future_returns < -self.threshold, 0, 1)  # SELL or HOLD
        )

        return labels

    def _prepare_features(
        self,
        df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare feature matrix from DataFrame.

        Args:
            df: Input DataFrame
            feature_cols: Columns to use as features

        Returns:
            Feature array and list of column names
        """
        # Default features for classification
        if feature_cols is None:
            candidate_features = [
                # Price features
                "returns_1d", "returns_5d", "momentum_5d", "momentum_20d",
                # Technical indicators
                "rsi_14", "macd", "macd_signal", "macd_histogram",
                "stoch_k", "stoch_d", "cci_20", "williams_r",
                # Volatility
                "atr_14", "bb_upper", "bb_lower", "bb_width",
                "volatility_5d", "volatility_20d",
                # Trend
                "adx_14", "sma_20", "sma_50", "ema_12", "ema_26",
                "price_sma_20_ratio", "price_sma_50_ratio",
                # Volume
                "obv", "volume_sma_20", "relative_volume",
            ]
            feature_cols = [c for c in candidate_features if c in df.columns]

            # Minimum features if indicators not present
            if len(feature_cols) < 5:
                # Create basic features from OHLCV
                feature_cols = []
                if "returns_1d" not in df.columns and "close" in df.columns:
                    df = df.copy()
                    df["returns_1d"] = df["close"].pct_change(1)
                    feature_cols.append("returns_1d")
                if "returns_5d" not in df.columns and "close" in df.columns:
                    df["returns_5d"] = df["close"].pct_change(5)
                    feature_cols.append("returns_5d")

        available_cols = [c for c in feature_cols if c in df.columns]

        if len(available_cols) == 0:
            raise ValueError(f"No valid features found. Available: {df.columns.tolist()}")

        features = df[available_cols].values
        return features, available_cols

    def train(
        self,
        df: pd.DataFrame,
        horizon: int = 1,
        feature_cols: Optional[List[str]] = None,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train LightGBM classifier on historical data.

        Args:
            df: DataFrame with OHLCV + indicator data
            horizon: Prediction horizon (periods ahead)
            feature_cols: Feature columns to use
            validation_split: Fraction of data for validation

        Returns:
            Training results with metrics
        """
        if not LIGHTGBM_AVAILABLE:
            return {
                "success": False,
                "error": "LightGBM not installed. Use: pip install lightgbm"
            }

        try:
            # Prepare features
            features, self.feature_columns = self._prepare_features(df, feature_cols)

            # Create labels
            labels = self._create_labels(df, horizon=horizon)

            # Remove rows with NaN labels (last `horizon` rows)
            valid_mask = ~np.isnan(labels)
            features = features[valid_mask]
            labels = labels[valid_mask].astype(int)

            logger.info(f"Training LightGBM on {len(features)} samples with {len(self.feature_columns)} features")
            logger.info(f"Class distribution: SELL={np.sum(labels==0)}, HOLD={np.sum(labels==1)}, BUY={np.sum(labels==2)}")

            # Handle NaN in features
            features = np.nan_to_num(features, nan=0.0)

            # Check minimum samples
            if len(features) < 100:
                return {
                    "success": False,
                    "error": f"Insufficient data: {len(features)} samples (need >= 100)"
                }

            # Split data (time-series aware - no shuffle)
            split_idx = int(len(features) * (1 - validation_split))
            X_train, X_val = features[:split_idx], features[split_idx:]
            y_train, y_val = labels[:split_idx], labels[split_idx:]

            # Create LightGBM datasets
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)

            # Train model
            callbacks = [
                lgb.early_stopping(stopping_rounds=20, verbose=False),
                lgb.log_evaluation(period=0),  # Suppress output
            ]

            self.model = lgb.train(
                self.params,
                train_data,
                num_boost_round=self.num_boost_round,
                valid_sets=[train_data, val_data],
                valid_names=["train", "val"],
                callbacks=callbacks,
            )

            self.is_trained = True
            self.last_train_date = datetime.now()

            # Calculate validation metrics
            val_pred_proba = self.model.predict(X_val)
            val_pred = np.argmax(val_pred_proba, axis=1)

            accuracy = np.mean(val_pred == y_val) * 100

            # Per-class metrics
            class_accuracy = {}
            for class_idx, class_name in self.LABELS.items():
                class_mask = y_val == class_idx
                if np.sum(class_mask) > 0:
                    class_acc = np.mean(val_pred[class_mask] == y_val[class_mask]) * 100
                    class_accuracy[class_name] = round(class_acc, 2)

            # Directional accuracy (BUY/SELL only, ignoring HOLD)
            directional_mask = (y_val != 1) & (val_pred != 1)
            if np.sum(directional_mask) > 0:
                directional_accuracy = np.mean(val_pred[directional_mask] == y_val[directional_mask]) * 100
            else:
                directional_accuracy = 0.0

            # Feature importance
            importance = self.model.feature_importance(importance_type="gain")
            self.feature_importance = dict(zip(self.feature_columns, importance.tolist()))

            # Sort by importance
            sorted_importance = sorted(
                self.feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]  # Top 10

            self.training_metrics = {
                "accuracy": round(accuracy, 2),
                "directional_accuracy": round(directional_accuracy, 2),
                "class_accuracy": class_accuracy,
                "best_iteration": self.model.best_iteration,
            }

            return {
                "success": True,
                "model_type": "lightgbm",
                "training_samples": len(X_train),
                "validation_samples": len(X_val),
                "features_used": self.feature_columns,
                "horizon": horizon,
                "threshold": self.threshold,
                "metrics": self.training_metrics,
                "top_features": dict(sorted_importance),
                "trained_at": self.last_train_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"LightGBM training failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def predict(
        self,
        df: pd.DataFrame,
        return_probabilities: bool = True
    ) -> Dict[str, Any]:
        """
        Generate classification predictions.

        Args:
            df: Data for prediction (must have same features as training)
            return_probabilities: Include probability scores

        Returns:
            Dictionary with classification and probabilities
        """
        if not self.is_trained or self.model is None:
            return {
                "success": False,
                "error": "Model not trained"
            }

        if not LIGHTGBM_AVAILABLE:
            return {
                "success": False,
                "error": "LightGBM not installed"
            }

        try:
            # Prepare features
            features, _ = self._prepare_features(df, self.feature_columns)

            # Handle NaN
            features = np.nan_to_num(features, nan=0.0)

            # Get prediction for last row
            last_features = features[-1:] if len(features) > 0 else features

            # Predict probabilities
            probabilities = self.model.predict(last_features)[0]
            predicted_class = int(np.argmax(probabilities))
            predicted_label = self.LABELS[predicted_class]
            confidence = float(probabilities[predicted_class])

            result = {
                "success": True,
                "model_type": "lightgbm",
                "signal": predicted_label,
                "confidence": round(confidence, 3),
                "generated_at": datetime.now().isoformat(),
            }

            if return_probabilities:
                result["probabilities"] = {
                    "SELL": round(float(probabilities[0]), 3),
                    "HOLD": round(float(probabilities[1]), 3),
                    "BUY": round(float(probabilities[2]), 3),
                }

            return result

        except Exception as e:
            logger.error(f"LightGBM prediction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def predict_batch(
        self,
        df: pd.DataFrame,
        return_probabilities: bool = True
    ) -> Dict[str, Any]:
        """
        Generate predictions for all rows in DataFrame.

        Args:
            df: Data for prediction
            return_probabilities: Include probability scores

        Returns:
            Dictionary with predictions and signals
        """
        if not self.is_trained or self.model is None:
            return {
                "success": False,
                "error": "Model not trained"
            }

        try:
            features, _ = self._prepare_features(df, self.feature_columns)
            features = np.nan_to_num(features, nan=0.0)

            probabilities = self.model.predict(features)
            predictions = np.argmax(probabilities, axis=1)
            labels = [self.LABELS[p] for p in predictions]
            confidences = np.max(probabilities, axis=1)

            result = {
                "success": True,
                "model_type": "lightgbm",
                "count": len(predictions),
                "signals": labels,
                "confidences": [round(c, 3) for c in confidences],
                "signal_distribution": {
                    "SELL": int(np.sum(predictions == 0)),
                    "HOLD": int(np.sum(predictions == 1)),
                    "BUY": int(np.sum(predictions == 2)),
                },
                "generated_at": datetime.now().isoformat(),
            }

            if return_probabilities:
                result["probabilities"] = probabilities.tolist()

            return result

        except Exception as e:
            logger.error(f"Batch prediction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_feature_importance(self, top_n: int = 10) -> Dict[str, float]:
        """Get top N most important features."""
        if not self.feature_importance:
            return {}

        sorted_features = sorted(
            self.feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return dict(sorted_features)

    def save(self, filepath: str) -> bool:
        """Save model to file."""
        if not self.is_trained or self.model is None:
            return False

        try:
            import joblib

            model_data = {
                "model": self.model,
                "config": self.config,
                "feature_columns": self.feature_columns,
                "feature_importance": self.feature_importance,
                "is_trained": self.is_trained,
                "last_train_date": self.last_train_date,
                "training_metrics": self.training_metrics,
                "params": self.params,
                "threshold": self.threshold,
            }
            joblib.dump(model_data, filepath)
            logger.info(f"LightGBM model saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load(self, filepath: str) -> bool:
        """Load model from file."""
        try:
            import joblib

            model_data = joblib.load(filepath)
            self.model = model_data["model"]
            self.config = model_data.get("config", {})
            self.feature_columns = model_data.get("feature_columns", [])
            self.feature_importance = model_data.get("feature_importance", {})
            self.is_trained = model_data.get("is_trained", True)
            self.last_train_date = model_data.get("last_train_date")
            self.training_metrics = model_data.get("training_metrics", {})
            self.params = model_data.get("params", self.DEFAULT_PARAMS)
            self.threshold = model_data.get("threshold", self.THRESHOLD)

            logger.info(f"LightGBM model loaded from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
