"""
Parquet Storage for TICK Data Agent.

Stores historical OHLCV data in Parquet format for efficient batch processing.
File structure follows client's DATA_LAKE_SCHEMA_STANDARD.md conventions.

Directory Structure:
    storage/historical/raw/{ticker}/{timeframe}/{ticker}_{timeframe}_{date_range}.parquet
    
Example:
    storage/historical/raw/AAPL/1d/AAPL_1d_2022-01-01_2024-12-31.parquet
    storage/historical/raw/AAPL/5m/AAPL_5m_2024-01-01_2024-01-31.parquet
"""

import os
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False

logger = logging.getLogger(__name__)


class ParquetStorage:
    """
    Parquet-based storage for historical OHLCV data.
    
    Optimized for batch reading/writing in training pipelines.
    """
    
    # Standard column schema
    SCHEMA_COLUMNS = ["ticker", "timeframe", "bar_ts", "open", "high", "low", "close", "volume"]
    
    def __init__(self, base_path: str = "storage/historical"):
        """
        Initialize Parquet storage.
        
        Args:
            base_path: Base directory for parquet files
        """
        self.base_path = Path(base_path)
        self.raw_path = self.base_path / "raw"
        self.features_path = self.base_path / "features"
        
        # Create directories
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.features_path.mkdir(parents=True, exist_ok=True)
        
        if not PARQUET_AVAILABLE:
            logger.warning("pyarrow not installed. Parquet operations will fail.")
    
    def _get_raw_dir(self, ticker: str, timeframe: str) -> Path:
        """Get directory path for a ticker/timeframe combination."""
        return self.raw_path / ticker.upper() / timeframe
    
    def _get_features_dir(self, ticker: str, timeframe: str) -> Path:
        """Get features directory for a ticker/timeframe."""
        return self.features_path / ticker.upper() / timeframe
    
    def _generate_filename(
        self,
        ticker: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime
    ) -> str:
        """Generate standardized filename."""
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        return f"{ticker.upper()}_{timeframe}_{start_str}_{end_str}.parquet"
    
    # =========================================================================
    # Write Operations
    # =========================================================================
    
    def save_ohlcv(
        self,
        df: pd.DataFrame,
        ticker: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Save OHLCV data to Parquet file.
        
        Args:
            df: DataFrame with OHLCV data
            ticker: Stock symbol
            timeframe: Data timeframe
            start_date: Start date (auto-detected if not provided)
            end_date: End date (auto-detected if not provided)
            
        Returns:
            Path to saved file
        """
        if not PARQUET_AVAILABLE:
            raise RuntimeError("pyarrow not installed")
        
        if df.empty:
            raise ValueError("Cannot save empty DataFrame")
        
        # Ensure standard columns
        df = self._validate_schema(df, ticker, timeframe)
        
        # Auto-detect date range
        if start_date is None:
            start_date = df["bar_ts"].min()
        if end_date is None:
            end_date = df["bar_ts"].max()
        
        # Ensure datetime
        if isinstance(start_date, date) and not isinstance(start_date, datetime):
            start_date = datetime.combine(start_date, datetime.min.time())
        if isinstance(end_date, date) and not isinstance(end_date, datetime):
            end_date = datetime.combine(end_date, datetime.min.time())
        
        # Create directory
        out_dir = self._get_raw_dir(ticker, timeframe)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename and path
        filename = self._generate_filename(ticker, timeframe, start_date, end_date)
        filepath = out_dir / filename
        
        # Sort by timestamp before saving
        df = df.sort_values("bar_ts").reset_index(drop=True)
        
        # Write to parquet
        df.to_parquet(
            filepath,
            engine="pyarrow",
            compression="snappy",
            index=False
        )
        
        logger.info(f"Saved {len(df)} rows to {filepath}")
        return str(filepath)
    
    def append_ohlcv(
        self,
        df: pd.DataFrame,
        ticker: str,
        timeframe: str
    ) -> str:
        """
        Append new data to existing parquet file, or create new if not exists.
        Handles deduplication automatically.
        
        Args:
            df: New OHLCV data
            ticker: Stock symbol
            timeframe: Data timeframe
            
        Returns:
            Path to saved file
        """
        # Load existing data if any
        existing_df = self.load_ohlcv(ticker, timeframe)
        
        if existing_df is not None and not existing_df.empty:
            # Combine and deduplicate
            df = self._validate_schema(df, ticker, timeframe)
            combined = pd.concat([existing_df, df], ignore_index=True)
            combined = combined.drop_duplicates(subset=["ticker", "timeframe", "bar_ts"], keep="last")
        else:
            combined = df
        
        return self.save_ohlcv(combined, ticker, timeframe)
    
    # =========================================================================
    # Read Operations
    # =========================================================================
    
    def load_ohlcv(
        self,
        ticker: str,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Optional[pd.DataFrame]:
        """
        Load OHLCV data from Parquet files.
        
        Args:
            ticker: Stock symbol
            timeframe: Data timeframe
            start_date: Filter start (optional)
            end_date: Filter end (optional)
            
        Returns:
            DataFrame with OHLCV data or None if not found
        """
        if not PARQUET_AVAILABLE:
            raise RuntimeError("pyarrow not installed")
        
        data_dir = self._get_raw_dir(ticker, timeframe)
        
        if not data_dir.exists():
            return None
        
        # Find all parquet files
        files = list(data_dir.glob("*.parquet"))
        
        if not files:
            return None
        
        # Load and concatenate all files
        dfs = []
        for f in files:
            try:
                df = pd.read_parquet(f)
                dfs.append(df)
            except Exception as e:
                logger.warning(f"Error reading {f}: {e}")
        
        if not dfs:
            return None
        
        result = pd.concat(dfs, ignore_index=True)
        result = result.drop_duplicates(subset=["ticker", "timeframe", "bar_ts"])
        result["bar_ts"] = pd.to_datetime(result["bar_ts"])
        
        # Apply date filters
        if start_date:
            result = result[result["bar_ts"] >= start_date]
        if end_date:
            result = result[result["bar_ts"] <= end_date]
        
        result = result.sort_values("bar_ts").reset_index(drop=True)
        
        return result if not result.empty else None
    
    def load_latest_bars(
        self,
        ticker: str,
        timeframe: str,
        n_bars: int = 100
    ) -> Optional[pd.DataFrame]:
        """
        Load the most recent N bars.
        
        Args:
            ticker: Stock symbol
            timeframe: Data timeframe
            n_bars: Number of bars to return
            
        Returns:
            DataFrame with most recent bars
        """
        df = self.load_ohlcv(ticker, timeframe)
        
        if df is None:
            return None
        
        return df.tail(n_bars).reset_index(drop=True)
    
    # =========================================================================
    # Feature Storage
    # =========================================================================
    
    def save_features(
        self,
        df: pd.DataFrame,
        ticker: str,
        timeframe: str
    ) -> str:
        """
        Save computed features to Parquet.
        
        Args:
            df: DataFrame with features
            ticker: Stock symbol
            timeframe: Data timeframe
            
        Returns:
            Path to saved file
        """
        if not PARQUET_AVAILABLE:
            raise RuntimeError("pyarrow not installed")
        
        if df.empty:
            raise ValueError("Cannot save empty features")
        
        # Create directory
        out_dir = self._get_features_dir(ticker, timeframe)
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine date range for filename
        if "bar_ts" in df.columns:
            start_date = df["bar_ts"].min()
            end_date = df["bar_ts"].max()
        else:
            start_date = datetime.now()
            end_date = datetime.now()
        
        filename = f"{ticker.upper()}_{timeframe}_features_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}.parquet"
        filepath = out_dir / filename
        
        df.to_parquet(filepath, engine="pyarrow", compression="snappy", index=False)
        
        logger.info(f"Saved features ({df.shape[1]} cols, {len(df)} rows) to {filepath}")
        return str(filepath)
    
    def load_features(
        self,
        ticker: str,
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """Load computed features."""
        if not PARQUET_AVAILABLE:
            raise RuntimeError("pyarrow not installed")
        
        features_dir = self._get_features_dir(ticker, timeframe)
        
        if not features_dir.exists():
            return None
        
        files = list(features_dir.glob("*.parquet"))
        
        if not files:
            return None
        
        # Load most recent file
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        try:
            return pd.read_parquet(files[0])
        except Exception as e:
            logger.error(f"Error loading features: {e}")
            return None
    
    # =========================================================================
    # Utility Methods
    # =========================================================================
    
    def list_tickers(self) -> List[str]:
        """List all tickers with stored data."""
        if not self.raw_path.exists():
            return []
        
        return [d.name for d in self.raw_path.iterdir() if d.is_dir()]
    
    def list_timeframes(self, ticker: str) -> List[str]:
        """List available timeframes for a ticker."""
        ticker_dir = self.raw_path / ticker.upper()
        
        if not ticker_dir.exists():
            return []
        
        return [d.name for d in ticker_dir.iterdir() if d.is_dir()]
    
    def get_data_range(self, ticker: str, timeframe: str) -> Optional[Dict[str, datetime]]:
        """Get the date range of stored data."""
        df = self.load_ohlcv(ticker, timeframe)
        
        if df is None or df.empty:
            return None
        
        return {
            "start": df["bar_ts"].min(),
            "end": df["bar_ts"].max(),
            "rows": len(df)
        }
    
    def delete_data(self, ticker: str, timeframe: Optional[str] = None) -> int:
        """
        Delete stored data.
        
        Args:
            ticker: Stock symbol
            timeframe: Specific timeframe (None = all timeframes)
            
        Returns:
            Number of files deleted
        """
        import shutil
        
        count = 0
        
        if timeframe:
            # Delete specific timeframe
            data_dir = self._get_raw_dir(ticker, timeframe)
            if data_dir.exists():
                count = len(list(data_dir.glob("*.parquet")))
                shutil.rmtree(data_dir)
                
            features_dir = self._get_features_dir(ticker, timeframe)
            if features_dir.exists():
                count += len(list(features_dir.glob("*.parquet")))
                shutil.rmtree(features_dir)
        else:
            # Delete all data for ticker
            ticker_raw = self.raw_path / ticker.upper()
            if ticker_raw.exists():
                for tf_dir in ticker_raw.iterdir():
                    count += len(list(tf_dir.glob("*.parquet")))
                shutil.rmtree(ticker_raw)
            
            ticker_features = self.features_path / ticker.upper()
            if ticker_features.exists():
                for tf_dir in ticker_features.iterdir():
                    count += len(list(tf_dir.glob("*.parquet")))
                shutil.rmtree(ticker_features)
        
        logger.info(f"Deleted {count} files for {ticker}/{timeframe or 'all'}")
        return count
    
    def _validate_schema(self, df: pd.DataFrame, ticker: str, timeframe: str) -> pd.DataFrame:
        """Ensure DataFrame has standard schema."""
        result = df.copy()
        
        # Ensure required columns exist
        if "ticker" not in result.columns:
            result["ticker"] = ticker.upper()
        if "timeframe" not in result.columns:
            result["timeframe"] = timeframe
        
        # Ensure bar_ts is datetime
        if "bar_ts" in result.columns:
            result["bar_ts"] = pd.to_datetime(result["bar_ts"])
        
        return result
    
    def health_check(self) -> Dict[str, Any]:
        """Check storage health."""
        if not PARQUET_AVAILABLE:
            return {"status": "unavailable", "error": "pyarrow not installed"}
        
        tickers = self.list_tickers()
        total_files = 0
        
        for ticker in tickers:
            for tf in self.list_timeframes(ticker):
                data_dir = self._get_raw_dir(ticker, tf)
                total_files += len(list(data_dir.glob("*.parquet")))
        
        return {
            "status": "healthy",
            "base_path": str(self.base_path),
            "tickers": len(tickers),
            "total_files": total_files
        }




