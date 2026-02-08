"""
TimescaleDB database connection and operations.
"""

import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import contextmanager
import logging

try:
    import psycopg2
    from psycopg2.extras import execute_values, RealDictCursor
    from psycopg2.pool import ThreadedConnectionPool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    """
    TimescaleDB database wrapper for TICK.
    Handles OHLCV data storage and retrieval.
    """
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self._pool: Optional[Any] = None
        self._connected = False
        
    def connect(self) -> bool:
        """Establish database connection pool."""
        if not PSYCOPG2_AVAILABLE:
            logger.warning("psycopg2 not installed. Database operations will be simulated.")
            return False
            
        try:
            self._pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=settings.db_pool_size + settings.db_max_overflow,
                dsn=self.database_url
            )
            self._connected = True
            logger.info("Database connection pool established")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            self._connected = False
            return False
    
    def disconnect(self):
        """Close all database connections."""
        if self._pool:
            self._pool.closeall()
            self._connected = False
            logger.info("Database connections closed")
    
    @contextmanager
    def get_connection(self):
        """Get a connection from the pool."""
        if not self._connected or not self._pool:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)
    
    def execute(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results as list of dicts."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if cursor.description:
                    return [dict(row) for row in cursor.fetchall()]
                return []
    
    def execute_many(self, query: str, data: List[tuple]):
        """Execute a query with multiple parameter sets."""
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                execute_values(cursor, query, data)
    
    # =========================================================================
    # OHLCV Operations
    # =========================================================================
    
    def insert_ohlcv(self, df: pd.DataFrame, table: str = "ohlcv_live"):
        """
        Insert OHLCV data into TimescaleDB.
        
        Args:
            df: DataFrame with columns [ticker, timeframe, bar_ts, open, high, low, close, volume]
            table: Target table name
        """
        if df.empty:
            return
        
        required_cols = ["ticker", "timeframe", "bar_ts", "open", "high", "low", "close", "volume"]
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"DataFrame must have columns: {required_cols}")
        
        # Prepare data for insertion
        data = [
            (
                row["ticker"],
                row["timeframe"],
                row["bar_ts"],
                float(row["open"]),
                float(row["high"]),
                float(row["low"]),
                float(row["close"]),
                int(row["volume"])
            )
            for _, row in df.iterrows()
        ]
        
        query = f"""
            INSERT INTO {table} (ticker, timeframe, bar_ts, open, high, low, close, volume)
            VALUES %s
            ON CONFLICT (ticker, timeframe, bar_ts) DO UPDATE SET
                open = EXCLUDED.open,
                high = EXCLUDED.high,
                low = EXCLUDED.low,
                close = EXCLUDED.close,
                volume = EXCLUDED.volume
        """
        
        self.execute_many(query, data)
        logger.debug(f"Inserted {len(data)} rows into {table}")
    
    def get_ohlcv(
        self,
        ticker: str,
        timeframe: str,
        start_ts: datetime = None,
        end_ts: datetime = None,
        limit: int = None,
        table: str = "ohlcv_live"
    ) -> pd.DataFrame:
        """
        Retrieve OHLCV data from TimescaleDB.
        
        Args:
            ticker: Stock symbol
            timeframe: Data timeframe (e.g., "5m", "1h", "1d")
            start_ts: Start timestamp (optional)
            end_ts: End timestamp (optional)
            limit: Maximum rows to return (optional)
            table: Source table name
            
        Returns:
            DataFrame with OHLCV data
        """
        conditions = ["ticker = %s", "timeframe = %s"]
        params = [ticker, timeframe]
        
        if start_ts:
            conditions.append("bar_ts >= %s")
            params.append(start_ts)
        
        if end_ts:
            conditions.append("bar_ts <= %s")
            params.append(end_ts)
        
        query = f"""
            SELECT ticker, timeframe, bar_ts, open, high, low, close, volume
            FROM {table}
            WHERE {" AND ".join(conditions)}
            ORDER BY bar_ts ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        results = self.execute(query, tuple(params))
        
        if not results:
            return pd.DataFrame(columns=["ticker", "timeframe", "bar_ts", "open", "high", "low", "close", "volume"])
        
        df = pd.DataFrame(results)
        df["bar_ts"] = pd.to_datetime(df["bar_ts"])
        return df
    
    def get_latest_bar(self, ticker: str, timeframe: str, table: str = "ohlcv_live") -> Optional[Dict]:
        """Get the most recent bar for a ticker."""
        query = f"""
            SELECT ticker, timeframe, bar_ts, open, high, low, close, volume
            FROM {table}
            WHERE ticker = %s AND timeframe = %s
            ORDER BY bar_ts DESC
            LIMIT 1
        """
        results = self.execute(query, (ticker, timeframe))
        return results[0] if results else None
    
    # =========================================================================
    # Features Operations
    # =========================================================================
    
    def insert_features(self, ticker: str, timeframe: str, bar_ts: datetime, features: Dict[str, float], table: str = "features_live"):
        """Insert calculated features."""
        import json
        
        query = f"""
            INSERT INTO {table} (ticker, timeframe, bar_ts, features)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (ticker, timeframe, bar_ts) DO UPDATE SET
                features = EXCLUDED.features
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (ticker, timeframe, bar_ts, json.dumps(features)))
    
    def get_features(self, ticker: str, timeframe: str, bar_ts: datetime = None, table: str = "features_live") -> Optional[Dict]:
        """Get features for a specific bar or the latest."""
        import json
        
        if bar_ts:
            query = f"""
                SELECT features FROM {table}
                WHERE ticker = %s AND timeframe = %s AND bar_ts = %s
            """
            params = (ticker, timeframe, bar_ts)
        else:
            query = f"""
                SELECT features FROM {table}
                WHERE ticker = %s AND timeframe = %s
                ORDER BY bar_ts DESC LIMIT 1
            """
            params = (ticker, timeframe)
        
        results = self.execute(query, params)
        if results and results[0].get("features"):
            return json.loads(results[0]["features"]) if isinstance(results[0]["features"], str) else results[0]["features"]
        return None
    
    # =========================================================================
    # Health Check
    # =========================================================================
    
    def health_check(self) -> Dict[str, Any]:
        """Check database health."""
        if not PSYCOPG2_AVAILABLE:
            return {"status": "unavailable", "reason": "psycopg2 not installed"}
        
        if not self._connected:
            return {"status": "disconnected"}
        
        try:
            result = self.execute("SELECT 1 as health")
            return {"status": "healthy", "connected": True}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}


# Global database instance
_database: Optional[Database] = None


def get_database() -> Database:
    """Get the global database instance."""
    global _database
    if _database is None:
        _database = Database()
    return _database
