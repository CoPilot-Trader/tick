# Support/Resistance Agent

**Developer**: Developer 2  
**Branch**: `feature/support-resistance-agent`  
**Status**: 🚧 In Development  
**Milestone**: M2 - Core Prediction Models

## Overview

The Support/Resistance Agent is responsible for:
- Identifying key support and resistance levels
- DBSCAN clustering for level detection
- Local extrema detection algorithm
- Level strength scoring (0-100)
- Historical validation of levels
- Target: 3-5 key levels per ticker, >60% show price reactions

## Directory Structure

```
support_resistance_agent/
├── __init__.py
├── agent.py              # Main agent class
├── interfaces.py         # Public interface definitions
├── detection/           # Level detection algorithms
│   ├── __init__.py
│   ├── dbscan_clustering.py
│   ├── extrema_detection.py
│   └── level_validator.py
├── scoring/            # Strength scoring
│   ├── __init__.py
│   └── strength_calculator.py
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── mocks/
└── README.md            # This file
```

## Interface

### Requires

- OHLCV data from Data Agent

### Provides

**Support/Resistance Levels**:
```python
{
    "symbol": "AAPL",
    "timestamp": "2024-01-15T10:30:00Z",
    "support_levels": [
        {
            "price": 145.00,
            "strength": 85,
            "type": "support",
            "touches": 5,
            "validated": True
        }
    ],
    "resistance_levels": [
        {
            "price": 155.00,
            "strength": 78,
            "type": "resistance",
            "touches": 4,
            "validated": True
        }
    ],
    "total_levels": 4
}
```

### API Endpoints

- `GET /api/v1/levels/{symbol}` - Get support/resistance levels
- `POST /api/v1/levels/detect` - Detect levels for symbol
- `GET /api/v1/levels/validate/{symbol}` - Validate levels

## Development Tasks

### Phase 1: Core Structure
- [x] Set up agent class structure
- [x] Implement base agent interface
- [ ] Create directory structure
- [ ] Set up testing framework

### Phase 2: Extrema Detection
- [ ] Implement local extrema detection
- [ ] Add peak/valley identification
- [ ] Add filtering logic
- [ ] Write unit tests

### Phase 3: DBSCAN Clustering
- [ ] Implement DBSCAN clustering
- [ ] Cluster extrema points
- [ ] Identify level clusters
- [ ] Write unit tests

### Phase 4: Strength Scoring
- [ ] Implement strength calculation (0-100)
- [ ] Add touch count scoring
- [ ] Add time-based scoring
- [ ] Write unit tests

### Phase 5: Validation
- [ ] Implement historical validation
- [ ] Add price reaction detection
- [ ] Calculate validation metrics (>60% target)
- [ ] Write unit tests

## Dependencies

- scikit-learn (DBSCAN)
- pandas
- numpy

## Acceptance Criteria (Milestone 2)

- Support/Resistance Agent identifies 3-5 key levels per ticker
- Levels have strength scores (0-100)
- >60% of identified levels show price reactions (validated)
- Detection completes in <3 seconds per ticker
- Levels are historically validated

## Notes

- Use DBSCAN to cluster similar price levels
- Strength score based on: number of touches, time relevance, price reaction
- Filter out weak levels (strength < 50)
- Support levels: price bounces up from level
- Resistance levels: price bounces down from level

