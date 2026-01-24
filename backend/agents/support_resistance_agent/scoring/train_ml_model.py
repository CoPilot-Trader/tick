"""
Training script for ML-based future level prediction model.

This script:
1. Collects historical level prediction data
2. Trains a LightGBM/XGBoost model to predict which rule-based predictions become valid
3. Saves the trained model for use in production

Usage:
    python train_ml_model.py --symbols AAPL MSFT GOOGL --lookback_days 365 --output_path models/level_predictor.model
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from agents.support_resistance_agent.agent import SupportResistanceAgent
from agents.support_resistance_agent.scoring.ml_level_predictor import MLLevelPredictor
from agents.support_resistance_agent.utils.logger import get_logger

logger = get_logger(__name__)


def collect_training_data(
    agent: SupportResistanceAgent,
    symbols: List[str],
    lookback_days: int = 365,
    timeframe: str = "1d"
) -> List[Dict[str, Any]]:
    """
    Collect historical level prediction data for training.
    
    Strategy:
    1. For each symbol, get historical data
    2. At each historical point, generate rule-based predictions
    3. Check if those predictions became valid levels in the future
    4. Create training examples with features and labels
    
    Args:
        agent: Initialized SupportResistanceAgent
        symbols: List of symbols to collect data for
        lookback_days: How far back to go
        timeframe: Data timeframe
    
    Returns:
        List of training examples
    """
    training_data = []
    
    for symbol in symbols:
        logger.info(f"Collecting training data for {symbol}...")
        
        try:
            # Get historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=lookback_days)
            
            df, data_source = agent.data_loader.load_ohlcv_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                timeframe=timeframe
            )
            
            if df.empty or len(df) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                continue
            
            # Slide a window through history
            # At each point, make predictions and check if they became valid
            window_size = 100  # Use 100 periods for prediction
            step_size = 20  # Step forward 20 periods each time
            
            for i in range(window_size, len(df) - 20, step_size):
                # Historical data up to this point
                historical_df = df.iloc[:i].copy()
                current_price = float(historical_df['close'].iloc[-1])
                
                # Future data to check if predictions became valid
                future_df = df.iloc[i:i+50].copy()  # Check next 50 periods
                
                # Generate rule-based predictions at this historical point
                predicted_levels = agent.level_projector.predict_future_levels(
                    historical_df,
                    current_price,
                    timeframe,
                    projection_periods=20
                )
                
                # Check which predictions became valid levels
                future_highs = future_df['high'].values
                future_lows = future_df['low'].values
                
                for pred_level in predicted_levels:
                    pred_price = pred_level['price']
                    pred_type = pred_level['type']
                    
                    # Check if price touched this level in the future (within 1%)
                    tolerance = pred_price * 0.01
                    touched = False
                    
                    if pred_type == 'support':
                        # Support: check if low touched the level
                        touched = any((future_lows <= pred_price + tolerance) & 
                                     (future_lows >= pred_price - tolerance))
                    else:  # resistance
                        # Resistance: check if high touched the level
                        touched = any((future_highs <= pred_price + tolerance) & 
                                     (future_highs >= pred_price - tolerance))
                    
                    # Create training example
                    training_example = {
                        'predicted_level': pred_level,
                        'actual_outcome': 1 if touched else 0,
                        'df': historical_df,
                        'current_price': current_price,
                        'timeframe': timeframe,
                        'symbol': symbol,
                        'timestamp': historical_df.index[-1]
                    }
                    
                    training_data.append(training_example)
            
            logger.info(f"Collected {len([d for d in training_data if d['symbol'] == symbol])} examples for {symbol}")
            
        except Exception as e:
            logger.error(f"Error collecting data for {symbol}: {e}")
            continue
    
    logger.info(f"Total training examples collected: {len(training_data)}")
    return training_data


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description="Train ML model for future level prediction")
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"],
                       help="Stock symbols to use for training")
    parser.add_argument("--lookback_days", type=int, default=365,
                       help="How many days of historical data to use")
    parser.add_argument("--timeframe", type=str, default="1d",
                       help="Data timeframe (1d, 1h, etc.)")
    parser.add_argument("--output_path", type=str, default="models/level_predictor.model",
                       help="Path to save trained model")
    parser.add_argument("--validation_split", type=float, default=0.2,
                       help="Fraction of data for validation")
    
    args = parser.parse_args()
    
    # Initialize agent
    logger.info("Initializing SupportResistanceAgent...")
    agent = SupportResistanceAgent(config={"use_mock_data": False})  # Use real data
    if not agent.initialize():
        logger.error("Failed to initialize agent")
        return
    
    # Collect training data
    logger.info("Collecting training data...")
    training_data = collect_training_data(
        agent,
        args.symbols,
        args.lookback_days,
        args.timeframe
    )
    
    if len(training_data) < 50:
        logger.error(f"Insufficient training data: {len(training_data)} examples. Need at least 50.")
        return
    
    # Initialize ML predictor
    logger.info("Initializing ML predictor...")
    ml_predictor = MLLevelPredictor(use_model=True)
    
    # Train model
    logger.info("Training model...")
    metrics = ml_predictor.train_model(
        training_data,
        validation_split=args.validation_split,
        model_path=args.output_path
    )
    
    if "error" in metrics:
        logger.error(f"Training failed: {metrics['error']}")
        return
    
    # Print results
    logger.info("=" * 50)
    logger.info("Training Results:")
    logger.info(f"  Training Samples: {metrics['training_samples']}")
    logger.info(f"  Validation Samples: {metrics['validation_samples']}")
    logger.info(f"  Training Accuracy: {metrics['train_accuracy']:.4f}")
    logger.info(f"  Validation Accuracy: {metrics['val_accuracy']:.4f}")
    logger.info(f"  Training AUC: {metrics['train_auc']:.4f}")
    logger.info(f"  Validation AUC: {metrics['val_auc']:.4f}")
    logger.info(f"  Model saved to: {args.output_path}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
