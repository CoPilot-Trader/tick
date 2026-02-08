"""
Trend Classification Agent - Main agent implementation.

Provides BUY/SELL/HOLD classification using:
- LightGBM classifier (primary)
- XGBoost classifier (alternative)

Milestone: M2 - Core Prediction Models
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pandas as pd

from core.interfaces.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class TrendClassificationAgent(BaseAgent):
    """
    Trend Classification Agent for directional signals.

    Features:
    - LightGBM and XGBoost classifiers
    - BUY/SELL/HOLD classification with probabilities
    - Multi-timeframe support (1h, 1d)
    - >55% directional accuracy target
    - Feature importance analysis
    - Model versioning via registry
    """

    SUPPORTED_TIMEFRAMES = ["1h", "1d"]
    TARGET_ACCURACY = 55.0  # Minimum accuracy target

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Trend Classification Agent."""
        super().__init__(name="trend_classification_agent", config=config)
        self.version = "2.0.0"
        self.supported_timeframes = self.SUPPORTED_TIMEFRAMES

        # Classifier instances (loaded on demand)
        self._classifiers: Dict[str, Any] = {}  # key: {symbol}_{timeframe}

        # Model registry and trainer
        self._registry = None
        self._trainer = None
        self._feature_builder = None

        # Configuration
        self._default_model = config.get("default_model", "lightgbm") if config else "lightgbm"
        self._threshold = config.get("threshold", 0.01) if config else 0.01

    def initialize(self) -> bool:
        """
        Initialize the Trend Classification Agent.

        - Set up classifier registry
        - Initialize training pipeline
        - Set up feature builder
        """
        try:
            from .models import ClassifierRegistry
            from .training import ClassifierTrainer
            from .features import FeatureBuilder

            self._registry = ClassifierRegistry()
            self._trainer = ClassifierTrainer(registry=self._registry)
            self._feature_builder = FeatureBuilder()

            self.initialized = True
            logger.info(f"TrendClassificationAgent v{self.version} initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize TrendClassificationAgent: {e}")
            self.initialized = False
            return False

    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Classify trend for a given symbol.

        Args:
            symbol: Stock symbol
            params: Optional parameters
                - timeframe: "1h" or "1d"
                - data: DataFrame with OHLCV + indicators

        Returns:
            Dictionary with trend classification (BUY/SELL/HOLD)
        """
        if not self.initialized:
            self.initialize()

        params = params or {}
        timeframe = params.get("timeframe", "1d")
        df = params.get("data")

        if df is None:
            return {
                "success": False,
                "error": "No data provided. Pass 'data' in params."
            }

        return self.classify(symbol=symbol, df=df, timeframe=timeframe)

    def classify(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = "1d",
        model_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Classify trend direction.

        Args:
            symbol: Stock symbol
            df: Recent OHLCV + indicator data
            timeframe: Timeframe (1h or 1d)
            model_type: "lightgbm" or "xgboost" (default: configured)

        Returns:
            Dictionary with classification result
        """
        if not self.initialized:
            self.initialize()

        if timeframe not in self.supported_timeframes:
            return {
                "success": False,
                "error": f"Unsupported timeframe: {timeframe}. Use one of {self.supported_timeframes}"
            }

        model_type = model_type or self._default_model

        try:
            # Build features
            df_feat = self._feature_builder.build_features(df)

            # Get or load classifier
            classifier = self._get_classifier(symbol, timeframe, model_type, df_feat)

            if classifier is None:
                return {
                    "success": False,
                    "error": "Failed to get or train classifier"
                }

            # Generate prediction
            result = classifier.predict(df_feat, return_probabilities=True)

            if result.get("success"):
                result["symbol"] = symbol
                result["timeframe"] = timeframe

            return result

        except Exception as e:
            logger.error(f"Classification failed for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }

    def _get_classifier(
        self,
        symbol: str,
        timeframe: str,
        model_type: str,
        df: pd.DataFrame
    ):
        """Get or load/train classifier."""
        cache_key = f"{symbol}_{timeframe}_{model_type}"

        if cache_key in self._classifiers:
            return self._classifiers[cache_key]

        # Try to load from registry
        if model_type == "lightgbm":
            from .models import LightGBMClassifier
            model_class = LightGBMClassifier
        else:
            from .models import XGBoostClassifier
            model_class = XGBoostClassifier

        load_result = self._registry.load_model(
            model_type, symbol, timeframe, model_class
        )

        if load_result.get("success"):
            self._classifiers[cache_key] = load_result["model"]
            return self._classifiers[cache_key]

        # Train new classifier
        logger.info(f"Training new {model_type} classifier for {symbol} ({timeframe})")

        classifier = model_class(config={"threshold": self._threshold})
        train_result = classifier.train(df)

        if train_result.get("success"):
            self._classifiers[cache_key] = classifier

            # Save to registry
            self._registry.save_model(
                model=classifier,
                name=model_type,
                symbol=symbol,
                timeframe=timeframe,
                model_type=model_type,
                metrics=train_result.get("metrics", {}),
            )

            return classifier

        logger.error(f"Failed to train classifier: {train_result.get('error')}")
        return None

    def classify_batch(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = "1d"
    ) -> Dict[str, Any]:
        """
        Generate classifications for all rows in DataFrame.

        Args:
            symbol: Stock symbol
            df: Historical data
            timeframe: Timeframe

        Returns:
            Dictionary with batch classifications
        """
        if not self.initialized:
            self.initialize()

        try:
            df_feat = self._feature_builder.build_features(df)

            classifier = self._get_classifier(
                symbol, timeframe, self._default_model, df_feat
            )

            if classifier is None:
                return {
                    "success": False,
                    "error": "Failed to get classifier"
                }

            result = classifier.predict_batch(df_feat)
            result["symbol"] = symbol
            result["timeframe"] = timeframe

            return result

        except Exception as e:
            logger.error(f"Batch classification failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def train(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = "1d",
        model_types: Optional[List[str]] = None,
        save_models: bool = True
    ) -> Dict[str, Any]:
        """
        Train classifiers for a symbol.

        Args:
            symbol: Stock symbol
            df: Historical data
            timeframe: Timeframe
            model_types: List of model types to train
            save_models: Save to registry

        Returns:
            Dictionary with training results
        """
        if not self.initialized:
            self.initialize()

        model_types = model_types or ["lightgbm", "xgboost"]

        try:
            if set(model_types) == {"lightgbm", "xgboost"}:
                # Train all
                return self._trainer.train_all(
                    df, symbol, timeframe,
                    horizon=1,
                    save_models=save_models
                )
            else:
                results = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "models": {},
                }

                for model_type in model_types:
                    if model_type == "lightgbm":
                        result = self._trainer.train_lightgbm(
                            df, symbol, timeframe,
                            save_model=save_models
                        )
                    else:
                        result = self._trainer.train_xgboost(
                            df, symbol, timeframe,
                            save_model=save_models
                        )
                    results["models"][model_type] = result

                return results

        except Exception as e:
            logger.error(f"Training failed for {symbol}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def cross_validate(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = "1d",
        n_splits: int = 5
    ) -> Dict[str, Any]:
        """
        Perform cross-validation for a symbol.

        Args:
            symbol: Stock symbol
            df: Historical data
            timeframe: Timeframe
            n_splits: Number of CV splits

        Returns:
            Cross-validation results
        """
        if not self.initialized:
            self.initialize()

        return self._trainer.cross_validate(
            df, symbol, timeframe,
            n_splits=n_splits,
            model_type=self._default_model
        )

    def compare_models(
        self,
        symbol: str,
        df: pd.DataFrame,
        timeframe: str = "1d",
        validation_days: int = 30
    ) -> Dict[str, Any]:
        """
        Compare LightGBM vs XGBoost for a symbol.

        Args:
            symbol: Stock symbol
            df: Historical data
            timeframe: Timeframe
            validation_days: Days for validation

        Returns:
            Comparison results with recommendation
        """
        if not self.initialized:
            self.initialize()

        return self._trainer.compare_models(df, symbol, timeframe, validation_days)

    def get_feature_importance(
        self,
        symbol: str,
        timeframe: str = "1d",
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Get feature importance from trained classifier.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe
            top_n: Number of top features

        Returns:
            Feature importance dict
        """
        cache_key = f"{symbol}_{timeframe}_{self._default_model}"

        if cache_key not in self._classifiers:
            return {
                "success": False,
                "error": "No classifier loaded for this symbol/timeframe"
            }

        classifier = self._classifiers[cache_key]
        importance = classifier.get_feature_importance(top_n=top_n)

        return {
            "success": True,
            "symbol": symbol,
            "timeframe": timeframe,
            "model_type": self._default_model,
            "top_features": importance,
        }

    def get_model_info(self, symbol: str, timeframe: str = "1d") -> Dict[str, Any]:
        """
        Get information about trained classifiers.

        Args:
            symbol: Stock symbol
            timeframe: Timeframe

        Returns:
            Model information
        """
        if not self.initialized:
            self.initialize()

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "lightgbm": self._registry.get_model_info("lightgbm", symbol, timeframe),
            "xgboost": self._registry.get_model_info("xgboost", symbol, timeframe),
            "cached_classifiers": [
                k for k in self._classifiers.keys()
                if k.startswith(f"{symbol}_{timeframe}")
            ],
        }

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cached classifiers.

        Args:
            symbol: Specific symbol to clear, or None for all
        """
        if symbol:
            keys_to_remove = [
                k for k in self._classifiers.keys()
                if k.startswith(symbol)
            ]
            for k in keys_to_remove:
                del self._classifiers[k]
        else:
            self._classifiers.clear()

    def health_check(self) -> Dict[str, Any]:
        """Check Trend Classification Agent health."""
        # Check if dependencies are available
        lightgbm_available = False
        xgboost_available = False

        try:
            import lightgbm
            lightgbm_available = True
        except ImportError:
            pass

        try:
            import xgboost
            xgboost_available = True
        except ImportError:
            pass

        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "agent": self.name,
            "version": self.version,
            "supported_timeframes": self.supported_timeframes,
            "target_accuracy": self.TARGET_ACCURACY,
            "default_model": self._default_model,
            "threshold": self._threshold,
            "dependencies": {
                "lightgbm": lightgbm_available,
                "xgboost": xgboost_available,
            },
            "cached_classifiers": len(self._classifiers),
        }


# Convenience function for standalone usage
def create_agent(config: Optional[Dict[str, Any]] = None) -> TrendClassificationAgent:
    """Create and initialize a Trend Classification Agent."""
    agent = TrendClassificationAgent(config=config)
    agent.initialize()
    return agent
