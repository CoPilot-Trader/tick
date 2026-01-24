"""
Unit Tests for Detection Module

Tests for:
- ExtremaDetector (peak/valley detection)
- DBSCANClusterer (level clustering)
- LevelValidator (level validation)

Why unit tests?
- Ensure each component works correctly in isolation
- Catch bugs early
- Document expected behavior
- Enable safe refactoring
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

# Import components to test
from ..detection import ExtremaDetector, DBSCANClusterer, LevelValidator


class TestExtremaDetector:
    """
    Test suite for ExtremaDetector.
    
    Tests:
    - Peak detection
    - Valley detection
    - Noise filtering
    - Edge cases
    """
    
    def test_detect_peaks_simple(self):
        """
        Test peak detection with simple price data.
        
        Creates a simple price pattern with clear peaks.
        """
        # Create simple data with clear peaks
        dates = pd.date_range('2022-01-01', periods=30, freq='D', tz='UTC')
        highs = [100, 102, 105, 103, 101, 108, 106, 104, 110, 107,
                 105, 103, 109, 106, 104, 112, 108, 105, 103, 100,
                 102, 104, 106, 108, 110, 108, 106, 104, 102, 100]
        
        df = pd.DataFrame({
            'timestamp': dates,
            'high': highs,
            'low': [h - 2 for h in highs],
            'open': [h - 1 for h in highs],
            'close': [h - 0.5 for h in highs],
            'volume': [1000000] * 30
        })
        
        detector = ExtremaDetector(window_size=3, min_distance=5)
        peaks = detector.detect_peaks(df)
        
        # Should detect peaks at indices with highest values
        assert len(peaks) > 0, "Should detect at least one peak"
        assert all('price' in p for p in peaks), "All peaks should have price"
        assert all('timestamp' in p for p in peaks), "All peaks should have timestamp"
        assert all('type' in p for p in peaks), "All peaks should have type"
        assert all(p['type'] == 'resistance' for p in peaks), "Peaks should be resistance type"
    
    def test_detect_valleys_simple(self):
        """Test valley detection with simple price data."""
        dates = pd.date_range('2022-01-01', periods=30, freq='D', tz='UTC')
        lows = [100, 98, 95, 97, 99, 92, 94, 96, 90, 93,
                95, 97, 91, 94, 96, 88, 92, 95, 97, 100,
                98, 96, 94, 92, 90, 92, 94, 96, 98, 100]
        
        df = pd.DataFrame({
            'timestamp': dates,
            'high': [l + 2 for l in lows],
            'low': lows,
            'open': [l + 1 for l in lows],
            'close': [l + 0.5 for l in lows],
            'volume': [1000000] * 30
        })
        
        detector = ExtremaDetector(window_size=3, min_distance=5)
        valleys = detector.detect_valleys(df)
        
        assert len(valleys) > 0, "Should detect at least one valley"
        assert all('price' in v for v in valleys), "All valleys should have price"
        assert all('type' in v for v in valleys), "All valleys should have type"
        assert all(v['type'] == 'support' for v in valleys), "Valleys should be support type"
    
    def test_filter_noise(self):
        """Test noise filtering removes insignificant extrema."""
        extrema = [
            {'price': 100.0, 'timestamp': datetime.now(timezone.utc), 'index': 0},
            {'price': 100.5, 'timestamp': datetime.now(timezone.utc), 'index': 1},  # Small change
            {'price': 105.0, 'timestamp': datetime.now(timezone.utc), 'index': 2},  # Large change
            {'price': 105.2, 'timestamp': datetime.now(timezone.utc), 'index': 3},  # Small change
        ]
        
        detector = ExtremaDetector()
        filtered = detector.filter_noise(extrema, min_price_change=0.01)  # 1% threshold
        
        # Should keep first, last, and significant changes
        assert len(filtered) <= len(extrema), "Filtering should reduce or keep same count"
        assert len(filtered) >= 2, "Should keep at least first and last"
    
    def test_empty_data(self):
        """Test handling of empty data."""
        df = pd.DataFrame(columns=['timestamp', 'high', 'low', 'open', 'close', 'volume'])
        
        detector = ExtremaDetector()
        peaks = detector.detect_peaks(df)
        valleys = detector.detect_valleys(df)
        
        assert peaks == [], "Empty data should return empty peaks"
        assert valleys == [], "Empty data should return empty valleys"
    
    def test_insufficient_data(self):
        """Test handling of insufficient data (less than window_size)."""
        dates = pd.date_range('2022-01-01', periods=5, freq='D')
        df = pd.DataFrame({
            'timestamp': dates,
            'high': [100, 102, 101, 103, 102],
            'low': [99, 101, 100, 102, 101],
            'open': [99.5, 101.5, 100.5, 102.5, 101.5],
            'close': [100, 102, 101, 103, 102],
            'volume': [1000000] * 5
        })
        
        detector = ExtremaDetector(window_size=10)  # Larger than data
        peaks = detector.detect_peaks(df)
        valleys = detector.detect_valleys(df)
        
        # Should handle gracefully (no error, may return empty or fewer results)
        assert isinstance(peaks, list), "Should return a list"
        assert isinstance(valleys, list), "Should return a list"


class TestDBSCANClusterer:
    """
    Test suite for DBSCANClusterer.
    
    Tests:
    - Clustering similar price levels
    - Filtering weak clusters
    - Edge cases
    """
    
    def test_cluster_levels_simple(self):
        """Test clustering with simple extrema points."""
        # Create extrema points that should cluster together
        extrema = [
            {'price': 100.0, 'timestamp': datetime.now(timezone.utc), 'type': 'resistance'},
            {'price': 100.5, 'timestamp': datetime.now(timezone.utc), 'type': 'resistance'},
            {'price': 100.3, 'timestamp': datetime.now(timezone.utc), 'type': 'resistance'},
            {'price': 150.0, 'timestamp': datetime.now(timezone.utc), 'type': 'resistance'},
            {'price': 150.2, 'timestamp': datetime.now(timezone.utc), 'type': 'resistance'},
        ]
        
        clusterer = DBSCANClusterer(eps=0.02, min_samples=2)
        levels = clusterer.cluster_levels(extrema)
        
        assert len(levels) > 0, "Should create at least one cluster"
        assert all('price' in l for l in levels), "All levels should have price"
        assert all('touches' in l for l in levels), "All levels should have touches count"
        assert all('cluster_id' in l for l in levels), "All levels should have cluster_id"
    
    def test_filter_clusters(self):
        """Test filtering weak clusters."""
        levels = [
            {'price': 100.0, 'touches': 1, 'type': 'support'},  # Weak (1 touch)
            {'price': 150.0, 'touches': 3, 'type': 'resistance'},  # Strong (3 touches)
            {'price': 200.0, 'touches': 2, 'type': 'support'},  # Moderate (2 touches)
        ]
        
        clusterer = DBSCANClusterer()
        filtered = clusterer.filter_clusters(levels, min_touches=2)
        
        # Should keep levels with >= 2 touches
        assert len(filtered) == 2, "Should filter out level with 1 touch"
        assert all(l['touches'] >= 2 for l in filtered), "All filtered levels should have >= 2 touches"
    
    def test_empty_extrema(self):
        """Test handling of empty extrema list."""
        clusterer = DBSCANClusterer()
        levels = clusterer.cluster_levels([])
        
        assert levels == [], "Empty extrema should return empty levels"
    
    def test_single_extrema(self):
        """Test handling of single extrema point."""
        extrema = [
            {'price': 100.0, 'timestamp': datetime.now(timezone.utc), 'type': 'support'}
        ]
        
        clusterer = DBSCANClusterer(eps=0.02, min_samples=1)
        levels = clusterer.cluster_levels(extrema)
        
        # With min_samples=1, should create a cluster
        assert isinstance(levels, list), "Should return a list"


class TestLevelValidator:
    """
    Test suite for LevelValidator.
    
    Tests:
    - Level validation
    - Price reaction detection
    - Validation rate calculation
    """
    
    def test_validate_level_support(self):
        """Test validation of support level (price should bounce up)."""
        # Create data where price touches support and bounces up
        dates = pd.date_range('2022-01-01', periods=30, freq='D', tz='UTC')
        support_price = 100.0
        
        # Price touches support at index 10, then bounces up
        lows = [102, 101, 100.5, 100.2, 100.1, 100.05, 100.0, 100.1, 100.5, 101,
                102, 103, 104, 105, 106, 107, 108, 109, 110, 111,
                112, 113, 114, 115, 116, 117, 118, 119, 120, 121]
        
        df = pd.DataFrame({
            'timestamp': dates,
            'high': [l + 2 for l in lows],
            'low': lows,
            'open': [l + 1 for l in lows],
            'close': [l + 0.5 for l in lows],
            'volume': [1000000] * 30
        })
        
        level = {
            'price': support_price,
            'type': 'support',
            'touches': 1
        }
        
        validator = LevelValidator(tolerance=0.01, lookforward_bars=5)
        validated = validator.validate_level(level, df)
        
        assert 'validated' in validated, "Should have validated field"
        assert 'validation_rate' in validated, "Should have validation_rate field"
        assert 'reaction_count' in validated, "Should have reaction_count field"
        assert 'touch_count' in validated, "Should have touch_count field"
    
    def test_validate_level_resistance(self):
        """Test validation of resistance level (price should bounce down)."""
        dates = pd.date_range('2022-01-01', periods=30, freq='D', tz='UTC')
        resistance_price = 150.0
        
        # Price touches resistance at index 10, then bounces down
        highs = [148, 149, 149.5, 149.8, 149.9, 149.95, 150.0, 149.9, 149.5, 149,
                 148, 147, 146, 145, 144, 143, 142, 141, 140, 139,
                 138, 137, 136, 135, 134, 133, 132, 131, 130, 129]
        
        df = pd.DataFrame({
            'timestamp': dates,
            'high': highs,
            'low': [h - 2 for h in highs],
            'open': [h - 1 for h in highs],
            'close': [h - 0.5 for h in highs],
            'volume': [1000000] * 30
        })
        
        level = {
            'price': resistance_price,
            'type': 'resistance',
            'touches': 1
        }
        
        validator = LevelValidator(tolerance=0.01, lookforward_bars=5)
        validated = validator.validate_level(level, df)
        
        assert 'validated' in validated, "Should have validated field"
        assert validated.get('validation_rate', 0) >= 0, "Validation rate should be >= 0"
        assert validated.get('validation_rate', 0) <= 1.0, "Validation rate should be <= 1.0"
    
    def test_validate_levels_batch(self):
        """Test batch validation of multiple levels."""
        dates = pd.date_range('2022-01-01', periods=50, freq='D', tz='UTC')
        df = pd.DataFrame({
            'timestamp': dates,
            'high': [150 + i * 0.1 for i in range(50)],
            'low': [148 + i * 0.1 for i in range(50)],
            'open': [149 + i * 0.1 for i in range(50)],
            'close': [149.5 + i * 0.1 for i in range(50)],
            'volume': [1000000] * 50
        })
        
        levels = [
            {'price': 150.0, 'type': 'support'},
            {'price': 155.0, 'type': 'resistance'},
        ]
        
        validator = LevelValidator()
        validated = validator.validate_levels(levels, df)
        
        assert len(validated) == len(levels), "Should validate all levels"
        assert all('validated' in l for l in validated), "All levels should have validated field"
        assert all('validation_rate' in l for l in validated), "All levels should have validation_rate"
    
    def test_empty_levels(self):
        """Test validation of empty levels list."""
        dates = pd.date_range('2022-01-01', periods=10, freq='D', tz='UTC')
        df = pd.DataFrame({
            'timestamp': dates,
            'high': [100] * 10,
            'low': [99] * 10,
            'open': [99.5] * 10,
            'close': [99.8] * 10,
            'volume': [1000000] * 10
        })
        
        validator = LevelValidator()
        validated = validator.validate_levels([], df)
        
        assert validated == [], "Empty levels should return empty list"
