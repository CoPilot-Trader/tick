"""
Level Validator for Support/Resistance Agent.

This module validates detected levels against historical price reactions.

Why validate?
- Not all detected levels are actually significant
- We want levels where price actually reacted (bounced or rejected)
- Validation helps us filter out false positives
- Target: >60% of levels should show price reactions

What is validation?
- Support level: Price should bounce UP from the level
- Resistance level: Price should bounce DOWN from the level
- We check if price touched the level and then reversed direction
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LevelValidator:
    """
    Validates support/resistance levels against historical price reactions.
    
    How validation works:
    1. For each level, find when price touched it (within tolerance)
    2. Check if price reversed direction after touching
    3. Support: price should go up after touching
    4. Resistance: price should go down after touching
    5. Calculate validation rate (how many levels actually worked)
    """
    
    def __init__(self, tolerance: float = 0.005, lookforward_bars: int = 5):
        """
        Initialize the level validator.
        
        Args:
            tolerance: Price tolerance for "touching" level (default: 0.5%)
                     - 0.005 = 0.5% of price
                     - For $100 level: price between $99.50-$100.50 is considered "touching"
            lookforward_bars: Number of bars to check after touch (default: 5)
                             - How many candles to look ahead to see if price reversed
        """
        self.tolerance = tolerance
        self.lookforward_bars = lookforward_bars
        logger.debug(f"LevelValidator initialized: tolerance={tolerance}, lookforward={lookforward_bars}")
    
    def validate_level(
        self,
        level: Dict[str, Any],
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Validate a single level against historical price data.
        
        Process:
        1. Find all times price touched the level (within tolerance)
        2. For each touch, check if price reversed direction
        3. Count successful reactions
        4. Mark level as validated if >50% of touches showed reaction
        
        Args:
            level: Level dictionary with 'price' and 'type' keys
            df: DataFrame with OHLCV data
        
        Returns:
            Updated level dictionary with validation info:
            - validated: True/False
            - reaction_count: Number of successful reactions
            - touch_count: Total number of touches
            - validation_rate: Percentage of successful reactions
        """
        level_price = level['price']
        level_type = level.get('type', 'unknown')
        
        # Find touches (when price came within tolerance of level)
        touches = self._find_touches(level_price, df, self.tolerance)
        
        if not touches:
            # No touches found - can't validate
            level['validated'] = False
            level['reaction_count'] = 0
            level['touch_count'] = 0
            level['validation_rate'] = 0.0
            return level
        
        # Performance optimization: For large datasets, sample touches
        # This prevents checking every single touch when there are hundreds
        max_touches_to_check = 50  # Reasonable limit for fast validation
        if len(touches) > max_touches_to_check:
            # Sample touches evenly across the dataset
            step = len(touches) // max_touches_to_check
            touches_to_check = touches[::step][:max_touches_to_check]
        else:
            touches_to_check = touches
        
        # Check reactions for sampled touches
        reactions = []
        for touch_idx in touches_to_check:
            reaction = self._check_reaction(
                touch_idx,
                level_price,
                level_type,
                df
            )
            reactions.append(reaction)
        
        # Calculate validation metrics (scale up for sampled touches)
        sampled_touches = len(touches_to_check)
        reaction_count = sum(reactions)
        touch_count = len(touches)  # Actual total
        # Scale reaction count estimate
        if sampled_touches > 0:
            scaled_reaction_count = int(reaction_count * (touch_count / sampled_touches))
        else:
            scaled_reaction_count = 0
        validation_rate = reaction_count / sampled_touches if sampled_touches > 0 else 0.0
        
        # Level is validated if >50% of touches showed reaction
        validated = validation_rate > 0.5
        
        level['validated'] = validated
        level['reaction_count'] = scaled_reaction_count  # Use scaled estimate
        level['touch_count'] = touch_count
        level['validation_rate'] = validation_rate
        
        logger.debug(
            f"Level {level_price:.2f} ({level_type}): "
            f"{reaction_count}/{touch_count} reactions ({validation_rate:.1%})"
        )
        
        return level
    
    def validate_levels(
        self,
        levels: List[Dict[str, Any]],
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Validate multiple levels.
        
        Args:
            levels: List of level dictionaries
            df: DataFrame with OHLCV data
        
        Returns:
            List of validated level dictionaries
        """
        validated_levels = []
        
        for level in levels:
            validated_level = self.validate_level(level, df)
            validated_levels.append(validated_level)
        
        # Calculate overall validation rate
        total_levels = len(validated_levels)
        validated_count = sum(1 for l in validated_levels if l['validated'])
        overall_rate = validated_count / total_levels if total_levels > 0 else 0.0
        
        logger.info(
            f"Validated {validated_count}/{total_levels} levels "
            f"({overall_rate:.1%} validation rate)"
        )
        
        return validated_levels
    
    def _find_touches(
        self,
        level_price: float,
        df: pd.DataFrame,
        tolerance: float
    ) -> List[int]:
        """
        Find all indices where price touched the level.
        
        A "touch" means:
        - For support: low price came within tolerance
        - For resistance: high price came within tolerance
        
        Args:
            level_price: The level price to check
            df: DataFrame with OHLCV data
            tolerance: Price tolerance (percentage)
        
        Returns:
            List of row indices where price touched the level
        """
        tolerance_amount = level_price * tolerance
        
        # Vectorized operation (much faster than loop)
        # Check if low or high came within tolerance of level
        low_touched = (df['low'] - level_price).abs() <= tolerance_amount
        high_touched = (df['high'] - level_price).abs() <= tolerance_amount
        
        # Get indices where either low or high touched
        touches = df[low_touched | high_touched].index.tolist()
        
        return touches
    
    def _check_reaction(
        self,
        touch_idx: int,
        level_price: float,
        level_type: str,
        df: pd.DataFrame
    ) -> bool:
        """
        Check if price reacted after touching the level.
        
        Reaction means:
        - Support: Price bounces UP (low touches level, then price goes up)
        - Resistance: Price bounces DOWN (high touches level, then price goes down)
        
        Optimized: Uses vectorized operations for faster checking.
        
        Args:
            touch_idx: Index where price touched level
            level_price: The level price
            level_type: 'support' or 'resistance'
            df: DataFrame with OHLCV data
        
        Returns:
            True if price reacted, False otherwise
        """
        # Don't check if we're too close to the end
        if touch_idx + self.lookforward_bars >= len(df):
            return False
        
        # Get future rows using vectorized slicing (faster than iloc)
        end_idx = min(touch_idx + self.lookforward_bars + 1, len(df))
        future_rows = df.iloc[touch_idx + 1:end_idx]
        
        if len(future_rows) == 0:
            return False
        
        # Vectorized operations (much faster)
        if level_type == 'support':
            # Support: price should bounce UP
            touch_price = df.iloc[touch_idx]['low']  # Support touched at low
            future_highs = future_rows['high'].values
            
            # Reaction if price goes up (future high > touch price * 1.01)
            reaction = np.any(future_highs > touch_price * 1.01)  # At least 1% bounce
            
        elif level_type == 'resistance':
            # Resistance: price should bounce DOWN
            touch_price = df.iloc[touch_idx]['high']  # Resistance touched at high
            future_lows = future_rows['low'].values
            
            # Reaction if price goes down (future low < touch price * 0.99)
            reaction = np.any(future_lows < touch_price * 0.99)  # At least 1% rejection
            
        else:
            # Unknown type - can't validate
            reaction = False
        
        return reaction
