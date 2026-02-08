"""
Position Manager for Backtesting Agent.

Tracks open positions, calculates P&L, and manages risk limits.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """Represents an open position."""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: float
    quantity: int
    entry_date: datetime
    entry_signal: str  # The signal that triggered entry
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L."""
        if self.side == 'long':
            return (current_price - self.entry_price) * self.quantity
        else:  # short
            return (self.entry_price - current_price) * self.quantity

    def unrealized_pnl_percent(self, current_price: float) -> float:
        """Calculate unrealized P&L as percentage."""
        if self.side == 'long':
            return ((current_price - self.entry_price) / self.entry_price) * 100
        else:
            return ((self.entry_price - current_price) / self.entry_price) * 100


@dataclass
class Trade:
    """Represents a completed trade."""
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: int
    entry_date: datetime
    exit_date: datetime
    entry_signal: str
    exit_signal: str
    pnl: float
    pnl_percent: float
    commission: float = 0.0
    slippage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def net_pnl(self) -> float:
        """P&L after commission and slippage."""
        return self.pnl - self.commission - self.slippage

    @property
    def is_winner(self) -> bool:
        """Check if trade was profitable."""
        return self.net_pnl > 0


class PositionManager:
    """
    Manages positions and tracks P&L during backtesting.

    Features:
    - Track open positions
    - Calculate unrealized P&L
    - Record completed trades
    - Enforce position limits
    - Track equity curve
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Position Manager.

        Args:
            config: Configuration options:
                   - initial_capital: Starting capital (default: 100000)
                   - max_position_size: Max % of capital per position (default: 0.1 = 10%)
                   - max_positions: Max concurrent positions (default: 5)
                   - commission_rate: Commission per trade (default: 0.001 = 0.1%)
                   - slippage_rate: Slippage per trade (default: 0.0005 = 0.05%)
        """
        self.config = config or {}
        self.initial_capital = self.config.get("initial_capital", 100000)
        self.max_position_size = self.config.get("max_position_size", 0.1)
        self.max_positions = self.config.get("max_positions", 5)
        self.commission_rate = self.config.get("commission_rate", 0.001)
        self.slippage_rate = self.config.get("slippage_rate", 0.0005)

        # State
        self.cash = self.initial_capital
        self.positions: Dict[str, Position] = {}  # symbol -> Position
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict[str, Any]] = []

        logger.info(f"PositionManager initialized with ${self.initial_capital:,.2f} capital")

    def reset(self) -> None:
        """Reset to initial state."""
        self.cash = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []

    def get_equity(self, current_prices: Dict[str, float]) -> float:
        """
        Calculate total equity (cash + unrealized P&L).

        Args:
            current_prices: Dict of symbol -> current price
        """
        equity = self.cash
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                equity += position.unrealized_pnl(current_prices[symbol])
        return equity

    def record_equity(self, date: datetime, current_prices: Dict[str, float]) -> None:
        """Record equity snapshot for equity curve."""
        equity = self.get_equity(current_prices)
        self.equity_curve.append({
            "date": date,
            "equity": equity,
            "cash": self.cash,
            "positions_value": equity - self.cash,
            "num_positions": len(self.positions)
        })

    def can_open_position(self, symbol: str) -> bool:
        """Check if we can open a new position."""
        if symbol in self.positions:
            return False  # Already have position in this symbol
        if len(self.positions) >= self.max_positions:
            return False
        return True

    def calculate_position_size(self, price: float) -> int:
        """
        Calculate position size based on available capital and limits.

        Returns number of shares to buy.
        """
        max_value = self.cash * self.max_position_size
        shares = int(max_value / price)
        return max(1, shares)  # At least 1 share

    def open_position(
        self,
        symbol: str,
        side: str,
        price: float,
        quantity: int,
        date: datetime,
        signal: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Position]:
        """
        Open a new position.

        Args:
            symbol: Stock symbol
            side: 'long' or 'short'
            price: Entry price
            quantity: Number of shares
            date: Entry date
            signal: Signal that triggered entry
            stop_loss: Optional stop loss price
            take_profit: Optional take profit price
            metadata: Optional additional data

        Returns:
            Position if opened, None otherwise
        """
        if not self.can_open_position(symbol):
            logger.warning(f"Cannot open position for {symbol}: limit reached or existing position")
            return None

        # Calculate costs
        slippage = price * self.slippage_rate
        effective_price = price + slippage if side == 'long' else price - slippage
        commission = effective_price * quantity * self.commission_rate
        total_cost = effective_price * quantity + commission

        if total_cost > self.cash:
            logger.warning(f"Insufficient cash for {symbol}: need ${total_cost:,.2f}, have ${self.cash:,.2f}")
            return None

        # Create position
        position = Position(
            symbol=symbol,
            side=side,
            entry_price=effective_price,
            quantity=quantity,
            entry_date=date,
            entry_signal=signal,
            stop_loss=stop_loss,
            take_profit=take_profit,
            metadata=metadata or {}
        )

        # Update state
        self.positions[symbol] = position
        self.cash -= total_cost

        logger.info(f"Opened {side} position: {quantity} {symbol} @ ${effective_price:.2f}")
        return position

    def close_position(
        self,
        symbol: str,
        price: float,
        date: datetime,
        signal: str
    ) -> Optional[Trade]:
        """
        Close an existing position.

        Args:
            symbol: Stock symbol
            price: Exit price
            date: Exit date
            signal: Signal that triggered exit

        Returns:
            Trade record if closed, None otherwise
        """
        if symbol not in self.positions:
            logger.warning(f"No position to close for {symbol}")
            return None

        position = self.positions[symbol]

        # Calculate costs
        slippage = price * self.slippage_rate
        effective_price = price - slippage if position.side == 'long' else price + slippage
        commission = effective_price * position.quantity * self.commission_rate

        # Calculate P&L
        if position.side == 'long':
            gross_pnl = (effective_price - position.entry_price) * position.quantity
        else:
            gross_pnl = (position.entry_price - effective_price) * position.quantity

        pnl_percent = (gross_pnl / (position.entry_price * position.quantity)) * 100

        # Create trade record
        trade = Trade(
            symbol=symbol,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=effective_price,
            quantity=position.quantity,
            entry_date=position.entry_date,
            exit_date=date,
            entry_signal=position.entry_signal,
            exit_signal=signal,
            pnl=gross_pnl,
            pnl_percent=pnl_percent,
            commission=commission,
            slippage=slippage * position.quantity,
            metadata=position.metadata
        )

        # Update state
        self.cash += effective_price * position.quantity - commission
        del self.positions[symbol]
        self.trades.append(trade)

        logger.info(f"Closed {position.side} position: {symbol} @ ${effective_price:.2f}, P&L: ${trade.net_pnl:,.2f}")
        return trade

    def check_stop_loss_take_profit(
        self,
        current_prices: Dict[str, float],
        date: datetime
    ) -> List[Trade]:
        """
        Check and execute stop loss/take profit orders.

        Returns list of executed trades.
        """
        executed_trades = []
        symbols_to_close = []

        for symbol, position in self.positions.items():
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]

            # Check stop loss
            if position.stop_loss:
                if position.side == 'long' and current_price <= position.stop_loss:
                    symbols_to_close.append((symbol, current_price, "stop_loss"))
                elif position.side == 'short' and current_price >= position.stop_loss:
                    symbols_to_close.append((symbol, current_price, "stop_loss"))

            # Check take profit
            if position.take_profit:
                if position.side == 'long' and current_price >= position.take_profit:
                    symbols_to_close.append((symbol, current_price, "take_profit"))
                elif position.side == 'short' and current_price <= position.take_profit:
                    symbols_to_close.append((symbol, current_price, "take_profit"))

        # Close positions
        for symbol, price, signal in symbols_to_close:
            trade = self.close_position(symbol, price, date, signal)
            if trade:
                executed_trades.append(trade)

        return executed_trades

    def get_summary(self) -> Dict[str, Any]:
        """Get position manager summary."""
        return {
            "initial_capital": self.initial_capital,
            "current_cash": self.cash,
            "open_positions": len(self.positions),
            "total_trades": len(self.trades),
            "positions": {
                symbol: {
                    "side": pos.side,
                    "entry_price": pos.entry_price,
                    "quantity": pos.quantity,
                    "entry_date": pos.entry_date.isoformat()
                }
                for symbol, pos in self.positions.items()
            }
        }
