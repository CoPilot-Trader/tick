# Trend Classification Agent

**Developer**: Developer 2  
**Branch**: `feature/trend-classification-agent`  
**Status**: 🚧 In Development  
**Milestone**: M2 - Core Prediction Models

## Overview

The Trend Classification Agent is responsible for:
- Directional signal prediction (BUY/SELL/HOLD)
- LightGBM/XGBoost classifier implementation
- Multi-timeframe support (1h, 1d)
- Probability scores for each direction
- Target: >55% directional accuracy

## Directory Structure

```
trend_classification_agent/
├── __init__.py
├── agent.py              # Main agent class
├── interfaces.py         # Public interface definitions
├── models/              # Classification models
│   ├── __init__.py
│   ├── lightgbm_classifier.py
│   ├── xgboost_classifier.py
│   └── model_trainer.py
├── features/           # Feature engineering for classification
│   ├── __init__.py
│   └── trend_features.py
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── mocks/
└── README.md            # This file
```

## Interface

### Requires

- Features from Feature Agent
- OHLCV data from Data Agent

### Provides

**Trend Classification**:
```python
{
    "symbol": "AAPL",
    "timestamp": "2024-01-15T10:30:00Z",
    "timeframe": "1d",
    "signal": "BUY",  # BUY, SELL, or HOLD
    "probabilities": {
        "BUY": 0.65,
        "SELL": 0.20,
        "HOLD": 0.15
    },
    "confidence": 0.65,
    "model": "lightgbm"
}
```

### API Endpoints

- `GET /api/v1/trend/{symbol}` - Get trend classification
- `POST /api/v1/trend/train` - Train classifier
- `GET /api/v1/trend/performance/{symbol}` - Get model performance

## Development Tasks

### Phase 1: Core Structure
- [x] Set up agent class structure
- [x] Implement base agent interface
- [ ] Create directory structure
- [ ] Set up testing framework

### Phase 2: Feature Engineering
- [ ] Implement trend-specific features
- [ ] Add label generation (BUY/SELL/HOLD)
- [ ] Add feature selection
- [ ] Write unit tests

### Phase 3: Model Implementation
- [ ] Implement LightGBM classifier
- [ ] Implement XGBoost classifier (optional)
- [ ] Add hyperparameter tuning
- [ ] Write unit tests

### Phase 4: Training Pipeline
- [ ] Implement training logic
- [ ] Add validation framework
- [ ] Add model evaluation (>55% accuracy target)
- [ ] Add model saving/loading
- [ ] Write unit tests

### Phase 5: Inference
- [ ] Implement prediction pipeline
- [ ] Add probability calculation
- [ ] Optimize inference speed
- [ ] Write unit tests

## Dependencies

- LightGBM
- XGBoost (optional)
- scikit-learn
- pandas
- numpy

## Acceptance Criteria (Milestone 2)

- Trend Classification Agent achieves >55% directional accuracy on validation set
- Supports multi-timeframe (1h, 1d)
- Returns BUY/SELL/HOLD with probability scores
- Model inference completes in <3 seconds per ticker
- Model training pipeline runs without errors

## Notes

- Focus on 1-day timeframe initially
- Use LightGBM as primary, XGBoost as alternative
- Label generation: BUY if price increases >X%, SELL if decreases >X%, else HOLD
- Feature engineering critical for accuracy

