"""
Extrema Detection for Support/Resistance Agent.

This module finds local peaks (resistance levels) and valleys (support levels)
in price data using scipy.signal.argrelextrema (as per specification).

What are extrema?
- Peak (Maximum): A point where price is higher than its neighbors (resistance)
- Valley (Minimum): A point where price is lower than its neighbors (support)

Why we need this:
- Support/Resistance levels are formed at price peaks and valleys
- We need to find these points before we can cluster them into levels

Implementation:
- Uses scipy.signal.argrelextrema for rolling window extrema detection
- Matches system specification requirements
"""

import pandas as pd
import numpy as np
from scipy.signal import argrelextrema
from typing import List, Dict, Any, Tuple
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ExtremaDetector:
    """
    Detects local peaks and valleys in price data.
    
    How it works:
    1. Scans through price data
    2. Compares each point with its neighbors
    3. Identifies peaks (highs) and valleys (lows)
    4. Filters out noise (small fluctuations)
    """
    
    def __init__(self, window_size: int = 5, min_distance: int = 10):
        """
        Initialize the extrema detector.
        
        Args:
            window_size: Number of neighbors to compare on each side (default: 5)
                        - Larger = fewer but more significant extrema
                        - Smaller = more but potentially noisy extrema
            min_distance: Minimum distance between extrema points (default: 10)
                         - Prevents detecting extrema too close together
        """
        self.window_size = window_size
        self.min_distance = min_distance
        logger.debug(f"ExtremaDetector initialized: window_size={window_size}, min_distance={min_distance}")
    
    def detect_peaks(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect peaks (resistance candidates) in price data using scipy.signal.argrelextrema.
        
        A peak is a point where:
        - High price is greater than N neighbors on both sides
        - Used to identify potential resistance levels
        
        Implementation uses scipy.signal.argrelextrema for rolling window detection
        (matches system specification).
        
        Args:
            df: DataFrame with OHLCV data (must have 'high' and 'timestamp' columns)
        
        Returns:
            List of peak dictionaries with:
            - timestamp: When the peak occurred
            - price: The high price at the peak
            - index: Row index in DataFrame
        """
        if 'high' not in df.columns or 'timestamp' not in df.columns:
            raise ValueError("DataFrame must have 'high' and 'timestamp' columns")
        
        highs = df['high'].values
        
        # Use scipy.signal.argrelextrema for peak detection
        # order parameter = window_size (number of points on each side to compare)
        # This matches the specification requirement
        peak_indices = argrelextrema(highs, np.greater, order=self.window_size)[0]
        
        # Apply min_distance filter to avoid peaks too close together
        if len(peak_indices) > 0 and self.min_distance > 0:
            filtered_indices = [peak_indices[0]]  # Always include first peak
            for idx in peak_indices[1:]:
                # Only add if far enough from previous peak
                if idx - filtered_indices[-1] >= self.min_distance:
                    filtered_indices.append(idx)
            peak_indices = np.array(filtered_indices)
        
        # Convert to list of dictionaries
        peaks = []
        for idx in peak_indices:
            peaks.append({
                'timestamp': df.iloc[idx]['timestamp'],
                'price': float(highs[idx]),
                'index': int(idx),
                'type': 'resistance'
            })
        
        logger.info(f"Detected {len(peaks)} peaks (resistance candidates) using scipy.signal.argrelextrema")
        return peaks
    
    def detect_valleys(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect valleys (support candidates) in price data using scipy.signal.argrelextrema.
        
        A valley is a point where:
        - Low price is lower than N neighbors on both sides
        - Used to identify potential support levels
        
        Implementation uses scipy.signal.argrelextrema for rolling window detection
        (matches system specification).
        
        Args:
            df: DataFrame with OHLCV data (must have 'low' and 'timestamp' columns)
        
        Returns:
            List of valley dictionaries with:
            - timestamp: When the valley occurred
            - price: The low price at the valley
            - index: Row index in DataFrame
        """
        if 'low' not in df.columns or 'timestamp' not in df.columns:
            raise ValueError("DataFrame must have 'low' and 'timestamp' columns")
        
        lows = df['low'].values
        
        # Use scipy.signal.argrelextrema for valley detection
        # order parameter = window_size (number of points on each side to compare)
        # This matches the specification requirement
        valley_indices = argrelextrema(lows, np.less, order=self.window_size)[0]
        
        # Apply min_distance filter to avoid valleys too close together
        if len(valley_indices) > 0 and self.min_distance > 0:
            filtered_indices = [valley_indices[0]]  # Always include first valley
            for idx in valley_indices[1:]:
                # Only add if far enough from previous valley
                if idx - filtered_indices[-1] >= self.min_distance:
                    filtered_indices.append(idx)
            valley_indices = np.array(filtered_indices)
        
        # Convert to list of dictionaries
        valleys = []
        for idx in valley_indices:
            valleys.append({
                'timestamp': df.iloc[idx]['timestamp'],
                'price': float(lows[idx]),
                'index': int(idx),
                'type': 'support'
            })
        
        logger.info(f"Detected {len(valleys)} valleys (support candidates) using scipy.signal.argrelextrema")
        return valleys
    
    def detect_all_extrema(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Detect both peaks and valleys.
        
        This is a convenience method that calls both detect_peaks() and detect_valleys().
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            Tuple of (peaks, valleys) lists
        """
        peaks = self.detect_peaks(df)
        valleys = self.detect_valleys(df)
        
        logger.info(f"Total extrema detected: {len(peaks)} peaks, {len(valleys)} valleys")
        return peaks, valleys
    
    def filter_noise(
        self,
        extrema: List[Dict[str, Any]],
        min_price_change: float = 0.01
    ) -> List[Dict[str, Any]]:
        """
        Filter out noise from extrema points.
        
        Why filter?
        - Small price movements might not be significant levels
        - Reduces number of extrema to process
        - Focuses on more important levels
        
        Args:
            extrema: List of extrema dictionaries
            min_price_change: Minimum price change to consider significant (default: 1%)
                            - 0.01 = 1% change
                            - Filters out very small fluctuations
        
        Returns:
            Filtered list of extrema
        """
        if not extrema:
            return []
        
        # Sort by price
        sorted_extrema = sorted(extrema, key=lambda x: x['price'])
        filtered = []
        
        for i, ext in enumerate(sorted_extrema):
            # For first and last, always include
            if i == 0 or i == len(sorted_extrema) - 1:
                filtered.append(ext)
                continue
            
            # Calculate price change from previous extrema
            prev_price = sorted_extrema[i - 1]['price']
            current_price = ext['price']
            price_change = abs(current_price - prev_price) / prev_price
            
            # Only include if price change is significant
            if price_change >= min_price_change:
                filtered.append(ext)
        
        logger.info(f"Filtered {len(extrema)} extrema to {len(filtered)} significant points")
        return filtered
