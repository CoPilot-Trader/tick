# Sentiment Aggregator

**Developer**: Developer 1  
**Branch**: `feature/sentiment-aggregator`  
**Status**: 🚧 In Development  
**Milestone**: M3 - Sentiment & Fusion

## Overview

The Sentiment Aggregator is responsible for:
- Combining multiple sentiment sources
- Time-weighted sentiment aggregation
- Impact scoring (High/Medium/Low)
- Providing aggregated sentiment to Fusion Agent

## Directory Structure

```
sentiment_aggregator/
├── __init__.py
├── agent.py              # Main agent class
├── interfaces.py         # Public interface definitions
├── aggregation/         # Aggregation logic
│   ├── __init__.py
│   ├── time_weighted.py
│   └── impact_scorer.py
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── mocks/
└── README.md            # This file
```

## Interface

### Requires

- Sentiment scores from LLM Sentiment Agent

### Provides

**Aggregated Sentiment**:
```python
{
    "symbol": "AAPL",
    "aggregated_sentiment": 0.68,  # -1.0 to +1.0
    "sentiment_label": "positive",
    "confidence": 0.82,
    "impact": "High",  # High, Medium, Low
    "news_count": 15,
    "time_weighted": True,
    "aggregated_at": "2024-01-15T10:30:00Z"
}
```

### API Endpoints

- `POST /api/v1/sentiment/aggregate` - Aggregate sentiment scores
- `GET /api/v1/sentiment/aggregated/{symbol}` - Get aggregated sentiment

## Development Tasks

### Phase 1: Core Structure
- [x] Set up agent class structure
- [x] Implement base agent interface
- [ ] Create directory structure
- [ ] Set up testing framework

### Phase 2: Aggregation Logic
- [ ] Implement multi-source combination
- [ ] Add time-weighted aggregation
- [ ] Add confidence calculation
- [ ] Write unit tests

### Phase 3: Impact Scoring
- [ ] Implement impact scoring (High/Medium/Low)
- [ ] Add news volume consideration
- [ ] Add recency weighting
- [ ] Write unit tests

## Dependencies

- pandas
- numpy

## Acceptance Criteria (Milestone 3)

- Sentiment Aggregator combines multiple sentiment sources
- Time-weighted aggregation functional
- Impact scoring operational (High/Medium/Low)
- Aggregated sentiment provided to Fusion Agent
- All agents integrated and communicating

## Notes

- Weight recent news more heavily
- Consider news volume in aggregation
- Impact scoring based on: sentiment strength, news volume, recency
- Provide clean interface for Fusion Agent

