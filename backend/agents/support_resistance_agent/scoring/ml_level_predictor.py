"""
Machine Learning-based Future Level Prediction.

This module uses LightGBM/XGBoost to learn from historical level data
and enhance rule-based predictions with data-driven confidence scores.

Hybrid Approach:
1. Rule-based methods generate initial predictions (Fibonacci, Round Numbers, Spacing)
2. ML model scores these predictions based on learned patterns
3. Combined output provides both interpretability and accuracy
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os
import pickle
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Try to import ML libraries (optional - graceful fallback if not available)
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logger.warning("LightGBM not available. ML-based prediction will be disabled.")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available. Will use LightGBM if available.")


class MLLevelPredictor:
    """
    Machine Learning model for scoring and enhancing future level predictions.
    
    The model learns from historical data:
    - Which rule-based predictions actually became valid levels
    - What features make a prediction more likely to succeed
    - How to adjust confidence scores based on market conditions
    """
    
    def __init__(self, model_path: Optional[str] = None, use_model: bool = True):
        """
        Initialize ML Level Predictor.
        
        Args:
            model_path: Path to saved model file (optional)
            use_model: Whether to use ML model (False = rule-based only)
        """
        self.model = None
        self.model_path = model_path
        self.use_model = use_model and (LIGHTGBM_AVAILABLE or XGBOOST_AVAILABLE)
        self.is_trained = False
        
        if self.use_model:
            if model_path and os.path.exists(model_path):
                self._load_model(model_path)
            else:
                logger.info("No pre-trained model found. Model will need training.")
        else:
            logger.info("ML model disabled. Using rule-based predictions only.")
    
    def _load_model(self, model_path: str):
        """Load a pre-trained model from disk."""
        try:
            if LIGHTGBM_AVAILABLE:
                self.model = lgb.Booster(model_file=model_path)
            elif XGBOOST_AVAILABLE:
                self.model = xgb.Booster()
                self.model.load_model(model_path)
            else:
                logger.warning("No ML library available. Cannot load model.")
                return
            
            self.is_trained = True
            logger.info(f"Loaded ML model from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            self.is_trained = False
    
    def _save_model(self, model_path: str):
        """Save the trained model to disk."""
        if not self.model:
            logger.warning("No model to save.")
            return
        
        try:
            os.makedirs(os.path.dirname(model_path) if os.path.dirname(model_path) else '.', exist_ok=True)
            
            if LIGHTGBM_AVAILABLE and isinstance(self.model, lgb.Booster):
                self.model.save_model(model_path)
            elif XGBOOST_AVAILABLE:
                self.model.save_model(model_path)
            
            logger.info(f"Saved ML model to {model_path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def extract_features(
        self,
        predicted_level: Dict[str, Any],
        df: pd.DataFrame,
        current_price: float,
        timeframe: str
    ) -> np.ndarray:
        """
        Extract features for a predicted level to feed into the ML model.
        
        Features:
        - Price distance from current (normalized)
        - Source type (Fibonacci, Round Number, Spacing)
        - Rule-based confidence
        - Recent volatility
        - Price trend (up/down)
        - Volume profile at predicted level
        - Historical level density near prediction
        """
        price = predicted_level['price']
        source = predicted_level.get('source', 'unknown')
        rule_confidence = predicted_level.get('confidence', 50)
        
        # Feature 1: Normalized price distance from current
        price_distance_pct = abs(price - current_price) / current_price if current_price > 0 else 0
        
        # Feature 2: Source type encoding (one-hot like)
        source_fibonacci = 1.0 if source == 'fibonacci' else 0.0
        source_round = 1.0 if source == 'round_number' else 0.0
        source_spacing = 1.0 if source == 'spacing_pattern' else 0.0
        
        # Feature 3: Rule-based confidence (normalized 0-1)
        rule_confidence_norm = rule_confidence / 100.0
        
        # Feature 4: Recent volatility (20-period)
        if len(df) >= 20:
            returns = df['close'].pct_change().tail(20)
            volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.0  # Annualized
        else:
            volatility = 0.0
        
        # Feature 5: Price trend (1 = up, -1 = down, 0 = neutral)
        if len(df) >= 10:
            recent_prices = df['close'].tail(10).values
            price_trend = 1.0 if recent_prices[-1] > recent_prices[0] else -1.0
        else:
            price_trend = 0.0
        
        # Feature 6: Volume profile at predicted level (if available)
        if 'volume' in df.columns and len(df) >= 20:
            # Find volume near predicted level (within 2%)
            price_window = current_price * 0.02
            near_volume = df[
                (df['low'] <= price + price_window) & 
                (df['high'] >= price - price_window)
            ]['volume'].sum() if len(df) > 0 else 0
            volume_norm = near_volume / df['volume'].tail(100).sum() if df['volume'].sum() > 0 else 0.0
        else:
            volume_norm = 0.0
        
        # Feature 7: Historical level density (how many levels near this price)
        if len(df) >= 50:
            # Count how many times price was near this level (within 1%)
            price_window = current_price * 0.01
            historical_touches = len(df[
                (df['low'] <= price + price_window) & 
                (df['high'] >= price - price_window)
            ])
            density = historical_touches / len(df) if len(df) > 0 else 0.0
        else:
            density = 0.0
        
        # Feature 8: Level type (1 = support, -1 = resistance)
        level_type = 1.0 if predicted_level.get('type') == 'support' else -1.0
        
        # Feature 9: Relative position in price range
        if len(df) >= 20:
            recent_high = df['high'].tail(50).max()
            recent_low = df['low'].tail(50).min()
            price_range = recent_high - recent_low
            if price_range > 0:
                relative_position = (price - recent_low) / price_range
            else:
                relative_position = 0.5
        else:
            relative_position = 0.5
        
        # Feature 10: Timeframe encoding (normalized)
        timeframe_map = {'1m': 0.0, '5m': 0.1, '15m': 0.2, '30m': 0.3, 
                        '1h': 0.4, '4h': 0.5, '1d': 0.6, '1w': 0.7, '1mo': 0.8, '1y': 1.0}
        timeframe_encoded = timeframe_map.get(timeframe, 0.5)
        
        # Combine all features into array
        features = np.array([
            price_distance_pct,
            source_fibonacci,
            source_round,
            source_spacing,
            rule_confidence_norm,
            volatility,
            price_trend,
            volume_norm,
            density,
            level_type,
            relative_position,
            timeframe_encoded
        ])
        
        return features
    
    def score_predictions(
        self,
        predicted_levels: List[Dict[str, Any]],
        df: pd.DataFrame,
        current_price: float,
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """
        Score rule-based predictions using ML model.
        
        Args:
            predicted_levels: List of rule-based predictions
            df: Historical price data
            current_price: Current market price
            timeframe: Data timeframe
        
        Returns:
            List of predictions with ML-enhanced confidence scores
        """
        if not self.use_model or not self.is_trained or not self.model:
            # No model available - return original predictions
            logger.debug("ML model not available. Using rule-based predictions only.")
            return predicted_levels
        
        if not predicted_levels:
            return []
        
        try:
            # Extract features for all predictions
            feature_matrix = np.array([
                self.extract_features(level, df, current_price, timeframe)
                for level in predicted_levels
            ])
            
            # Get ML predictions (probability that level will become valid)
            if LIGHTGBM_AVAILABLE and isinstance(self.model, lgb.Booster):
                ml_scores = self.model.predict(feature_matrix)
            elif XGBOOST_AVAILABLE:
                ml_scores = self.model.predict(xgb.DMatrix(feature_matrix))
            else:
                logger.warning("ML library not available for prediction.")
                return predicted_levels
            
            # Combine rule-based and ML-based confidence
            # Weight: 40% rule-based, 60% ML-based (ML learns from data)
            enhanced_levels = []
            for i, level in enumerate(predicted_levels):
                ml_score = float(ml_scores[i]) * 100  # Convert to 0-100 scale
                rule_confidence = level.get('confidence', 50)
                
                # Hybrid confidence: weighted average
                hybrid_confidence = (0.4 * rule_confidence) + (0.6 * ml_score)
                hybrid_confidence = max(0, min(100, hybrid_confidence))  # Clamp to 0-100
                
                enhanced_level = level.copy()
                enhanced_level['confidence'] = round(hybrid_confidence, 2)
                enhanced_level['rule_confidence'] = round(rule_confidence, 2)  # Keep original
                enhanced_level['ml_confidence'] = round(ml_score, 2)  # ML score
                enhanced_level['prediction_source'] = 'hybrid'  # Mark as hybrid prediction
                
                enhanced_levels.append(enhanced_level)
            
            # Re-sort by enhanced confidence
            enhanced_levels = sorted(enhanced_levels, key=lambda x: x.get('confidence', 0), reverse=True)
            
            logger.debug(f"Enhanced {len(enhanced_levels)} predictions with ML model")
            return enhanced_levels
            
        except Exception as e:
            logger.error(f"Error in ML scoring: {e}. Falling back to rule-based predictions.")
            return predicted_levels
    
    def train_model(
        self,
        training_data: List[Dict[str, Any]],
        validation_split: float = 0.2,
        model_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Train the ML model on historical level prediction data.
        
        Args:
            training_data: List of training examples, each containing:
                - 'predicted_level': Original rule-based prediction
                - 'actual_outcome': Whether level became valid (1) or not (0)
                - 'df': Historical price data at prediction time
                - 'current_price': Price at prediction time
                - 'timeframe': Timeframe used
            validation_split: Fraction of data to use for validation
            model_path: Where to save the trained model
        
        Returns:
            Dictionary with training metrics
        """
        if not self.use_model:
            return {"error": "ML model is disabled"}
        
        if not training_data or len(training_data) < 50:
            logger.warning(f"Insufficient training data ({len(training_data) if training_data else 0} examples). Need at least 50.")
            return {"error": "Insufficient training data"}
        
        try:
            # Extract features and labels
            X = []
            y = []
            
            for example in training_data:
                features = self.extract_features(
                    example['predicted_level'],
                    example['df'],
                    example['current_price'],
                    example['timeframe']
                )
                X.append(features)
                y.append(example['actual_outcome'])
            
            X = np.array(X)
            y = np.array(y)
            
            # Split into train/validation
            split_idx = int(len(X) * (1 - validation_split))
            X_train, X_val = X[:split_idx], X[split_idx:]
            y_train, y_val = y[:split_idx], y[split_idx:]
            
            # Train model
            if LIGHTGBM_AVAILABLE:
                train_data = lgb.Dataset(X_train, label=y_train)
                val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
                
                params = {
                    'objective': 'binary',
                    'metric': 'binary_logloss',
                    'boosting_type': 'gbdt',
                    'num_leaves': 31,
                    'learning_rate': 0.05,
                    'feature_fraction': 0.9,
                    'bagging_fraction': 0.8,
                    'bagging_freq': 5,
                    'verbose': -1
                }
                
                self.model = lgb.train(
                    params,
                    train_data,
                    num_boost_round=100,
                    valid_sets=[val_data],
                    callbacks=[lgb.early_stopping(stopping_rounds=10), lgb.log_evaluation(period=10)]
                )
                
            elif XGBOOST_AVAILABLE:
                dtrain = xgb.DMatrix(X_train, label=y_train)
                dval = xgb.DMatrix(X_val, label=y_val)
                
                params = {
                    'objective': 'binary:logistic',
                    'eval_metric': 'logloss',
                    'max_depth': 6,
                    'learning_rate': 0.05,
                    'subsample': 0.8,
                    'colsample_bytree': 0.9
                }
                
                self.model = xgb.train(
                    params,
                    dtrain,
                    num_boost_round=100,
                    evals=[(dval, 'validation')],
                    early_stopping_rounds=10,
                    verbose_eval=10
                )
            else:
                return {"error": "No ML library available"}
            
            self.is_trained = True
            
            # Calculate metrics
            if LIGHTGBM_AVAILABLE:
                train_pred = self.model.predict(X_train)
                val_pred = self.model.predict(X_val)
            else:
                train_pred = self.model.predict(xgb.DMatrix(X_train))
                val_pred = self.model.predict(xgb.DMatrix(X_val))
            
            from sklearn.metrics import accuracy_score, roc_auc_score
            
            train_acc = accuracy_score(y_train, (train_pred > 0.5).astype(int))
            val_acc = accuracy_score(y_val, (val_pred > 0.5).astype(int))
            train_auc = roc_auc_score(y_train, train_pred)
            val_auc = roc_auc_score(y_val, val_pred)
            
            metrics = {
                'train_accuracy': round(train_acc, 4),
                'val_accuracy': round(val_acc, 4),
                'train_auc': round(train_auc, 4),
                'val_auc': round(val_auc, 4),
                'training_samples': len(X_train),
                'validation_samples': len(X_val)
            }
            
            # Save model if path provided
            if model_path:
                self._save_model(model_path)
            
            logger.info(f"Model trained successfully. Val Accuracy: {val_acc:.4f}, Val AUC: {val_auc:.4f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"error": str(e)}
