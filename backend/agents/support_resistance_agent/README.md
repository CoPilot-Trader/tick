# Support/Resistance Agent

**Developer**: Developer 2  
**Status**: ✅ **Production Ready - 100% Specification Compliant**  
**Milestone**: M2 - Core Prediction Models

## Quick Overview

The Support/Resistance Agent identifies key price levels with strength scores, breakout probabilities, volume confirmation, and ML-enhanced future level predictions.

**Key Features:**
- ✅ 100% specification compliance
- ✅ Multi-timeframe support (1m to 1y)
- ✅ Level validity projection
- ✅ ML-enhanced future level prediction (hybrid approach)
- ✅ Volume profile analysis
- ✅ Breakout probability calculation
- ✅ Real-time capable (<3 seconds per ticker)

## Quick Start

```python
from agents.support_resistance_agent.agent import SupportResistanceAgent

# Initialize agent
agent = SupportResistanceAgent(config={"use_mock_data": True})
agent.initialize()

# Detect levels
result = agent.process("AAPL", params={
    "min_strength": 50,
    "max_levels": 5,
    "timeframe": "1d",
    "project_future": True
})

print(result)
```

## API Endpoints

- `GET /api/v1/levels/{symbol}` - Get levels for a symbol
- `POST /api/v1/levels/detect` - Detect levels
- `POST /api/v1/levels/batch` - Batch detection
- `GET /api/v1/levels/{symbol}/nearest` - Get nearest levels
- `GET /api/v1/levels/health` - Health check

## Output Format

```python
{
    "symbol": "AAPL",
    "current_price": 150.00,
    "support_levels": [
        {
            "price": 145.00,
            "strength": 85,
            "type": "support",
            "breakout_probability": 45.2,
            "volume": 1500000,
            "has_volume_confirmation": True,
            "projected_valid_until": "2024-03-15T00:00:00Z"
        }
    ],
    "resistance_levels": [...],
    "predicted_future_levels": [...]  # If project_future=True
}
```

## Configuration

```python
config = {
    "use_mock_data": True,           # Use mock data or real data
    "enable_cache": True,             # Enable caching
    "use_ml_predictions": True,       # Enable ML enhancement
    "ml_model_path": None            # Path to ML model (optional)
}
```

## Features

### Core Detection
- **Extrema Detection**: Uses `scipy.signal.argrelextrema`
- **DBSCAN Clustering**: Groups similar price levels
- **Level Validation**: Historical price reaction validation
- **Volume Profile**: High-volume node identification

### Scoring
- **Strength Score**: 0-100 based on touches, time, reactions
- **Breakout Probability**: 0-100% probability of level breaking
- **Volume Confirmation**: Volume-based level validation

### Projection
- **Level Validity**: Predicts when levels become invalid
- **Future Prediction**: Predicts new levels (Fibonacci, Round Numbers, Spacing)
- **ML Enhancement**: Optional ML model for improved accuracy

## Performance

- **Single ticker**: <3 seconds
- **Batch (10 tickers)**: ~15-30 seconds (sequential) or ~5-10 seconds (parallel)
- **Cache hit**: <0.1 seconds

## Dependencies

**Required:**
- pandas, numpy, scipy, scikit-learn, yfinance

**Optional (for ML):**
- lightgbm, xgboost

## Documentation

For complete documentation, see:
- **`IMPLEMENTATION_SUMMARY.md`** - Complete implementation details, enhancements, ML prediction guide, and specification compliance

## Status

✅ **Production Ready** - All features implemented and tested
✅ **100% Specification Compliant** - All specified features complete
✅ **Optimized** - Handles 1-100 tickers efficiently
