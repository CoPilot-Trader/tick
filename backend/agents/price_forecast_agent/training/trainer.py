"""
Unified Forecast Trainer for Price Forecast Agent.

Provides:
- Training pipeline for Prophet and LSTM models
- Hyperparameter tuning
- Model selection
- Training orchestration
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import numpy as np
import pandas as pd

from ..models.prophet_model import ProphetModel
from ..models.lstm_model import LSTMModel
from ..models.model_registry import ModelRegistry
from .walk_forward import WalkForwardValidator

logger = logging.getLogger(__name__)


class ForecastTrainer:
    """
    Unified training pipeline for forecast models.

    Features:
    - Train Prophet (baseline) and LSTM (primary) models
    - Walk-forward validation
    - Model comparison and selection
    - Automatic model registration
    """

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Forecast Trainer.

        Args:
            registry: Model registry for saving models
            config: Training configuration
        """
        self.registry = registry or ModelRegistry()
        self.config = config or {}

        # Default training configuration
        self.prophet_config = self.config.get("prophet", {
            "changepoint_prior_scale": 0.05,
            "seasonality_mode": "multiplicative",
        })

        self.lstm_config = self.config.get("lstm", {
            "sequence_length": 60,
            "lstm_units": [128, 64],
            "dropout_rate": 0.2,
            "epochs": 100,
        })

    def train_prophet(
        self,
        df: pd.DataFrame,
        symbol: str,
        validate: bool = True,
        save_model: bool = True
    ) -> Dict[str, Any]:
        """
        Train Prophet model for a symbol.

        Args:
            df: Historical OHLCV data
            symbol: Stock symbol
            validate: Perform validation
            save_model: Save to registry

        Returns:
            Training results
        """
        logger.info(f"Training Prophet model for {symbol}")

        model = ProphetModel(config=self.prophet_config)
        result = model.train(df, price_col="close", validate=validate)

        if result.get("success") and save_model:
            save_result = self.registry.save_model(
                model=model,
                name="prophet",
                symbol=symbol,
                model_type="prophet",
                metrics=result.get("metrics", {}),
                metadata={
                    "date_range": result.get("date_range"),
                    "training_samples": result.get("training_samples"),
                }
            )
            result["saved"] = save_result.get("success", False)
            result["version"] = save_result.get("version")

        return result

    def train_lstm(
        self,
        df: pd.DataFrame,
        symbol: str,
        feature_cols: Optional[List[str]] = None,
        save_model: bool = True
    ) -> Dict[str, Any]:
        """
        Train LSTM model for a symbol.

        Args:
            df: Historical OHLCV + features data
            symbol: Stock symbol
            feature_cols: Feature columns to use
            save_model: Save to registry

        Returns:
            Training results
        """
        logger.info(f"Training LSTM model for {symbol}")

        model = LSTMModel(config=self.lstm_config)
        result = model.train(
            df,
            target_col="close",
            feature_cols=feature_cols,
            validation_split=0.2
        )

        if result.get("success") and save_model:
            save_result = self.registry.save_model(
                model=model,
                name="lstm",
                symbol=symbol,
                model_type="lstm",
                metrics=result.get("metrics", {}),
                metadata={
                    "features_used": result.get("features_used"),
                    "sequence_length": result.get("sequence_length"),
                    "data_frequency": result.get("data_frequency"),
                }
            )
            result["saved"] = save_result.get("success", False)
            result["version"] = save_result.get("version")

        return result

    def train_all(
        self,
        df: pd.DataFrame,
        symbol: str,
        feature_cols: Optional[List[str]] = None,
        save_models: bool = True
    ) -> Dict[str, Any]:
        """
        Train all model types for a symbol.

        Args:
            df: Historical data
            symbol: Stock symbol
            feature_cols: Feature columns for LSTM
            save_models: Save to registry

        Returns:
            Training results for all models
        """
        results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "models": {},
        }

        # Train Prophet
        prophet_result = self.train_prophet(
            df, symbol,
            validate=True,
            save_model=save_models
        )
        results["models"]["prophet"] = prophet_result

        # Train LSTM
        lstm_result = self.train_lstm(
            df, symbol,
            feature_cols=feature_cols,
            save_model=save_models
        )
        results["models"]["lstm"] = lstm_result

        # Summary
        results["summary"] = {
            "prophet_success": prophet_result.get("success", False),
            "lstm_success": lstm_result.get("success", False),
            "total_models": 2,
            "successful_models": sum([
                prophet_result.get("success", False),
                lstm_result.get("success", False),
            ]),
        }

        return results

    def train_with_walk_forward(
        self,
        df: pd.DataFrame,
        symbol: str,
        model_type: str = "prophet",
        n_splits: int = 5,
        test_size: int = 30
    ) -> Dict[str, Any]:
        """
        Train and validate model using walk-forward validation.

        Args:
            df: Historical data
            symbol: Stock symbol
            model_type: "prophet" or "lstm"
            n_splits: Number of validation folds
            test_size: Test size per fold

        Returns:
            Walk-forward validation results
        """
        logger.info(f"Walk-forward validation for {symbol} ({model_type})")

        validator = WalkForwardValidator(
            n_splits=n_splits,
            test_size=test_size,
            expanding=True
        )

        if model_type == "prophet":
            model_class = ProphetModel
            config = self.prophet_config
        else:
            model_class = LSTMModel
            config = self.lstm_config

        result = validator.validate_model(
            model_class=model_class,
            df=df,
            target_col="close",
            model_config=config
        )

        result["symbol"] = symbol
        result["model_type"] = model_type

        return result

    def compare_models(
        self,
        df: pd.DataFrame,
        symbol: str,
        validation_days: int = 30
    ) -> Dict[str, Any]:
        """
        Train and compare Prophet vs LSTM models.

        Args:
            df: Historical data
            symbol: Stock symbol
            validation_days: Days for validation

        Returns:
            Comparison results with recommendation
        """
        logger.info(f"Comparing models for {symbol}")

        # Split data
        train_df = df.iloc[:-validation_days]
        val_df = df.iloc[-validation_days:]

        # Train both models
        prophet_model = ProphetModel(config=self.prophet_config)
        prophet_result = prophet_model.train(train_df, validate=False)

        lstm_model = LSTMModel(config=self.lstm_config)
        lstm_result = lstm_model.train(train_df, validate=False)

        # Evaluate on held-out validation set
        results = {
            "symbol": symbol,
            "validation_days": validation_days,
            "models": {},
        }

        # Evaluate Prophet
        if prophet_result.get("success"):
            prophet_pred = prophet_model.predict(horizons=["1d"])
            if prophet_pred.get("success"):
                # Simple evaluation: compare last prediction with actual
                pred_price = prophet_pred["predictions"]["1d"]["price"]
                actual_price = val_df["close"].iloc[0]
                prophet_error = abs((pred_price - actual_price) / actual_price) * 100

                results["models"]["prophet"] = {
                    "trained": True,
                    "mape_first_day": round(prophet_error, 2),
                    "training_metrics": prophet_result.get("metrics", {}),
                }
        else:
            results["models"]["prophet"] = {
                "trained": False,
                "error": prophet_result.get("error"),
            }

        # Evaluate LSTM
        if lstm_result.get("success"):
            lstm_pred = lstm_model.predict(train_df, horizons=["1d"])
            if lstm_pred.get("success"):
                pred_price = lstm_pred["predictions"]["1d"]["price"]
                actual_price = val_df["close"].iloc[0]
                lstm_error = abs((pred_price - actual_price) / actual_price) * 100

                results["models"]["lstm"] = {
                    "trained": True,
                    "mape_first_day": round(lstm_error, 2),
                    "training_metrics": lstm_result.get("metrics", {}),
                }
        else:
            results["models"]["lstm"] = {
                "trained": False,
                "error": lstm_result.get("error"),
            }

        # Recommendation
        prophet_ok = results["models"].get("prophet", {}).get("trained", False)
        lstm_ok = results["models"].get("lstm", {}).get("trained", False)

        if prophet_ok and lstm_ok:
            prophet_mape = results["models"]["prophet"].get("mape_first_day", float("inf"))
            lstm_mape = results["models"]["lstm"].get("mape_first_day", float("inf"))

            if lstm_mape < prophet_mape:
                recommendation = "lstm"
                reason = f"LSTM had lower error ({lstm_mape:.1f}% vs {prophet_mape:.1f}%)"
            else:
                recommendation = "prophet"
                reason = f"Prophet had lower error ({prophet_mape:.1f}% vs {lstm_mape:.1f}%)"
        elif lstm_ok:
            recommendation = "lstm"
            reason = "Only LSTM trained successfully"
        elif prophet_ok:
            recommendation = "prophet"
            reason = "Only Prophet trained successfully"
        else:
            recommendation = None
            reason = "Neither model trained successfully"

        results["recommendation"] = {
            "model": recommendation,
            "reason": reason,
        }

        return results

    def retrain_if_stale(
        self,
        symbol: str,
        df: pd.DataFrame,
        max_age_days: int = 7,
        model_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Retrain models if they're older than max_age_days.

        Args:
            symbol: Stock symbol
            df: Current data
            max_age_days: Maximum model age before retraining
            model_types: Types to check ("prophet", "lstm")

        Returns:
            Retraining results
        """
        model_types = model_types or ["prophet", "lstm"]
        results = {"symbol": symbol, "retrained": []}

        for model_type in model_types:
            info = self.registry.get_model_info(model_type, symbol)

            if not info.get("success"):
                # No model exists, train new one
                logger.info(f"No {model_type} model found for {symbol}, training new one")
                if model_type == "prophet":
                    train_result = self.train_prophet(df, symbol)
                else:
                    train_result = self.train_lstm(df, symbol)
                results["retrained"].append({
                    "model_type": model_type,
                    "reason": "no_existing_model",
                    "success": train_result.get("success", False),
                })
                continue

            # Check age
            versions = info.get("versions", [])
            if not versions:
                continue

            latest_version = versions[-1]
            created_at = datetime.fromisoformat(latest_version["created_at"])
            age_days = (datetime.now() - created_at).days

            if age_days > max_age_days:
                logger.info(
                    f"Model {model_type} for {symbol} is {age_days} days old, retraining"
                )
                if model_type == "prophet":
                    train_result = self.train_prophet(df, symbol)
                else:
                    train_result = self.train_lstm(df, symbol)
                results["retrained"].append({
                    "model_type": model_type,
                    "reason": f"model_age_{age_days}_days",
                    "success": train_result.get("success", False),
                })

        return results
