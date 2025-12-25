# Price Forecast Agent

**Developer**: Developer 2  
**Branch**: `feature/price-forecast-agent`  
**Status**: 🚧 In Development  
**Milestone**: M2 - Core Prediction Models

## Overview

The Price Forecast Agent is responsible for:
- Multi-horizon price prediction (1h, 4h, 1d, 1w)
- Prophet model implementation (baseline)
- LSTM model implementation (primary)
- Confidence interval calculation
- Model training pipeline with walk-forward validation

## Directory Structure

```
price_forecast_agent/
├── __init__.py
├── agent.py              # Main agent class
├── interfaces.py         # Public interface definitions
├── models/              # Prediction models
│   ├── __init__.py
│   ├── prophet_model.py
│   ├── lstm_model.py
│   └── model_trainer.py
├── training/            # Training pipeline
│   ├── __init__.py
│   ├── walk_forward.py
│   └── validation.py
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── mocks/
└── README.md            # This file
```

## Interface

### Requires

- OHLCV data from Data Agent
- Features from Feature Agent

### Provides

**Price Predictions**:
```python
{
    "symbol": "AAPL",
    "current_price": 150.25,
    "predictions": [
        {
            "horizon": "1h",
            "predicted_price": 150.50,
            "confidence": 0.75,
            "upper_bound": 151.00,
            "lower_bound": 150.00,
            "model": "lstm"
        },
        {
            "horizon": "4h",
            "predicted_price": 151.25,
            "confidence": 0.70,
            "upper_bound": 152.50,
            "lower_bound": 150.00,
            "model": "lstm"
        },
        {
            "horizon": "1d",
            "predicted_price": 152.30,
            "confidence": 0.65,
            "upper_bound": 155.00,
            "lower_bound": 149.50,
            "model": "lstm"
        },
        {
            "horizon": "1w",
            "predicted_price": 158.75,
            "confidence": 0.60,
            "upper_bound": 165.00,
            "lower_bound": 152.00,
            "model": "lstm"
        }
    ],
    "predicted_at": "2024-01-15T10:30:00Z"
}
```

### API Endpoints

- `GET /api/v1/forecast/{symbol}` - Get price forecasts
- `POST /api/v1/forecast/train` - Train models
- `GET /api/v1/forecast/performance/{symbol}` - Get model performance

## Development Tasks

### Phase 1: Core Structure
- [x] Set up agent class structure
- [x] Implement base agent interface
- [ ] Create directory structure
- [ ] Set up testing framework

### Phase 2: Prophet Model (Baseline)
- [ ] Implement Prophet model
- [ ] Add multi-horizon support
- [ ] Add confidence intervals
- [ ] Write unit tests

### Phase 3: LSTM Model (Primary)
- [ ] Implement LSTM architecture
- [ ] Add sequence preparation
- [ ] Add multi-horizon support
- [ ] Add confidence intervals
- [ ] Write unit tests

### Phase 4: Training Pipeline
- [ ] Implement walk-forward validation
- [ ] Add model training logic
- [ ] Add model evaluation
- [ ] Add model saving/loading
- [ ] Write unit tests

### Phase 5: Inference
- [ ] Implement prediction pipeline
- [ ] Add model serving
- [ ] Optimize inference speed
- [ ] Write unit tests

## Dependencies

- Prophet (Facebook)
- TensorFlow/Keras (for LSTM)
- scikit-learn
- pandas
- numpy

## Acceptance Criteria (Milestone 2)

- Price Forecast Agent generates predictions for all timeframes (1h, 4h, 1d, 1w)
- Predictions include confidence intervals
- Price predictions within 10% of actual price for 1-day horizon (50% of test cases)
- Model inference completes in <3 seconds per ticker
- Walk-forward validation framework operational
- Model training pipeline runs without errors

## Notes

- Prophet serves as baseline, LSTM as primary model
- Focus on 1-day predictions initially (most important)
- Use walk-forward validation to prevent overfitting
- Model should be retrainable via API

