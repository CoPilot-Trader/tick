"""
Volume Profile Analysis for Support/Resistance Agent.

This module identifies support/resistance levels based on volume distribution
across price levels (price-by-volume histogram).

Why Volume Profile?
- High-volume price nodes indicate significant trading activity
- These nodes often act as support/resistance levels
- Complements price-based detection methods
- Provides additional confirmation for detected levels

How it works:
1. Creates price-by-volume histogram (bins price data by volume)
2. Identifies high-volume nodes (price levels with above-average volume)
3. Filters nodes to find significant levels
4. Returns volume-based support/resistance levels
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VolumeProfileAnalyzer:
    """
    Analyzes volume distribution to identify support/resistance levels.
    
    Volume Profile Concept:
    - Divides price range into bins
    - Calculates total volume traded at each price bin
    - High-volume nodes = significant price levels
    """
    
    def __init__(
        self,
        num_bins: int = 50,
        min_volume_threshold: float = 0.6,
        min_touches: int = 2
    ):
        """
        Initialize the volume profile analyzer.
        
        Args:
            num_bins: Number of price bins for histogram (default: 50)
                    - More bins = finer granularity
                    - Fewer bins = broader levels
            min_volume_threshold: Minimum volume percentile to consider (default: 0.6 = 60th percentile)
                                - 0.6 means only top 40% volume nodes are considered
            min_touches: Minimum number of times price should touch a volume node (default: 2)
        """
        self.num_bins = num_bins
        self.min_volume_threshold = min_volume_threshold
        self.min_touches = min_touches
        logger.debug(
            f"VolumeProfileAnalyzer initialized: "
            f"bins={num_bins}, threshold={min_volume_threshold}, min_touches={min_touches}"
        )
    
    def analyze_volume_profile(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Analyze volume distribution to create volume profile.
        
        Process:
        1. Determine price range (min low to max high)
        2. Divide into bins
        3. Calculate volume at each price bin
        4. Identify high-volume nodes
        
        Args:
            df: DataFrame with OHLCV data (must have 'high', 'low', 'volume', 'close' columns)
        
        Returns:
            Dictionary with:
            - price_bins: Array of price bin centers
            - volume_profile: Array of volumes at each bin
            - high_volume_nodes: List of high-volume price levels
        """
        if 'high' not in df.columns or 'low' not in df.columns or 'volume' not in df.columns:
            raise ValueError("DataFrame must have 'high', 'low', and 'volume' columns")
        
        # Get price range
        min_price = float(df['low'].min())
        max_price = float(df['high'].max())
        price_range = max_price - min_price
        
        if price_range == 0:
            logger.warning("Price range is zero, cannot create volume profile")
            return {
                'price_bins': np.array([]),
                'volume_profile': np.array([]),
                'high_volume_nodes': []
            }
        
        # Create price bins
        bin_edges = np.linspace(min_price, max_price, self.num_bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Calculate volume at each price bin
        # Optimized: use vectorized operations where possible
        volume_profile = np.zeros(self.num_bins)
        
        # Get arrays for faster access
        lows = df['low'].values
        highs = df['high'].values
        volumes = df['volume'].values
        
        # Vectorized calculation for each bin
        for i in range(self.num_bins):
            bin_low = bin_edges[i]
            bin_high = bin_edges[i + 1]
            
            # Vectorized overlap calculation
            overlap_lows = np.maximum(lows, bin_low)
            overlap_highs = np.minimum(highs, bin_high)
            
            # Find candles that overlap with this bin
            overlaps = overlap_lows < overlap_highs
            candle_ranges = highs - lows
            
            # Calculate overlap ratios (avoid division by zero)
            valid_ranges = candle_ranges > 0
            overlap_ratios = np.where(
                valid_ranges & overlaps,
                (overlap_highs - overlap_lows) / candle_ranges,
                0
            )
            
            # Sum volume contributions for this bin
            volume_profile[i] = np.sum(volumes * overlap_ratios)
        
        # Find high-volume nodes (above threshold)
        if len(volume_profile) > 0:
            volume_threshold = np.percentile(volume_profile, self.min_volume_threshold * 100)
            high_volume_indices = np.where(volume_profile >= volume_threshold)[0]
            
            high_volume_nodes = [
                {
                    'price': float(bin_centers[i]),
                    'volume': float(volume_profile[i]),
                    'volume_percentile': float((volume_profile[i] - volume_profile.min()) / 
                                                (volume_profile.max() - volume_profile.min()) * 100)
                    if volume_profile.max() > volume_profile.min() else 0.0
                }
                for i in high_volume_indices
            ]
        else:
            high_volume_nodes = []
        
        logger.info(
            f"Volume profile analysis: {len(high_volume_nodes)} high-volume nodes identified "
            f"(threshold: {self.min_volume_threshold * 100:.0f}th percentile)"
        )
        
        return {
            'price_bins': bin_centers,
            'volume_profile': volume_profile,
            'high_volume_nodes': high_volume_nodes
        }
    
    def detect_volume_levels(
        self,
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Detect support/resistance levels based on volume profile.
        
        Process:
        1. Analyze volume profile
        2. Identify high-volume nodes
        3. Determine if nodes are support or resistance based on price action
        4. Filter by minimum touches
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            List of level dictionaries with:
            - price: Level price (from volume node)
            - type: 'support' or 'resistance'
            - volume: Volume at this level
            - volume_percentile: Volume percentile (0-100)
            - touches: Number of times price touched this level
        """
        # Analyze volume profile
        profile_result = self.analyze_volume_profile(df)
        high_volume_nodes = profile_result['high_volume_nodes']
        
        if not high_volume_nodes:
            logger.warning("No high-volume nodes found in volume profile")
            return []
        
        # Determine support/resistance for each node
        levels = []
        current_price = float(df.iloc[-1]['close'])
        
        for node in high_volume_nodes:
            node_price = node['price']
            
            # Count touches (how many times price came within tolerance)
            tolerance = node_price * 0.01  # 1% tolerance
            touches = self._count_touches(df, node_price, tolerance)
            
            if touches < self.min_touches:
                continue  # Skip nodes with too few touches
            
            # Determine type: support if below current price, resistance if above
            if node_price < current_price:
                level_type = 'support'
            else:
                level_type = 'resistance'
            
            levels.append({
                'price': node_price,
                'type': level_type,
                'volume': node['volume'],
                'volume_percentile': node['volume_percentile'],
                'touches': touches,
                'source': 'volume_profile'
            })
        
        # Sort by volume (highest first)
        levels = sorted(levels, key=lambda x: x['volume'], reverse=True)
        
        logger.info(f"Detected {len(levels)} volume-based levels")
        return levels
    
    def _count_touches(
        self,
        df: pd.DataFrame,
        level_price: float,
        tolerance: float
    ) -> int:
        """
        Count how many times price touched a level (within tolerance).
        
        Args:
            df: DataFrame with OHLCV data
            level_price: Level price to check
            tolerance: Price tolerance
        
        Returns:
            Number of touches
        """
        # Vectorized operation (much faster than iterrows)
        # Check if level is within candle range (low - tolerance <= level <= high + tolerance)
        touches = ((df['low'] - tolerance) <= level_price) & (level_price <= (df['high'] + tolerance))
        return int(touches.sum())
    
    def merge_with_price_levels(
        self,
        price_levels: List[Dict[str, Any]],
        volume_levels: List[Dict[str, Any]],
        merge_tolerance: float = 0.02
    ) -> List[Dict[str, Any]]:
        """
        Merge volume-based levels with price-based levels.
        
        If a volume level is close to a price level, merge them and enhance
        the price level with volume information.
        
        Args:
            price_levels: List of price-based level dictionaries
            volume_levels: List of volume-based level dictionaries
            merge_tolerance: Price tolerance for merging (default: 2%)
        
        Returns:
            Enhanced list of levels with volume information
        """
        merged_levels = []
        used_volume_levels = set()
        
        # First, add all price levels
        for price_level in price_levels:
            price = price_level['price']
            merged_level = price_level.copy()
            
            # Check if any volume level is close
            for i, volume_level in enumerate(volume_levels):
                if i in used_volume_levels:
                    continue
                
                volume_price = volume_level['price']
                price_diff = abs(price - volume_price) / price
                
                if price_diff <= merge_tolerance:
                    # Merge: add volume information to price level
                    merged_level['volume'] = volume_level.get('volume', 0)
                    merged_level['volume_percentile'] = volume_level.get('volume_percentile', 0)
                    merged_level['has_volume_confirmation'] = True
                    # Preserve timestamps from price level (volume levels don't have timestamps)
                    # first_touch and last_touch should already be in price_level, so keep them
                    used_volume_levels.add(i)
                    break
            else:
                # No volume confirmation
                merged_level['has_volume_confirmation'] = False
            
            merged_levels.append(merged_level)
        
        # Add unused volume levels as new levels
        for i, volume_level in enumerate(volume_levels):
            if i not in used_volume_levels:
                merged_levels.append(volume_level)
        
        logger.info(
            f"Merged {len(price_levels)} price levels with {len(volume_levels)} volume levels: "
            f"{len(merged_levels)} total levels"
        )
        
        return merged_levels

