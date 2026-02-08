"""
Backtest Simulator for Backtesting Agent.

Main simulation engine that orchestrates backtesting.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import pandas as pd

from .position_manager import PositionManager, Trade
from .trade_executor import TradeExecutor

logger = logging.getLogger(__name__)


class BacktestSimulator:
    """
    Main backtesting simulation engine.

    Features:
    - Historical simulation with OHLCV data
    - Signal-based trading
    - Position management
    - Equity curve tracking
    - Walk-forward support
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Backtest Simulator.

        Args:
            config: Configuration options passed to components
        """
        self.config = config or {}

        # Initialize components
        self.position_manager = PositionManager(config)
        self.trade_executor = TradeExecutor(self.position_manager, config)

        # Results storage
        self.daily_returns: List[Dict[str, Any]] = []
        self.signals_processed: int = 0

        logger.info("BacktestSimulator initialized")

    def reset(self) -> None:
        """Reset simulator state for new backtest."""
        self.position_manager.reset()
        self.daily_returns = []
        self.signals_processed = 0

    def run(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        signals: List[Dict[str, Any]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run backtest simulation.

        Args:
            symbol: Stock symbol
            price_data: DataFrame with OHLCV data (indexed by date)
            signals: List of daily signals with dates
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with backtest results
        """
        self.reset()

        # Convert signals to dict keyed by date
        signal_dict = {}
        for sig in signals:
            sig_date = sig.get("date")
            if isinstance(sig_date, str):
                sig_date = datetime.fromisoformat(sig_date.replace("Z", "+00:00"))
            if sig_date:
                # Normalize to date only (no time component)
                if hasattr(sig_date, 'date'):
                    sig_date = sig_date.date()
                signal_dict[sig_date] = sig

        # Ensure price_data has a proper index
        if 'timestamp' in price_data.columns:
            price_data = price_data.set_index('timestamp')

        # Filter by date range (handle both tz-aware and tz-naive timestamps)
        if start_date:
            start_ts = pd.Timestamp(start_date)
            if price_data.index.tz is not None and start_ts.tz is None:
                start_ts = start_ts.tz_localize('UTC')
            price_data = price_data[price_data.index >= start_ts]
        if end_date:
            end_ts = pd.Timestamp(end_date)
            if price_data.index.tz is not None and end_ts.tz is None:
                end_ts = end_ts.tz_localize('UTC')
            price_data = price_data[price_data.index <= end_ts]

        if price_data.empty:
            return {
                "status": "error",
                "message": "No data in date range",
                "symbol": symbol
            }

        # Track starting values
        start_equity = self.position_manager.initial_capital
        prev_equity = start_equity

        # Simulate day by day
        for idx, (date, row) in enumerate(price_data.iterrows()):
            # Normalize date
            current_date = pd.Timestamp(date)
            date_key = current_date.date() if hasattr(current_date, 'date') else current_date

            # Get OHLCV
            ohlcv = {
                "open": row.get("open", row.get("Open", 0)),
                "high": row.get("high", row.get("High", 0)),
                "low": row.get("low", row.get("Low", 0)),
                "close": row.get("close", row.get("Close", 0)),
                "volume": row.get("volume", row.get("Volume", 0))
            }

            # Get signal for this date (or default to HOLD)
            signal = signal_dict.get(date_key, {
                "signal": "HOLD",
                "confidence": 0.0,
                "fused_score": 0.0
            })

            if signal.get("signal") != "HOLD":
                self.signals_processed += 1

            # Process trades
            self.trade_executor.process_day(
                symbol=symbol,
                signal=signal,
                ohlcv=ohlcv,
                date=current_date.to_pydatetime() if hasattr(current_date, 'to_pydatetime') else current_date
            )

            # Record equity
            current_prices = {symbol: ohlcv["close"]}
            self.position_manager.record_equity(
                current_date.to_pydatetime() if hasattr(current_date, 'to_pydatetime') else current_date,
                current_prices
            )

            # Calculate daily return
            current_equity = self.position_manager.get_equity(current_prices)
            daily_return = (current_equity - prev_equity) / prev_equity if prev_equity > 0 else 0

            self.daily_returns.append({
                "date": current_date,
                "equity": current_equity,
                "daily_return": daily_return,
                "signal": signal.get("signal", "HOLD")
            })

            prev_equity = current_equity

        # Close remaining positions at end
        if price_data.empty:
            final_prices = {}
        else:
            last_row = price_data.iloc[-1]
            final_prices = {symbol: last_row.get("close", last_row.get("Close", 0))}

        last_date = price_data.index[-1] if not price_data.empty else datetime.now()
        self.trade_executor.close_all_positions(
            final_prices,
            last_date.to_pydatetime() if hasattr(last_date, 'to_pydatetime') else last_date
        )

        # Calculate final equity
        final_equity = self.position_manager.get_equity(final_prices)

        # Build results
        return {
            "status": "success",
            "symbol": symbol,
            "start_date": price_data.index[0].isoformat() if not price_data.empty else None,
            "end_date": price_data.index[-1].isoformat() if not price_data.empty else None,
            "initial_capital": start_equity,
            "final_equity": final_equity,
            "total_return": ((final_equity - start_equity) / start_equity) * 100,
            "total_trades": len(self.position_manager.trades),
            "signals_processed": self.signals_processed,
            "trades": [self._trade_to_dict(t) for t in self.position_manager.trades],
            "equity_curve": self.position_manager.equity_curve,
            "daily_returns": self.daily_returns
        }

    def run_walk_forward(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        signal_generator,
        train_days: int = 252,
        test_days: int = 63,
        step_days: int = 21
    ) -> Dict[str, Any]:
        """
        Run walk-forward backtest.

        Walk-forward testing trains on historical data, then tests on
        out-of-sample data, and repeats by stepping forward.

        Args:
            symbol: Stock symbol
            price_data: Full historical DataFrame
            signal_generator: Callable that takes (symbol, train_data) and returns signals
            train_days: Training period in days (default: 252 = 1 year)
            test_days: Testing period in days (default: 63 = 1 quarter)
            step_days: Days to step forward each iteration (default: 21 = 1 month)

        Returns:
            Dictionary with walk-forward results
        """
        if 'timestamp' in price_data.columns:
            price_data = price_data.set_index('timestamp')

        results = []
        all_trades = []
        all_equity = []

        total_days = len(price_data)
        current_start = 0

        iteration = 0
        while current_start + train_days + test_days <= total_days:
            iteration += 1

            # Split data
            train_end = current_start + train_days
            test_end = train_end + test_days

            train_data = price_data.iloc[current_start:train_end]
            test_data = price_data.iloc[train_end:test_end]

            # Generate signals using training data
            try:
                signals = signal_generator(symbol, train_data)
            except Exception as e:
                logger.error(f"Signal generation failed in iteration {iteration}: {e}")
                signals = []

            # Run backtest on test data
            self.reset()
            result = self.run(
                symbol=symbol,
                price_data=test_data,
                signals=signals
            )

            if result.get("status") == "success":
                result["iteration"] = iteration
                result["train_start"] = train_data.index[0].isoformat()
                result["train_end"] = train_data.index[-1].isoformat()
                results.append(result)
                all_trades.extend(result.get("trades", []))
                all_equity.extend(result.get("equity_curve", []))

            # Step forward
            current_start += step_days

        # Aggregate results
        if not results:
            return {
                "status": "error",
                "message": "No valid walk-forward iterations completed",
                "symbol": symbol
            }

        total_pnl = sum(r.get("total_return", 0) for r in results)
        avg_return = total_pnl / len(results)

        return {
            "status": "success",
            "symbol": symbol,
            "iterations": len(results),
            "train_days": train_days,
            "test_days": test_days,
            "step_days": step_days,
            "total_trades": len(all_trades),
            "average_return_per_period": avg_return,
            "cumulative_return": total_pnl,
            "iteration_results": results,
            "all_trades": all_trades,
            "equity_curve": all_equity
        }

    def _trade_to_dict(self, trade: Trade) -> Dict[str, Any]:
        """Convert Trade object to dictionary."""
        return {
            "symbol": trade.symbol,
            "side": trade.side,
            "entry_price": trade.entry_price,
            "exit_price": trade.exit_price,
            "quantity": trade.quantity,
            "entry_date": trade.entry_date.isoformat() if trade.entry_date else None,
            "exit_date": trade.exit_date.isoformat() if trade.exit_date else None,
            "entry_signal": trade.entry_signal,
            "exit_signal": trade.exit_signal,
            "pnl": trade.pnl,
            "pnl_percent": trade.pnl_percent,
            "net_pnl": trade.net_pnl,
            "is_winner": trade.is_winner
        }
