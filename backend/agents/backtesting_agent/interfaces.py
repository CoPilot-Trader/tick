"""
Public interfaces for the Backtesting Agent.
"""

from typing import List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class Trade(BaseModel):
    """Trade execution record."""
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    signal: str  # BUY or SELL


class BacktestResults(BaseModel):
    """Backtesting results."""
    symbol: str
    start_date: datetime
    end_date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    sharpe_ratio: float
    max_drawdown: float
    average_profit_per_trade: float
    metrics: Dict[str, Any]  # Cumulative PnL, daily returns, drawdown curve
    backtested_at: datetime

