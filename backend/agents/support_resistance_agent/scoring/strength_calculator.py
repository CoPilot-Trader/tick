"""
Strength Calculator for Support/Resistance Agent.

This module calculates strength scores (0-100) and breakout probabilities (0-100%)
for detected levels.

Why strength scoring?
- Not all levels are equally important
- Strong levels (high score) are more reliable
- Helps filter out weak levels
- Provides confidence metric for trading decisions

Strength factors:
1. Touch count (40%): More touches = stronger level
2. Time relevance (30%): Recent touches = more relevant
3. Price reaction (30%): Better reactions = stronger level

Breakout Probability:
- Calculates probability that price will break through a level
- Based on: distance from current price, strength score, historical patterns
"""

from typing import List, Dict, Any
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)


class StrengthCalculator:
    """
    Calculates strength scores for support/resistance levels.
    
    Strength Score Formula:
    Strength = (
        Touch_Count_Score * 0.4 +      # 40% weight
        Time_Relevance_Score * 0.3 +    # 30% weight
        Price_Reaction_Score * 0.3     # 30% weight
    ) * 100
    
    Score ranges from 0-100:
    - 80-100: Very strong level (highly reliable)
    - 60-79:  Strong level (reliable)
    - 40-59:  Moderate level (somewhat reliable)
    - 0-39:   Weak level (unreliable, should be filtered)
    """
    
    def __init__(
        self,
        touch_weight: float = 0.4,
        time_weight: float = 0.3,
        reaction_weight: float = 0.3
    ):
        """
        Initialize the strength calculator.
        
        Args:
            touch_weight: Weight for touch count score (default: 0.4 = 40%)
            time_weight: Weight for time relevance score (default: 0.3 = 30%)
            reaction_weight: Weight for price reaction score (default: 0.3 = 30%)
        
        Note: Weights should sum to 1.0
        """
        self.touch_weight = touch_weight
        self.time_weight = time_weight
        self.reaction_weight = reaction_weight
        
        # Verify weights sum to 1.0
        total_weight = touch_weight + time_weight + reaction_weight
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total_weight}, not 1.0. Normalizing...")
            self.touch_weight /= total_weight
            self.time_weight /= total_weight
            self.reaction_weight /= total_weight
        
        logger.debug(
            f"StrengthCalculator initialized: "
            f"touch={self.touch_weight}, time={self.time_weight}, reaction={self.reaction_weight}"
        )
    
    def calculate_strength(self, level: Dict[str, Any], current_date: datetime = None) -> int:
        """
        Calculate strength score for a level.
        
        Args:
            level: Level dictionary with:
                - touches: Number of times price touched
                - touch_count: Alternative key for touches
                - validation_rate: Percentage of successful reactions
                - first_touch: First touch timestamp
                - last_touch: Last touch timestamp
            current_date: Current date for time relevance (default: now)
        
        Returns:
            Strength score (0-100 integer)
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        # Get touch count
        touches = level.get('touches', level.get('touch_count', 0))
        
        # Calculate component scores
        touch_score = self._touch_count_score(touches)
        time_score = self._time_relevance_score(level, current_date)
        reaction_score = self._price_reaction_score(level)
        
        # Calculate weighted average
        strength = (
            touch_score * self.touch_weight +
            time_score * self.time_weight +
            reaction_score * self.reaction_weight
        ) * 100
        
        # Round to integer (0-100)
        strength = int(round(strength))
        strength = max(0, min(100, strength))  # Clamp to 0-100
        
        logger.debug(
            f"Level {level.get('price', 0):.2f}: "
            f"strength={strength} "
            f"(touch={touch_score:.2f}, time={time_score:.2f}, reaction={reaction_score:.2f})"
        )
        
        return strength
    
    def calculate_strengths(
        self,
        levels: List[Dict[str, Any]],
        current_date: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate strength scores for multiple levels.
        
        Args:
            levels: List of level dictionaries
            current_date: Current date for time relevance
        
        Returns:
            List of levels with 'strength' key added
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        for level in levels:
            level['strength'] = self.calculate_strength(level, current_date)
        
        logger.info(f"Calculated strength scores for {len(levels)} levels")
        return levels
    
    def calculate_breakout_probability(
        self,
        level: Dict[str, Any],
        current_price: float
    ) -> float:
        """
        Calculate breakout probability (0-100%) for a level.
        
        Breakout probability factors:
        1. Distance from current price (closer = higher probability)
        2. Strength score (stronger = lower probability of breaking)
        3. Level type (support vs resistance)
        4. Historical breakout patterns (if available)
        
        Args:
            level: Level dictionary with:
                - price: Level price
                - strength: Strength score (0-100)
                - type: 'support' or 'resistance'
            current_price: Current market price
        
        Returns:
            Breakout probability as percentage (0.0-100.0)
        """
        level_price = level.get('price', 0)
        strength = level.get('strength', 50)
        level_type = level.get('type', 'unknown')
        
        if level_price == 0:
            return 0.0
        
        # Calculate distance factor (0-1)
        # Closer to level = higher probability of breakout
        price_distance = abs(current_price - level_price) / level_price
        distance_factor = max(0.0, min(1.0, 1.0 - (price_distance * 10)))  # Normalize
        
        # Strength factor (0-1)
        # Stronger levels = lower probability of breaking
        # Convert strength (0-100) to inverse factor (1.0-0.0)
        strength_factor = 1.0 - (strength / 100.0)
        
        # Direction factor
        # For support: higher probability if price is approaching from above
        # For resistance: higher probability if price is approaching from below
        if level_type == 'support':
            # Support: price below level = approaching, higher breakout prob
            if current_price < level_price:
                direction_factor = 1.0
            else:
                # Price above support = already broken, low prob
                direction_factor = 0.2
        elif level_type == 'resistance':
            # Resistance: price above level = approaching, higher breakout prob
            if current_price > level_price:
                direction_factor = 1.0
            else:
                # Price below resistance = not approaching, lower prob
                direction_factor = 0.3
        else:
            direction_factor = 0.5
        
        # Calculate weighted breakout probability
        # Distance: 40%, Strength: 30%, Direction: 30%
        breakout_prob = (
            distance_factor * 0.4 +
            strength_factor * 0.3 +
            direction_factor * 0.3
        ) * 100.0
        
        # Clamp to 0-100%
        breakout_prob = max(0.0, min(100.0, breakout_prob))
        
        logger.debug(
            f"Level {level_price:.2f} ({level_type}): "
            f"breakout_prob={breakout_prob:.1f}% "
            f"(distance={distance_factor:.2f}, strength={strength_factor:.2f}, direction={direction_factor:.2f})"
        )
        
        return breakout_prob
    
    def calculate_breakout_probabilities(
        self,
        levels: List[Dict[str, Any]],
        current_price: float
    ) -> List[Dict[str, Any]]:
        """
        Calculate breakout probabilities for multiple levels.
        
        Args:
            levels: List of level dictionaries
            current_price: Current market price
        
        Returns:
            List of levels with 'breakout_probability' key added
        """
        for level in levels:
            level['breakout_probability'] = self.calculate_breakout_probability(
                level,
                current_price
            )
        
        logger.info(f"Calculated breakout probabilities for {len(levels)} levels")
        return levels
    
    def _touch_count_score(self, touches: int) -> float:
        """
        Calculate score based on number of touches.
        
        More touches = stronger level (more times price respected the level)
        
        Scoring:
        - 1 touch: 0.2 (20%)
        - 2 touches: 0.4 (40%)
        - 3 touches: 0.6 (60%)
        - 4 touches: 0.75 (75%)
        - 5+ touches: 1.0 (100%)
        
        Args:
            touches: Number of touches
        
        Returns:
            Score from 0.0 to 1.0
        """
        if touches == 0:
            return 0.0
        elif touches == 1:
            return 0.2
        elif touches == 2:
            return 0.4
        elif touches == 3:
            return 0.6
        elif touches == 4:
            return 0.75
        else:  # 5 or more
            return 1.0
    
    def _time_relevance_score(
        self,
        level: Dict[str, Any],
        current_date: datetime
    ) -> float:
        """
        Calculate score based on how recent the level was touched.
        
        More recent touches = more relevant (level is still active)
        
        Scoring:
        - Touched in last 30 days: 1.0 (100%)
        - Touched in last 90 days: 0.8 (80%)
        - Touched in last 180 days: 0.6 (60%)
        - Touched in last 365 days: 0.4 (40%)
        - Older than 365 days: 0.2 (20%)
        
        Args:
            level: Level dictionary with 'last_touch' timestamp
            current_date: Current date for comparison
        
        Returns:
            Score from 0.0 to 1.0
        """
        from datetime import timedelta
        
        last_touch = level.get('last_touch')
        if not last_touch:
            # No touch info - assume old
            return 0.2
        
        # Convert to datetime if it's a string
        if isinstance(last_touch, str):
            from dateutil.parser import parse
            last_touch = parse(last_touch)
        
        # Handle pandas Timestamp (timezone-aware)
        if hasattr(last_touch, 'to_pydatetime'):
            last_touch = last_touch.to_pydatetime()
        
        # Make timezone-aware if needed
        if last_touch.tzinfo is None and current_date.tzinfo is not None:
            from datetime import timezone
            last_touch = last_touch.replace(tzinfo=timezone.utc)
        elif last_touch.tzinfo is not None and current_date.tzinfo is None:
            from datetime import timezone
            current_date = current_date.replace(tzinfo=timezone.utc)
        
        # Calculate days since last touch
        days_ago = (current_date - last_touch).days
        
        if days_ago <= 30:
            return 1.0
        elif days_ago <= 90:
            return 0.8
        elif days_ago <= 180:
            return 0.6
        elif days_ago <= 365:
            return 0.4
        else:
            return 0.2
    
    def _price_reaction_score(self, level: Dict[str, Any]) -> float:
        """
        Calculate score based on price reaction quality.
        
        Better reactions (higher validation rate) = stronger level
        
        Scoring:
        - validation_rate >= 0.8: 1.0 (100%) - Excellent reactions
        - validation_rate >= 0.6: 0.8 (80%) - Good reactions
        - validation_rate >= 0.4: 0.6 (60%) - Moderate reactions
        - validation_rate >= 0.2: 0.4 (40%) - Poor reactions
        - validation_rate < 0.2: 0.2 (20%) - Very poor reactions
        
        Args:
            level: Level dictionary with 'validation_rate' key
        
        Returns:
            Score from 0.0 to 1.0
        """
        validation_rate = level.get('validation_rate', 0.0)
        
        if validation_rate >= 0.8:
            return 1.0
        elif validation_rate >= 0.6:
            return 0.8
        elif validation_rate >= 0.4:
            return 0.6
        elif validation_rate >= 0.2:
            return 0.4
        else:
            return 0.2
