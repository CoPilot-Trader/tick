"""
Support/Resistance Agent - Main agent implementation.

Optimized for efficient processing of 1-100 tickers with:
- Batch processing support
- Result caching
- Performance optimizations
- Real-time capable
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from core.interfaces.base_agent import BaseAgent

# Import our components
from .detection import ExtremaDetector, DBSCANClusterer, LevelValidator, VolumeProfileAnalyzer
from .scoring import StrengthCalculator, LevelProjector
from .utils import DataLoader, get_logger

logger = get_logger(__name__)


class SupportResistanceAgent(BaseAgent):
    """
    Support/Resistance Agent for identifying key price levels.
    
    Optimized Features:
    - Single ticker processing (<3 seconds)
    - Batch processing (1-100 tickers efficiently)
    - Result caching (avoid reprocessing)
    - Performance optimized algorithms
    
    Developer: Developer 2
    Milestone: M2 - Core Prediction Models
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Support/Resistance Agent."""
        super().__init__(name="support_resistance_agent", config=config)
        self.version = "1.0.0"
        
        # Configuration
        self.config = config or {}
        self.use_mock_data = self.config.get("use_mock_data", True)
        self.enable_cache = self.config.get("enable_cache", True)
        self.max_levels = self.config.get("max_levels", 5)
        self.min_strength = self.config.get("min_strength", 50)
        
        # Initialize components (lazy loading for performance)
        self.data_loader: Optional[DataLoader] = None
        self.extrema_detector: Optional[ExtremaDetector] = None
        self.clusterer: Optional[DBSCANClusterer] = None
        self.validator: Optional[LevelValidator] = None
        self.strength_calculator: Optional[StrengthCalculator] = None
        self.volume_analyzer: Optional[VolumeProfileAnalyzer] = None
        self.level_projector: Optional[LevelProjector] = None
        
        # Cache for results (in-memory, can be replaced with Redis for production)
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._cache_ttl = timedelta(hours=1)  # Cache expires after 1 hour
        
        logger.info("SupportResistanceAgent initialized")
    
    def initialize(self) -> bool:
        """
        Initialize the Support/Resistance Agent.
        
        Sets up all components with optimized parameters.
        """
        try:
            # Initialize data loader
            self.data_loader = DataLoader(
                use_mock_data=self.use_mock_data,
                data_agent=self.config.get("data_agent")
            )
            
            # Initialize detection components with optimized parameters
            self.extrema_detector = ExtremaDetector(
                window_size=5,  # Balanced: not too sensitive, not too strict
                min_distance=10  # Minimum distance between extrema
            )
            
            self.clusterer = DBSCANClusterer(
                eps=0.02,  # 2% price tolerance for clustering
                min_samples=2  # At least 2 touches for a level (reduced for better detection)
            )
            
            self.validator = LevelValidator(
                tolerance=0.005,  # 0.5% tolerance for touches
                lookforward_bars=5  # Check 5 bars ahead for reactions
            )
            
            # Initialize strength calculator
            self.strength_calculator = StrengthCalculator(
                touch_weight=0.4,  # 40% weight on touch count
                time_weight=0.3,   # 30% weight on time relevance
                reaction_weight=0.3  # 30% weight on price reactions
            )
            
            # Initialize volume profile analyzer
            self.volume_analyzer = VolumeProfileAnalyzer(
                num_bins=50,  # 50 price bins for volume histogram
                min_volume_threshold=0.6,  # Top 40% volume nodes
                min_touches=2  # Minimum touches for volume levels
            )
            
            # Initialize level projector (with optional ML model)
            ml_model_path = self.config.get("ml_model_path")
            use_ml = self.config.get("use_ml_predictions", True)  # Enable ML by default
            self.level_projector = LevelProjector(use_ml=use_ml, ml_model_path=ml_model_path)
            
            self.initialized = True
            logger.info("SupportResistanceAgent initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SupportResistanceAgent: {e}", exc_info=True)
            self.initialized = False
            return False
    
    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect support/resistance levels for a given symbol.
        
        This is the main entry point. It handles:
        - Cache checking
        - Data loading
        - Level detection pipeline
        - Result formatting
        
        Args:
            symbol: Stock symbol
            params: Optional parameters:
                - min_strength: Minimum strength score (default: 50)
                - max_levels: Maximum levels per type (default: 5)
                - use_cache: Use cached results (default: True)
                - timeframe: Data timeframe ("1m", "1h", "1d", "1w", "1mo", "1y") (default: "1d")
                - project_future: Predict future levels (default: False)
                - projection_periods: Number of periods to project ahead (default: 20)
            
        Returns:
            Dictionary with support/resistance levels
        """
        if not self.initialized:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Agent not initialized. Call initialize() first."
            }
        
        params = params or {}
        min_strength = params.get("min_strength", self.min_strength)
        max_levels = params.get("max_levels", self.max_levels)
        use_cache = params.get("use_cache", self.enable_cache)
        timeframe = params.get("timeframe", "1d")
        project_future = params.get("project_future", False)
        projection_periods = params.get("projection_periods", 20)
        lookback_days = params.get("lookback_days")  # Optional custom lookback
        
        # Check cache first (performance optimization)
        # Include lookback_days in cache key if provided
        cache_key_parts = [symbol, str(min_strength), str(max_levels), timeframe, str(project_future)]
        if lookback_days:
            cache_key_parts.append(str(lookback_days))
        cache_key = "_".join(cache_key_parts)
        
        if use_cache and self._is_cached(cache_key):
            logger.info(f"Returning cached results for {symbol}")
            return self._get_cached(cache_key)
        
        # Detect levels
        result = self.detect_levels(symbol, min_strength, max_levels, timeframe, project_future, projection_periods, lookback_days)
        
        # Cache result
        if use_cache:
            self._cache_result(cache_key, result)
        
        return result
    
    def detect_levels(
        self,
        symbol: str,
        min_strength: int = 50,
        max_levels: int = 5,
        timeframe: str = "1d",
        project_future: bool = False,
        projection_periods: int = 20,
        lookback_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Detect support and resistance levels.
        
        Complete pipeline:
        1. Load OHLCV data
        2. Detect extrema (peaks and valleys)
        3. Cluster extrema into levels
        4. Validate levels
        5. Calculate strength scores
        6. Filter and rank levels
        
        Args:
            symbol: Stock symbol
            min_strength: Minimum strength score (0-100)
            max_levels: Maximum number of levels per type
            timeframe: Data timeframe ("1m", "1h", "1d", "1w", "1mo", "1y") (default: "1d")
            project_future: Whether to predict future levels (default: False)
            projection_periods: Number of periods ahead to project (default: 20)
            
        Returns:
            Dictionary with detected levels
        """
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Load data
            logger.info(f"Loading data for {symbol}...")
            from datetime import timezone
            now = datetime.now(timezone.utc)
            
            # Determine lookback period: use custom if provided, otherwise use default based on timeframe
            if lookback_days is not None:
                # Use custom lookback period
                actual_lookback_days = lookback_days
                logger.info(f"Using custom lookback period: {lookback_days} days")
            else:
                # Use default lookback period based on timeframe
                timeframe_days_map = {
                    '1m': 30,    # 30 days for 1-minute data
                    '5m': 30,
                    '15m': 30,
                    '30m': 30,
                    '1h': 90,    # 90 days for 1-hour data
                    '4h': 90,
                    '1d': 730,   # 2 years for daily data
                    '1w': 1095,  # 3 years for weekly data
                    '1mo': 1825, # 5 years for monthly data
                    '1y': 3650   # 10 years for yearly data
                }
                actual_lookback_days = timeframe_days_map.get(timeframe, 730)
                logger.info(f"Using default lookback period for {timeframe}: {actual_lookback_days} days")
            
            df, data_source = self.data_loader.load_ohlcv_data(
                symbol=symbol,
                start_date=now - timedelta(days=actual_lookback_days),
                end_date=now,
                timeframe=timeframe
            )
            
            if df.empty:
                actual_lookback_days = lookback_days if lookback_days is not None else 730
                return {
                    "symbol": symbol,
                    "status": "error",
                    "message": f"No data available for {symbol} with the requested parameters (timeframe: {timeframe}, lookback: {actual_lookback_days} days). Try reducing the lookback period or using a different timeframe."
                }
            
            # Check minimum data requirement
            # For daily data: ~60% of lookback days (accounts for weekends/holidays)
            # For other timeframes: at least 50 data points or lookback period, whichever is lower
            if timeframe == "1d":
                # Daily data: expect ~60% trading days (weekends + holidays reduce available days)
                min_required = max(50, int(actual_lookback_days * 0.6))
            else:
                # For intraday data, use a more lenient requirement
                min_required = max(30, min(50, actual_lookback_days))
            
            if len(df) < min_required:
                actual_lookback_days = lookback_days if lookback_days is not None else 730
                logger.warning(f"Only {len(df)} data points available for {symbol}. Minimum {min_required} recommended for reliable detection.")
                return {
                    "symbol": symbol,
                    "status": "error",
                    "message": f"Insufficient data for {symbol}: Only {len(df)} data points available. Need at least {min_required} data points for {actual_lookback_days} days lookback. Try reducing the lookback period or using a different timeframe."
                }
            
            current_price = float(df.iloc[-1]['close'])
            
            # Step 2: Detect extrema
            logger.debug(f"Detecting extrema for {symbol}...")
            peaks, valleys = self.extrema_detector.detect_all_extrema(df)
            
            # Filter noise (less aggressive for better results)
            # min_price_change=0.005 means 0.5% change (less strict)
            peaks = self.extrema_detector.filter_noise(peaks, min_price_change=0.005)
            valleys = self.extrema_detector.filter_noise(valleys, min_price_change=0.005)
            
            # Performance optimization: Limit extrema if too many (prevents slow clustering)
            max_extrema = 500  # Reasonable limit for fast processing
            if len(peaks) > max_extrema:
                logger.warning(f"Too many peaks ({len(peaks)}), limiting to {max_extrema} strongest")
                # Sort by price (keep most significant) and limit
                peaks = sorted(peaks, key=lambda x: x['price'], reverse=True)[:max_extrema]
            if len(valleys) > max_extrema:
                logger.warning(f"Too many valleys ({len(valleys)}), limiting to {max_extrema} strongest")
                # Sort by price (keep most significant) and limit
                valleys = sorted(valleys, key=lambda x: x['price'])[:max_extrema]
            
            # Step 3: Cluster extrema into levels
            logger.debug(f"Clustering extrema for {symbol}...")
            resistance_levels = self.clusterer.cluster_levels(peaks)
            support_levels = self.clusterer.cluster_levels(valleys)
            
            # Filter weak clusters (allow single touches for now, will be filtered by strength later)
            resistance_levels = self.clusterer.filter_clusters(resistance_levels, min_touches=1)
            support_levels = self.clusterer.filter_clusters(support_levels, min_touches=1)
            
            # Step 4: Validate levels (optimized for large datasets)
            logger.info(f"Validating levels for {symbol} ({len(resistance_levels)} resistance, {len(support_levels)} support)...")
            
            # Performance optimization: Skip validation for very large datasets or limit validation
            data_size = len(df)
            skip_validation = data_size > 200  # Skip validation if more than 200 data points (too slow for real-time)
            
            if skip_validation:
                logger.warning(f"Large dataset ({data_size} points) - skipping validation for performance")
                # Set default validation values
                for level in resistance_levels + support_levels:
                    level['validated'] = False
                    level['validation_rate'] = 0.5  # Assume moderate validation
                    level['reaction_count'] = level.get('touches', 0) // 2
                    level['touch_count'] = level.get('touches', 0)
            else:
                # Limit validation to top levels only (performance optimization)
                # For smaller datasets, only validate top 10 levels total
                max_levels_to_validate = min(10, len(resistance_levels) + len(support_levels))
                resistance_to_validate = sorted(resistance_levels, key=lambda x: x.get('touches', 0), reverse=True)[:max_levels_to_validate // 2]
                support_to_validate = sorted(support_levels, key=lambda x: x.get('touches', 0), reverse=True)[:max_levels_to_validate // 2]
                
                # Validate only the top levels
                validated_resistance = self.validator.validate_levels(resistance_to_validate, df)
                validated_support = self.validator.validate_levels(support_to_validate, df)
                
                # Merge validated results back with unvalidated (set default validation for unvalidated)
                validated_dict = {l['price']: l for l in validated_resistance}
                resistance_levels = [
                    validated_dict.get(l['price'], {**l, 'validated': False, 'validation_rate': 0.0, 'reaction_count': 0, 'touch_count': l.get('touches', 0)})
                    for l in resistance_levels
                ]
                validated_dict = {l['price']: l for l in validated_support}
                support_levels = [
                    validated_dict.get(l['price'], {**l, 'validated': False, 'validation_rate': 0.0, 'reaction_count': 0, 'touch_count': l.get('touches', 0)})
                    for l in support_levels
                ]
            
            # Step 5: Calculate strength scores
            logger.debug(f"Calculating strength scores for {symbol}...")
            from datetime import timezone
            current_date = datetime.now(timezone.utc)
            resistance_levels = self.strength_calculator.calculate_strengths(resistance_levels, current_date)
            support_levels = self.strength_calculator.calculate_strengths(support_levels, current_date)
            
            # Step 5.5: Detect volume-based levels and merge
            logger.debug(f"Analyzing volume profile for {symbol}...")
            volume_levels = self.volume_analyzer.detect_volume_levels(df)
            
            # Calculate strength for volume levels (they may not have all required fields)
            volume_resistance = [v for v in volume_levels if v.get('type') == 'resistance']
            volume_support = [v for v in volume_levels if v.get('type') == 'support']
            
            # Add default values for volume levels to enable strength calculation
            for level in volume_resistance + volume_support:
                if 'validation_rate' not in level:
                    level['validation_rate'] = 0.5  # Default moderate validation
                if 'touches' not in level:
                    level['touches'] = level.get('touch_count', 2)
            
            # Calculate strength for volume levels
            if volume_resistance:
                volume_resistance = self.strength_calculator.calculate_strengths(volume_resistance, current_date)
            if volume_support:
                volume_support = self.strength_calculator.calculate_strengths(volume_support, current_date)
            
            # Merge close levels (volume + price)
            resistance_levels = self.volume_analyzer.merge_with_price_levels(
                resistance_levels,
                volume_resistance,
                merge_tolerance=0.02
            )
            support_levels = self.volume_analyzer.merge_with_price_levels(
                support_levels,
                volume_support,
                merge_tolerance=0.02
            )
            
            # Ensure all levels have strength (recalculate if needed after merge)
            for level in resistance_levels:
                if 'strength' not in level or level.get('strength', 0) == 0:
                    level['strength'] = self.strength_calculator.calculate_strength(level, current_date)
            for level in support_levels:
                if 'strength' not in level or level.get('strength', 0) == 0:
                    level['strength'] = self.strength_calculator.calculate_strength(level, current_date)
            
            # Step 5.6: Calculate breakout probabilities
            logger.debug(f"Calculating breakout probabilities for {symbol}...")
            resistance_levels = self.strength_calculator.calculate_breakout_probabilities(
                resistance_levels, current_price
            )
            support_levels = self.strength_calculator.calculate_breakout_probabilities(
                support_levels, current_price
            )
            
            # Step 5.7: Project levels forward in time (if requested)
            predicted_future_levels = []
            if project_future:
                logger.debug(f"Predicting future levels for {symbol}...")
                
                # Predict new future levels based on patterns
                predicted_future_levels = self.level_projector.predict_future_levels(
                    df, current_price, timeframe, projection_periods
                )
                
                # Project existing levels forward (add validity projections)
                # Convert projection_periods to days based on timeframe
                timeframe_days_map = {
                    '1m': 1/1440, '5m': 5/1440, '15m': 15/1440, '30m': 30/1440,
                    '1h': 1/24, '4h': 4/24,
                    '1d': 1, '1w': 7, '1mo': 30, '1y': 365
                }
                projection_days = int(projection_periods * timeframe_days_map.get(timeframe, 1))
                
                all_levels = resistance_levels + support_levels
                for level in all_levels:
                    projection = self.level_projector.project_level_validity(level, projection_days)
                    level['projected_valid_until'] = projection.get('valid_until')
                    level['projected_validity_probability'] = projection.get('validity_probability')
                    level['projected_strength'] = projection.get('projected_strength')
                    level['timeframe'] = timeframe
                    level['projection_periods'] = projection_periods
            
            # Step 6: Filter by strength and limit count
            resistance_levels = [
                level for level in resistance_levels
                if level['strength'] >= min_strength
            ]
            support_levels = [
                level for level in support_levels
                if level['strength'] >= min_strength
            ]
            
            # Sort by strength (highest first) and limit
            resistance_levels = sorted(
                resistance_levels,
                key=lambda x: x['strength'],
                reverse=True
            )[:max_levels]
            
            support_levels = sorted(
                support_levels,
                key=lambda x: x['strength'],
                reverse=True
            )[:max_levels]
            
            # Format response
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Format levels
            formatted_support = self._format_levels(support_levels)
            formatted_resistance = self._format_levels(resistance_levels)
            
            # Create key price levels summary (Price + Strength + Direction format)
            key_levels_summary = self._create_key_levels_summary(
                formatted_support, 
                formatted_resistance, 
                current_price
            )
            
            result = {
                "symbol": symbol,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "current_price": current_price,
                "timeframe": timeframe,
                "support_levels": formatted_support,
                "resistance_levels": formatted_resistance,
                "key_price_levels": key_levels_summary,  # New: Formatted summary
                "total_levels": len(support_levels) + len(resistance_levels),
                "nearest_support": support_levels[0]['price'] if support_levels else None,
                "nearest_resistance": resistance_levels[0]['price'] if resistance_levels else None,
                "processing_time_seconds": round(processing_time, 3),
                "metadata": {
                    "peaks_detected": len(peaks),
                    "valleys_detected": len(valleys),
                    "data_points": len(df),
                    "lookback_days": actual_lookback_days,
                    "lookback_days_source": "custom" if lookback_days is not None else "default",
                    "default_lookback_days": self._get_default_lookback_days(timeframe),
                    "timeframe": timeframe,
                    "custom_lookback": lookback_days is not None,
                    "data_source": data_source,
                    "data_source_label": self._get_data_source_label(data_source)
                }
            }
            
            # Add predicted future levels if requested
            if project_future and predicted_future_levels:
                result["predicted_future_levels"] = self._format_predicted_levels(predicted_future_levels)
                result["projection_periods"] = projection_periods
                result["projection_timeframe"] = timeframe
            
            logger.info(
                f"Level detection complete for {symbol}: "
                f"{len(support_levels)} support, {len(resistance_levels)} resistance "
                f"({processing_time:.2f}s)"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting levels for {symbol}: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "status": "error",
                "message": str(e)
            }
    
    def detect_levels_batch(
        self,
        symbols: List[str],
        min_strength: int = 50,
        max_levels: int = 5,
        use_parallel: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Detect levels for multiple tickers efficiently.
        
        Optimized for batch processing (1-100 tickers):
        - Sequential processing (default, simpler)
        - Parallel processing (optional, faster for many tickers)
        - Cache utilization
        - Progress tracking
        
        Args:
            symbols: List of stock symbols
            min_strength: Minimum strength score
            max_levels: Maximum levels per type
            use_parallel: Use parallel processing (default: False)
                        - True: Faster for 10+ tickers
                        - False: Simpler, works for any number
        
        Returns:
            Dictionary mapping symbol to results
        """
        start_time = datetime.utcnow()
        results = {}
        
        logger.info(f"Starting batch detection for {len(symbols)} tickers...")
        
        if use_parallel and len(symbols) > 5:
            # Parallel processing for large batches
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            with ThreadPoolExecutor(max_workers=min(10, len(symbols))) as executor:
                future_to_symbol = {
                    executor.submit(self.process, symbol, {
                        "min_strength": min_strength,
                        "max_levels": max_levels,
                        "use_cache": True
                    }): symbol
                    for symbol in symbols
                }
                
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        results[symbol] = future.result()
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        results[symbol] = {
                            "symbol": symbol,
                            "status": "error",
                            "message": str(e)
                        }
        else:
            # Sequential processing (simpler, more reliable)
            for i, symbol in enumerate(symbols, 1):
                logger.info(f"Processing {symbol} ({i}/{len(symbols)})...")
                results[symbol] = self.process(symbol, {
                    "min_strength": min_strength,
                    "max_levels": max_levels,
                    "use_cache": True
                })
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        avg_time = total_time / len(symbols) if symbols else 0
        
        logger.info(
            f"Batch detection complete: {len(symbols)} tickers in {total_time:.2f}s "
            f"(avg: {avg_time:.2f}s per ticker)"
        )
        
        return results
    
    def _format_levels(self, levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format levels for response."""
        formatted = []
        for level in levels:
            # Convert datetime objects to ISO format strings for JSON serialization
            first_touch = level.get('first_touch')
            last_touch = level.get('last_touch')
            
            # Handle pandas Timestamp objects
            if first_touch is not None:
                if hasattr(first_touch, 'to_pydatetime'):
                    first_touch = first_touch.to_pydatetime()
                if isinstance(first_touch, datetime):
                    first_touch = first_touch.isoformat() + "Z" if first_touch.tzinfo else first_touch.isoformat()
                elif not isinstance(first_touch, str):
                    first_touch = str(first_touch)
            
            if last_touch is not None:
                if hasattr(last_touch, 'to_pydatetime'):
                    last_touch = last_touch.to_pydatetime()
                if isinstance(last_touch, datetime):
                    last_touch = last_touch.isoformat() + "Z" if last_touch.tzinfo else last_touch.isoformat()
                elif not isinstance(last_touch, str):
                    last_touch = str(last_touch)
            
            formatted_level = {
                "price": level['price'],
                "strength": level['strength'],
                "type": level.get('type', 'unknown'),
                "touches": level.get('touches', level.get('touch_count', 0)),
                "validated": level.get('validated', False),
                "validation_rate": level.get('validation_rate', 0.0),
                "breakout_probability": round(level.get('breakout_probability', 0.0), 1),  # Add breakout probability
                "first_touch": first_touch,
                "last_touch": last_touch
            }
            
            # Add volume information if available
            if 'volume' in level:
                formatted_level['volume'] = level.get('volume', 0)
                formatted_level['volume_percentile'] = round(level.get('volume_percentile', 0.0), 1)
                formatted_level['has_volume_confirmation'] = level.get('has_volume_confirmation', False)
            
            formatted.append(formatted_level)
        return formatted
    
    def _format_predicted_levels(self, predicted_levels: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format predicted future levels for response."""
        formatted = []
        for level in predicted_levels:
            formatted.append({
                "price": level['price'],
                "type": level.get('type', 'unknown'),
                "source": level.get('source', 'pattern'),
                "confidence": round(level.get('confidence', 0), 1),
                "projected_timeframe": level.get('projected_timeframe', 20),
                "is_predicted": True
            })
        return formatted
    
    def _create_key_levels_summary(
        self, 
        support_levels: List[Dict[str, Any]], 
        resistance_levels: List[Dict[str, Any]],
        current_price: float
    ) -> List[Dict[str, Any]]:
        """
        Create key price levels summary in format: Price + Strength + Direction.
        
        This matches the specification: Key Price Levels with Level Strength Score (0-100)
        and Breakout Probability % in format: Price + Strength + Direction.
        
        Args:
            support_levels: List of formatted support levels
            resistance_levels: List of formatted resistance levels
            current_price: Current stock price
            
        Returns:
            List of key levels with formatted summary
        """
        key_levels = []
        
        # Combine all levels and sort by price
        all_levels = []
        for level in support_levels:
            all_levels.append({
                **level,
                "direction": "SUPPORT"  # Direction: price bounces UP from support
            })
        for level in resistance_levels:
            all_levels.append({
                **level,
                "direction": "RESISTANCE"  # Direction: price bounces DOWN from resistance
            })
        
        # Sort by strength (highest first) to get key levels
        all_levels.sort(key=lambda x: x.get('strength', 0), reverse=True)
        
        # Create formatted summary for each key level
        for level in all_levels:
            price = level.get('price', 0)
            strength = level.get('strength', 0)
            breakout_prob = level.get('breakout_probability', 0.0)
            direction = level.get('direction', 'UNKNOWN')
            level_type = level.get('type', 'unknown')
            
            # Determine relative position to current price
            if price < current_price:
                position = "BELOW"
            elif price > current_price:
                position = "ABOVE"
            else:
                position = "AT"
            
            # Create formatted string: Price + Strength + Direction
            formatted_string = f"${price:.2f} | Strength: {strength}/100 | {direction} | Breakout: {breakout_prob}%"
            
            key_levels.append({
                "price": round(price, 2),
                "strength": strength,
                "strength_score": f"{strength}/100",  # Formatted strength score
                "breakout_probability": round(breakout_prob, 1),
                "breakout_probability_percent": f"{breakout_prob}%",  # Formatted percentage
                "direction": direction,
                "type": level_type,
                "position": position,  # Relative to current price
                "formatted": formatted_string,  # Complete formatted string: Price + Strength + Direction
                "touches": level.get('touches', 0),
                "validated": level.get('validated', False)
            })
        
        return key_levels
    
    def _get_data_source_label(self, data_source: str) -> str:
        """Get human-readable label for data source."""
        labels = {
            "data_agent": "Data Agent (Internal)",
            "yfinance": "Yahoo Finance (Real-time)",
            "mock_data": "Mock Data (Test)"
        }
        return labels.get(data_source, data_source)
    
    def _get_default_lookback_days(self, timeframe: str) -> int:
        """Get default lookback days for a given timeframe."""
        timeframe_days_map = {
            '1m': 30,    # 30 days for 1-minute data
            '5m': 30,
            '15m': 30,
            '30m': 30,
            '1h': 90,    # 90 days for 1-hour data
            '4h': 90,
            '1d': 730,   # 2 years for daily data
            '1w': 1095,  # 3 years for weekly data
            '1mo': 1825, # 5 years for monthly data
            '1y': 3650   # 10 years for yearly data
        }
        return timeframe_days_map.get(timeframe, 730)
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if result is cached and not expired."""
        if cache_key not in self._cache:
            return False
        
        if cache_key not in self._cache_timestamps:
            return False
        
        age = datetime.utcnow() - self._cache_timestamps[cache_key]
        return age < self._cache_ttl
    
    def _get_cached(self, cache_key: str) -> Dict[str, Any]:
        """Get cached result."""
        return self._cache[cache_key].copy()
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]) -> None:
        """Cache a result."""
        self._cache[cache_key] = result
        self._cache_timestamps[cache_key] = datetime.utcnow()
        
        # Limit cache size (keep last 100 entries)
        if len(self._cache) > 100:
            oldest_key = min(self._cache_timestamps.keys(), key=lambda k: self._cache_timestamps[k])
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]
    
    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """
        Clear cache for a symbol or all symbols.
        
        Args:
            symbol: Symbol to clear (None = clear all)
        """
        if symbol:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{symbol}_")]
            for key in keys_to_remove:
                del self._cache[key]
                del self._cache_timestamps[key]
            logger.info(f"Cleared cache for {symbol}")
        else:
            self._cache.clear()
            self._cache_timestamps.clear()
            logger.info("Cleared all cache")
    
    def validate_levels(
        self,
        symbol: str,
        levels: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate levels against historical price reactions.
        
        Args:
            symbol: Stock symbol
            levels: List of levels to validate
            
        Returns:
            Dictionary with validation results
        """
        if not self.initialized:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Agent not initialized"
            }
        
        # Load data
        from datetime import timezone
        now = datetime.now(timezone.utc)
        df, _ = self.data_loader.load_ohlcv_data(
            symbol=symbol,
            start_date=now - timedelta(days=730),
            end_date=now,
            timeframe="1d"
        )
        
        # Validate
        validated_levels = self.validator.validate_levels(levels, df)
        
        return {
            "symbol": symbol,
            "levels": validated_levels,
            "validation_rate": sum(1 for l in validated_levels if l['validated']) / len(validated_levels) if validated_levels else 0.0
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check Support/Resistance Agent health."""
        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "agent": self.name,
            "version": self.version,
            "cache_size": len(self._cache),
            "components_initialized": {
                "data_loader": self.data_loader is not None,
                "extrema_detector": self.extrema_detector is not None,
                "clusterer": self.clusterer is not None,
                "validator": self.validator is not None,
                "strength_calculator": self.strength_calculator is not None
            }
        }
