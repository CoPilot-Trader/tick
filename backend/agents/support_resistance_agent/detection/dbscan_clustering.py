"""
DBSCAN Clustering for Support/Resistance Agent.

This module uses DBSCAN (Density-Based Spatial Clustering) to group
similar price levels together.

Why DBSCAN?
- Groups nearby extrema points into clusters
- Each cluster represents a potential support/resistance level
- Automatically finds the number of clusters (we don't need to specify)
- Handles outliers (noise points that don't belong to any cluster)

How it works:
1. Takes extrema points (peaks/valleys)
2. Groups points that are close together (within eps distance)
3. Each cluster center becomes a support/resistance level
"""

import numpy as np
from sklearn.cluster import DBSCAN
from typing import List, Dict, Any
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DBSCANClusterer:
    """
    Clusters extrema points using DBSCAN algorithm.
    
    DBSCAN Parameters:
    - eps: Maximum distance between points in the same cluster
    - min_samples: Minimum number of points to form a cluster
    """
    
    def __init__(self, eps: float = 0.02, min_samples: int = 3):
        """
        Initialize the DBSCAN clusterer.
        
        Args:
            eps: Maximum distance between points in same cluster (default: 0.02 = 2%)
                - 0.02 means points within 2% of price are in same cluster
                - For $100 stock: points between $98-$102 are in same cluster
                - Smaller = more clusters, stricter grouping
                - Larger = fewer clusters, looser grouping
            min_samples: Minimum points needed to form a cluster (default: 3)
                        - A level needs at least 3 touches to be significant
                        - Fewer = more clusters (including weak ones)
                        - More = fewer clusters (only strong levels)
        """
        self.eps = eps
        self.min_samples = min_samples
        logger.debug(f"DBSCANClusterer initialized: eps={eps}, min_samples={min_samples}")
    
    def cluster_levels(self, extrema: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Cluster extrema points into support/resistance levels.
        
        Process:
        1. Extract prices from extrema points
        2. Reshape for DBSCAN (needs 2D array)
        3. Run DBSCAN clustering
        4. Calculate cluster centers (average price of cluster)
        5. Count touches (points in each cluster)
        
        Args:
            extrema: List of extrema dictionaries with 'price' key
        
        Returns:
            List of level dictionaries with:
            - price: Cluster center (average price)
            - touches: Number of points in cluster
            - cluster_id: DBSCAN cluster ID
            - points: List of prices in this cluster
        """
        if not extrema:
            logger.warning("No extrema points provided for clustering")
            return []
        
        # Extract prices
        prices = np.array([ext['price'] for ext in extrema])
        
        # DBSCAN needs 2D array, so reshape
        # Shape: (n_points, 1) - one feature (price)
        prices_2d = prices.reshape(-1, 1)
        
        # Run DBSCAN
        # eps is in absolute price units, so we need to scale it
        # For a $100 stock, eps=0.02 means $2 difference
        # We'll use percentage-based eps: eps * median_price
        median_price = np.median(prices)
        scaled_eps = self.eps * median_price
        
        logger.debug(f"Running DBSCAN: {len(prices)} points, scaled_eps={scaled_eps:.2f}")
        clustering = DBSCAN(eps=scaled_eps, min_samples=self.min_samples).fit(prices_2d)
        
        # Get cluster labels
        labels = clustering.labels_
        
        # Group points by cluster (keep track of indices for timestamp access)
        clusters = {}
        cluster_indices = {}  # Track which extrema indices belong to each cluster
        for i, label in enumerate(labels):
            if label == -1:
                # -1 means noise/outlier (not in any cluster)
                continue
            
            if label not in clusters:
                clusters[label] = []
                cluster_indices[label] = []
            clusters[label].append(prices[i])
            cluster_indices[label].append(i)  # Store index to access extrema data
        
        # Calculate cluster centers and create level dictionaries
        levels = []
        for cluster_id, cluster_prices in clusters.items():
            # Cluster center = average price
            center_price = np.mean(cluster_prices)
            
            # Find the closest actual extrema point to the center
            closest_idx = np.argmin(np.abs(prices - center_price))
            closest_extrema = extrema[closest_idx]
            
            # Get all extrema points in this cluster to find first and last touch
            cluster_extrema_indices = cluster_indices[cluster_id]
            cluster_extrema_points = [extrema[idx] for idx in cluster_extrema_indices]
            
            # Extract timestamps from all extrema points in cluster
            timestamps = []
            for extrema_point in cluster_extrema_points:
                timestamp = extrema_point.get('timestamp')
                if timestamp is not None:
                    timestamps.append(timestamp)
            
            # Calculate first_touch (earliest) and last_touch (latest)
            first_touch = None
            last_touch = None
            if timestamps:
                # Sort timestamps to find earliest and latest
                sorted_timestamps = sorted(timestamps)
                first_touch = sorted_timestamps[0]  # Earliest
                last_touch = sorted_timestamps[-1]  # Latest
            
            # If no timestamps found, try to get from closest extrema as fallback
            if first_touch is None:
                first_touch = closest_extrema.get('timestamp')
            if last_touch is None:
                last_touch = closest_extrema.get('timestamp')
            
            level = {
                'price': float(center_price),
                'touches': len(cluster_prices),
                'cluster_id': int(cluster_id),
                'points': [float(p) for p in cluster_prices],
                'type': closest_extrema.get('type', 'unknown'),
                'first_touch': first_touch,
                'last_touch': last_touch,
            }
            levels.append(level)
        
        logger.info(f"Clustered {len(extrema)} extrema into {len(levels)} levels")
        return levels
    
    def filter_clusters(
        self,
        levels: List[Dict[str, Any]],
        min_touches: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Filter out weak clusters (levels with too few touches).
        
        Why filter?
        - Levels with only 1-2 touches might be noise
        - We want levels that price has touched multiple times
        - More touches = stronger level
        
        Args:
            levels: List of level dictionaries
            min_touches: Minimum number of touches required (default: 2)
        
        Returns:
            Filtered list of levels
        """
        filtered = [level for level in levels if level['touches'] >= min_touches]
        logger.info(f"Filtered {len(levels)} levels to {len(filtered)} with >= {min_touches} touches")
        return filtered
    
    def calculate_centers(self, clusters: Dict[int, List[float]]) -> Dict[int, float]:
        """
        Calculate center price for each cluster.
        
        Cluster center = average of all prices in the cluster.
        This becomes the support/resistance level price.
        
        Args:
            clusters: Dictionary mapping cluster_id to list of prices
        
        Returns:
            Dictionary mapping cluster_id to center price
        """
        centers = {}
        for cluster_id, prices in clusters.items():
            centers[cluster_id] = float(np.mean(prices))
        return centers
