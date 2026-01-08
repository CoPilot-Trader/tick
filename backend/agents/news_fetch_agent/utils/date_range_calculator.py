"""
Date Range Calculator for Time Horizons

This module calculates appropriate date ranges for news fetching based on
prediction time horizons. Different horizons require different news windows.

Why Date Range Calculator?
- Centralizes date range logic
- Ensures consistent date ranges across agents
- Easy to adjust time windows for different horizons
- Handles edge cases (weekends, holidays, etc.)
"""

from typing import Tuple, Dict, Any
from datetime import datetime, timedelta, timezone


class DateRangeCalculator:
    """
    Calculator for date ranges based on time horizons.
    
    Maps prediction time horizons to appropriate news date ranges.
    Recent horizons (1s, 1m) need very recent news, while longer
    horizons (1mo, 1y) can use older news.
    
    Example:
        calculator = DateRangeCalculator()
        from_date, to_date = calculator.calculate("1d", symbol="AAPL")
    """
    
    # Time horizon to news window mapping
    HORIZON_WINDOWS: Dict[str, Dict[str, Any]] = {
        "1s": {
            "window_minutes": 5,
            "description": "Last 5 minutes - breaking news only"
        },
        "1m": {
            "window_minutes": 15,
            "description": "Last 15 minutes - very recent news"
        },
        "1h": {
            "window_hours": 6,
            "description": "Last 6 hours - intraday news"
        },
        "1d": {
            "window_days": 3,
            "description": "Last 3 days - daily news cycle"
        },
        "1w": {
            "window_days": 7,
            "description": "Last week - weekly trends"
        },
        "1mo": {
            "window_days": 30,
            "description": "Last month - monthly trends"
        },
        "1y": {
            "window_days": 365,
            "description": "Last year - long-term trends"
        }
    }
    
    @classmethod
    def calculate(cls, time_horizon: str, symbol: str = None, current_time: datetime = None, min_articles: int = None) -> Tuple[datetime, datetime]:
        """
        Calculate date range for a given time horizon.
        
        Args:
            time_horizon: Prediction time horizon ("1s", "1m", "1h", "1d", "1w", "1mo", "1y")
            symbol: Stock symbol (optional, for logging)
            current_time: Current time (default: now, UTC)
            min_articles: Minimum articles required (optional, for dynamic adjustment)
        
        Returns:
            Tuple of (from_date, to_date) in UTC timezone
        
        Raises:
            ValueError: If time_horizon is not supported
        
        Example:
            from_date, to_date = DateRangeCalculator.calculate("1d", "AAPL")
            # Returns: (3 days ago, now)
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        elif current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        
        # Normalize time horizon
        time_horizon = time_horizon.lower().strip()
        
        if time_horizon not in cls.HORIZON_WINDOWS:
            raise ValueError(
                f"Unsupported time_horizon: {time_horizon}. "
                f"Supported: {list(cls.HORIZON_WINDOWS.keys())}"
            )
        
        window_config = cls.HORIZON_WINDOWS[time_horizon]
        to_date = current_time
        
        # Calculate from_date based on window type
        if "window_minutes" in window_config:
            base_window = window_config["window_minutes"]
            from_date = current_time - timedelta(minutes=base_window)
        elif "window_hours" in window_config:
            base_window = window_config["window_hours"]
            from_date = current_time - timedelta(hours=base_window)
        elif "window_days" in window_config:
            base_window = window_config["window_days"]
            from_date = current_time - timedelta(days=base_window)
        else:
            # Default to 1 day if config is missing
            base_window = 1
            from_date = current_time - timedelta(days=base_window)
        
        # Dynamic window adjustment: If min_articles is specified and we might need more news,
        # we'll expand the window. This is handled by the caller after initial fetch.
        # For now, return the base window. The caller can expand if needed.
        
        return from_date, to_date
    
    @classmethod
    def get_window_description(cls, time_horizon: str) -> str:
        """
        Get description of the news window for a time horizon.
        
        Args:
            time_horizon: Prediction time horizon
        
        Returns:
            Description string
        
        Example:
            desc = DateRangeCalculator.get_window_description("1d")
            # Returns: "Last 3 days - daily news cycle"
        """
        time_horizon = time_horizon.lower().strip()
        if time_horizon in cls.HORIZON_WINDOWS:
            return cls.HORIZON_WINDOWS[time_horizon].get("description", "")
        return f"Unknown horizon: {time_horizon}"
    
    @classmethod
    def expand_window(cls, time_horizon: str, from_date: datetime, to_date: datetime, multiplier: float = 1.5) -> Tuple[datetime, datetime]:
        """
        Expand date window if not enough articles were found.
        
        This is used for dynamic window adjustment - if initial fetch doesn't
        return enough articles, expand the window to get more news.
        
        Args:
            time_horizon: Prediction time horizon
            from_date: Current from_date
            to_date: Current to_date (usually now)
            multiplier: How much to expand (default: 1.5 = 50% expansion)
        
        Returns:
            Tuple of (expanded_from_date, to_date)
        
        Example:
            expanded_from, to = DateRangeCalculator.expand_window("1d", from_date, to_date)
            # Expands 3-day window to 4.5 days
        """
        time_horizon = time_horizon.lower().strip()
        window_config = cls.HORIZON_WINDOWS.get(time_horizon, {})
        
        # Calculate original window size
        if "window_minutes" in window_config:
            window_size = (to_date - from_date).total_seconds() / 60  # minutes
            expanded_size = window_size * multiplier
            expanded_from = to_date - timedelta(minutes=expanded_size)
        elif "window_hours" in window_config:
            window_size = (to_date - from_date).total_seconds() / 3600  # hours
            expanded_size = window_size * multiplier
            expanded_from = to_date - timedelta(hours=expanded_size)
        elif "window_days" in window_config:
            window_size = (to_date - from_date).total_seconds() / 86400  # days
            expanded_size = window_size * multiplier
            expanded_from = to_date - timedelta(days=expanded_size)
        else:
            # Default: expand by multiplier
            window_size = (to_date - from_date).total_seconds() / 86400
            expanded_size = window_size * multiplier
            expanded_from = to_date - timedelta(days=expanded_size)
        
        return expanded_from, to_date
    
    @classmethod
    def format_for_api(cls, from_date: datetime, to_date: datetime, api_format: str = "iso") -> Dict[str, str]:
        """
        Format dates for API requests.
        
        Different APIs expect different date formats:
        - Finnhub: YYYY-MM-DD
        - NewsAPI: YYYY-MM-DD or ISO format
        - Alpha Vantage: Varies
        
        Args:
            from_date: Start date
            to_date: End date
            api_format: Format type ("iso", "finnhub", "newsapi")
        
        Returns:
            Dictionary with formatted dates: {"from": "...", "to": "..."}
        
        Example:
            dates = DateRangeCalculator.format_for_api(from_date, to_date, "finnhub")
            # Returns: {"from": "2024-01-15", "to": "2024-01-18"}
        """
        if api_format == "finnhub":
            # Finnhub expects YYYY-MM-DD format
            return {
                "from": from_date.strftime("%Y-%m-%d"),
                "to": to_date.strftime("%Y-%m-%d")
            }
        elif api_format == "newsapi":
            # NewsAPI accepts ISO format or YYYY-MM-DD
            return {
                "from": from_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "to": to_date.strftime("%Y-%m-%dT%H:%M:%S")
            }
        else:
            # Default: ISO format
            return {
                "from": from_date.isoformat(),
                "to": to_date.isoformat()
            }

