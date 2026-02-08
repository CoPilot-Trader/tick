"""
Backtesting Agent - Main agent implementation.

Provides historical simulation and performance analysis for trading strategies.

Developer: Lead Developer
Milestone: M4 - Backtesting & Integration
Version: 2.0.0
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
import pandas as pd

from core.interfaces.base_agent import BaseAgent
from .engine import BacktestSimulator, PositionManager
from .metrics import MetricsCalculator

logger = logging.getLogger(__name__)


class BacktestingAgent(BaseAgent):
    """
    Backtesting Agent for simulating historical performance.

    This agent:
    1. Simulates trading based on historical signals
    2. Tracks positions and equity
    3. Calculates comprehensive performance metrics
    4. Supports walk-forward testing

    Features:
    - Signal-based trading simulation
    - Position sizing and risk management
    - Stop loss and take profit handling
    - Comprehensive metrics (Sharpe, Sortino, Drawdown, etc.)
    - Walk-forward backtesting

    Developer: Lead Developer
    Milestone: M4 - Backtesting & Integration
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Backtesting Agent."""
        super().__init__(name="backtesting_agent", config=config)
        self.version = "2.0.0"

        # Default configuration
        self.default_config = {
            "initial_capital": 100000,
            "max_position_size": 0.1,  # 10% max per position
            "max_positions": 5,
            "commission_rate": 0.001,  # 0.1%
            "slippage_rate": 0.0005,  # 0.05%
            "min_confidence": 0.5,
            "stop_loss_pct": 0.05,  # 5%
            "take_profit_pct": 0.10,  # 10%
            "risk_free_rate": 0.02  # 2% annual
        }

        # Merge with provided config
        self.config = {**self.default_config, **(config or {})}

        # Components (initialized in initialize())
        self.simulator: Optional[BacktestSimulator] = None
        self.metrics_calculator: Optional[MetricsCalculator] = None

    def initialize(self) -> bool:
        """
        Initialize the Backtesting Agent.

        Sets up:
        - Simulation engine
        - Metrics calculator
        """
        try:
            # Initialize simulator
            self.simulator = BacktestSimulator(self.config)

            # Initialize metrics calculator
            self.metrics_calculator = MetricsCalculator(
                risk_free_rate=self.config.get("risk_free_rate", 0.02)
            )

            self.initialized = True
            logger.info(f"BacktestingAgent v{self.version} initialized")
            return True

        except Exception as e:
            logger.error(f"Error initializing Backtesting Agent: {e}", exc_info=True)
            self.initialized = False
            return False

    def process(self, symbol: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run backtest for a given symbol.

        Args:
            symbol: Stock symbol
            params: Parameters:
                   - price_data: DataFrame with OHLCV data (required)
                   - signals: List of signals (required)
                   - start_date: Optional start date
                   - end_date: Optional end date
                   - calculate_metrics: Calculate detailed metrics (default: True)

        Returns:
            Dictionary with backtesting results and metrics
        """
        if not self.initialized:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Agent not initialized. Call initialize() first."
            }

        params = params or {}
        price_data = params.get("price_data")
        signals = params.get("signals", [])
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        calculate_metrics = params.get("calculate_metrics", True)

        if price_data is None:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "price_data is required"
            }

        try:
            # Run simulation
            result = self.simulator.run(
                symbol=symbol,
                price_data=price_data,
                signals=signals,
                start_date=start_date,
                end_date=end_date
            )

            if result.get("status") != "success":
                return result

            # Calculate metrics if requested
            if calculate_metrics and self.metrics_calculator:
                metrics = self.metrics_calculator.calculate_all(
                    trades=result.get("trades", []),
                    equity_curve=result.get("equity_curve", []),
                    daily_returns=result.get("daily_returns", []),
                    initial_capital=self.config.get("initial_capital", 100000)
                )
                result["metrics"] = metrics

            return result

        except Exception as e:
            logger.error(f"Error running backtest for {symbol}: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "status": "error",
                "message": str(e)
            }

    def run_backtest(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        signals: List[Dict[str, Any]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Run historical backtest (convenience method).

        Args:
            symbol: Stock symbol
            price_data: DataFrame with OHLCV data
            signals: List of historical signals
            start_date: Backtest start date
            end_date: Backtest end date

        Returns:
            Dictionary with backtesting results
        """
        return self.process(symbol, params={
            "price_data": price_data,
            "signals": signals,
            "start_date": start_date,
            "end_date": end_date
        })

    def walk_forward_backtest(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        signal_generator: Callable,
        train_days: int = 252,
        test_days: int = 63,
        step_days: int = 21
    ) -> Dict[str, Any]:
        """
        Run walk-forward backtest.

        Walk-forward testing:
        1. Train on historical period
        2. Generate signals
        3. Test on out-of-sample period
        4. Step forward and repeat

        Args:
            symbol: Stock symbol
            price_data: Full historical DataFrame
            signal_generator: Callable(symbol, train_data) -> signals
            train_days: Training period in days (default: 252 = 1 year)
            test_days: Testing period in days (default: 63 = 1 quarter)
            step_days: Days to step forward (default: 21 = 1 month)

        Returns:
            Dictionary with walk-forward results
        """
        if not self.initialized:
            return {
                "symbol": symbol,
                "status": "error",
                "message": "Agent not initialized"
            }

        try:
            result = self.simulator.run_walk_forward(
                symbol=symbol,
                price_data=price_data,
                signal_generator=signal_generator,
                train_days=train_days,
                test_days=test_days,
                step_days=step_days
            )

            # Calculate aggregate metrics
            if result.get("status") == "success" and self.metrics_calculator:
                metrics = self.metrics_calculator.calculate_all(
                    trades=result.get("all_trades", []),
                    equity_curve=result.get("equity_curve", []),
                    daily_returns=[],  # Not aggregated for walk-forward
                    initial_capital=self.config.get("initial_capital", 100000)
                )
                result["aggregate_metrics"] = metrics

            return result

        except Exception as e:
            logger.error(f"Error in walk-forward backtest: {e}", exc_info=True)
            return {
                "symbol": symbol,
                "status": "error",
                "message": str(e)
            }

    def calculate_metrics(
        self,
        trades: List[Dict[str, Any]],
        equity_curve: List[Dict[str, Any]],
        daily_returns: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics from trade data.

        Args:
            trades: List of executed trades
            equity_curve: Equity curve over time
            daily_returns: Optional daily return records

        Returns:
            Dictionary with performance metrics
        """
        if not self.metrics_calculator:
            return {"status": "error", "message": "Metrics calculator not initialized"}

        return self.metrics_calculator.calculate_all(
            trades=trades,
            equity_curve=equity_curve,
            daily_returns=daily_returns or [],
            initial_capital=self.config.get("initial_capital", 100000)
        )

    def generate_report(
        self,
        backtest_result: Dict[str, Any],
        symbol: str
    ) -> str:
        """
        Generate human-readable performance report.

        Args:
            backtest_result: Result from run_backtest
            symbol: Stock symbol

        Returns:
            Formatted report string
        """
        if not self.metrics_calculator:
            return "Metrics calculator not initialized"

        metrics = backtest_result.get("metrics", {})
        period = f"{backtest_result.get('start_date', 'N/A')} to {backtest_result.get('end_date', 'N/A')}"

        return self.metrics_calculator.generate_report(metrics, symbol, period)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.copy()

    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update configuration.

        Args:
            new_config: New configuration values

        Returns:
            True if successful
        """
        try:
            self.config.update(new_config)

            # Reinitialize components with new config
            if self.initialized:
                self.simulator = BacktestSimulator(self.config)
                self.metrics_calculator = MetricsCalculator(
                    risk_free_rate=self.config.get("risk_free_rate", 0.02)
                )

            logger.info(f"Configuration updated: {new_config}")
            return True
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False

    def health_check(self) -> Dict[str, Any]:
        """Check Backtesting Agent health."""
        return {
            "status": "healthy" if self.initialized else "not_initialized",
            "agent": self.name,
            "version": self.version,
            "config": {
                "initial_capital": self.config.get("initial_capital"),
                "max_position_size": self.config.get("max_position_size"),
                "commission_rate": self.config.get("commission_rate"),
                "stop_loss_pct": self.config.get("stop_loss_pct"),
                "take_profit_pct": self.config.get("take_profit_pct")
            },
            "components": {
                "simulator": self.simulator is not None,
                "metrics_calculator": self.metrics_calculator is not None
            }
        }
