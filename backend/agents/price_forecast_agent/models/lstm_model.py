"""
LSTM Model for Primary Price Forecasting.

Uses TensorFlow/Keras LSTM for deep learning-based forecasting with:
- Multi-layer LSTM architecture
- Feature engineering integration
- Dropout regularization
- Multi-horizon predictions
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Optional import - TensorFlow may not be installed
TF_AVAILABLE = False
tf = None  # Placeholder for type checking

try:
    import tensorflow as tf
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout, BatchNormalization
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except ImportError:
    # Create placeholder classes for type hints when TF not available
    Sequential = None
    load_model = None
    logger.warning("TensorFlow not installed. Use: pip install tensorflow")


class LSTMModel:
    """
    LSTM-based price forecasting model.

    Architecture:
    - Input: sequence of normalized features
    - 2 LSTM layers (128 -> 64 units)
    - Dropout for regularization
    - Dense output layer

    Features:
    - Multi-horizon predictions
    - Confidence estimation via MC Dropout
    - Feature scaling/normalization
    - Early stopping
    """

    # Default architecture configuration
    DEFAULT_CONFIG = {
        "sequence_length": 60,      # Look-back window
        "lstm_units": [128, 64],    # LSTM layer sizes
        "dropout_rate": 0.2,        # Dropout rate
        "learning_rate": 0.001,     # Adam learning rate
        "batch_size": 32,           # Training batch size
        "epochs": 100,              # Max epochs
        "patience": 10,             # Early stopping patience
        "mc_samples": 50,           # Monte Carlo samples for confidence
    }

    # Horizon configurations (horizon name -> steps ahead)
    HORIZON_CONFIG = {
        "1h": 1,    # 1 step (assuming hourly data)
        "4h": 4,    # 4 steps
        "1d": 24,   # 24 steps (or 1 for daily data)
        "1w": 168,  # 168 steps (or 7 for daily data)
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LSTM Model.

        Args:
            config: Configuration dict with architecture params
        """
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self.model: Optional[tf.keras.Model] = None
        self.is_trained = False
        self.last_train_date: Optional[datetime] = None
        self.training_metrics: Dict[str, float] = {}

        # Normalization parameters
        self.feature_means: Optional[np.ndarray] = None
        self.feature_stds: Optional[np.ndarray] = None
        self.target_mean: Optional[float] = None
        self.target_std: Optional[float] = None

        # Feature columns used in training
        self.feature_columns: List[str] = []

        # Data frequency (detected during training)
        self.data_frequency: str = "1h"  # Default hourly

    def _build_model(self, input_shape: Tuple[int, int]) -> Any:
        """
        Build LSTM model architecture.

        Args:
            input_shape: (sequence_length, num_features)

        Returns:
            Compiled Keras model
        """
        if not TF_AVAILABLE:
            raise RuntimeError("TensorFlow not installed")

        model = Sequential([
            # First LSTM layer
            LSTM(
                self.config["lstm_units"][0],
                return_sequences=True,
                input_shape=input_shape
            ),
            BatchNormalization(),
            Dropout(self.config["dropout_rate"]),

            # Second LSTM layer
            LSTM(
                self.config["lstm_units"][1],
                return_sequences=False
            ),
            BatchNormalization(),
            Dropout(self.config["dropout_rate"]),

            # Dense layers
            Dense(32, activation="relu"),
            Dropout(self.config["dropout_rate"]),
            Dense(1)  # Single output: predicted price
        ])

        model.compile(
            optimizer=Adam(learning_rate=self.config["learning_rate"]),
            loss="mse",
            metrics=["mae"]
        )

        return model

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
        # Default features if not specified
        if feature_cols is None:
            # Use OHLCV + any calculated indicators
            candidate_features = [
                "open", "high", "low", "close", "volume",
                "rsi_14", "macd", "macd_signal", "macd_histogram",
                "atr_14", "bb_upper", "bb_lower", "bb_middle",
                "ema_12", "ema_26", "sma_20", "sma_50",
                "obv", "returns_1d", "returns_5d", "daily_range"
            ]
            feature_cols = [c for c in candidate_features if c in df.columns]

            # At minimum, need OHLCV
            if len(feature_cols) < 4:
                feature_cols = ["open", "high", "low", "close"]
                if "volume" in df.columns:
                    feature_cols.append("volume")

        # Filter to available columns
        available_cols = [c for c in feature_cols if c in df.columns]

        if len(available_cols) == 0:
            raise ValueError(f"No valid features found. Available: {df.columns.tolist()}")

        features = df[available_cols].values
        return features, available_cols

    def _create_sequences(
        self,
        features: np.ndarray,
        target: np.ndarray,
        sequence_length: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sliding window sequences for LSTM.

        Args:
            features: Feature array (n_samples, n_features)
            target: Target array (n_samples,)
            sequence_length: Number of time steps per sequence

        Returns:
            X (sequences) and y (targets)
        """
        X, y = [], []

        for i in range(len(features) - sequence_length):
            X.append(features[i:i + sequence_length])
            y.append(target[i + sequence_length])

        return np.array(X), np.array(y)

    def _normalize_features(
        self,
        features: np.ndarray,
        fit: bool = False
    ) -> np.ndarray:
        """
        Normalize features using z-score normalization.

        Args:
            features: Feature array
            fit: Whether to fit normalization params

        Returns:
            Normalized features
        """
        if fit:
            self.feature_means = np.nanmean(features, axis=0)
            self.feature_stds = np.nanstd(features, axis=0)
            # Avoid division by zero
            self.feature_stds = np.where(
                self.feature_stds == 0,
                1.0,
                self.feature_stds
            )

        if self.feature_means is None or self.feature_stds is None:
            raise ValueError("Normalization parameters not set")

        normalized = (features - self.feature_means) / self.feature_stds
        return np.nan_to_num(normalized, nan=0.0)

    def _normalize_target(
        self,
        target: np.ndarray,
        fit: bool = False
    ) -> np.ndarray:
        """Normalize target using z-score."""
        if fit:
            self.target_mean = float(np.nanmean(target))
            self.target_std = float(np.nanstd(target))
            if self.target_std == 0:
                self.target_std = 1.0

        if self.target_mean is None or self.target_std is None:
            raise ValueError("Target normalization parameters not set")

        return (target - self.target_mean) / self.target_std

    def _denormalize_target(self, normalized: np.ndarray) -> np.ndarray:
        """Denormalize target back to original scale."""
        if self.target_mean is None or self.target_std is None:
            raise ValueError("Target normalization parameters not set")

        return normalized * self.target_std + self.target_mean

    def _detect_frequency(self, df: pd.DataFrame) -> str:
        """Detect data frequency from DataFrame."""
        if "bar_ts" in df.columns:
            timestamps = pd.to_datetime(df["bar_ts"])
        elif "timestamp" in df.columns:
            timestamps = pd.to_datetime(df["timestamp"])
        elif isinstance(df.index, pd.DatetimeIndex):
            timestamps = df.index
        else:
            return "1d"  # Default to daily

        if len(timestamps) < 2:
            return "1d"

        # Calculate median time difference
        diff = timestamps.diff().median()

        if diff <= pd.Timedelta(hours=1):
            return "1h"
        elif diff <= pd.Timedelta(hours=4):
            return "4h"
        else:
            return "1d"

    def train(
        self,
        df: pd.DataFrame,
        target_col: str = "close",
        feature_cols: Optional[List[str]] = None,
        validation_split: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train LSTM model on historical data.

        Args:
            df: DataFrame with OHLCV + indicator data
            target_col: Column to predict
            feature_cols: Feature columns to use
            validation_split: Fraction of data for validation

        Returns:
            Training results with metrics
        """
        if not TF_AVAILABLE:
            return {
                "success": False,
                "error": "TensorFlow not installed. Use: pip install tensorflow"
            }

        try:
            # Detect data frequency
            self.data_frequency = self._detect_frequency(df)
            logger.info(f"Detected data frequency: {self.data_frequency}")

            # Prepare features
            features, self.feature_columns = self._prepare_features(df, feature_cols)
            target = df[target_col].values

            logger.info(f"Using features: {self.feature_columns}")
            logger.info(f"Data shape: {features.shape}")

            # Check minimum data requirement
            min_samples = self.config["sequence_length"] + 50
            if len(features) < min_samples:
                return {
                    "success": False,
                    "error": f"Insufficient data: {len(features)} rows (need >= {min_samples})"
                }

            # Normalize
            features_norm = self._normalize_features(features, fit=True)
            target_norm = self._normalize_target(target, fit=True)

            # Create sequences
            X, y = self._create_sequences(
                features_norm,
                target_norm,
                self.config["sequence_length"]
            )

            logger.info(f"Created {len(X)} sequences")

            # Split data
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]

            # Build model
            input_shape = (X.shape[1], X.shape[2])
            self.model = self._build_model(input_shape)

            # Callbacks
            callbacks = [
                EarlyStopping(
                    monitor="val_loss",
                    patience=self.config["patience"],
                    restore_best_weights=True
                ),
                ReduceLROnPlateau(
                    monitor="val_loss",
                    factor=0.5,
                    patience=5,
                    min_lr=1e-6
                )
            ]

            # Train
            logger.info("Training LSTM model...")
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=self.config["epochs"],
                batch_size=self.config["batch_size"],
                callbacks=callbacks,
                verbose=0
            )

            self.is_trained = True
            self.last_train_date = datetime.now()

            # Calculate metrics on validation set
            val_pred_norm = self.model.predict(X_val, verbose=0).flatten()
            val_pred = self._denormalize_target(val_pred_norm)
            val_actual = self._denormalize_target(y_val)

            mape = np.mean(np.abs((val_actual - val_pred) / val_actual)) * 100
            rmse = np.sqrt(np.mean((val_actual - val_pred) ** 2))
            mae = np.mean(np.abs(val_actual - val_pred))

            # Directional accuracy
            actual_direction = np.sign(np.diff(val_actual))
            pred_direction = np.sign(np.diff(val_pred))
            direction_accuracy = np.mean(actual_direction == pred_direction) * 100

            self.training_metrics = {
                "mape": round(mape, 2),
                "rmse": round(rmse, 4),
                "mae": round(mae, 4),
                "direction_accuracy": round(direction_accuracy, 2),
                "final_loss": round(float(history.history["loss"][-1]), 6),
                "final_val_loss": round(float(history.history["val_loss"][-1]), 6),
                "epochs_trained": len(history.history["loss"]),
            }

            return {
                "success": True,
                "model_type": "lstm",
                "training_samples": len(X_train),
                "validation_samples": len(X_val),
                "features_used": self.feature_columns,
                "sequence_length": self.config["sequence_length"],
                "data_frequency": self.data_frequency,
                "metrics": self.training_metrics,
                "trained_at": self.last_train_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"LSTM training failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def predict(
        self,
        df: pd.DataFrame,
        horizons: Optional[List[str]] = None,
        use_mc_dropout: bool = True
    ) -> Dict[str, Any]:
        """
        Generate predictions for specified horizons.

        Args:
            df: Recent data for prediction (must have same features as training)
            horizons: List of horizons ["1h", "4h", "1d", "1w"]
            use_mc_dropout: Use Monte Carlo Dropout for confidence estimation

        Returns:
            Dictionary with predictions and confidence intervals
        """
        if not self.is_trained or self.model is None:
            return {
                "success": False,
                "error": "Model not trained"
            }

        if not TF_AVAILABLE:
            return {
                "success": False,
                "error": "TensorFlow not installed"
            }

        try:
            horizons = horizons or ["1h", "4h", "1d", "1w"]

            # Prepare features
            features, _ = self._prepare_features(df, self.feature_columns)

            # Need at least sequence_length points
            if len(features) < self.config["sequence_length"]:
                return {
                    "success": False,
                    "error": f"Need at least {self.config['sequence_length']} data points"
                }

            # Use last sequence
            features_norm = self._normalize_features(features, fit=False)
            last_sequence = features_norm[-self.config["sequence_length"]:]
            last_sequence = last_sequence.reshape(1, *last_sequence.shape)

            # Current price (last close)
            current_price = float(df["close"].iloc[-1])

            predictions = {}

            for horizon in horizons:
                if horizon not in self.HORIZON_CONFIG:
                    continue

                steps = self._get_steps_for_horizon(horizon)

                if use_mc_dropout:
                    # Monte Carlo Dropout for uncertainty estimation
                    mc_predictions = []
                    for _ in range(self.config["mc_samples"]):
                        # Training=True enables dropout during inference
                        pred_norm = self.model(last_sequence, training=True).numpy().flatten()[0]
                        pred = self._denormalize_target(np.array([pred_norm]))[0]
                        mc_predictions.append(pred)

                    mc_predictions = np.array(mc_predictions)
                    predicted_value = float(np.mean(mc_predictions))
                    std = float(np.std(mc_predictions))

                    # Confidence intervals (95%)
                    price_lower = predicted_value - 1.96 * std
                    price_upper = predicted_value + 1.96 * std

                    # Confidence based on prediction spread
                    coefficient_of_variation = std / abs(predicted_value) if predicted_value != 0 else 1
                    confidence = max(0.3, min(0.95, 1 - coefficient_of_variation))

                else:
                    # Single prediction
                    pred_norm = self.model.predict(last_sequence, verbose=0).flatten()[0]
                    predicted_value = float(self._denormalize_target(np.array([pred_norm]))[0])

                    # Estimate uncertainty from training metrics
                    if "rmse" in self.training_metrics:
                        std = self.training_metrics["rmse"]
                    else:
                        std = abs(predicted_value) * 0.05

                    price_lower = predicted_value - 1.96 * std
                    price_upper = predicted_value + 1.96 * std
                    confidence = 0.7

                # Direction
                direction = "UP" if predicted_value > current_price else "DOWN" if predicted_value < current_price else "NEUTRAL"

                # Scale prediction for longer horizons (simple approach)
                # For multi-step ahead, we'd ideally use iterative prediction
                if steps > 1:
                    # Simple scaling - in production, use iterative prediction
                    change = predicted_value - current_price
                    predicted_value = current_price + change * min(steps / 24, 2)
                    price_lower = current_price + (price_lower - current_price) * min(steps / 24, 2)
                    price_upper = current_price + (price_upper - current_price) * min(steps / 24, 2)
                    confidence *= (1 - 0.1 * np.log1p(steps / 24))  # Decrease confidence with horizon

                predictions[horizon] = {
                    "price": round(predicted_value, 2),
                    "confidence": round(max(0.3, confidence), 3),
                    "direction": direction,
                    "price_lower": round(max(0, price_lower), 2),
                    "price_upper": round(price_upper, 2),
                    "change_pct": round((predicted_value - current_price) / current_price * 100, 2),
                }

            return {
                "success": True,
                "model_type": "lstm",
                "current_price": current_price,
                "predictions": predictions,
                "data_frequency": self.data_frequency,
                "generated_at": datetime.now().isoformat(),
                "model_trained_at": self.last_train_date.isoformat() if self.last_train_date else None,
            }

        except Exception as e:
            logger.error(f"LSTM prediction failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def _get_steps_for_horizon(self, horizon: str) -> int:
        """Get number of steps for horizon based on data frequency."""
        base_steps = self.HORIZON_CONFIG.get(horizon, 1)

        # Adjust based on data frequency
        if self.data_frequency == "1d":
            # Daily data
            mapping = {"1h": 1, "4h": 1, "1d": 1, "1w": 7}
            return mapping.get(horizon, 1)
        elif self.data_frequency == "4h":
            mapping = {"1h": 1, "4h": 1, "1d": 6, "1w": 42}
            return mapping.get(horizon, 1)
        else:
            # Hourly or more frequent
            return base_steps

    def save(self, filepath: str) -> bool:
        """Save model and normalization params to file."""
        if not self.is_trained or self.model is None:
            return False

        try:
            import joblib

            # Save Keras model
            model_path = filepath + ".keras"
            self.model.save(model_path)

            # Save metadata
            metadata = {
                "config": self.config,
                "feature_columns": self.feature_columns,
                "feature_means": self.feature_means,
                "feature_stds": self.feature_stds,
                "target_mean": self.target_mean,
                "target_std": self.target_std,
                "is_trained": self.is_trained,
                "last_train_date": self.last_train_date,
                "training_metrics": self.training_metrics,
                "data_frequency": self.data_frequency,
            }
            joblib.dump(metadata, filepath + ".meta")

            logger.info(f"LSTM model saved to {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False

    def load(self, filepath: str) -> bool:
        """Load model and normalization params from file."""
        try:
            import joblib

            # Load Keras model
            model_path = filepath + ".keras"
            self.model = load_model(model_path)

            # Load metadata
            metadata = joblib.load(filepath + ".meta")
            self.config = metadata.get("config", self.DEFAULT_CONFIG)
            self.feature_columns = metadata.get("feature_columns", [])
            self.feature_means = metadata.get("feature_means")
            self.feature_stds = metadata.get("feature_stds")
            self.target_mean = metadata.get("target_mean")
            self.target_std = metadata.get("target_std")
            self.is_trained = metadata.get("is_trained", True)
            self.last_train_date = metadata.get("last_train_date")
            self.training_metrics = metadata.get("training_metrics", {})
            self.data_frequency = metadata.get("data_frequency", "1d")

            logger.info(f"LSTM model loaded from {filepath}")
            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
