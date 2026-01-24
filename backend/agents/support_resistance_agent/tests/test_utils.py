"""
Unit Tests for Utilities Module

Tests for:
- DataLoader (data loading)
- Logger (logging)
- Retry (retry logic)
"""

import pytest
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock

from ..utils import DataLoader, get_logger, retry_with_backoff


class TestDataLoader:
    """
    Test suite for DataLoader.
    
    Tests:
    - Mock data loading
    - Data validation
    - Date filtering
    - Error handling
    """
    
    def test_load_mock_data(self):
        """Test loading mock OHLCV data."""
        loader = DataLoader(use_mock_data=True)
        
        # Load data for a known ticker
        df, data_source = loader.load_ohlcv_data('AAPL')
        
        assert not df.empty, "Should load data"
        assert 'timestamp' in df.columns, "Should have timestamp column"
        assert 'open' in df.columns, "Should have open column"
        assert 'high' in df.columns, "Should have high column"
        assert 'low' in df.columns, "Should have low column"
        assert 'close' in df.columns, "Should have close column"
        assert 'volume' in df.columns, "Should have volume column"
    
    def test_data_validation(self):
        """Test data validation checks."""
        loader = DataLoader(use_mock_data=True)
        df, data_source = loader.load_ohlcv_data('AAPL')
        
        # Validation should pass for valid data
        # (validation is done internally in load_ohlcv_data)
        assert not df.empty, "Valid data should load successfully"
    
    def test_date_filtering(self):
        """Test date range filtering."""
        loader = DataLoader(use_mock_data=True)
        
        # Load with date range
        start_date = datetime(2022, 6, 1, tzinfo=timezone.utc)
        end_date = datetime(2022, 12, 31, tzinfo=timezone.utc)
        
        df, data_source = loader.load_ohlcv_data(
            'AAPL',
            start_date=start_date,
            end_date=end_date
        )
        
        if not df.empty:
            # If data exists in range, verify it's filtered
            assert df['timestamp'].min() >= start_date, "Should filter by start date"
            assert df['timestamp'].max() <= end_date, "Should filter by end date"
    
    def test_missing_symbol(self):
        """Test handling of missing symbol in mock data."""
        loader = DataLoader(use_mock_data=True)
        
        with pytest.raises(ValueError, match="not found in mock data"):
            loader.load_ohlcv_data('INVALID_SYMBOL')
    
    def test_mock_data_file_not_found(self):
        """Test handling of missing mock data file."""
        loader = DataLoader(use_mock_data=True)
        # Temporarily change path to non-existent file
        original_path = loader.mock_data_path
        loader.mock_data_path = Path('/nonexistent/path/data.json')
        
        with pytest.raises(FileNotFoundError):
            loader.load_ohlcv_data('AAPL')
        
        # Restore path
        loader.mock_data_path = original_path


class TestLogger:
    """
    Test suite for logger utility.
    
    Tests:
    - Logger creation
    - Logger configuration
    """
    
    def test_get_logger(self):
        """Test logger creation."""
        logger = get_logger(__name__)
        
        assert logger is not None, "Should return a logger"
        assert logger.name == __name__, "Logger name should match"
    
    def test_logger_level(self):
        """Test logger with custom level."""
        logger = get_logger(__name__, level=10)  # DEBUG level
        
        assert logger.level == 10, "Logger should have correct level"


class TestRetry:
    """
    Test suite for retry utility.
    
    Tests:
    - Retry on failure
    - Exponential backoff
    - Max retries
    """
    
    def test_retry_success_first_attempt(self):
        """Test that successful function doesn't retry."""
        call_count = [0]
        
        @retry_with_backoff(max_retries=3)
        def successful_func():
            call_count[0] += 1
            return "success"
        
        result = successful_func()
        
        assert result == "success", "Should return success"
        assert call_count[0] == 1, "Should only call once (no retry needed)"
    
    def test_retry_on_failure(self):
        """Test retry on failure."""
        call_count = [0]
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def failing_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Temporary failure")
            return "success"
        
        result = failing_func()
        
        assert result == "success", "Should succeed after retry"
        assert call_count[0] == 2, "Should retry once"
    
    def test_retry_max_attempts(self):
        """Test that retry stops after max attempts."""
        call_count = [0]
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01)
        def always_failing_func():
            call_count[0] += 1
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError, match="Always fails"):
            always_failing_func()
        
        assert call_count[0] == 3, "Should try max_retries + 1 times (initial + retries)"
