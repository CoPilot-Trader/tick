"""
Unit Tests for Scoring Module

Tests for:
- StrengthCalculator (0-100 strength scores)

Why unit tests?
- Verify strength calculation formula works correctly
- Test edge cases (0 touches, old levels, etc.)
- Ensure scores are in correct range (0-100)
"""

import pytest
from datetime import datetime, timedelta, timezone
from ..scoring import StrengthCalculator


class TestStrengthCalculator:
    """
    Test suite for StrengthCalculator.
    
    Tests:
    - Strength calculation
    - Touch count scoring
    - Time relevance scoring
    - Price reaction scoring
    - Edge cases
    """
    
    def test_calculate_strength_basic(self):
        """Test basic strength calculation."""
        level = {
            'price': 100.0,
            'touches': 3,
            'validation_rate': 0.7,
            'last_touch': datetime.now(timezone.utc) - timedelta(days=30),
            'type': 'support'
        }
        
        calculator = StrengthCalculator()
        strength = calculator.calculate_strength(level)
        
        assert 0 <= strength <= 100, "Strength should be between 0-100"
        assert isinstance(strength, int), "Strength should be an integer"
    
    def test_touch_count_scoring(self):
        """Test touch count scoring component."""
        calculator = StrengthCalculator()
        
        # Test different touch counts (based on actual implementation)
        assert calculator._touch_count_score(0) == 0.0, "0 touches = 0 score"
        assert calculator._touch_count_score(1) == 0.2, "1 touch = 0.2 score"
        assert calculator._touch_count_score(2) == 0.4, "2 touches = 0.4 score"
        assert calculator._touch_count_score(3) == 0.6, "3 touches = 0.6 score"
        assert calculator._touch_count_score(4) == 0.75, "4 touches = 0.75 score"
        assert calculator._touch_count_score(5) == 1.0, "5+ touches = 1.0 score"
        assert calculator._touch_count_score(10) == 1.0, "10 touches = 1.0 score (max)"
    
    def test_time_relevance_scoring(self):
        """Test time relevance scoring."""
        calculator = StrengthCalculator()
        now = datetime.now(timezone.utc)
        
        # Recent touch (within 30 days)
        level_recent = {
            'last_touch': now - timedelta(days=15)
        }
        score_recent = calculator._time_relevance_score(level_recent, now)
        assert score_recent == 1.0, "Recent touch (within 30 days) should score 1.0"
        
        # Old touch (over 365 days)
        level_old = {
            'last_touch': now - timedelta(days=400)
        }
        score_old = calculator._time_relevance_score(level_old, now)
        assert score_old == 0.2, "Old touch (over 365 days) should score 0.2"
        
        # Medium touch (90-180 days) - should be 0.6
        level_medium = {
            'last_touch': now - timedelta(days=120)
        }
        score_medium = calculator._time_relevance_score(level_medium, now)
        assert score_medium == 0.6, "Medium touch (90-180 days) should score 0.6"
    
    def test_price_reaction_scoring(self):
        """Test price reaction scoring."""
        calculator = StrengthCalculator()
        
        # High validation rate (>=0.8)
        level_high = {'validation_rate': 0.9}
        score_high = calculator._price_reaction_score(level_high)
        assert score_high == 1.0, "High validation rate (>=0.8) should score 1.0"
        
        # Low validation rate (<0.3)
        level_low = {'validation_rate': 0.1}
        score_low = calculator._price_reaction_score(level_low)
        assert score_low == 0.2, "Low validation rate (<0.3) should score 0.2"
        
        # Medium validation rate (0.3-0.8)
        level_medium = {'validation_rate': 0.6}
        score_medium = calculator._price_reaction_score(level_medium)
        assert score_medium == 0.8, "Medium validation rate (0.3-0.8) should score 0.8"
    
    def test_calculate_strengths_batch(self):
        """Test batch strength calculation."""
        levels = [
            {
                'price': 100.0,
                'touches': 3,
                'validation_rate': 0.7,
                'last_touch': datetime.now(timezone.utc) - timedelta(days=30),
                'type': 'support'
            },
            {
                'price': 150.0,
                'touches': 5,
                'validation_rate': 0.8,
                'last_touch': datetime.now(timezone.utc) - timedelta(days=15),
                'type': 'resistance'
            }
        ]
        
        calculator = StrengthCalculator()
        scored = calculator.calculate_strengths(levels)
        
        assert len(scored) == len(levels), "Should score all levels"
        assert all('strength' in l for l in scored), "All levels should have strength"
        assert all(0 <= l['strength'] <= 100 for l in scored), "All strengths should be 0-100"
    
    def test_missing_last_touch(self):
        """Test handling of missing last_touch."""
        level = {
            'price': 100.0,
            'touches': 3,
            'validation_rate': 0.7,
            # No last_touch
        }
        
        calculator = StrengthCalculator()
        strength = calculator.calculate_strength(level)
        
        # Should still calculate strength (assumes old level, scores 0.2 for time)
        assert 0 <= strength <= 100, "Should still return valid strength"
        # With 3 touches (0.6), old time (0.2), 0.7 validation (0.8)
        # Expected: (0.6*0.4 + 0.2*0.3 + 0.8*0.3) * 100 = (0.24 + 0.06 + 0.24) * 100 = 54
        assert strength >= 50, "Should have reasonable strength even without last_touch"
    
    def test_string_timestamp(self):
        """Test handling of string timestamp."""
        level = {
            'price': 100.0,
            'touches': 3,
            'validation_rate': 0.7,
            'last_touch': '2024-01-15T10:00:00Z'  # String format
        }
        
        calculator = StrengthCalculator()
        strength = calculator.calculate_strength(level)
        
        assert 0 <= strength <= 100, "Should handle string timestamps"
