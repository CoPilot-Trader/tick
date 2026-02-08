"""
XGBoost Classifier for Trend Classification.

Uses XGBoost as an alternative to LightGBM with:
- Multi-class classification
- Probability outputs
- Feature importance analysis
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Optional import - XGBoost may not be installed
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not installed. Use: pip install xgboost")


class XGBoostClassifier:
    """
    XGBoost-based trend classifier.

    Classes:
    - 0 (SELL): Price decreases >1% in horizon
    - 1 (HOLD): Price changes <1% in horizon
    - 2 (BUY): Price increases >1% in horizon

    Similar interface to LightGBMClassifier for interchangeability.
    """

    LABELS = {0: "SELL", 1: "HOLD", 2: "BUY"}
    LABEL_TO_INT = {"SELL": 0, "HOLD": 1, "BUY": 2}

    DEFAULT_PARAMS = {
        "objective": "multi:softprob",
        "num_class": 3,
        "eval_metric": "mlogloss",
        "max_depth": 6,
        "learning_rate": 0.1,
        "n_estimators": 100,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": 42,
        "verbosity": 0,
    }

    THRESHOLD = 0.01

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize XGBoost Classifier.

        Args:
            config: Configuration dict
        """
        self.config = config or {}
        self.model = None
        self.is_trained = False
        self.last_train_date: Optional[datetime] = None
        self.training_metrics: Dict[str, float] = {}

        self.threshold = self.config.get("threshold", self.THRESHOLD)
        self.params = {**self.DEFAULT_PARAMS, **self.config.get("params", {})}

        self.feature_columns: List[str] = []
        self.feature_importance: Dict[str, float] = {}

    def _create_labels(
        self,
        df: pd.DataFrame,
        horizon: int = 1,
        target_col: str = "close"
    ) -> np.ndarray:
        """Create classification labels based on future returns."""
        future_returns = df[target_col].pct_change(horizon).shift(-horizon)

        labels = np.where(
            future_returns > self.threshold, 2,
            np.where(future_returns < -self.threshold, 0, 1)
        )

        return labels

    def _prepare_features(
        self,
        df: pd.DataFrame,
        feature_cols: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """Prepare feature matrix from DataFrame."""
        if feature_cols is None:
            candidate_features = [
                "returns_1d", "returns_5d", "momentum_5d", "momentum_20d",
                "rsi_14", "macd", "macd_signal", "macd_histogram",
                "stoch_k", "stoch_d", "cci_20", "williams_r",
                "atr_14", "bb_upper", "bb_lower", "bb_width",
                "volatility_5d", "volatility_20d",
                "adx_14", "sma_20", "sma_50", "ema_12", "ema_26",
                "obv", "volume_sma_20", "relative_volume",
            ]
            feature_cols = [c for c in candidate_features if c in df.columns]

        available_cols = [c for c in feature_cols if c in df.columns]

        if len(available_cols) == 0:
            raise ValueError(f"No valid features found")

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
        Train XGBoost classifier.

        Args:
            df: DataFrame with data
            horizon: Prediction horizon
            feature_cols: Feature columns
            validation_split: Validation fraction

        Returns:
            Training results
        """
        if not XGBOOST_AVAILABLE:
            return {
                "success": False,
                "error": "XGBoost not installed. Use: pip install xgboost"
            }

        try:
            features, self.feature_columns = self._prepare_features(df, feature_cols)
            labels = self._create_labels(df, horizon=horizon)

            valid_mask = ~np.isnan(labels)
            features = features[valid_mask]
            labels = labels[valid_mask].astype(int)

            features = np.nan_to_num(features, nan=0.0)

            if len(features) < 100:
                return {
                    "success": False,
                    "error": f"Insufficient data: {len(features)} samples"
                }

            split_idx = int(len(features) * (1 - validation_split))
            X_train, X_val = features[:split_idx], features[split_idx:]
            y_train, y_val = labels[:split_idx], labels[split_idx:]

            # Extract params for XGBClassifier
            n_estimators = self.params.pop("n_estimators", 100)

            self.model = xgb.XGBClassifier(
                n_estimators=n_estimators,
                **self.params,
                early_stopping_rounds=20,
            )

            self.model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                verbose=False
            )

            self.is_trained = True
            self.last_train_date = datetime.now()

            # Metrics
            val_pred = self.model.predict(X_val)
            accuracy = np.mean(val_pred == y_val) * 100

            directional_mask = (y_val != 1) & (val_pred != 1)
            if np.sum(directional_mask) > 0:
                directional_accuracy = np.mean(val_pred[directional_mask] == y_val[directional_mask]) * 100
            else:
                directional_accuracy = 0.0

            # Feature importance
            importance = self.model.feature_importances_
            self.feature_importance = dict(zip(self.feature_columns, importance.tolist()))

            self.training_metrics = {
                "accuracy": round(accuracy, 2),
                "directional_accuracy": round(directional_accuracy, 2),
            }

            return {
                "success": True,
                "model_type": "xgboost",
                "training_samples": len(X_train),
                "validation_samples": len(X_val),
                "metrics": self.training_metrics,
                "trained_at": self.last_train_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"XGBoost training failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def predict(
        self,
        df: pd.DataFrame,
        return_probabilities: bool = True
    ) -> Dict[str, Any]:
        """Generate classification predictions."""
        if not self.is_trained or self.model is None:
            return {
                "success": False,
                "error": "Model not trained"
            }

        try:
            features, _ = self._prepare_features(df, self.feature_columns)
            features = np.nan_to_num(features, nan=0.0)
            last_features = features[-1:]

            probabilities = self.model.predict_proba(last_features)[0]
            predicted_class = int(np.argmax(probabilities))
            predicted_label = self.LABELS[predicted_class]
            confidence = float(probabilities[predicted_class])

            result = {
                "success": True,
                "model_type": "xgboost",
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
            logger.error(f"XGBoost prediction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def save(self, filepath: str) -> bool:
        """Save model to file."""
        if not self.is_trained or self.model is None:
            return False

        try:
            import joblib
            model_data = {
                "model": self.model,
                "feature_columns": self.feature_columns,
                "feature_importance": self.feature_importance,
                "is_trained": self.is_trained,
                "last_train_date": self.last_train_date,
                "training_metrics": self.training_metrics,
            }
            joblib.dump(model_data, filepath)
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
            self.feature_columns = model_data.get("feature_columns", [])
            self.feature_importance = model_data.get("feature_importance", {})
            self.is_trained = model_data.get("is_trained", True)
            self.last_train_date = model_data.get("last_train_date")
            self.training_metrics = model_data.get("training_metrics", {})
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
