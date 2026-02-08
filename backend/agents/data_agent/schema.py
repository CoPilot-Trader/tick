"""
============================================================================
TICK DATA PIPELINE - SCHEMA CONSTANTS & STANDARDIZATION
============================================================================
Adapted from client's Copilot Intelligence schema_constants.py

Purpose: Universal schema definitions, join keys, sector mappings
Design: Extensible registry pattern for adding new modules
Usage:
    from schema import SchemaRegistry, JOIN_KEYS, normalize_dataframe, ModuleType
============================================================================
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CORE JOIN KEYS - All modules MUST use these for merging
# ============================================================================

JOIN_KEYS = {
    "primary": ["ticker", "timeframe", "timestamp"],
    "ticker_only": ["ticker"],
    "market_wide": ["timeframe", "timestamp"],  # For _MARKET data
    "time_only": ["timestamp"],
}

# Special ticker for market-wide data (VIX, yields, sector rotation, etc)
MARKET_TICKER = "_MARKET"

# ============================================================================
# TIMEFRAME NORMALIZATION
# ============================================================================

TIMEFRAME_ALIASES = {
    # Input variants -> Canonical form
    "1m": "1min",
    "1min": "1min",
    "5m": "5min",
    "5min": "5min",
    "10m": "10min",
    "10min": "10min",
    "15m": "15min",
    "15min": "15min",
    "30m": "30min",
    "30min": "30min",
    "1h": "60min",
    "60m": "60min",
    "60min": "60min",
    "hourly": "60min",
    "d": "daily",
    "1d": "daily",
    "daily": "daily",
    "day": "daily",
    "w": "weekly",
    "1w": "weekly",
    "weekly": "weekly",
}

SUPPORTED_TIMEFRAMES = ["1min", "5min", "10min", "15min", "30min", "60min", "daily", "weekly"]


def normalize_timeframe(tf: str) -> str:
    """Convert any timeframe variant to canonical form."""
    tf_lower = str(tf).lower().strip()
    return TIMEFRAME_ALIASES.get(tf_lower, tf_lower)


# ============================================================================
# COLUMN NAME STANDARDIZATION
# ============================================================================

COLUMN_ALIASES = {
    # Ticker variations
    "symbol": "ticker",
    "sym": "ticker",
    "stock": "ticker",

    # Timestamp variations
    "date": "timestamp",
    "datetime": "timestamp",
    "time": "timestamp",
    "dt": "timestamp",
    "bar_time": "timestamp",
    "bar_ts": "timestamp",
    "trade_date": "timestamp",

    # Timeframe variations
    "tf": "timeframe",
    "interval": "timeframe",
    "resolution": "timeframe",

    # Price variations
    "close_price": "close",
    "adj_close": "close",
    "adjusted_close": "close",
    "open_price": "open",
    "high_price": "high",
    "low_price": "low",

    # Volume variations
    "vol": "volume",
    "trade_volume": "volume",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to standard names."""
    rename_map = {}
    for col in df.columns:
        col_lower = col.lower().strip()
        if col_lower in COLUMN_ALIASES:
            rename_map[col] = COLUMN_ALIASES[col_lower]

    if rename_map:
        df = df.rename(columns=rename_map)
        logger.debug(f"Renamed columns: {rename_map}")

    return df


# ============================================================================
# SECTOR MAPPINGS (GICS-based)
# ============================================================================

SECTOR_MAPPING = {
    # Technology
    "XLK": "technology", "AAPL": "technology", "MSFT": "technology",
    "NVDA": "technology", "GOOGL": "technology", "META": "technology",
    "AVGO": "technology", "ORCL": "technology", "CRM": "technology",
    "AMD": "technology", "ADBE": "technology", "INTC": "technology",

    # Financials
    "XLF": "financials", "JPM": "financials", "BAC": "financials",
    "WFC": "financials", "GS": "financials", "MS": "financials",
    "C": "financials", "BLK": "financials", "SCHW": "financials",

    # Healthcare
    "XLV": "healthcare", "UNH": "healthcare", "JNJ": "healthcare",
    "PFE": "healthcare", "ABBV": "healthcare", "MRK": "healthcare",
    "LLY": "healthcare", "TMO": "healthcare",

    # Consumer Discretionary
    "XLY": "consumer_discretionary", "AMZN": "consumer_discretionary",
    "TSLA": "consumer_discretionary", "HD": "consumer_discretionary",
    "MCD": "consumer_discretionary", "NKE": "consumer_discretionary",

    # Consumer Staples
    "XLP": "consumer_staples", "PG": "consumer_staples",
    "KO": "consumer_staples", "PEP": "consumer_staples",
    "WMT": "consumer_staples", "COST": "consumer_staples",

    # Energy
    "XLE": "energy", "XOM": "energy", "CVX": "energy",
    "COP": "energy", "SLB": "energy", "EOG": "energy",

    # Industrials
    "XLI": "industrials", "CAT": "industrials", "BA": "industrials",
    "HON": "industrials", "UPS": "industrials", "RTX": "industrials",

    # Materials
    "XLB": "materials", "LIN": "materials", "APD": "materials",
    "SHW": "materials", "FCX": "materials", "NEM": "materials",

    # Utilities
    "XLU": "utilities", "NEE": "utilities", "DUK": "utilities",
    "SO": "utilities", "D": "utilities",

    # Real Estate
    "XLRE": "real_estate", "AMT": "real_estate", "PLD": "real_estate",
    "CCI": "real_estate", "EQIX": "real_estate",

    # Communication Services
    "XLC": "communication_services", "GOOG": "communication_services",
    "DIS": "communication_services", "NFLX": "communication_services",
    "VZ": "communication_services", "T": "communication_services",
}

# Sector ETF to sector name mapping
SECTOR_ETFS = {
    "XLK": "technology",
    "XLF": "financials",
    "XLV": "healthcare",
    "XLY": "consumer_discretionary",
    "XLP": "consumer_staples",
    "XLE": "energy",
    "XLI": "industrials",
    "XLB": "materials",
    "XLU": "utilities",
    "XLRE": "real_estate",
    "XLC": "communication_services",
}

# Risk classification
RISK_ON_SECTORS = ["technology", "consumer_discretionary", "financials", "communication_services"]
RISK_OFF_SECTORS = ["utilities", "consumer_staples", "healthcare", "real_estate"]
CYCLICAL_SECTORS = ["energy", "materials", "industrials"]


def get_sector(ticker: str) -> Optional[str]:
    """Get sector for a ticker."""
    return SECTOR_MAPPING.get(ticker.upper())


def is_risk_on_sector(sector: str) -> bool:
    """Check if sector is risk-on."""
    return sector in RISK_ON_SECTORS


# ============================================================================
# MODULE REGISTRY - Extensible pattern for all modules
# ============================================================================

class ModuleType(Enum):
    """Classification of module output types."""
    MARKET_WIDE = "market_wide"      # VIX, yields, macro - applies to all tickers
    TICKER_SPECIFIC = "ticker"        # Sentiment, earnings - per ticker
    SECTOR_LEVEL = "sector"           # Rotation, flows - per sector
    EVENT_BASED = "event"             # Calendar events, discrete occurrences


@dataclass
class ModuleSchema:
    """Schema definition for a context module."""

    module_id: str                      # e.g., "mod09"
    module_name: str                    # e.g., "correlation"
    module_type: ModuleType
    description: str

    # Output columns this module produces
    output_columns: List[str]

    # Required columns (must be present)
    required_columns: List[str] = field(default_factory=lambda: ["timestamp"])

    # Join strategy
    join_keys: List[str] = field(default_factory=lambda: ["ticker", "timeframe", "timestamp"])

    # Prefixes for column disambiguation when merging
    column_prefix: str = ""

    # Data freshness requirements
    max_staleness_hours: int = 24       # How old data can be before warning
    update_frequency: str = "daily"      # daily, intraday, realtime

    # Dependencies on other modules
    depends_on: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.column_prefix:
            self.column_prefix = f"{self.module_id}_"


class SchemaRegistry:
    """
    Central registry for all module schemas.
    Extensible pattern - add new modules by registering them.
    """

    _modules: Dict[str, ModuleSchema] = {}

    @classmethod
    def register(cls, schema: ModuleSchema) -> None:
        """Register a module schema."""
        cls._modules[schema.module_id] = schema
        logger.info(f"Registered module: {schema.module_id} ({schema.module_name})")

    @classmethod
    def get(cls, module_id: str) -> Optional[ModuleSchema]:
        """Get a module schema by ID."""
        return cls._modules.get(module_id)

    @classmethod
    def get_all(cls) -> Dict[str, ModuleSchema]:
        """Get all registered modules."""
        return cls._modules.copy()

    @classmethod
    def get_by_type(cls, module_type: ModuleType) -> List[ModuleSchema]:
        """Get all modules of a specific type."""
        return [m for m in cls._modules.values() if m.module_type == module_type]

    @classmethod
    def get_market_wide_modules(cls) -> List[ModuleSchema]:
        """Get modules that produce market-wide data."""
        return cls.get_by_type(ModuleType.MARKET_WIDE)

    @classmethod
    def get_ticker_modules(cls) -> List[ModuleSchema]:
        """Get modules that produce ticker-specific data."""
        return cls.get_by_type(ModuleType.TICKER_SPECIFIC)

    @classmethod
    def get_load_order(cls) -> List[str]:
        """Get modules in dependency order for loading."""
        loaded = set()
        order = []

        def load(mod_id: str):
            if mod_id in loaded:
                return
            schema = cls._modules.get(mod_id)
            if schema:
                for dep in schema.depends_on:
                    load(dep)
                loaded.add(mod_id)
                order.append(mod_id)

        for mod_id in cls._modules:
            load(mod_id)

        return order


# ============================================================================
# REGISTER CONTEXT MODULES
# ============================================================================

# Module 06: Event Calendar (FOMC, CPI, Jobs, GDP)
SchemaRegistry.register(ModuleSchema(
    module_id="mod06",
    module_name="events",
    module_type=ModuleType.EVENT_BASED,
    description="Economic calendar, FOMC/CPI proximity, event timing",
    output_columns=[
        "days_to_fomc", "days_to_cpi", "days_to_jobs", "days_to_gdp",
        "event_proximity_score", "is_fomc_week", "is_cpi_week",
        "next_event_type", "next_event_date",
    ],
    required_columns=["timestamp"],
    join_keys=["timestamp"],
    column_prefix="evt_",
    update_frequency="daily",
))

# Module 09: Correlation & Macro (VIX, yields, regime)
SchemaRegistry.register(ModuleSchema(
    module_id="mod09",
    module_name="macro",
    module_type=ModuleType.MARKET_WIDE,
    description="VIX, yields, cross-asset correlations, macro regime",
    output_columns=[
        "vix_level", "vix_percentile", "vix_term_structure",
        "yield_2y", "yield_10y", "yield_spread_2s10s", "yield_curve_inverted",
        "spx_bond_corr_20d", "spx_vix_corr_20d",
        "macro_regime", "regime_confidence",
    ],
    required_columns=["timestamp"],
    join_keys=["timestamp"],
    column_prefix="macro_",
    update_frequency="daily",
    max_staleness_hours=24,
))

# Module 10: Sentiment (news, social)
SchemaRegistry.register(ModuleSchema(
    module_id="mod10",
    module_name="sentiment",
    module_type=ModuleType.TICKER_SPECIFIC,
    description="Ticker-level news sentiment, social signals",
    output_columns=[
        "news_sentiment_score", "news_volume_24h", "sentiment_momentum",
        "social_buzz_score", "analyst_sentiment",
        "sentiment_divergence",
    ],
    required_columns=["ticker", "timestamp"],
    join_keys=["ticker", "timestamp"],
    column_prefix="sent_",
    update_frequency="intraday",
    max_staleness_hours=4,
))

# Module 11: Sector Rotation
SchemaRegistry.register(ModuleSchema(
    module_id="mod11",
    module_name="rotation",
    module_type=ModuleType.SECTOR_LEVEL,
    description="Sector rotation, risk-on/off flows",
    output_columns=[
        "sector", "sector_momentum_5d", "sector_momentum_20d",
        "sector_relative_strength", "sector_flow_score",
        "rotation_phase", "risk_appetite_score",
        "defensive_rotation", "cyclical_rotation", "sector_rank",
    ],
    required_columns=["timestamp"],
    join_keys=["timestamp"],
    column_prefix="rot_",
    update_frequency="daily",
    depends_on=["mod09"],
))

# Module 13: Earnings
SchemaRegistry.register(ModuleSchema(
    module_id="mod13",
    module_name="earnings",
    module_type=ModuleType.TICKER_SPECIFIC,
    description="Earnings dates, surprise history, guidance",
    output_columns=[
        "days_to_earnings", "earnings_date", "earnings_time",
        "last_surprise_pct", "surprise_history_avg", "beat_rate_4q",
        "guidance_sentiment", "is_earnings_week",
        "implied_move", "historical_earnings_vol",
    ],
    required_columns=["ticker", "timestamp"],
    join_keys=["ticker", "timestamp"],
    column_prefix="earn_",
    update_frequency="daily",
    max_staleness_hours=24,
))

# Module 14: Economic Data
SchemaRegistry.register(ModuleSchema(
    module_id="mod14",
    module_name="economic",
    module_type=ModuleType.MARKET_WIDE,
    description="CPI, gas prices, unemployment, consumer sentiment",
    output_columns=[
        "cpi_yoy", "cpi_mom", "cpi_trend", "core_cpi_yoy",
        "gas_price", "gas_price_change_mom",
        "unemployment_rate", "unemployment_trend",
        "consumer_sentiment", "sentiment_change_mom",
        "economic_surprise_index", "fed_funds_rate",
    ],
    required_columns=["timestamp"],
    join_keys=["timestamp"],
    column_prefix="econ_",
    update_frequency="daily",
    max_staleness_hours=24,
))


# ============================================================================
# DATAFRAME NORMALIZATION UTILITIES
# ============================================================================

def normalize_dataframe(
    df: pd.DataFrame,
    module_schema: Optional[ModuleSchema] = None,
    add_market_ticker: bool = False,
) -> pd.DataFrame:
    """
    Normalize a dataframe to standard schema.
    """
    df = df.copy()

    # Step 1: Normalize column names
    df = normalize_columns(df)

    # Step 2: Normalize timeframe if present
    if "timeframe" in df.columns:
        df["timeframe"] = df["timeframe"].apply(normalize_timeframe)

    # Step 3: Ensure timestamp is datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Step 4: Add market ticker for market-wide data
    if add_market_ticker and "ticker" not in df.columns:
        df["ticker"] = MARKET_TICKER

    # Step 5: Uppercase tickers
    if "ticker" in df.columns:
        df["ticker"] = df["ticker"].str.upper()

    # Step 6: Validate against schema if provided
    if module_schema:
        missing_required = set(module_schema.required_columns) - set(df.columns)
        if missing_required:
            logger.warning(f"Missing required columns for {module_schema.module_id}: {missing_required}")

    return df


def add_sector_column(df: pd.DataFrame) -> pd.DataFrame:
    """Add sector column based on ticker."""
    if "ticker" in df.columns:
        df["sector"] = df["ticker"].map(lambda t: get_sector(t))
    return df


def validate_join_keys(df: pd.DataFrame, keys: List[str]) -> bool:
    """Validate that join keys are present and not null."""
    for key in keys:
        if key not in df.columns:
            logger.error(f"Missing join key: {key}")
            return False
        if df[key].isna().any():
            null_count = df[key].isna().sum()
            logger.warning(f"Join key '{key}' has {null_count} null values")
    return True


# ============================================================================
# MERGE UTILITIES
# ============================================================================

def merge_market_wide_context(
    signals_df: pd.DataFrame,
    context_df: pd.DataFrame,
    context_prefix: str = "",
) -> pd.DataFrame:
    """
    Merge market-wide context (VIX, yields, etc) to signals.
    Uses timestamp-based asof merge.
    """
    if "timestamp" not in signals_df.columns or "timestamp" not in context_df.columns:
        raise ValueError("Both dataframes must have 'timestamp' column")

    signals_df = signals_df.sort_values("timestamp")
    context_df = context_df.sort_values("timestamp")

    # Prefix context columns to avoid collision
    if context_prefix:
        context_cols = [c for c in context_df.columns if c != "timestamp"]
        rename_map = {c: f"{context_prefix}{c}" for c in context_cols}
        context_df = context_df.rename(columns=rename_map)

    # Asof merge - get most recent context for each signal
    merged = pd.merge_asof(
        signals_df,
        context_df,
        on="timestamp",
        direction="backward",
    )

    return merged


def merge_ticker_context(
    signals_df: pd.DataFrame,
    context_df: pd.DataFrame,
    context_prefix: str = "",
) -> pd.DataFrame:
    """
    Merge ticker-specific context (sentiment, earnings) to signals.
    Uses ticker + timestamp based asof merge.
    """
    required = ["ticker", "timestamp"]
    for col in required:
        if col not in signals_df.columns or col not in context_df.columns:
            raise ValueError(f"Both dataframes must have '{col}' column")

    signals_df = signals_df.sort_values(["ticker", "timestamp"])
    context_df = context_df.sort_values(["ticker", "timestamp"])

    # Prefix context columns
    if context_prefix:
        context_cols = [c for c in context_df.columns if c not in required]
        rename_map = {c: f"{context_prefix}{c}" for c in context_cols}
        context_df = context_df.rename(columns=rename_map)

    # Merge by ticker, then asof on timestamp within each ticker
    merged_dfs = []
    for ticker in signals_df["ticker"].unique():
        sig_ticker = signals_df[signals_df["ticker"] == ticker]
        ctx_ticker = context_df[context_df["ticker"] == ticker]

        if len(ctx_ticker) > 0:
            merged_ticker = pd.merge_asof(
                sig_ticker,
                ctx_ticker.drop(columns=["ticker"]),
                on="timestamp",
                direction="backward",
            )
        else:
            merged_ticker = sig_ticker

        merged_dfs.append(merged_ticker)

    return pd.concat(merged_dfs, ignore_index=True) if merged_dfs else signals_df


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Constants
    "JOIN_KEYS",
    "MARKET_TICKER",
    "TIMEFRAME_ALIASES",
    "SUPPORTED_TIMEFRAMES",
    "COLUMN_ALIASES",
    "SECTOR_MAPPING",
    "SECTOR_ETFS",
    "RISK_ON_SECTORS",
    "RISK_OFF_SECTORS",
    "CYCLICAL_SECTORS",

    # Enums and Classes
    "ModuleType",
    "ModuleSchema",
    "SchemaRegistry",

    # Functions
    "normalize_timeframe",
    "normalize_columns",
    "normalize_dataframe",
    "get_sector",
    "is_risk_on_sector",
    "add_sector_column",
    "validate_join_keys",
    "merge_market_wide_context",
    "merge_ticker_context",
]
