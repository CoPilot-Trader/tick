"""
============================================================================
TICK DATA PIPELINE - CONTEXT LOADER
============================================================================
Adapted from client's Copilot Intelligence context_loader.py

Purpose: Load all context modules and merge to signals
Design: Extensible loader pattern with caching and validation

Usage:
    from context.loader import ContextLoader
    loader = ContextLoader()
    enriched = loader.enrich_signals(raw_signals_df)
============================================================================
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np

from ..schema import (
    SchemaRegistry,
    ModuleSchema,
    ModuleType,
    MARKET_TICKER,
    normalize_dataframe,
    add_sector_column,
    validate_join_keys,
    merge_market_wide_context,
    merge_ticker_context,
)

logger = logging.getLogger(__name__)


@dataclass
class LoaderConfig:
    """Configuration for the context loader."""
    max_lookback_days: int = 30
    fill_missing_with_last: bool = True
    validate_on_load: bool = True
    enable_cache: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    log_load_times: bool = True
    warn_on_stale_data: bool = True

    @classmethod
    def from_env(cls) -> "LoaderConfig":
        """Create config from environment variables."""
        return cls(
            max_lookback_days=int(os.getenv("CONTEXT_LOOKBACK_DAYS", "30")),
            enable_cache=os.getenv("CONTEXT_CACHE_ENABLED", "true").lower() == "true",
        )


class ContextLoader:
    """
    Main loader for all context modules.

    Features:
    - Auto-discovers modules from registry
    - Loads and caches context data
    - Handles different merge strategies per module type
    - Validates data freshness

    Usage:
        loader = ContextLoader()

        # Enrich signals with all context
        enriched = loader.enrich_signals(raw_signals_df)

        # Get specific context
        macro = loader.get_macro_context(date="2025-01-15")
    """

    def __init__(self, config: Optional[LoaderConfig] = None):
        self.config = config or LoaderConfig.from_env()
        self._cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}
        self._modules: Dict[str, Any] = {}

        # Lazy-load context module instances
        self._init_modules()

    def _init_modules(self) -> None:
        """Initialize context module instances."""
        try:
            from .mod06_events import EventsContext
            from .mod09_macro import MacroContext
            from .mod10_sentiment import SentimentContext
            from .mod11_rotation import RotationContext
            from .mod13_earnings import EarningsContext
            from .mod14_economic import EconomicContext

            self._modules = {
                "mod06": EventsContext(),
                "mod09": MacroContext(),
                "mod10": SentimentContext(),
                "mod11": RotationContext(),
                "mod13": EarningsContext(),
                "mod14": EconomicContext(),
            }
            logger.info(f"Initialized {len(self._modules)} context modules")
        except ImportError as e:
            logger.warning(f"Some context modules not available: {e}")

    # ========================================================================
    # CACHE MANAGEMENT
    # ========================================================================

    def _get_cache_key(self, module_id: str, date: str) -> str:
        """Generate cache key."""
        return f"{module_id}_{date}"

    def _get_from_cache(self, cache_key: str) -> Optional[pd.DataFrame]:
        """Get data from cache if valid."""
        if not self.config.enable_cache:
            return None

        if cache_key in self._cache:
            df, cached_at = self._cache[cache_key]
            age = (datetime.now() - cached_at).total_seconds()
            if age < self.config.cache_ttl_seconds:
                logger.debug(f"Cache hit: {cache_key} (age: {age:.1f}s)")
                return df.copy()

        return None

    def _put_in_cache(self, cache_key: str, df: pd.DataFrame) -> None:
        """Store data in cache."""
        if self.config.enable_cache:
            self._cache[cache_key] = (df.copy(), datetime.now())

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.info("Context cache cleared")

    # ========================================================================
    # CONTEXT LOADING
    # ========================================================================

    def load_module_context(
        self,
        module_id: str,
        date: Optional[str] = None,
        tickers: Optional[List[str]] = None,
    ) -> Optional[pd.DataFrame]:
        """
        Load context data for a specific module.

        Args:
            module_id: Module ID (e.g., "mod09")
            date: Date string (YYYY-MM-DD), defaults to today
            tickers: List of tickers (for ticker-specific modules)

        Returns:
            DataFrame with context data
        """
        if module_id not in self._modules:
            logger.warning(f"Module {module_id} not available")
            return None

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Check cache
        cache_key = self._get_cache_key(module_id, date)
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # Load from module
        module = self._modules[module_id]
        try:
            if hasattr(module, "get_context"):
                df = module.get_context(date=date, tickers=tickers)
            else:
                logger.warning(f"Module {module_id} has no get_context method")
                return None

            if df is not None and not df.empty:
                self._put_in_cache(cache_key, df)

            return df

        except Exception as e:
            logger.error(f"Error loading {module_id} context: {e}")
            return None

    def load_all_context(
        self,
        date: Optional[str] = None,
        tickers: Optional[List[str]] = None,
        modules: Optional[List[str]] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Load all context modules for a given date.

        Args:
            date: Target date (defaults to today)
            tickers: List of tickers for ticker-specific modules
            modules: Optional list of specific modules to load

        Returns:
            Dict mapping module_id to DataFrame
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # Get modules to load (in dependency order)
        if modules:
            module_ids = modules
        else:
            module_ids = SchemaRegistry.get_load_order()

        context = {}
        for mod_id in module_ids:
            if mod_id in self._modules:
                df = self.load_module_context(mod_id, date, tickers)
                if df is not None:
                    context[mod_id] = df
                    logger.debug(f"Loaded {mod_id}: {len(df)} rows")

        return context

    # ========================================================================
    # SIGNAL ENRICHMENT
    # ========================================================================

    def enrich_signals(
        self,
        signals_df: pd.DataFrame,
        date: Optional[str] = None,
        modules: Optional[List[str]] = None,
        add_sectors: bool = True,
    ) -> pd.DataFrame:
        """
        Enrich signals DataFrame with all context modules.

        This is the main entry point for adding context to trading signals.

        Args:
            signals_df: Raw signals DataFrame (must have ticker, timestamp)
            date: Date for context lookup (defaults to signals' max date)
            modules: Specific modules to use (defaults to all)
            add_sectors: Whether to add sector column based on ticker

        Returns:
            Enriched signals DataFrame with all context columns
        """
        if signals_df.empty:
            logger.warning("Empty signals DataFrame, nothing to enrich")
            return signals_df

        # Normalize input signals
        signals_df = normalize_dataframe(signals_df)

        # Validate required columns
        if not validate_join_keys(signals_df, ["ticker", "timestamp"]):
            logger.error("Signals missing required join keys")
            return signals_df

        # Add sector column if requested
        if add_sectors:
            signals_df = add_sector_column(signals_df)

        # Determine date for context
        if date is None:
            date = pd.to_datetime(signals_df["timestamp"]).max().strftime("%Y-%m-%d")

        # Get tickers for ticker-specific modules
        tickers = signals_df["ticker"].unique().tolist()

        # Load all context
        context = self.load_all_context(date, tickers=tickers, modules=modules)

        # Merge context based on module type
        enriched = signals_df.copy()

        for mod_id, context_df in context.items():
            schema = SchemaRegistry.get(mod_id)
            if not schema:
                continue

            try:
                if schema.module_type == ModuleType.MARKET_WIDE:
                    enriched = merge_market_wide_context(
                        enriched, context_df, schema.column_prefix
                    )

                elif schema.module_type == ModuleType.TICKER_SPECIFIC:
                    enriched = merge_ticker_context(
                        enriched, context_df, schema.column_prefix
                    )

                elif schema.module_type == ModuleType.SECTOR_LEVEL:
                    enriched = self._merge_sector_context(
                        enriched, context_df, schema.column_prefix
                    )

                elif schema.module_type == ModuleType.EVENT_BASED:
                    enriched = merge_market_wide_context(
                        enriched, context_df, schema.column_prefix
                    )

                logger.debug(f"Merged {mod_id}")

            except Exception as e:
                logger.error(f"Failed to merge {mod_id}: {e}")

        # Log enrichment summary
        new_cols = len(enriched.columns) - len(signals_df.columns)
        logger.info(
            f"Enriched {len(enriched)} signals with {new_cols} context columns "
            f"from {len(context)} modules"
        )

        return enriched

    def _merge_sector_context(
        self,
        signals_df: pd.DataFrame,
        sector_df: pd.DataFrame,
        prefix: str,
    ) -> pd.DataFrame:
        """Merge sector-level context using sector column."""
        if "sector" not in signals_df.columns:
            signals_df = add_sector_column(signals_df)

        if "sector" not in sector_df.columns:
            logger.warning("Sector context missing 'sector' column")
            return signals_df

        # Prefix context columns
        rename_cols = [c for c in sector_df.columns if c not in ["sector", "timestamp"]]
        sector_df = sector_df.rename(columns={c: f"{prefix}{c}" for c in rename_cols})

        # Merge on sector + timestamp
        merged = pd.merge(
            signals_df,
            sector_df,
            on=["sector", "timestamp"] if "timestamp" in sector_df.columns else ["sector"],
            how="left",
        )

        return merged

    # ========================================================================
    # CONVENIENCE LOADERS
    # ========================================================================

    def get_macro_context(self, date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get macro/VIX context (MOD09)."""
        return self.load_module_context("mod09", date)

    def get_events_context(self, date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get events calendar context (MOD06)."""
        return self.load_module_context("mod06", date)

    def get_economic_context(self, date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get economic data context (MOD14)."""
        return self.load_module_context("mod14", date)

    def get_sentiment_context(
        self, tickers: List[str], date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """Get ticker sentiment context (MOD10)."""
        return self.load_module_context("mod10", date, tickers)

    def get_earnings_context(
        self, tickers: List[str], date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """Get ticker earnings context (MOD13)."""
        return self.load_module_context("mod13", date, tickers)

    def get_rotation_context(self, date: Optional[str] = None) -> Optional[pd.DataFrame]:
        """Get sector rotation context (MOD11)."""
        return self.load_module_context("mod11", date)

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def get_module_status(self) -> pd.DataFrame:
        """Get status of all context modules."""
        rows = []
        for mod_id, module in self._modules.items():
            schema = SchemaRegistry.get(mod_id)
            rows.append({
                "module_id": mod_id,
                "name": schema.module_name if schema else "unknown",
                "type": schema.module_type.value if schema else "unknown",
                "available": module is not None,
                "output_columns": len(schema.output_columns) if schema else 0,
            })
        return pd.DataFrame(rows)

    def print_status(self) -> None:
        """Print module status summary."""
        status = self.get_module_status()
        print("\n" + "=" * 60)
        print("CONTEXT MODULE STATUS")
        print("=" * 60)

        for _, row in status.iterrows():
            icon = "✓" if row["available"] else "○"
            print(
                f"  {icon} {row['module_id']:8} | {row['name']:12} | "
                f"{row['type']:15} | {row['output_columns']} columns"
            )

        print("=" * 60 + "\n")
