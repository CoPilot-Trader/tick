"""
Prophet Model for Baseline Price Forecasting.

Uses Facebook Prophet for time series forecasting with:
- Automatic seasonality detection (daily, weekly, yearly)
- Trend changepoint detection
- Holiday effects (market-aware)
- Uncertainty intervals
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Optional import - Prophet may not be installed
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not installed. Use: pip install prophet")


class ProphetModel:
    """
    Prophet-based price forecasting model.

    Features:
    - Multiplicative seasonality for price data
    - Custom market holidays
    - Configurable changepoint detection
    - Multi-horizon predictions with confidence intervals
    """

    # Market holidays (US)
    MARKET_HOLIDAYS = [
        {"holiday": "new_year", "ds": pd.to_datetime("2024-01-01"), "lower_window": -1, "upper_window": 1},
        {"holiday": "mlk_day", "ds": pd.to_datetime("2024-01-15"), "lower_window": 0, "upper_window": 0},
        {"holiday": "presidents_day", "ds": pd.to_datetime("2024-02-19"), "lower_window": 0, "upper_window": 0},
        {"holiday": "good_friday", "ds": pd.to_datetime("2024-03-29"), "lower_window": 0, "upper_window": 0},
        {"holiday": "memorial_day", "ds": pd.to_datetime("2024-05-27"), "lower_window": 0, "upper_window": 0},
        {"holiday": "juneteenth", "ds": pd.to_datetime("2024-06-19"), "lower_window": 0, "upper_window": 0},
        {"holiday": "independence_day", "ds": pd.to_datetime("2024-07-04"), "lower_window": 0, "upper_window": 0},
        {"holiday": "labor_day", "ds": pd.to_datetime("2024-09-02"), "lower_window": 0, "upper_window": 0},
        {"holiday": "thanksgiving", "ds": pd.to_datetime("2024-11-28"), "lower_window": 0, "upper_window": 1},
        {"holiday": "christmas", "ds": pd.to_datetime("2024-12-25"), "lower_window": -1, "upper_window": 0},
    ]

    # Horizon configurations (horizon name -> periods in days)
    HORIZON_CONFIG = {
        "1h": 1/24,      # 1 hour = 1/24 day
        "4h": 4/24,      # 4 hours
        "1d": 1,         # 1 day
        "1w": 7,         # 1 week
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Prophet Model.

        Args:
            config: Optional configuration dict
                - changepoint_prior_scale: Trend flexibility (default: 0.05)
                - seasonality_prior_scale: Seasonality strength (default: 10)
                - seasonality_mode: 'multiplicative' or 'additive'
                - include_holidays: Include market holidays
        """
        self.config = config or {}
        self.model: Optional[Prophet] = None
        self.is_trained = False
        self.last_train_date: Optional[datetime] = None
        self.training_metrics: Dict[str, float] = {}

        # Model hyperparameters
        self.changepoint_prior_scale = self.config.get("changepoint_prior_scale", 0.05)
        self.seasonality_prior_scale = self.config.get("seasonality_prior_scale", 10)
        self.seasonality_mode = self.config.get("seasonality_mode", "multiplicative")
        self.include_holidays = self.config.get("include_holidays", True)

    def _prepare_data(self, df: pd.DataFrame, price_col: str = "close") -> pd.DataFrame:
        """
        Prepare data for Prophet.

        Prophet requires columns 'ds' (datetime) and 'y' (value).

        Args:
            df: Input DataFrame with OHLCV data
            price_col: Column to use for prediction (default: 'close')

        Returns:
            DataFrame with 'ds' and 'y' columns
        """
        prophet_df = pd.DataFrame()

        # Get timestamp column
        if "bar_ts" in df.columns:
            prophet_df["ds"] = pd.to_datetime(df["bar_ts"])
        elif "timestamp" in df.columns:
            prophet_df["ds"] = pd.to_datetime(df["timestamp"])
        elif isinstance(df.index, pd.DatetimeIndex):
            prophet_df["ds"] = df.index
        else:
            raise ValueError("No valid datetime column found")

        # Get price column
        if price_col in df.columns:
            prophet_df["y"] = df[price_col].values
        else:
            raise ValueError(f"Price column '{price_col}' not found")

        # Remove timezone if present (Prophet doesn't handle tz well)
        if prophet_df["ds"].dt.tz is not None:
            prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)

        # Sort by date
        prophet_df = prophet_df.sort_values("ds").reset_index(drop=True)

        # Remove any NaN values
        prophet_df = prophet_df.dropna()

        return prophet_df

    def _get_holidays_df(self) -> pd.DataFrame:
        """Create holidays DataFrame for Prophet."""
        if not self.include_holidays:
            return pd.DataFrame()

        holidays_list = []
        # Generate holidays for multiple years
        for year_offset in range(-2, 3):  # 5 years of holidays
            for holiday in self.MARKET_HOLIDAYS:
                new_holiday = holiday.copy()
                new_holiday["ds"] = holiday["ds"] + pd.DateOffset(years=year_offset)
                holidays_list.append(new_holiday)

        return pd.DataFrame(holidays_list)

    def train(
        self,
        df: pd.DataFrame,
        price_col: str = "close",
        validate: bool = True,
        validation_days: int = 30
    ) -> Dict[str, Any]:
        """
        Train Prophet model on historical data.

        Args:
            df: DataFrame with OHLCV data
            price_col: Column to predict
            validate: Whether to perform validation
            validation_days: Days to hold out for validation

        Returns:
            Training results with metrics
        """
        if not PROPHET_AVAILABLE:
            return {
                "success": False,
                "error": "Prophet not installed. Use: pip install prophet"
            }

        try:
            # Prepare data
            prophet_df = self._prepare_data(df, price_col)

            if len(prophet_df) < 60:
                return {
                    "success": False,
                    "error": f"Insufficient data: {len(prophet_df)} rows (need >= 60)"
                }

            # Split for validation
            if validate and len(prophet_df) > validation_days:
                train_df = prophet_df.iloc[:-validation_days]
                val_df = prophet_df.iloc[-validation_days:]
            else:
                train_df = prophet_df
                val_df = None

            # Initialize Prophet
            holidays_df = self._get_holidays_df()

            self.model = Prophet(
                seasonality_mode=self.seasonality_mode,
                changepoint_prior_scale=self.changepoint_prior_scale,
                seasonality_prior_scale=self.seasonality_prior_scale,
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,  # Usually noisy for daily data
                holidays=holidays_df if len(holidays_df) > 0 else None,
            )

            # Fit model
            logger.info(f"Training Prophet on {len(train_df)} data points...")
            self.model.fit(train_df)

            self.is_trained = True
            self.last_train_date = datetime.now()

            # Calculate validation metrics
            metrics = {}
            if val_df is not None and len(val_df) > 0:
                future = self.model.make_future_dataframe(periods=len(val_df))
                forecast = self.model.predict(future)

                # Get predictions for validation period
                val_predictions = forecast.tail(len(val_df))["yhat"].values
                val_actual = val_df["y"].values

                # Calculate metrics
                mape = np.mean(np.abs((val_actual - val_predictions) / val_actual)) * 100
                rmse = np.sqrt(np.mean((val_actual - val_predictions) ** 2))
                mae = np.mean(np.abs(val_actual - val_predictions))

                # Directional accuracy
                if len(val_actual) > 1:
                    actual_direction = np.sign(np.diff(val_actual))
                    pred_direction = np.sign(np.diff(val_predictions))
                    direction_accuracy = np.mean(actual_direction == pred_direction) * 100
                else:
                    direction_accuracy = 0.0

                metrics = {
                    "mape": round(mape, 2),
                    "rmse": round(rmse, 4),
                    "mae": round(mae, 4),
                    "direction_accuracy": round(direction_accuracy, 2),
                    "validation_days": validation_days,
                }

            self.training_metrics = metrics

            return {
                "success": True,
                "model_type": "prophet",
                "training_samples": len(train_df),
                "date_range": {
                    "start": str(train_df["ds"].min()),
                    "end": str(train_df["ds"].max()),
                },
                "metrics": metrics,
                "trained_at": self.last_train_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Prophet training failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def predict(
        self,
        horizons: Optional[List[str]] = None,
        return_components: bool = False
    ) -> Dict[str, Any]:
        """
        Generate predictions for specified horizons.

        Args:
            horizons: List of horizons ["1h", "4h", "1d", "1w"]
            return_components: Include trend/seasonality components

        Returns:
            Dictionary with predictions and confidence intervals
        """
        if not self.is_trained or self.model is None:
            return {
                "success": False,
                "error": "Model not trained"
            }

        if not PROPHET_AVAILABLE:
            return {
                "success": False,
                "error": "Prophet not installed"
            }

        try:
            horizons = horizons or list(self.HORIZON_CONFIG.keys())

            # Get maximum horizon in days
            max_horizon_days = max(self.HORIZON_CONFIG.get(h, 1) for h in horizons)
            periods = max(int(np.ceil(max_horizon_days)), 1)

            # Make future dataframe
            future = self.model.make_future_dataframe(periods=periods, freq="D")
            forecast = self.model.predict(future)

            # Get last known value for reference
            last_value = forecast.iloc[-periods - 1]["yhat"] if len(forecast) > periods else forecast.iloc[0]["yhat"]

            predictions = {}
            for horizon in horizons:
                if horizon not in self.HORIZON_CONFIG:
                    continue

                horizon_days = self.HORIZON_CONFIG[horizon]

                # Get appropriate row (interpolate for sub-day)
                if horizon_days < 1:
                    # For sub-day, use last prediction scaled
                    idx = -periods
                    row = forecast.iloc[idx]
                    factor = horizon_days  # Linear interpolation
                    predicted_change = (row["yhat"] - last_value) * factor
                    predicted_value = last_value + predicted_change

                    # Scale confidence interval
                    yhat_lower = last_value + (row["yhat_lower"] - last_value) * factor
                    yhat_upper = last_value + (row["yhat_upper"] - last_value) * factor
                else:
                    idx = -periods + int(horizon_days) - 1
                    if idx >= 0 or abs(idx) > len(forecast):
                        idx = -1
                    row = forecast.iloc[idx]
                    predicted_value = row["yhat"]
                    yhat_lower = row["yhat_lower"]
                    yhat_upper = row["yhat_upper"]

                # Calculate confidence
                confidence_interval = yhat_upper - yhat_lower
                # Confidence decreases as interval widens
                base_confidence = 0.8
                confidence = max(0.3, base_confidence - (confidence_interval / predicted_value) * 0.5)

                # Direction
                direction = "UP" if predicted_value > last_value else "DOWN" if predicted_value < last_value else "NEUTRAL"

                predictions[horizon] = {
                    "price": round(predicted_value, 2),
                    "confidence": round(confidence, 3),
                    "direction": direction,
                    "price_lower": round(yhat_lower, 2),
                    "price_upper": round(yhat_upper, 2),
                    "change_pct": round((predicted_value - last_value) / last_value * 100, 2),
                }

                if return_components and "trend" in row:
                    predictions[horizon]["components"] = {
                        "trend": round(row["trend"], 2),
                        "weekly": round(row.get("weekly", 0), 2),
                        "yearly": round(row.get("yearly", 0), 2),
                    }

            return {
                "success": True,
                "model_type": "prophet",
                "current_price": round(last_value, 2),
                "predictions": predictions,
                "generated_at": datetime.now().isoformat(),
                "model_trained_at": self.last_train_date.isoformat() if self.last_train_date else None,
            }

        except Exception as e:
            logger.error(f"Prophet prediction failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_trend_changepoints(self) -> Dict[str, Any]:
        """Get detected trend changepoints from the model."""
        if not self.is_trained or self.model is None:
            return {"success": False, "error": "Model not trained"}

        try:
            changepoints = self.model.changepoints
            return {
                "success": True,
                "changepoints": [str(cp) for cp in changepoints],
                "count": len(changepoints),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def save(self, filepath: str) -> bool:
        """Save model to file."""
        if not self.is_trained or self.model is None:
            return False

        try:
            import joblib
            model_data = {
                "model": self.model,
                "config": self.config,
                "is_trained": self.is_trained,
                "last_train_date": self.last_train_date,
                "training_metrics": self.training_metrics,
            }
            joblib.dump(model_data, filepath)
            logger.info(f"Prophet model saved to {filepath}")
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
            self.is_trained = model_data.get("is_trained", True)
            self.last_train_date = model_data.get("last_train_date")
            self.training_metrics = model_data.get("training_metrics", {})
            logger.info(f"Prophet model loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
