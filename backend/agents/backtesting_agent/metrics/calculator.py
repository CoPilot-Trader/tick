"""
Performance Metrics Calculator for Backtesting Agent.

Calculates comprehensive trading performance metrics.
"""

import logging
import math
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Calculates trading performance metrics.

    Metrics calculated:
    - Total P&L and return
    - Win rate and profit factor
    - Sharpe ratio
    - Sortino ratio
    - Max drawdown
    - Calmar ratio
    - Average trade metrics
    - Streak analysis
    """

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize Metrics Calculator.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation (default: 2%)
        """
        self.risk_free_rate = risk_free_rate
        self.daily_risk_free = risk_free_rate / 252  # Convert to daily

    def calculate_all(
        self,
        trades: List[Dict[str, Any]],
        equity_curve: List[Dict[str, Any]],
        daily_returns: List[Dict[str, Any]],
        initial_capital: float
    ) -> Dict[str, Any]:
        """
        Calculate all performance metrics.

        Args:
            trades: List of completed trades
            equity_curve: List of equity snapshots
            daily_returns: List of daily return records
            initial_capital: Starting capital

        Returns:
            Dictionary with all metrics
        """
        if not trades and not equity_curve:
            return self._empty_metrics()

        # Basic trade metrics
        trade_metrics = self._calculate_trade_metrics(trades)

        # Return metrics
        return_metrics = self._calculate_return_metrics(
            equity_curve, daily_returns, initial_capital
        )

        # Risk metrics
        risk_metrics = self._calculate_risk_metrics(daily_returns)

        # Drawdown metrics
        drawdown_metrics = self._calculate_drawdown_metrics(equity_curve)

        # Combine all metrics
        return {
            **trade_metrics,
            **return_metrics,
            **risk_metrics,
            **drawdown_metrics,
            "calculated_at": datetime.utcnow().isoformat() + "Z"
        }

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "total_pnl": 0.0,
            "total_return_pct": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "max_drawdown_pct": 0.0,
            "calmar_ratio": 0.0,
            "avg_trade_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "avg_holding_period_days": 0.0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "calculated_at": datetime.utcnow().isoformat() + "Z"
        }

    def _calculate_trade_metrics(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trade-based metrics."""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "avg_trade_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "avg_holding_period_days": 0.0,
                "max_consecutive_wins": 0,
                "max_consecutive_losses": 0
            }

        # Separate winners and losers
        pnls = [t.get("net_pnl", t.get("pnl", 0)) for t in trades]
        winners = [p for p in pnls if p > 0]
        losers = [p for p in pnls if p <= 0]

        # Basic counts
        total_trades = len(trades)
        winning_trades = len(winners)
        losing_trades = len(losers)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # Profit factor
        gross_profit = sum(winners) if winners else 0
        gross_loss = abs(sum(losers)) if losers else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0

        # Averages
        avg_trade_pnl = sum(pnls) / len(pnls) if pnls else 0
        avg_win = sum(winners) / len(winners) if winners else 0
        avg_loss = sum(losers) / len(losers) if losers else 0

        # Extremes
        largest_win = max(winners) if winners else 0
        largest_loss = min(losers) if losers else 0

        # Holding period
        holding_periods = []
        for trade in trades:
            entry = trade.get("entry_date")
            exit = trade.get("exit_date")
            if entry and exit:
                if isinstance(entry, str):
                    entry = datetime.fromisoformat(entry.replace("Z", "+00:00"))
                if isinstance(exit, str):
                    exit = datetime.fromisoformat(exit.replace("Z", "+00:00"))
                holding_periods.append((exit - entry).days)

        avg_holding = sum(holding_periods) / len(holding_periods) if holding_periods else 0

        # Consecutive wins/losses
        max_wins, max_losses = self._calculate_streaks(trades)

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": round(win_rate * 100, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float('inf') else "inf",
            "avg_trade_pnl": round(avg_trade_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "avg_holding_period_days": round(avg_holding, 1),
            "max_consecutive_wins": max_wins,
            "max_consecutive_losses": max_losses
        }

    def _calculate_return_metrics(
        self,
        equity_curve: List[Dict[str, Any]],
        daily_returns: List[Dict[str, Any]],
        initial_capital: float
    ) -> Dict[str, Any]:
        """Calculate return-based metrics."""
        if not equity_curve:
            return {
                "total_pnl": 0.0,
                "total_return_pct": 0.0,
                "annualized_return": 0.0,
                "daily_return_avg": 0.0,
                "daily_return_std": 0.0
            }

        # Total P&L
        final_equity = equity_curve[-1].get("equity", initial_capital)
        total_pnl = final_equity - initial_capital
        total_return_pct = (total_pnl / initial_capital) * 100

        # Daily returns
        returns = [r.get("daily_return", 0) for r in daily_returns]
        avg_daily_return = sum(returns) / len(returns) if returns else 0

        # Standard deviation
        if len(returns) > 1:
            mean = avg_daily_return
            variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1)
            std_daily_return = math.sqrt(variance)
        else:
            std_daily_return = 0

        # Annualized return
        trading_days = len(returns)
        if trading_days > 0:
            annualized_return = ((1 + avg_daily_return) ** 252 - 1) * 100
        else:
            annualized_return = 0

        return {
            "total_pnl": round(total_pnl, 2),
            "total_return_pct": round(total_return_pct, 2),
            "annualized_return": round(annualized_return, 2),
            "daily_return_avg": round(avg_daily_return * 100, 4),
            "daily_return_std": round(std_daily_return * 100, 4)
        }

    def _calculate_risk_metrics(self, daily_returns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate risk-adjusted metrics."""
        if not daily_returns:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "volatility_annual": 0.0
            }

        returns = [r.get("daily_return", 0) for r in daily_returns]

        if len(returns) < 2:
            return {
                "sharpe_ratio": 0.0,
                "sortino_ratio": 0.0,
                "volatility_annual": 0.0
            }

        # Calculate Sharpe Ratio
        avg_return = sum(returns) / len(returns)
        excess_returns = [r - self.daily_risk_free for r in returns]
        avg_excess = sum(excess_returns) / len(excess_returns)

        # Standard deviation
        variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = math.sqrt(variance)

        # Annualized Sharpe
        sharpe_ratio = (avg_excess / std_dev) * math.sqrt(252) if std_dev > 0 else 0

        # Sortino Ratio (uses downside deviation)
        downside_returns = [r for r in returns if r < 0]
        if downside_returns and len(downside_returns) > 1:
            downside_variance = sum(r ** 2 for r in downside_returns) / len(downside_returns)
            downside_dev = math.sqrt(downside_variance)
            sortino_ratio = (avg_excess / downside_dev) * math.sqrt(252) if downside_dev > 0 else 0
        else:
            sortino_ratio = sharpe_ratio  # No downside, use Sharpe

        # Annualized volatility
        volatility_annual = std_dev * math.sqrt(252) * 100

        return {
            "sharpe_ratio": round(sharpe_ratio, 2),
            "sortino_ratio": round(sortino_ratio, 2),
            "volatility_annual": round(volatility_annual, 2)
        }

    def _calculate_drawdown_metrics(self, equity_curve: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate drawdown metrics."""
        if not equity_curve:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_pct": 0.0,
                "max_drawdown_duration_days": 0,
                "calmar_ratio": 0.0,
                "current_drawdown_pct": 0.0
            }

        equities = [e.get("equity", 0) for e in equity_curve]
        if not equities:
            return {
                "max_drawdown": 0.0,
                "max_drawdown_pct": 0.0,
                "max_drawdown_duration_days": 0,
                "calmar_ratio": 0.0,
                "current_drawdown_pct": 0.0
            }

        # Calculate drawdown series
        peak = equities[0]
        max_drawdown = 0
        max_drawdown_pct = 0
        drawdown_start = 0
        max_drawdown_duration = 0
        current_drawdown_duration = 0

        for i, equity in enumerate(equities):
            if equity > peak:
                peak = equity
                if current_drawdown_duration > max_drawdown_duration:
                    max_drawdown_duration = current_drawdown_duration
                current_drawdown_duration = 0
            else:
                drawdown = peak - equity
                drawdown_pct = (drawdown / peak) * 100 if peak > 0 else 0
                current_drawdown_duration += 1

                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                    max_drawdown_pct = drawdown_pct

        # Current drawdown
        current_drawdown_pct = ((peak - equities[-1]) / peak) * 100 if peak > 0 else 0

        # Calmar ratio (annualized return / max drawdown)
        if len(equities) > 1:
            total_return = (equities[-1] - equities[0]) / equities[0]
            trading_days = len(equities)
            annualized_return = ((1 + total_return) ** (252 / trading_days) - 1) * 100 if trading_days > 0 else 0
            calmar_ratio = annualized_return / max_drawdown_pct if max_drawdown_pct > 0 else 0
        else:
            calmar_ratio = 0

        return {
            "max_drawdown": round(max_drawdown, 2),
            "max_drawdown_pct": round(max_drawdown_pct, 2),
            "max_drawdown_duration_days": max_drawdown_duration,
            "calmar_ratio": round(calmar_ratio, 2),
            "current_drawdown_pct": round(current_drawdown_pct, 2)
        }

    def _calculate_streaks(self, trades: List[Dict[str, Any]]) -> tuple:
        """Calculate maximum consecutive wins and losses."""
        if not trades:
            return 0, 0

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            pnl = trade.get("net_pnl", trade.get("pnl", 0))

            if pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    def generate_report(
        self,
        metrics: Dict[str, Any],
        symbol: str,
        period: str
    ) -> str:
        """
        Generate human-readable performance report.

        Args:
            metrics: Calculated metrics dictionary
            symbol: Stock symbol
            period: Time period description

        Returns:
            Formatted report string
        """
        report = f"""
========================================
BACKTEST PERFORMANCE REPORT
========================================
Symbol: {symbol}
Period: {period}

--- RETURNS ---
Total P&L: ${metrics.get('total_pnl', 0):,.2f}
Total Return: {metrics.get('total_return_pct', 0):.2f}%
Annualized Return: {metrics.get('annualized_return', 0):.2f}%

--- TRADES ---
Total Trades: {metrics.get('total_trades', 0)}
Winning Trades: {metrics.get('winning_trades', 0)}
Losing Trades: {metrics.get('losing_trades', 0)}
Win Rate: {metrics.get('win_rate', 0):.2f}%
Profit Factor: {metrics.get('profit_factor', 0)}

--- AVERAGES ---
Avg Trade P&L: ${metrics.get('avg_trade_pnl', 0):,.2f}
Avg Win: ${metrics.get('avg_win', 0):,.2f}
Avg Loss: ${metrics.get('avg_loss', 0):,.2f}
Avg Holding Period: {metrics.get('avg_holding_period_days', 0):.1f} days

--- RISK METRICS ---
Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}
Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}
Annual Volatility: {metrics.get('volatility_annual', 0):.2f}%

--- DRAWDOWN ---
Max Drawdown: ${metrics.get('max_drawdown', 0):,.2f}
Max Drawdown %: {metrics.get('max_drawdown_pct', 0):.2f}%
Max Drawdown Duration: {metrics.get('max_drawdown_duration_days', 0)} days
Calmar Ratio: {metrics.get('calmar_ratio', 0):.2f}

--- STREAKS ---
Max Consecutive Wins: {metrics.get('max_consecutive_wins', 0)}
Max Consecutive Losses: {metrics.get('max_consecutive_losses', 0)}

========================================
"""
        return report
