# Fusion Agent

**Developer**: Lead Developer  
**Branch**: `feature/fusion-agent`  
**Status**: 🚧 In Development  
**Milestone**: M3 - Sentiment & Fusion

## Overview

The Fusion Agent is responsible for:
- Rule-based signal fusion logic
- Weighted combination of all signals
- Final BUY/SELL/HOLD signal generation
- Confidence score calculation
- Providing unified trading signals

## Directory Structure

```
fusion_agent/
├── __init__.py
├── agent.py              # Main agent class
├── interfaces.py         # Public interface definitions
├── fusion/              # Fusion logic
│   ├── __init__.py
│   ├── rule_engine.py
│   ├── weight_calculator.py
│   └── signal_generator.py
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── mocks/
└── README.md            # This file
```

## Interface

### Requires

- Price forecasts from Price Forecast Agent
- Trend classification from Trend Classification Agent
- Support/resistance levels from Support/Resistance Agent
- Aggregated sentiment from Sentiment Aggregator

### Provides

**Fused Trading Signal**:
```python
{
    "symbol": "AAPL",
    "signal": "BUY",  # BUY, SELL, or HOLD
    "confidence": 0.78,  # 0.0 to 1.0
    "components": {
        "price_forecast": {
            "weight": 0.30,
            "contribution": 0.25,
            "signal": "BUY"
        },
        "trend_classification": {
            "weight": 0.25,
            "contribution": 0.20,
            "signal": "BUY"
        },
        "support_resistance": {
            "weight": 0.20,
            "contribution": 0.15,
            "signal": "NEUTRAL"
        },
        "sentiment": {
            "weight": 0.25,
            "contribution": 0.18,
            "signal": "BUY"
        }
    },
    "fused_at": "2024-01-15T10:30:00Z"
}
```

### API Endpoints

- `GET /api/v1/signals/{symbol}` - Get fused trading signal
- `POST /api/v1/signals/fuse` - Fuse signals for symbol
- `GET /api/v1/signals/components/{symbol}` - Get component signals

## Development Tasks

### Phase 1: Core Structure
- [x] Set up agent class structure
- [x] Implement base agent interface
- [ ] Create directory structure
- [ ] Set up testing framework

### Phase 2: Rule Engine
- [ ] Implement rule-based fusion logic
- [ ] Add signal combination rules
- [ ] Add conflict resolution
- [ ] Write unit tests

### Phase 3: Weight Calculation
- [ ] Implement weighted combination
- [ ] Add dynamic weight adjustment
- [ ] Add weight validation
- [ ] Write unit tests

### Phase 4: Signal Generation
- [ ] Implement final signal generation
- [ ] Add confidence calculation
- [ ] Add component tracking
- [ ] Write unit tests

## Dependencies

- None (uses outputs from other agents)

## Acceptance Criteria (Milestone 3)

- Fusion Agent generates unified trading signals from all inputs
- Rule-based fusion logic operational
- Weighted combination functional
- Final BUY/SELL/HOLD signal generated with confidence
- All agents integrated and communicating via defined interfaces
- End-to-end pipeline from news to fused signal operational

## Notes

- Use rule-based approach (not ML) for transparency
- Weights can be configurable
- Handle conflicting signals appropriately
- Confidence based on component agreement
- Provide detailed component breakdown

