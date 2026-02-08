"""
MOD09: Macro/VIX Context Module

Provides market-wide context about volatility regime, yields, and correlations.
This is one of the most impactful context modules for predictions.

Output columns (prefix: macro_):
- vix_level: Current VIX value
- vix_percentile: VIX percentile (rolling 252-day)
- vix_regime: Regime classification (low, medium, high, extreme)
- yield_2y: 2-year treasury yield
- yield_10y: 10-year treasury yield
- yield_spread_2s10s: Yield curve spread (10Y - 2Y)
- yield_curve_inverted: Boolean flag for inverted curve
- macro_regime: Overall market regime (risk_on, risk_off, transition)
- regime_confidence: Confidence in regime classification (0-1)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class MacroContext:
    """
    Macro/VIX context module.

    Uses FRED for treasury yields and yfinance for VIX.
    """

    # VIX regime thresholds
    VIX_REGIMES = {
        "low": (0, 15),
        "medium": (15, 20),
        "high": (20, 30),
        "extreme": (30, 100),
    }

    def __init__(self):
        self._fred_collector = None
        self._yf_collector = None
        self._vix_history: Optional[pd.DataFrame] = None

    def _get_fred_collector(self):
        """Lazy-load FRED collector."""
        if self._fred_collector is None:
            try:
                from ..collectors import FREDCollector
                self._fred_collector = FREDCollector()
                self._fred_collector.initialize()
            except Exception as e:
                logger.warning(f"Could not initialize FRED collector: {e}")
        return self._fred_collector

    def _get_yf_collector(self):
        """Lazy-load YFinance collector."""
        if self._yf_collector is None:
            try:
                from ..collectors import YFinanceCollector
                self._yf_collector = YFinanceCollector()
                self._yf_collector.initialize()
            except Exception as e:
                logger.warning(f"Could not initialize YFinance collector: {e}")
        return self._yf_collector

    def _get_vix_regime(self, vix: float) -> str:
        """Classify VIX into regime."""
        for regime, (low, high) in self.VIX_REGIMES.items():
            if low <= vix < high:
                return regime
        return "extreme"

    def _calculate_vix_percentile(self, current_vix: float, history: pd.Series) -> float:
        """Calculate VIX percentile relative to history."""
        if history is None or len(history) < 20:
            return 50.0  # Default to median if insufficient history

        percentile = (history < current_vix).sum() / len(history) * 100
        return percentile

    def _determine_macro_regime(
        self,
        vix_regime: str,
        yield_curve_inverted: bool,
        vix_percentile: float,
    ) -> tuple:
        """Determine overall macro regime and confidence."""
        # Risk-off signals
        risk_off_signals = 0
        if vix_regime in ["high", "extreme"]:
            risk_off_signals += 1
        if yield_curve_inverted:
            risk_off_signals += 1
        if vix_percentile > 70:
            risk_off_signals += 1

        # Determine regime
        if risk_off_signals >= 2:
            regime = "risk_off"
            confidence = min(0.9, 0.5 + risk_off_signals * 0.15)
        elif risk_off_signals == 1:
            regime = "transition"
            confidence = 0.5
        else:
            regime = "risk_on"
            confidence = min(0.9, 0.7 - vix_percentile / 200)

        return regime, confidence

    def get_context(
        self,
        date: Optional[str] = None,
        tickers: Optional[List[str]] = None,  # Not used for market-wide module
    ) -> pd.DataFrame:
        """
        Get macro context for a date.

        Returns DataFrame with columns:
        - timestamp, vix_level, vix_percentile, vix_regime,
          yield_2y, yield_10y, yield_spread_2s10s, yield_curve_inverted,
          macro_regime, regime_confidence
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        current_date = datetime.strptime(date, "%Y-%m-%d")

        # Get VIX data
        vix_level = None
        vix_percentile = 50.0
        vix_regime = "medium"

        yf = self._get_yf_collector()
        if yf:
            try:
                # Fetch VIX history for percentile calculation
                vix_result = yf.fetch_historical(
                    "^VIX",
                    current_date - timedelta(days=365),
                    current_date,
                    "1d"
                )
                if vix_result.success and vix_result.data is not None:
                    vix_df = vix_result.data
                    if not vix_df.empty and "close" in vix_df.columns:
                        vix_level = float(vix_df["close"].iloc[-1])
                        vix_percentile = self._calculate_vix_percentile(
                            vix_level, vix_df["close"]
                        )
                        vix_regime = self._get_vix_regime(vix_level)
            except Exception as e:
                logger.warning(f"Failed to fetch VIX: {e}")

        # Get treasury yields from FRED
        yield_2y = None
        yield_10y = None
        yield_spread = None
        yield_curve_inverted = False

        fred = self._get_fred_collector()
        if fred:
            try:
                yields = fred.fetch_treasury_yields(
                    current_date - timedelta(days=7),
                    current_date
                )
                if yields is not None and not yields.empty:
                    latest = yields.iloc[-1]
                    yield_2y = latest.get("yield_2y")
                    yield_10y = latest.get("yield_10y")
                    yield_spread = latest.get("yield_spread_2s10s")
                    yield_curve_inverted = bool(latest.get("yield_curve_inverted", False))
            except Exception as e:
                logger.warning(f"Failed to fetch yields: {e}")

        # Determine macro regime
        macro_regime, regime_confidence = self._determine_macro_regime(
            vix_regime, yield_curve_inverted, vix_percentile
        )

        row = {
            "timestamp": current_date,
            "vix_level": vix_level,
            "vix_percentile": vix_percentile,
            "vix_regime": vix_regime,
            "yield_2y": yield_2y,
            "yield_10y": yield_10y,
            "yield_spread_2s10s": yield_spread,
            "yield_curve_inverted": yield_curve_inverted,
            "macro_regime": macro_regime,
            "regime_confidence": regime_confidence,
        }

        return pd.DataFrame([row])

    def get_vix_regime_for_date(self, date: str) -> str:
        """Get just the VIX regime for a specific date."""
        ctx = self.get_context(date)
        if ctx is not None and not ctx.empty:
            return ctx.iloc[0]["vix_regime"]
        return "medium"  # Default
