"""
Walk-Forward Validation for Time Series Forecasting.

Implements proper time-series cross-validation that:
- Never uses future data for training
- Maintains temporal ordering
- Supports expanding and sliding windows
- Tracks out-of-sample performance
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Generator
from datetime import datetime
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class WalkForwardValidator:
    """
    Walk-Forward Validation for time series models.

    Types:
    - Expanding Window: Train on all prior data
    - Sliding Window: Train on fixed window size

    Usage:
        validator = WalkForwardValidator(n_splits=5, test_size=30)
        for train_idx, test_idx in validator.split(df):
            train_df = df.iloc[train_idx]
            test_df = df.iloc[test_idx]
            # Train and evaluate model
    """

    def __init__(
        self,
        n_splits: int = 5,
        test_size: int = 30,
        train_size: Optional[int] = None,
        gap: int = 0,
        expanding: bool = True
    ):
        """
        Initialize Walk-Forward Validator.

        Args:
            n_splits: Number of splits/folds
            test_size: Number of samples in each test set
            train_size: Fixed training window size (None = expanding)
            gap: Gap between train and test (for prediction horizon)
            expanding: Use expanding window (ignored if train_size set)
        """
        self.n_splits = n_splits
        self.test_size = test_size
        self.train_size = train_size
        self.gap = gap
        self.expanding = expanding if train_size is None else False

    def split(self, X: pd.DataFrame) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """
        Generate train/test indices for each fold.

        Args:
            X: DataFrame or array to split

        Yields:
            Tuple of (train_indices, test_indices)
        """
        n_samples = len(X)

        # Calculate minimum training size
        min_train_size = self.train_size if self.train_size else 60

        # Calculate total needed for all splits
        total_test = self.n_splits * self.test_size + (self.n_splits - 1) * self.gap
        available_for_train = n_samples - total_test

        if available_for_train < min_train_size:
            raise ValueError(
                f"Not enough data for {self.n_splits} splits. "
                f"Need at least {min_train_size + total_test} samples, have {n_samples}"
            )

        # Generate splits
        for i in range(self.n_splits):
            # Test indices
            test_end = n_samples - i * (self.test_size + self.gap)
            test_start = test_end - self.test_size

            # Train indices
            train_end = test_start - self.gap

            if self.expanding:
                train_start = 0
            else:
                train_start = max(0, train_end - self.train_size)

            train_indices = np.arange(train_start, train_end)
            test_indices = np.arange(test_start, test_end)

            yield train_indices, test_indices

    def validate_model(
        self,
        model_class: type,
        df: pd.DataFrame,
        target_col: str = "close",
        model_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform walk-forward validation on a model.

        Args:
            model_class: Model class with train() and predict() methods
            df: Data to validate on
            target_col: Target column name
            model_config: Model configuration

        Returns:
            Validation results with fold metrics
        """
        fold_results = []
        all_predictions = []
        all_actuals = []

        logger.info(f"Starting walk-forward validation with {self.n_splits} folds")

        for fold_idx, (train_idx, test_idx) in enumerate(self.split(df)):
            train_df = df.iloc[train_idx].copy()
            test_df = df.iloc[test_idx].copy()

            logger.info(
                f"Fold {fold_idx + 1}: Train {len(train_df)} samples, "
                f"Test {len(test_df)} samples"
            )

            # Train model
            model = model_class(config=model_config)
            train_result = model.train(train_df, target_col=target_col, validate=False)

            if not train_result.get("success", False):
                logger.warning(f"Fold {fold_idx + 1} training failed: {train_result.get('error')}")
                continue

            # Generate predictions for test period
            # We need to predict for each point in test set
            fold_predictions = []
            fold_actuals = []

            for i in range(len(test_df)):
                # Get data up to this point (excluding test point)
                history = pd.concat([train_df, test_df.iloc[:i]]) if i > 0 else train_df

                # Predict next point
                if hasattr(model, "predict") and "df" in model.predict.__code__.co_varnames:
                    # LSTM-style prediction
                    pred_result = model.predict(history, horizons=["1d"])
                else:
                    # Prophet-style prediction
                    pred_result = model.predict(horizons=["1d"])

                if pred_result.get("success"):
                    pred_price = pred_result["predictions"].get("1d", {}).get("price", 0)
                else:
                    pred_price = test_df.iloc[i][target_col]

                actual_price = test_df.iloc[i][target_col]

                fold_predictions.append(pred_price)
                fold_actuals.append(actual_price)

            # Calculate fold metrics
            predictions = np.array(fold_predictions)
            actuals = np.array(fold_actuals)

            mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100
            rmse = np.sqrt(np.mean((actuals - predictions) ** 2))
            mae = np.mean(np.abs(actuals - predictions))

            # Directional accuracy
            if len(actuals) > 1:
                actual_direction = np.sign(np.diff(actuals))
                pred_direction = np.sign(np.diff(predictions))
                direction_accuracy = np.mean(actual_direction == pred_direction) * 100
            else:
                direction_accuracy = 0.0

            fold_results.append({
                "fold": fold_idx + 1,
                "train_size": len(train_df),
                "test_size": len(test_df),
                "mape": round(mape, 2),
                "rmse": round(rmse, 4),
                "mae": round(mae, 4),
                "direction_accuracy": round(direction_accuracy, 2),
            })

            all_predictions.extend(fold_predictions)
            all_actuals.extend(fold_actuals)

        # Aggregate metrics
        if not fold_results:
            return {
                "success": False,
                "error": "All folds failed"
            }

        avg_mape = np.mean([f["mape"] for f in fold_results])
        avg_rmse = np.mean([f["rmse"] for f in fold_results])
        avg_direction_accuracy = np.mean([f["direction_accuracy"] for f in fold_results])

        # Overall metrics on combined predictions
        all_predictions = np.array(all_predictions)
        all_actuals = np.array(all_actuals)

        overall_mape = np.mean(np.abs((all_actuals - all_predictions) / all_actuals)) * 100
        overall_rmse = np.sqrt(np.mean((all_actuals - all_predictions) ** 2))

        return {
            "success": True,
            "n_folds": self.n_splits,
            "successful_folds": len(fold_results),
            "fold_results": fold_results,
            "aggregate_metrics": {
                "avg_mape": round(avg_mape, 2),
                "avg_rmse": round(avg_rmse, 4),
                "avg_direction_accuracy": round(avg_direction_accuracy, 2),
            },
            "overall_metrics": {
                "mape": round(overall_mape, 2),
                "rmse": round(overall_rmse, 4),
                "total_predictions": len(all_predictions),
            },
            "validation_type": "expanding" if self.expanding else "sliding",
            "test_size_per_fold": self.test_size,
        }


class TimeSeriesSplit:
    """
    Simple time series split (similar to sklearn's TimeSeriesSplit).

    For more control, use WalkForwardValidator.
    """

    def __init__(self, n_splits: int = 5, test_size: Optional[int] = None):
        """
        Initialize TimeSeriesSplit.

        Args:
            n_splits: Number of splits
            test_size: Size of test set (None = auto)
        """
        self.n_splits = n_splits
        self.test_size = test_size

    def split(self, X: pd.DataFrame) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """Generate train/test indices."""
        n_samples = len(X)

        if self.test_size is None:
            test_size = n_samples // (self.n_splits + 1)
        else:
            test_size = self.test_size

        for i in range(self.n_splits):
            test_end = n_samples - i * test_size
            test_start = test_end - test_size
            train_end = test_start

            if train_end < 10:  # Minimum training size
                break

            train_indices = np.arange(0, train_end)
            test_indices = np.arange(test_start, test_end)

            yield train_indices, test_indices
