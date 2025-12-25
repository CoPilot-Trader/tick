# Backtesting Agent

**Developer**: Lead Developer  
**Branch**: `feature/backtesting-agent`  
**Status**: 🚧 In Development  
**Milestone**: M4 - Backtesting & Integration

## Overview

The Backtesting Agent is responsible for:
- Historical simulation engine
- Trade execution logic (entry/exit based on signals)
- Performance metrics calculation (PnL, Sharpe ratio, drawdown, win rate)
- Walk-forward backtesting framework
- Results visualization and reporting

## Directory Structure

```
backtesting_agent/
├── __init__.py
├── agent.py              # Main agent class
├── interfaces.py         # Public interface definitions
├── engine/              # Backtesting engine
│   ├── __init__.py
│   ├── simulator.py
│   └── trade_executor.py
├── metrics/             # Performance metrics
│   ├── __init__.py
│   ├── pnl_calculator.py
│   ├── sharpe_calculator.py
│   └── drawdown_calculator.py
├── validation/          # Walk-forward validation
│   ├── __init__.py
│   └── walk_forward.py
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── mocks/
└── README.md            # This file
```

## Interface

### Requires

- Historical OHLCV data from Data Agent
- Fused signals from Fusion Agent (historical)

### Provides

**Backtesting Results**:
```python
{
    "symbol": "AAPL",
    "start_date": "2023-01-01",
    "end_date": "2024-01-15",
    "total_trades": 45,
    "winning_trades": 28,
    "losing_trades": 17,
    "win_rate": 0.622,
    "total_pnl": 1250.50,
    "sharpe_ratio": 1.85,
    "max_drawdown": -8.5,
    "average_profit_per_trade": 27.79,
    "metrics": {
        "cumulative_pnl": [1000, 1050, 1100, ...],
        "daily_returns": [0.02, -0.01, 0.03, ...],
        "drawdown_curve": [0, -1.5, -2.0, ...]
    },
    "backtested_at": "2024-01-15T10:30:00Z"
}
```

### API Endpoints

- `POST /api/v1/backtest/run` - Run backtest
- `GET /api/v1/backtest/results/{symbol}` - Get backtest results
- `POST /api/v1/backtest/walk-forward` - Run walk-forward backtest

## Development Tasks

### Phase 1: Core Structure
- [x] Set up agent class structure
- [x] Implement base agent interface
- [ ] Create directory structure
- [ ] Set up testing framework

### Phase 2: Simulation Engine
- [ ] Implement historical simulation
- [ ] Add trade execution logic
- [ ] Add position management
- [ ] Write unit tests

### Phase 3: Performance Metrics
- [ ] Implement PnL calculation
- [ ] Implement Sharpe ratio calculation
- [ ] Implement drawdown calculation
- [ ] Implement win rate calculation
- [ ] Write unit tests

### Phase 4: Walk-Forward Validation
- [ ] Implement walk-forward framework
- [ ] Add rolling window logic
- [ ] Add validation metrics
- [ ] Write unit tests

## Dependencies

- pandas
- numpy

## Acceptance Criteria (Milestone 4)

- Backtesting Agent runs historical simulations on 6+ months of data
- Performance metrics calculated and reported accurately
- Backtesting completes on 6 months of data in <10 minutes
- Performance metrics match expected calculations (validated manually)
- Walk-forward backtesting shows consistent performance
- System handles errors gracefully without crashing

## Notes

- Use historical signals (not real-time) for backtesting
- Simulate realistic trade execution (slippage, fees)
- Calculate all required metrics accurately
- Walk-forward validation prevents overfitting
- Handle edge cases (no trades, all wins, all losses)

