"""
Price Forecast Agent - Main agent implementation.

Provides multi-horizon price predictions using:
- Prophet model (baseline)
- LSTM model (primary)

Milestone: M2 - Core Prediction Models
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from core.interfaces.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class PriceForecastAgent(BaseAgent):
    """
    Price Forecast Agent for multi-horizon price prediction.

    Features:
    - Prophet model for baseline forecasts (interpretable, fast)
    - LSTM model for primary forecasts (higher accuracy)
    - Multi-horizon predictions (1h, 4h, 1d, 1w)
    - Confidence intervals
    - Walk-forward validation
    - Model versioning via registry
    """

    SUPPORTED_HORIZONS = ["1h", "4h", "1d", "1w"]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Price Forecast Agent."""
        super().__init__(name="price_forecast_agent", config=config)
        self.version = "2.0.0"
        self.supported_horizons = self.SUPPORTED_HORIZONS

        # Model instances (loaded on demand)
        self._prophet_models: Dict[str, Any] = {}  # symbol -> ProphetModel
        self._lstm_models: Dict[str, Any] = {}     # symbol -> LSTMModel

        # Model registry
        self._registry = None
        self._trainer = None

        # Configuration
        self._use_ensemble = config.get("use_ensemble", True) if config else True
        self._default_model = config.get("default_model", "lstm") if config else "lstm"

    def initialize(self) -> bool:
        """
        Initialize the Price Forecast Agent.

        - Set up model registry
        - Initialize training pipeline
        """
        try:
            from .models import ModelRegistry
            from .training import ForecastTrainer

            self._registry = ModelRegistry()
            self._trainer = ForecastTrainer(registry=self._registry)

            self.initialized = True
            logger.info(f"PriceForecastAgent v{self.version} initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize PriceForecastAgent: {e}")
            self.initialized = False
            return False

    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate price forecasts for a given symbol.

        Args:
            symbol: Stock symbol
            params: Optional parameters
                - horizons: List of horizons to predict
                - use_baseline: Use Prophet instead of LSTM
                - include_components: Include trend/seasonality

        Returns:
            Dictionary with price predictions for all horizons
        """
        if not self.initialized:
            self.initialize()

        params = params or {}
        horizons = params.get("horizons", self.supported_horizons)
        use_baseline = params.get("use_baseline", False)
        df = params.get("data")

        if df is None:
            return {
                "success": False,
                "error": "No data provided. Pass 'data' in params."
            }

        return self.predict(
            symbol=symbol,
            df=df,
            horizons=horizons,
            use_baseline=use_baseline
        )

    def predict(
        self,
        symbol: str,
        df: pd.DataFrame,
        horizons: Optional[List[str]] = None,
        use_baseline: bool = False,
        use_ensemble: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Generate price predictions for specified horizons.

        Args:
            symbol: Stock symbol
            df: Recent OHLCV data for prediction
            horizons: List of horizons (default: all supported)
            use_baseline: Use Prophet instead of LSTM
            use_ensemble: Use ensemble of both models

        Returns:
            Dictionary with predictions
        """
        if not self.initialized:
            self.initialize()

        horizons = horizons or self.supported_horizons
        use_ensemble = use_ensemble if use_ensemble is not None else self._use_ensemble

        try:
            # Determine which model(s) to use
            if use_baseline:
                result = self._predict_prophet(symbol, df, horizons)
            elif use_ensemble:
                result = self._predict_ensemble(symbol, df, horizons)
            else:
                result = self._predict_lstm(symbol, df, horizons)

            # If the ML model returned a soft failure, fall back to baseline
            if result.get("success"):
                return result
            raise RuntimeError(result.get("error", "ML model returned success=False"))

        except Exception as e:
            logger.warning(f"ML prediction failed for {symbol}: {e} — falling back to statistical baseline")
            try:
                return self._predict_statistical_baseline(symbol, df, horizons)
            except Exception as e2:
                logger.error(f"Statistical baseline also failed for {symbol}: {e2}")
                return {
                    "success": False,
                    "error": str(e)
                }

    def _predict_prophet(
        self,
        symbol: str,
        df: pd.DataFrame,
        horizons: List[str]
    ) -> Dict[str, Any]:
        """Generate predictions using Prophet model."""
        from .models import ProphetModel

        # Get or load model
        if symbol not in self._prophet_models:
            # Try to load from registry
            result = self._registry.load_model("prophet", symbol, ProphetModel)
            if result.get("success"):
                self._prophet_models[symbol] = result["model"]
            else:
                # Train new model
                logger.info(f"Training new Prophet model for {symbol}")
                model = ProphetModel()
                train_result = model.train(df)
                if not train_result.get("success"):
                    return train_result
                self._prophet_models[symbol] = model

        model = self._prophet_models[symbol]
        return model.predict(horizons=horizons)

    def _predict_lstm(
        self,
        symbol: str,
        df: pd.DataFrame,
        horizons: List[str]
    ) -> Dict[str, Any]:
        """Generate predictions using LSTM model."""
        from .models import LSTMModel

        # Get or load model
        if symbol not in self._lstm_models:
            # Try to load from registry
            result = self._registry.load_model("lstm", symbol, LSTMModel)
            if result.get("success"):
                self._lstm_models[symbol] = result["model"]
            else:
                # Train new model
                logger.info(f"Training new LSTM model for {symbol}")
                model = LSTMModel()
                train_result = model.train(df)
                if not train_result.get("success"):
                    return train_result
                self._lstm_models[symbol] = model

        model = self._lstm_models[symbol]
        return model.predict(df, horizons=horizons)

    def _predict_ensemble(
        self,
        symbol: str,
        df: pd.DataFrame,
        horizons: List[str]
    ) -> Dict[str, Any]:
        """Generate ensemble predictions from both models."""
        prophet_result = self._predict_prophet(symbol, df, horizons)
        lstm_result = self._predict_lstm(symbol, df, horizons)

        # If one fails, use the other
        if not prophet_result.get("success"):
            return lstm_result
        if not lstm_result.get("success"):
            return prophet_result

        # Combine predictions
        ensemble_predictions = {}
        current_price = lstm_result.get("current_price", prophet_result.get("current_price"))

        for horizon in horizons:
            prophet_pred = prophet_result.get("predictions", {}).get(horizon, {})
            lstm_pred = lstm_result.get("predictions", {}).get(horizon, {})

            if not prophet_pred or not lstm_pred:
                # Use available prediction
                ensemble_predictions[horizon] = lstm_pred or prophet_pred
                continue

            # Weighted average (LSTM weighted higher)
            prophet_weight = 0.3
            lstm_weight = 0.7

            prophet_price = prophet_pred.get("price", current_price)
            lstm_price = lstm_pred.get("price", current_price)
            ensemble_price = prophet_price * prophet_weight + lstm_price * lstm_weight

            prophet_conf = prophet_pred.get("confidence", 0.5)
            lstm_conf = lstm_pred.get("confidence", 0.5)
            ensemble_conf = prophet_conf * prophet_weight + lstm_conf * lstm_weight

            # Use LSTM's direction if confidence is higher
            if lstm_conf >= prophet_conf:
                direction = lstm_pred.get("direction", "NEUTRAL")
            else:
                direction = prophet_pred.get("direction", "NEUTRAL")

            # Combine confidence intervals
            lower = min(
                prophet_pred.get("price_lower", ensemble_price * 0.95),
                lstm_pred.get("price_lower", ensemble_price * 0.95)
            )
            upper = max(
                prophet_pred.get("price_upper", ensemble_price * 1.05),
                lstm_pred.get("price_upper", ensemble_price * 1.05)
            )

            ensemble_predictions[horizon] = {
                "price": round(ensemble_price, 2),
                "confidence": round(ensemble_conf, 3),
                "direction": direction,
                "price_lower": round(lower, 2),
                "price_upper": round(upper, 2),
                "change_pct": round((ensemble_price - current_price) / current_price * 100, 2),
                "components": {
                    "prophet_price": round(prophet_price, 2),
                    "lstm_price": round(lstm_price, 2),
                    "prophet_weight": prophet_weight,
                    "lstm_weight": lstm_weight,
                }
            }

        return {
            "success": True,
            "model_type": "ensemble",
            "symbol": symbol,
            "current_price": current_price,
            "predictions": ensemble_predictions,
            "generated_at": datetime.now().isoformat(),
        }

    def _predict_statistical_baseline(
        self,
        symbol: str,
        df: pd.DataFrame,
        horizons: List[str],
    ) -> Dict[str, Any]:
        """
        Pure-statistics baseline that needs no ML libraries.
        Uses EMA momentum + recent volatility to project price.
        Always available — acts as fallback when Prophet/TF are absent.
        """
        import numpy as np

        closes = df["close"].values if "close" in df.columns else df.iloc[:, 3].values
        current_price = float(closes[-1])

        # Simple momentum: EMA-10 slope projected forward
        ema_span = min(10, len(closes))
        weights = np.exp(np.linspace(-1, 0, ema_span))
        weights /= weights.sum()
        ema_recent = np.dot(closes[-ema_span:], weights)
        momentum = (current_price - ema_recent) / ema_recent  # fractional move per ~10 bars

        # Volatility from last 20 bars
        vol_window = min(20, len(closes) - 1)
        returns = np.diff(closes[-vol_window - 1:]) / closes[-vol_window - 1:-1]
        daily_vol = float(np.std(returns)) if len(returns) > 0 else 0.01

        horizon_bars = {"1h": 0.04, "4h": 0.17, "1d": 1.0, "1w": 5.0}

        predictions = {}
        for h in horizons:
            bars = horizon_bars.get(h, 1.0)
            projected_move = momentum * bars
            predicted_price = round(current_price * (1 + projected_move), 2)
            band = daily_vol * (bars ** 0.5) * current_price * 1.96  # ~95% CI
            direction = "UP" if predicted_price >= current_price else "DOWN"

            predictions[h] = {
                "price": predicted_price,
                "confidence": round(max(0.3, min(0.8, 1 - daily_vol * 10)), 3),
                "direction": direction,
                "price_lower": round(predicted_price - band, 2),
                "price_upper": round(predicted_price + band, 2),
                "change_pct": round(projected_move * 100, 2),
            }

        return {
            "success": True,
            "model_type": "statistical_baseline",
            "symbol": symbol,
            "current_price": current_price,
            "predictions": predictions,
            "generated_at": datetime.now().isoformat(),
        }

    def train_models(
        self,
        symbol: str,
        df: pd.DataFrame,
        walk_forward: bool = True,
        save_models: bool = True
    ) -> Dict[str, Any]:
        """
        Train models for a symbol.

        Args:
            symbol: Stock symbol
            df: Historical data
            walk_forward: Use walk-forward validation
            save_models: Save to registry

        Returns:
            Dictionary with training results
        """
        if not self.initialized:
            self.initialize()

        try:
            if walk_forward:
                # Train with walk-forward validation
                prophet_result = self._trainer.train_with_walk_forward(
                    df, symbol, model_type="prophet", n_splits=5
                )
                lstm_result = self._trainer.train_with_walk_forward(
                    df, symbol, model_type="lstm", n_splits=5
                )

                # Also train final models on all data
                final_result = self._trainer.train_all(df, symbol, save_models=save_models)

                return {
                    "success": True,
                    "symbol": symbol,
                    "walk_forward_validation": {
                        "prophet": prophet_result,
                        "lstm": lstm_result,
                    },
                    "final_training": final_result,
                }
            else:
                return self._trainer.train_all(df, symbol, save_models=save_models)

        except Exception as e:
            logger.error(f"Training failed for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def compare_models(
        self,
        symbol: str,
        df: pd.DataFrame,
        validation_days: int = 30
    ) -> Dict[str, Any]:
        """
        Compare Prophet vs LSTM for a symbol.

        Args:
            symbol: Stock symbol
            df: Historical data
            validation_days: Days for validation

        Returns:
            Comparison results with recommendation
        """
        if not self.initialized:
            self.initialize()

        return self._trainer.compare_models(df, symbol, validation_days)

    def get_model_info(self, symbol: str) -> Dict[str, Any]:
        """
        Get information about trained models for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Model information
        """
        if not self.initialized:
            self.initialize()

        return {
            "symbol": symbol,
            "prophet": self._registry.get_model_info("prophet", symbol),
            "lstm": self._registry.get_model_info("lstm", symbol),
            "cached_models": {
                "prophet": symbol in self._prophet_models,
                "lstm": symbol in self._lstm_models,
            }
        }

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cached models.

        Args:
            symbol: Specific symbol to clear, or None for all
        """
        if symbol:
            self._prophet_models.pop(symbol, None)
            self._lstm_models.pop(symbol, None)
        else:
            self._prophet_models.clear()
            self._lstm_models.clear()

    def health_check(self) -> Dict[str, Any]:
        """Check Price Forecast Agent health."""
        # Check if models are available
        try:
            from .models import ProphetModel, LSTMModel, ModelRegistry
            from .training import ForecastTrainer

            models_available = True
        except ImportError as e:
            models_available = False
            import_error = str(e)

        # Check if ML libraries are available
        prophet_available = False
        tensorflow_available = False

        try:
            from prophet import Prophet
            prophet_available = True
        except ImportError:
            pass

        try:
            import tensorflow
            tensorflow_available = True
        except ImportError:
            pass

        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "agent": self.name,
            "version": self.version,
            "supported_horizons": self.supported_horizons,
            "default_model": self._default_model,
            "use_ensemble": self._use_ensemble,
            "models_available": models_available,
            "dependencies": {
                "prophet": prophet_available,
                "tensorflow": tensorflow_available,
            },
            "cached_models": {
                "prophet_count": len(self._prophet_models),
                "lstm_count": len(self._lstm_models),
            },
        }


# Convenience function for standalone usage
def create_agent(config: Optional[Dict[str, Any]] = None) -> PriceForecastAgent:
    """Create and initialize a Price Forecast Agent."""
    agent = PriceForecastAgent(config=config)
    agent.initialize()
    return agent
