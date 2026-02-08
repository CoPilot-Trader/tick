"""
Technical Indicators Module for TICK Feature Agent.

This module contains indicator calculations extracted from the client's codebase
and standardized for use in both historical (batch) and inference (live) pipelines.

Extracted from:
- modules/swing_scalp_classifier.py (ATR, Volume Ratio, Session Phase)
- modules/level_exhaustion.py (RSI, MAs)
- signals/volume.py (Volume features)
- analysis/spx_move_discovery.py (VWAP, Feature engineering)

All indicators are designed to work with pandas DataFrames with columns:
[open, high, low, close, volume] and optionally a datetime index.
"""

from .volatility import (
    calc_atr,
    calc_atr_percentile,
    calc_bollinger_bands,
    calc_historical_volatility,
)

from .momentum import (
    calc_rsi,
    calc_macd,
    calc_stochastic,
    calc_cci,
    calc_williams_r,
)

from .trend import (
    calc_sma,
    calc_ema,
    calc_adx,
    calc_plus_di,
    calc_minus_di,
)

from .volume import (
    calc_volume_ratio,
    calc_obv,
    calc_vwap,
    calc_relative_volume,
    calc_volume_ma,
    calc_volume_acceleration,
    tag_reversal_with_accel,
)

from .time import (
    get_session_phase,
    get_session_minutes,
    is_market_hours,
)

from .price import (
    calc_returns,
    calc_price_position,
    calc_bar_features,
    calc_momentum_features,
    calc_compression_features,
    calc_daily_context,
)

__all__ = [
    # Volatility
    "calc_atr",
    "calc_atr_percentile",
    "calc_bollinger_bands",
    "calc_historical_volatility",
    # Momentum
    "calc_rsi",
    "calc_macd",
    "calc_stochastic",
    "calc_cci",
    "calc_williams_r",
    # Trend
    "calc_sma",
    "calc_ema",
    "calc_adx",
    "calc_plus_di",
    "calc_minus_di",
    # Volume
    "calc_volume_ratio",
    "calc_obv",
    "calc_vwap",
    "calc_relative_volume",
    "calc_volume_ma",
    "calc_volume_acceleration",
    "tag_reversal_with_accel",
    # Time
    "get_session_phase",
    "get_session_minutes",
    "is_market_hours",
    # Price
    "calc_returns",
    "calc_price_position",
    "calc_bar_features",
    "calc_momentum_features",
    "calc_compression_features",
    "calc_daily_context",
]
