"""
Trade Executor for Backtesting Agent.

Executes trades based on signals and manages order flow.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from .position_manager import PositionManager, Trade

logger = logging.getLogger(__name__)


class TradeExecutor:
    """
    Executes trades based on fusion signals.

    Features:
    - Signal interpretation (BUY/SELL/HOLD)
    - Confidence-based position sizing
    - Stop loss and take profit calculation
    - Order validation
    """

    def __init__(
        self,
        position_manager: PositionManager,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Trade Executor.

        Args:
            position_manager: PositionManager instance
            config: Configuration options:
                   - min_confidence: Min confidence to execute (default: 0.5)
                   - use_confidence_sizing: Scale position by confidence (default: True)
                   - stop_loss_pct: Stop loss percentage (default: 0.05 = 5%)
                   - take_profit_pct: Take profit percentage (default: 0.10 = 10%)
                   - require_strong_signal: Only trade strong signals (default: False)
        """
        self.position_manager = position_manager
        self.config = config or {}

        self.min_confidence = self.config.get("min_confidence", 0.5)
        self.use_confidence_sizing = self.config.get("use_confidence_sizing", True)
        self.stop_loss_pct = self.config.get("stop_loss_pct", 0.05)
        self.take_profit_pct = self.config.get("take_profit_pct", 0.10)
        self.require_strong_signal = self.config.get("require_strong_signal", False)

        logger.info(f"TradeExecutor initialized: min_confidence={self.min_confidence}")

    def should_execute(self, signal: Dict[str, Any]) -> bool:
        """
        Determine if signal should be executed.

        Args:
            signal: Fusion signal with 'signal', 'confidence', etc.

        Returns:
            True if signal should be executed
        """
        # Check minimum confidence
        confidence = signal.get("confidence", 0.0)
        if confidence < self.min_confidence:
            logger.debug(f"Signal rejected: confidence {confidence:.2f} < {self.min_confidence}")
            return False

        # Check signal type
        signal_type = signal.get("signal", "HOLD")
        if signal_type == "HOLD":
            return False

        # Check for strong signal requirement
        if self.require_strong_signal:
            fused_score = abs(signal.get("fused_score", 0.0))
            if fused_score < 0.5:
                logger.debug(f"Signal rejected: fused_score {fused_score:.2f} not strong enough")
                return False

        return True

    def calculate_stops(
        self,
        price: float,
        side: str
    ) -> tuple:
        """
        Calculate stop loss and take profit levels.

        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if side == 'long':
            stop_loss = price * (1 - self.stop_loss_pct)
            take_profit = price * (1 + self.take_profit_pct)
        else:  # short
            stop_loss = price * (1 + self.stop_loss_pct)
            take_profit = price * (1 - self.take_profit_pct)

        return stop_loss, take_profit

    def execute_signal(
        self,
        symbol: str,
        signal: Dict[str, Any],
        price: float,
        date: datetime
    ) -> Optional[Trade]:
        """
        Execute a trading signal.

        Args:
            symbol: Stock symbol
            signal: Fusion signal
            price: Current price
            date: Current date

        Returns:
            Trade if executed, None otherwise
        """
        signal_type = signal.get("signal", "HOLD")
        confidence = signal.get("confidence", 0.0)

        # HOLD signals don't require action
        if signal_type == "HOLD":
            return None

        # Check if we have an existing position
        has_position = symbol in self.position_manager.positions

        if has_position:
            position = self.position_manager.positions[symbol]

            # Check if signal is opposite to current position (exit signal)
            if (signal_type == "SELL" and position.side == "long") or \
               (signal_type == "BUY" and position.side == "short"):
                # Close position
                return self.position_manager.close_position(
                    symbol=symbol,
                    price=price,
                    date=date,
                    signal=signal_type
                )
            else:
                # Signal matches position direction, no action
                return None
        else:
            # No position, check if we should open one
            if not self.should_execute(signal):
                return None

            # Determine position side and size
            side = "long" if signal_type == "BUY" else "short"

            # Calculate position size (potentially scaled by confidence)
            base_size = self.position_manager.calculate_position_size(price)
            if self.use_confidence_sizing:
                # Scale by confidence (50% confidence = 50% of base size)
                size = max(1, int(base_size * confidence))
            else:
                size = base_size

            # Calculate stops
            stop_loss, take_profit = self.calculate_stops(price, side)

            # Open position
            position = self.position_manager.open_position(
                symbol=symbol,
                side=side,
                price=price,
                quantity=size,
                date=date,
                signal=signal_type,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={
                    "confidence": confidence,
                    "fused_score": signal.get("fused_score", 0.0),
                    "reasoning": signal.get("reasoning", "")
                }
            )

            return None  # Position opened, no completed trade yet

    def process_day(
        self,
        symbol: str,
        signal: Dict[str, Any],
        ohlcv: Dict[str, Any],
        date: datetime
    ) -> List[Trade]:
        """
        Process a single day's trading.

        Args:
            symbol: Stock symbol
            signal: Fusion signal for this day
            ohlcv: OHLCV data for this day
            date: Current date

        Returns:
            List of completed trades
        """
        trades = []
        close_price = ohlcv.get("close", 0.0)
        high_price = ohlcv.get("high", close_price)
        low_price = ohlcv.get("low", close_price)

        # Check stop loss / take profit first
        current_prices = {symbol: low_price}  # Use low for stop checks on longs
        sl_trades = self.position_manager.check_stop_loss_take_profit(
            current_prices, date
        )
        trades.extend(sl_trades)

        # Then execute signal
        trade = self.execute_signal(symbol, signal, close_price, date)
        if trade:
            trades.append(trade)

        return trades

    def close_all_positions(
        self,
        current_prices: Dict[str, float],
        date: datetime
    ) -> List[Trade]:
        """
        Close all open positions (end of backtest).

        Returns:
            List of closing trades
        """
        trades = []
        symbols = list(self.position_manager.positions.keys())

        for symbol in symbols:
            if symbol in current_prices:
                trade = self.position_manager.close_position(
                    symbol=symbol,
                    price=current_prices[symbol],
                    date=date,
                    signal="backtest_end"
                )
                if trade:
                    trades.append(trade)

        return trades
