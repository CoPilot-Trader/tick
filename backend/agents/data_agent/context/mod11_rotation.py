"""
MOD11: Sector Rotation Context Module

Provides sector-level context for understanding market rotation and flows.

Output columns (prefix: rot_):
- sector: Sector name (technology, financials, etc.)
- sector_momentum_5d: 5-day sector momentum
- sector_momentum_20d: 20-day sector momentum
- sector_relative_strength: Sector performance vs SPY
- sector_flow_score: Estimated sector flow (based on ETF volume)
- rotation_phase: Economic cycle phase (early_cycle, mid_cycle, late_cycle, recession)
- risk_appetite_score: Market risk appetite (0-1)
- defensive_rotation: Signal for defensive sector rotation
- cyclical_rotation: Signal for cyclical sector rotation
- sector_rank: Sector ranking (1 = best performing)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np

from ..schema import SECTOR_ETFS, RISK_ON_SECTORS, RISK_OFF_SECTORS, CYCLICAL_SECTORS

logger = logging.getLogger(__name__)


class RotationContext:
    """
    Sector rotation context module.

    Uses yfinance for sector ETF data to calculate rotation signals.
    """

    def __init__(self):
        self._yf_collector = None
        self._sector_data_cache: Optional[pd.DataFrame] = None
        self._cache_date: Optional[str] = None

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

    def _fetch_sector_etf_data(
        self,
        end_date: datetime,
        lookback_days: int = 30,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch price data for all sector ETFs."""
        yf = self._get_yf_collector()
        if not yf:
            return {}

        start_date = end_date - timedelta(days=lookback_days)
        sector_data = {}

        for etf, sector in SECTOR_ETFS.items():
            try:
                result = yf.fetch_historical(etf, start_date, end_date, "1d")
                if result.success and result.data is not None and not result.data.empty:
                    sector_data[sector] = result.data
            except Exception as e:
                logger.debug(f"Could not fetch {etf}: {e}")

        # Also fetch SPY for relative strength
        try:
            spy_result = yf.fetch_historical("SPY", start_date, end_date, "1d")
            if spy_result.success and spy_result.data is not None:
                sector_data["_benchmark"] = spy_result.data
        except Exception as e:
            logger.debug(f"Could not fetch SPY: {e}")

        return sector_data

    def _calculate_momentum(self, df: pd.DataFrame, days: int) -> float:
        """Calculate momentum (return) over N days."""
        if df is None or df.empty or len(df) < days:
            return 0.0

        if "close" in df.columns:
            start_price = df["close"].iloc[-days] if len(df) >= days else df["close"].iloc[0]
            end_price = df["close"].iloc[-1]
            return (end_price - start_price) / start_price * 100

        return 0.0

    def _calculate_relative_strength(
        self,
        sector_df: pd.DataFrame,
        benchmark_df: pd.DataFrame,
        days: int = 20,
    ) -> float:
        """Calculate sector relative strength vs benchmark."""
        sector_momentum = self._calculate_momentum(sector_df, days)
        benchmark_momentum = self._calculate_momentum(benchmark_df, days)
        return sector_momentum - benchmark_momentum

    def _determine_rotation_phase(
        self,
        risk_on_momentum: float,
        risk_off_momentum: float,
        cyclical_momentum: float,
    ) -> str:
        """
        Determine economic cycle phase based on sector performance.

        - early_cycle: Cyclicals and financials lead
        - mid_cycle: Technology and industrials lead
        - late_cycle: Energy and materials lead
        - recession: Utilities and consumer staples lead
        """
        if risk_off_momentum > risk_on_momentum and risk_off_momentum > 0:
            return "recession"
        elif cyclical_momentum > risk_on_momentum:
            return "late_cycle"
        elif risk_on_momentum > 2:
            return "early_cycle"
        else:
            return "mid_cycle"

    def get_context(
        self,
        date: Optional[str] = None,
        tickers: Optional[List[str]] = None,  # Not directly used
    ) -> pd.DataFrame:
        """
        Get sector rotation context.

        Returns DataFrame with one row per sector containing:
        - sector, timestamp, sector_momentum_5d, sector_momentum_20d,
          sector_relative_strength, rotation_phase, risk_appetite_score,
          defensive_rotation, cyclical_rotation, sector_rank
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        current_date = datetime.strptime(date, "%Y-%m-%d")

        # Fetch sector ETF data
        sector_data = self._fetch_sector_etf_data(current_date, lookback_days=30)

        if not sector_data:
            logger.warning("No sector data available")
            return pd.DataFrame()

        benchmark = sector_data.get("_benchmark")
        rows = []

        # Calculate metrics for each sector
        sector_metrics = {}
        for sector in SECTOR_ETFS.values():
            if sector not in sector_data:
                continue

            df = sector_data[sector]
            momentum_5d = self._calculate_momentum(df, 5)
            momentum_20d = self._calculate_momentum(df, 20)
            rel_strength = self._calculate_relative_strength(df, benchmark) if benchmark is not None else momentum_20d

            sector_metrics[sector] = {
                "momentum_5d": momentum_5d,
                "momentum_20d": momentum_20d,
                "relative_strength": rel_strength,
            }

        # Calculate aggregate metrics for rotation phase
        risk_on_momentum = np.mean([
            sector_metrics.get(s, {}).get("momentum_20d", 0)
            for s in RISK_ON_SECTORS if s in sector_metrics
        ])

        risk_off_momentum = np.mean([
            sector_metrics.get(s, {}).get("momentum_20d", 0)
            for s in RISK_OFF_SECTORS if s in sector_metrics
        ])

        cyclical_momentum = np.mean([
            sector_metrics.get(s, {}).get("momentum_20d", 0)
            for s in CYCLICAL_SECTORS if s in sector_metrics
        ])

        rotation_phase = self._determine_rotation_phase(
            risk_on_momentum, risk_off_momentum, cyclical_momentum
        )

        # Calculate risk appetite score (0-1)
        if risk_on_momentum + risk_off_momentum != 0:
            risk_appetite = (risk_on_momentum - risk_off_momentum + 10) / 20
            risk_appetite = np.clip(risk_appetite, 0, 1)
        else:
            risk_appetite = 0.5

        # Rank sectors by relative strength
        sorted_sectors = sorted(
            sector_metrics.items(),
            key=lambda x: x[1]["relative_strength"],
            reverse=True
        )
        sector_ranks = {s: i + 1 for i, (s, _) in enumerate(sorted_sectors)}

        # Build output rows
        for sector, metrics in sector_metrics.items():
            row = {
                "timestamp": current_date,
                "sector": sector,
                "sector_momentum_5d": metrics["momentum_5d"],
                "sector_momentum_20d": metrics["momentum_20d"],
                "sector_relative_strength": metrics["relative_strength"],
                "sector_flow_score": 0.0,  # Would need volume data
                "rotation_phase": rotation_phase,
                "risk_appetite_score": risk_appetite,
                "defensive_rotation": risk_off_momentum > risk_on_momentum,
                "cyclical_rotation": cyclical_momentum > risk_on_momentum,
                "sector_rank": sector_ranks.get(sector, 0),
            }
            rows.append(row)

        return pd.DataFrame(rows)

    def get_sector_ranking(self, date: Optional[str] = None) -> List[str]:
        """Get sectors ranked by relative strength."""
        ctx = self.get_context(date)
        if ctx is not None and not ctx.empty:
            ctx = ctx.sort_values("sector_rank")
            return ctx["sector"].tolist()
        return []

    def get_rotation_phase(self, date: Optional[str] = None) -> str:
        """Get current rotation phase."""
        ctx = self.get_context(date)
        if ctx is not None and not ctx.empty:
            return ctx.iloc[0]["rotation_phase"]
        return "mid_cycle"
