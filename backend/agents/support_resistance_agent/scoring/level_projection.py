"""
Level Projection for Support/Resistance Agent.

This module predicts:
1. How long existing levels will remain valid (level expiry)
2. Future potential levels based on historical patterns
3. Level strength decay over time

Why we need this:
- Levels don't last forever - they weaken over time
- We can predict when levels might become invalid
- Pattern recognition can help identify where new levels might form
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from ..utils.logger import get_logger
import numpy as np

logger = get_logger(__name__)

# Import ML predictor (optional - graceful fallback if not available)
try:
    from .ml_level_predictor import MLLevelPredictor
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.debug("ML Level Predictor not available")


class LevelProjector:
    """
    Projects levels forward in time and predicts future levels.
    
    Capabilities:
    1. Level Expiry Prediction - When will a level become invalid?
    2. Strength Decay - How will level strength change over time?
    3. Pattern-Based Prediction - Where might new levels form?
    4. ML-Enhanced Predictions - Uses machine learning to improve accuracy (hybrid approach)
    """
    
    def __init__(self, use_ml: bool = True, ml_model_path: Optional[str] = None):
        """
        Initialize the level projector.
        
        Args:
            use_ml: Whether to use ML model for enhanced predictions (default: True)
            ml_model_path: Path to pre-trained ML model (optional)
        """
        logger.debug("LevelProjector initialized")
        self.use_ml = False  # Default to False
        self.ml_predictor = None
        
        # Only try to use ML if explicitly requested and available
        if use_ml and ML_AVAILABLE:
            try:
                self.ml_predictor = MLLevelPredictor(model_path=ml_model_path, use_model=True)
                if self.ml_predictor.is_trained:
                    self.use_ml = True
                    logger.info("ML model loaded successfully. Using hybrid prediction approach.")
                else:
                    logger.info("ML model not trained yet. Using rule-based predictions only.")
            except Exception as e:
                logger.warning(f"Failed to initialize ML predictor: {e}. Using rule-based only.")
                self.use_ml = False
        elif use_ml and not ML_AVAILABLE:
            logger.info("ML libraries not available. Using rule-based predictions only.")
            self.use_ml = False
    
    def project_level_validity(
        self,
        level: Dict[str, Any],
        projection_days: int = 30
    ) -> Dict[str, Any]:
        """
        Project how long a level will remain valid.
        
        Factors:
        - Time since last touch (older = less valid)
        - Strength score (stronger = longer validity)
        - Historical level lifespan patterns
        
        Args:
            level: Level dictionary with strength, last_touch, etc.
            projection_days: How many days ahead to project (default: 30)
        
        Returns:
            Dictionary with:
            - valid_until: Estimated date when level becomes invalid
            - validity_probability: Probability level is still valid (0-100%)
            - projected_strength: Estimated strength after projection_days
        """
        from datetime import timezone
        
        strength = level.get('strength', 50)
        last_touch = level.get('last_touch')
        current_date = datetime.now(timezone.utc)
        
        # Calculate days since last touch
        if last_touch:
            if isinstance(last_touch, str):
                from dateutil.parser import parse
                last_touch = parse(last_touch)
            if hasattr(last_touch, 'to_pydatetime'):
                last_touch = last_touch.to_pydatetime()
            if last_touch.tzinfo is None:
                last_touch = last_touch.replace(tzinfo=timezone.utc)
            days_since_touch = (current_date - last_touch).days
        else:
            days_since_touch = 365  # Assume old if no touch data
        
        # Estimate level lifespan based on strength
        # Stronger levels (80+) last longer (90-180 days)
        # Weaker levels (50-80) last shorter (30-90 days)
        if strength >= 80:
            base_lifespan_days = 120  # Strong levels last ~4 months
        elif strength >= 60:
            base_lifespan_days = 60   # Moderate levels last ~2 months
        else:
            base_lifespan_days = 30   # Weak levels last ~1 month
        
        # Adjust for time since last touch
        # If touched recently, add more lifespan
        if days_since_touch <= 30:
            remaining_lifespan = base_lifespan_days
        elif days_since_touch <= 90:
            remaining_lifespan = base_lifespan_days - (days_since_touch - 30)
        else:
            remaining_lifespan = max(7, base_lifespan_days - (days_since_touch - 30))  # At least 7 days
        
        # Calculate validity date
        valid_until = current_date + timedelta(days=remaining_lifespan)
        
        # Calculate validity probability after projection_days
        if projection_days <= remaining_lifespan:
            # Level should still be valid
            validity_probability = max(50, 100 - (projection_days / remaining_lifespan * 50))
        else:
            # Level might be invalid
            validity_probability = max(10, 50 - ((projection_days - remaining_lifespan) / 30 * 40))
        
        # Project strength decay
        # Strength decreases over time (5-10 points per month)
        strength_decay_per_month = 5 if strength >= 80 else 8 if strength >= 60 else 10
        months_projected = projection_days / 30
        projected_strength = max(0, strength - (strength_decay_per_month * months_projected))
        
        return {
            'valid_until': valid_until.isoformat() + "Z",
            'validity_probability': round(validity_probability, 1),
            'projected_strength': round(projected_strength, 1),
            'remaining_lifespan_days': remaining_lifespan,
            'days_since_last_touch': days_since_touch
        }
    
    def predict_future_levels(
        self,
        df,
        current_price: float,
        timeframe: str = "1d",
        projection_periods: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Predict potential future support/resistance levels based on patterns.
        
        Methods:
        1. Fibonacci retracements from recent swing high/low
        2. Round number levels (psychological levels)
        3. Trend-based projections
        4. Historical level spacing patterns
        
        Args:
            df: Historical price data
            current_price: Current market price
            timeframe: Data timeframe ("1d", "1h", etc.)
            projection_periods: Number of periods ahead to predict
        
        Returns:
            List of predicted level dictionaries
        """
        if df.empty or len(df) < 20:
            return []
        
        predicted_levels = []
        
        # Method 1: Fibonacci Retracements
        recent_high = float(df['high'].tail(50).max())
        recent_low = float(df['low'].tail(50).min())
        price_range = recent_high - recent_low
        
        if price_range > 0:
            # Fibonacci levels: 0.236, 0.382, 0.5, 0.618, 0.786
            fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
            
            for fib in fib_levels:
                # Support levels (below current price)
                support_price = recent_low + (price_range * fib)
                if support_price < current_price and support_price > current_price * 0.9:
                    predicted_levels.append({
                        'price': round(support_price, 2),
                        'type': 'support',
                        'source': 'fibonacci',
                        'confidence': 60 - (abs(support_price - current_price) / current_price * 100),
                        'projected_timeframe': projection_periods
                    })
                
                # Resistance levels (above current price)
                resistance_price = recent_high - (price_range * (1 - fib))
                if resistance_price > current_price and resistance_price < current_price * 1.1:
                    predicted_levels.append({
                        'price': round(resistance_price, 2),
                        'type': 'resistance',
                        'source': 'fibonacci',
                        'confidence': 60 - (abs(resistance_price - current_price) / current_price * 100),
                        'projected_timeframe': projection_periods
                    })
        
        # Method 2: Round Number Levels (Psychological Levels)
        # Round numbers like $100, $150, $200 are often support/resistance
        round_numbers = self._get_round_numbers(current_price)
        for round_num in round_numbers:
            if abs(round_num - current_price) / current_price < 0.1:  # Within 10%
                level_type = 'support' if round_num < current_price else 'resistance'
                predicted_levels.append({
                    'price': round_num,
                    'type': level_type,
                    'source': 'round_number',
                    'confidence': 50,
                    'projected_timeframe': projection_periods
                })
        
        # Method 3: Historical Level Spacing
        # If historical levels are spaced by X%, predict next level at similar spacing
        historical_levels = self._extract_historical_levels(df)
        if len(historical_levels) >= 2:
            avg_spacing = self._calculate_avg_spacing(historical_levels)
            if avg_spacing > 0:
                # Predict next support (below current)
                next_support = current_price - (current_price * avg_spacing)
                if next_support > 0:
                    predicted_levels.append({
                        'price': round(next_support, 2),
                        'type': 'support',
                        'source': 'spacing_pattern',
                        'confidence': 45,
                        'projected_timeframe': projection_periods
                    })
                
                # Predict next resistance (above current)
                next_resistance = current_price + (current_price * avg_spacing)
                predicted_levels.append({
                    'price': round(next_resistance, 2),
                    'type': 'resistance',
                    'source': 'spacing_pattern',
                    'confidence': 45,
                    'projected_timeframe': projection_periods
                })
        
        # Remove duplicates and sort by confidence
        predicted_levels = self._deduplicate_levels(predicted_levels)
        predicted_levels = sorted(predicted_levels, key=lambda x: x.get('confidence', 0), reverse=True)
        
        # Enhance predictions with ML model if available
        if self.use_ml and self.ml_predictor and self.ml_predictor.is_trained:
            try:
                predicted_levels = self.ml_predictor.score_predictions(
                    predicted_levels,
                    df,
                    current_price,
                    timeframe
                )
                logger.info(f"Enhanced {len(predicted_levels)} predictions with ML model")
            except Exception as e:
                logger.warning(f"ML enhancement failed: {e}. Using rule-based predictions only.")
        
        logger.info(f"Predicted {len(predicted_levels)} future levels")
        return predicted_levels
    
    def _get_round_numbers(self, price: float) -> List[float]:
        """Get nearby round numbers (psychological levels)."""
        round_numbers = []
        
        # Round to nearest 5, 10, 25, 50, 100
        if price < 10:
            increments = [1, 2, 5]
        elif price < 100:
            increments = [5, 10, 25]
        elif price < 1000:
            increments = [10, 25, 50, 100]
        else:
            increments = [50, 100, 250, 500]
        
        for inc in increments:
            # Round down
            lower = (price // inc) * inc
            if lower > 0 and abs(lower - price) / price < 0.1:
                round_numbers.append(lower)
            
            # Round up
            upper = ((price // inc) + 1) * inc
            if abs(upper - price) / price < 0.1:
                round_numbers.append(upper)
        
        return sorted(set(round_numbers))
    
    def _extract_historical_levels(self, df) -> List[float]:
        """Extract historical support/resistance levels from price data."""
        levels = []
        
        # Use recent highs and lows as level candidates
        recent_highs = df['high'].tail(100).values
        recent_lows = df['low'].tail(100).values
        
        # Find significant levels (appear multiple times)
        from collections import Counter
        all_prices = list(recent_highs) + list(recent_lows)
        
        # Round to nearest 0.5% for grouping
        rounded_prices = [round(p / (p * 0.005)) * (p * 0.005) for p in all_prices]
        price_counts = Counter(rounded_prices)
        
        # Levels that appear 3+ times are significant
        for price, count in price_counts.items():
            if count >= 3:
                levels.append(price)
        
        return sorted(levels)
    
    def _calculate_avg_spacing(self, levels: List[float]) -> float:
        """Calculate average spacing between levels as percentage."""
        if len(levels) < 2:
            return 0.0
        
        spacings = []
        for i in range(1, len(levels)):
            spacing = abs(levels[i] - levels[i-1]) / levels[i-1]
            spacings.append(spacing)
        
        return np.mean(spacings) if spacings else 0.0
    
    def _deduplicate_levels(self, levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate levels (within 1% of each other)."""
        if not levels:
            return []
        
        unique_levels = []
        seen_prices = set()
        
        for level in levels:
            price = level['price']
            # Check if similar price already seen
            is_duplicate = False
            for seen_price in seen_prices:
                if abs(price - seen_price) / seen_price < 0.01:  # Within 1%
                    is_duplicate = True
                    # Keep the one with higher confidence
                    for existing in unique_levels:
                        if abs(existing['price'] - seen_price) / seen_price < 0.01:
                            if level.get('confidence', 0) > existing.get('confidence', 0):
                                unique_levels.remove(existing)
                                unique_levels.append(level)
                                seen_prices.remove(seen_price)
                                seen_prices.add(price)
                            break
                    break
            
            if not is_duplicate:
                unique_levels.append(level)
                seen_prices.add(price)
        
        return unique_levels
    
    def project_levels_for_timeframe(
        self,
        levels: List[Dict[str, Any]],
        timeframe: str,
        projection_periods: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Project levels for a specific timeframe (1m, 1h, 1d, 1w, 1y).
        
        Converts projection periods to actual time:
        - 1m: 20 periods = 20 minutes
        - 1h: 20 periods = 20 hours
        - 1d: 20 periods = 20 days
        - 1w: 20 periods = 20 weeks
        - 1y: 20 periods = 20 years
        
        Args:
            levels: List of current levels
            timeframe: Target timeframe
            projection_periods: Number of periods to project
        
        Returns:
            List of projected levels with timeframe-specific validity
        """
        timeframe_days_map = {
            '1m': 1/1440,  # 1 minute = 1/1440 days
            '5m': 5/1440,
            '15m': 15/1440,
            '30m': 30/1440,
            '1h': 1/24,     # 1 hour = 1/24 days
            '4h': 4/24,
            '1d': 1,        # 1 day
            '1w': 7,        # 1 week = 7 days
            '1mo': 30,      # 1 month ≈ 30 days
            '1y': 365       # 1 year = 365 days
        }
        
        projection_days = projection_periods * timeframe_days_map.get(timeframe, 1)
        
        projected_levels = []
        for level in levels:
            projection = self.project_level_validity(level, int(projection_days))
            
            projected_level = level.copy()
            projected_level.update({
                'projected_valid_until': projection['valid_until'],
                'projected_validity_probability': projection['validity_probability'],
                'projected_strength': projection['projected_strength'],
                'timeframe': timeframe,
                'projection_periods': projection_periods
            })
            projected_levels.append(projected_level)
        
        return projected_levels

