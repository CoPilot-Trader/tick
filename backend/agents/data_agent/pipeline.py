"""
============================================================================
TICK DATA PIPELINE - Historical & Real-time Pipelines
============================================================================
Purpose: Orchestrate data flow from raw OHLCV to enriched features

Historical Pipeline:
    Raw OHLCV → Feature Agent → Context Loader → Enriched Data → Storage

Real-time Pipeline:
    Price Tick → Update Buffer → Incremental Features → Cached Context → Output
============================================================================
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd
import numpy as np

from .schema import normalize_dataframe, normalize_timeframe

logger = logging.getLogger(__name__)


class HistoricalPipeline:
    """
    Pipeline for generating enriched historical data for model training.

    Fetches OHLCV data, calculates technical indicators, enriches with
    context modules, and stores in Parquet format.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._data_agent = None
        self._feature_agent = None
        self._context_loader = None
        self._storage = None

        # Default data path
        self.data_path = self.config.get(
            "data_path",
            os.getenv("DATA_LAKE_ROOT", "/srv/data_lake")
        )

    def _get_data_agent(self):
        """Lazy-load Data Agent."""
        if self._data_agent is None:
            from .agent import DataAgent
            self._data_agent = DataAgent(self.config)
            self._data_agent.initialize()
        return self._data_agent

    def _get_feature_agent(self):
        """Lazy-load Feature Agent."""
        if self._feature_agent is None:
            from ..feature_agent.agent import FeatureAgent
            self._feature_agent = FeatureAgent(self.config)
            self._feature_agent.initialize()
        return self._feature_agent

    def _get_context_loader(self):
        """Lazy-load Context Loader."""
        if self._context_loader is None:
            from .context import ContextLoader
            self._context_loader = ContextLoader()
        return self._context_loader

    def _get_storage(self):
        """Lazy-load Parquet Storage."""
        if self._storage is None:
            from .storage import ParquetStorage
            self._storage = ParquetStorage(base_path=self.data_path)
        return self._storage

    async def run(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "daily",
        enrich: bool = True,
        save: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """
        Run the historical pipeline for a list of tickers.

        Args:
            tickers: List of stock symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            timeframe: Data timeframe (daily, 5min, etc.)
            enrich: Whether to enrich with context modules
            save: Whether to save to storage

        Returns:
            Dict mapping ticker to enriched DataFrame
        """
        logger.info(f"Starting historical pipeline for {len(tickers)} tickers")
        logger.info(f"Date range: {start_date} to {end_date}, timeframe: {timeframe}")

        data_agent = self._get_data_agent()
        feature_agent = self._get_feature_agent()
        context_loader = self._get_context_loader() if enrich else None
        storage = self._get_storage() if save else None

        results = {}
        timeframe_normalized = normalize_timeframe(timeframe)

        for ticker in tickers:
            try:
                logger.info(f"Processing {ticker}...")

                # Step 1: Fetch OHLCV data
                ohlcv = data_agent.fetch_historical_sync(
                    ticker, start_date, end_date, timeframe
                )

                if ohlcv is None or ohlcv.empty:
                    logger.warning(f"No OHLCV data for {ticker}")
                    continue

                logger.debug(f"  Fetched {len(ohlcv)} bars for {ticker}")

                # Step 2: Calculate technical indicators
                with_features = feature_agent.calculate_all(ohlcv)
                logger.debug(f"  Calculated features: {len(with_features.columns)} columns")

                # Step 3: Enrich with context
                if enrich and context_loader:
                    # Prepare for context loader (needs ticker and timestamp columns)
                    with_features["ticker"] = ticker.upper()
                    if "timestamp" not in with_features.columns and "bar_ts" in with_features.columns:
                        with_features["timestamp"] = with_features["bar_ts"]

                    enriched = context_loader.enrich_signals(
                        with_features,
                        date=end_date.strftime("%Y-%m-%d"),
                    )
                    logger.debug(f"  Enriched to {len(enriched.columns)} columns")
                else:
                    enriched = with_features

                # Step 4: Save to storage
                if save and storage:
                    storage.save_ticker_data(
                        ticker=ticker,
                        data=enriched,
                        timeframe=timeframe_normalized,
                    )
                    logger.debug(f"  Saved to storage")

                results[ticker] = enriched

            except Exception as e:
                logger.error(f"Pipeline error for {ticker}: {e}")
                continue

        logger.info(f"Historical pipeline complete. Processed {len(results)}/{len(tickers)} tickers")
        return results

    def run_sync(
        self,
        tickers: List[str],
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "daily",
        enrich: bool = True,
        save: bool = True,
    ) -> Dict[str, pd.DataFrame]:
        """Synchronous version of run()."""
        import asyncio
        return asyncio.run(self.run(tickers, start_date, end_date, timeframe, enrich, save))

    def backfill(
        self,
        tickers: List[str],
        days: int = 365,
        timeframe: str = "daily",
    ) -> Dict[str, pd.DataFrame]:
        """
        Backfill historical data for specified tickers.

        Args:
            tickers: List of stock symbols
            days: Number of days to backfill
            timeframe: Data timeframe

        Returns:
            Dict of enriched DataFrames
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        return self.run_sync(
            tickers=tickers,
            start_date=start_date,
            end_date=end_date,
            timeframe=timeframe,
            enrich=True,
            save=True,
        )


class RealtimePipeline:
    """
    Pipeline for real-time feature generation.

    Maintains a sliding window of recent bars and calculates
    features incrementally for low-latency inference.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        buffer_size: int = 100,
        context_cache_ttl: int = 300,  # 5 minutes
    ):
        self.config = config or {}
        self.buffer_size = buffer_size
        self.context_cache_ttl = context_cache_ttl

        # Per-ticker buffers
        self._buffers: Dict[str, pd.DataFrame] = {}
        self._feature_agent = None
        self._context_cache: Dict[str, tuple] = {}  # {ticker: (context_df, timestamp)}

    def _get_feature_agent(self):
        """Lazy-load Feature Agent."""
        if self._feature_agent is None:
            from ..feature_agent.agent import FeatureAgent
            self._feature_agent = FeatureAgent(self.config)
            self._feature_agent.initialize()
        return self._feature_agent

    def _get_context_loader(self):
        """Get context loader for cache refresh."""
        from .context import ContextLoader
        return ContextLoader()

    def update_buffer(self, ticker: str, bar: Dict[str, Any]) -> None:
        """
        Add a new bar to the ticker's buffer.

        Args:
            ticker: Stock symbol
            bar: Dict with OHLCV data (timestamp, open, high, low, close, volume)
        """
        ticker = ticker.upper()

        # Create new row
        new_row = pd.DataFrame([bar])

        if ticker not in self._buffers:
            self._buffers[ticker] = new_row
        else:
            self._buffers[ticker] = pd.concat(
                [self._buffers[ticker], new_row],
                ignore_index=True
            )

            # Trim to buffer size
            if len(self._buffers[ticker]) > self.buffer_size:
                self._buffers[ticker] = self._buffers[ticker].tail(self.buffer_size)

    def get_cached_context(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached context for ticker, refresh if stale."""
        ticker = ticker.upper()
        now = datetime.now()

        if ticker in self._context_cache:
            ctx, cached_at = self._context_cache[ticker]
            age = (now - cached_at).total_seconds()
            if age < self.context_cache_ttl:
                return ctx

        # Refresh context
        try:
            loader = self._get_context_loader()

            # Get all relevant context
            context = {}

            # Macro context (market-wide)
            macro = loader.get_macro_context()
            if macro is not None and not macro.empty:
                context.update(macro.iloc[0].to_dict())

            # Earnings context (ticker-specific)
            earnings = loader.get_earnings_context([ticker])
            if earnings is not None and not earnings.empty:
                ticker_earnings = earnings[earnings["ticker"] == ticker]
                if not ticker_earnings.empty:
                    context.update(ticker_earnings.iloc[0].to_dict())

            # Rotation context (sector)
            rotation = loader.get_rotation_context()
            if rotation is not None and not rotation.empty:
                # Get this ticker's sector context
                from .schema import get_sector
                sector = get_sector(ticker)
                if sector:
                    sector_ctx = rotation[rotation["sector"] == sector]
                    if not sector_ctx.empty:
                        context.update(sector_ctx.iloc[0].to_dict())

            self._context_cache[ticker] = (context, now)
            return context

        except Exception as e:
            logger.warning(f"Failed to refresh context for {ticker}: {e}")
            return {}

    def process_tick(self, ticker: str, bar: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a new price tick and return enriched features.

        Args:
            ticker: Stock symbol
            bar: Dict with OHLCV data

        Returns:
            Dict with all features for inference
        """
        ticker = ticker.upper()

        # Update buffer
        self.update_buffer(ticker, bar)

        # Get buffer as DataFrame
        buffer_df = self._buffers.get(ticker)
        if buffer_df is None or buffer_df.empty:
            return {"error": "No data in buffer"}

        # Calculate features on buffer
        feature_agent = self._get_feature_agent()
        with_features = feature_agent.calculate_all(buffer_df.copy())

        # Get latest row
        latest_features = with_features.iloc[-1].to_dict()

        # Add cached context
        context = self.get_cached_context(ticker)
        if context:
            latest_features.update(context)

        # Add metadata
        latest_features["ticker"] = ticker
        latest_features["pipeline_timestamp"] = datetime.now().isoformat()

        return latest_features

    def clear_buffer(self, ticker: Optional[str] = None) -> None:
        """Clear buffer for specific ticker or all tickers."""
        if ticker:
            self._buffers.pop(ticker.upper(), None)
        else:
            self._buffers.clear()

    def clear_context_cache(self) -> None:
        """Clear context cache."""
        self._context_cache.clear()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def backfill_tickers(
    tickers: List[str],
    days: int = 365,
    timeframe: str = "daily",
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to backfill historical data.

    Args:
        tickers: List of stock symbols
        days: Number of days to backfill
        timeframe: Data timeframe

    Returns:
        Dict of enriched DataFrames
    """
    pipeline = HistoricalPipeline()
    return pipeline.backfill(tickers, days, timeframe)


def get_enriched_data(
    ticker: str,
    start_date: datetime,
    end_date: datetime,
    timeframe: str = "daily",
) -> Optional[pd.DataFrame]:
    """
    Convenience function to get enriched data for a single ticker.
    """
    pipeline = HistoricalPipeline()
    results = pipeline.run_sync(
        tickers=[ticker],
        start_date=start_date,
        end_date=end_date,
        timeframe=timeframe,
        enrich=True,
        save=False,
    )
    return results.get(ticker)
