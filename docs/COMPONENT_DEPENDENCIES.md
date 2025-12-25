# Component Dependencies & Interfaces

This document defines the interfaces and dependencies between all agents in the multi-agent system based on the SoW.

## Interface Standards

All agents must implement the base agent interface defined in `backend/core/interfaces/base_agent.py`.

## Complete Agent List

1. **Data Agent** (Lead Developer - M1)
2. **Feature Agent** (Lead Developer - M1)
3. **Price Forecast Agent** (Developer 2 - M2)
4. **Trend Classification Agent** (Developer 2 - M2)
5. **Support/Resistance Agent** (Developer 2 - M2)
6. **News Fetch Agent** (Developer 1 - M3)
7. **LLM Sentiment Agent** (Developer 1 - M3)
8. **Sentiment Aggregator** (Developer 1 - M3)
9. **Fusion Agent** (Lead Developer - M3)
10. **Backtesting Agent** (Lead Developer - M4)
11. **Orchestrator** (Lead Developer - All)

---

## Component Specifications

### Data Agent

**Developer**: Lead Developer  
**Location**: `backend/agents/data_agent/`  
**Milestone**: M1

#### Provides

**Historical OHLCV Data**:
```python
{
    "symbol": "AAPL",
    "data": [
        {
            "timestamp": "2024-01-15T10:00:00Z",
            "open": 150.25,
            "high": 151.50,
            "low": 149.80,
            "close": 150.95,
            "volume": 1000000
        }
    ],
    "timeframe": "1h",
    "start_date": "2022-01-01",
    "end_date": "2024-01-15"
}
```

**Real-time Data**:
```python
{
    "symbol": "AAPL",
    "timestamp": "2024-01-15T10:30:00Z",
    "open": 150.25,
    "high": 151.50,
    "low": 149.80,
    "close": 150.95,
    "volume": 1000000,
    "timeframe": "5m"
}
```

#### API Endpoints

- `GET /api/v1/data/historical/{symbol}` - Get historical data
- `GET /api/v1/data/realtime/{symbol}` - Get real-time data
- `POST /api/v1/data/ingest` - Trigger data ingestion

---

### Feature Agent

**Developer**: Lead Developer  
**Location**: `backend/agents/feature_agent/`  
**Milestone**: M1

#### Requires

- OHLCV data from Data Agent

#### Provides

**Technical Indicators & Features**:
```python
{
    "symbol": "AAPL",
    "timestamp": "2024-01-15T10:30:00Z",
    "indicators": {
        "rsi": 58.5,
        "macd": 1.25,
        "bb_upper": 155.00,
        "bb_lower": 145.00,
        "sma_50": 148.00,
        "ema_20": 150.25
        # ... 20+ indicators
    },
    "features": {
        "returns_1d": 0.02,
        "volatility_30d": 0.15
    }
}
```

#### API Endpoints

- `GET /api/v1/features/{symbol}` - Get features for symbol
- `POST /api/v1/features/calculate` - Calculate features

---

### Price Forecast Agent

**Developer**: Developer 2  
**Location**: `backend/agents/price_forecast_agent/`  
**Milestone**: M2

#### Requires

- OHLCV data from Data Agent
- Features from Feature Agent

#### Provides

**Price Forecasts**:
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
            "horizon": "1d",
            "predicted_price": 152.30,
            "confidence": 0.65,
            "upper_bound": 155.00,
            "lower_bound": 149.50,
            "model": "lstm"
        }
    ],
    "predicted_at": "2024-01-15T10:30:00Z"
}
```

#### API Endpoints

- `GET /api/v1/forecast/{symbol}` - Get price forecasts
- `POST /api/v1/forecast/train` - Train models

---

### Trend Classification Agent

**Developer**: Developer 2  
**Location**: `backend/agents/trend_classification_agent/`  
**Milestone**: M2

#### Requires

- Features from Feature Agent
- OHLCV data from Data Agent

#### Provides

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

#### API Endpoints

- `GET /api/v1/trend/{symbol}` - Get trend classification
- `POST /api/v1/trend/train` - Train classifier

---

### Support/Resistance Agent

**Developer**: Developer 2  
**Location**: `backend/agents/support_resistance_agent/`  
**Milestone**: M2

#### Requires

- OHLCV data from Data Agent

#### Provides

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

#### API Endpoints

- `GET /api/v1/levels/{symbol}` - Get support/resistance levels
- `POST /api/v1/levels/detect` - Detect levels

---

### News Fetch Agent

**Developer**: Developer 1  
**Location**: `backend/agents/news_fetch_agent/`  
**Milestone**: M3

#### Provides

**News Articles**:
```python
{
    "symbol": "AAPL",
    "articles": [
        {
            "id": "article_123",
            "title": "Apple Reports Strong Q4 Earnings",
            "source": "Reuters",
            "published_at": "2024-01-15T10:00:00Z",
            "url": "https://...",
            "summary": "Apple Inc reported...",
            "relevance_score": 0.92
        }
    ],
    "fetched_at": "2024-01-15T10:30:00Z",
    "total_count": 15
}
```

#### API Endpoints

- `GET /api/v1/news/{symbol}` - Get news for symbol
- `POST /api/v1/news/fetch` - Trigger news fetch

---

### LLM Sentiment Agent

**Developer**: Developer 1  
**Location**: `backend/agents/llm_sentiment_agent/`  
**Milestone**: M3

#### Requires

- News articles from News Fetch Agent

#### Provides

**Sentiment Scores**:
```python
{
    "symbol": "AAPL",
    "article_id": "article_123",
    "sentiment_score": 0.75,  # -1.0 to +1.0
    "sentiment_label": "positive",
    "confidence": 0.85,
    "processed_at": "2024-01-15T10:30:00Z",
    "cached": False
}
```

#### API Endpoints

- `POST /api/v1/sentiment/analyze` - Analyze news sentiment
- `GET /api/v1/sentiment/cache/stats` - Get cache statistics

---

### Sentiment Aggregator

**Developer**: Developer 1  
**Location**: `backend/agents/sentiment_aggregator/`  
**Milestone**: M3

#### Requires

- Sentiment scores from LLM Sentiment Agent

#### Provides

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

#### API Endpoints

- `POST /api/v1/sentiment/aggregate` - Aggregate sentiment scores
- `GET /api/v1/sentiment/aggregated/{symbol}` - Get aggregated sentiment

---

### Fusion Agent

**Developer**: Lead Developer  
**Location**: `backend/agents/fusion_agent/`  
**Milestone**: M3

#### Requires

- Price forecasts from Price Forecast Agent
- Trend classification from Trend Classification Agent
- Support/resistance levels from Support/Resistance Agent
- Aggregated sentiment from Sentiment Aggregator

#### Provides

**Fused Trading Signal**:
```python
{
    "symbol": "AAPL",
    "signal": "BUY",  # BUY, SELL, or HOLD
    "confidence": 0.78,
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

#### API Endpoints

- `GET /api/v1/signals/{symbol}` - Get fused trading signal
- `POST /api/v1/signals/fuse` - Fuse signals for symbol

---

### Backtesting Agent

**Developer**: Lead Developer  
**Location**: `backend/agents/backtesting_agent/`  
**Milestone**: M4

#### Requires

- Historical OHLCV data from Data Agent
- Historical fused signals from Fusion Agent

#### Provides

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
    "backtested_at": "2024-01-15T10:30:00Z"
}
```

#### API Endpoints

- `POST /api/v1/backtest/run` - Run backtest
- `GET /api/v1/backtest/results/{symbol}` - Get backtest results

---

## Complete Data Flow

```
User Request
    ↓
Frontend (Lead Developer)
    ↓
Orchestrator (Lead Developer)
    ↓
    ├─→ Data Agent (Lead Developer - M1)
    │   └─→ OHLCV Data
    │       ├─→ Feature Agent (Lead Developer - M1)
    │       │   └─→ Technical Indicators
    │       │       ├─→ Price Forecast Agent (Developer 2 - M2)
    │       │       └─→ Trend Classification Agent (Developer 2 - M2)
    │       └─→ Support/Resistance Agent (Developer 2 - M2)
    │
    └─→ News Fetch Agent (Developer 1 - M3)
        └─→ News Articles
            └─→ LLM Sentiment Agent (Developer 1 - M3)
                └─→ Sentiment Scores
                    └─→ Sentiment Aggregator (Developer 1 - M3)
                        └─→ Aggregated Sentiment
    ↓
Fusion Agent (Lead Developer - M3)
    └─→ Combines all signals
        └─→ Fused Trading Signal
            └─→ Backtesting Agent (Lead Developer - M4)
                └─→ Performance Metrics
    ↓
Frontend displays results
```

## Mock Data

Each developer should create mock data matching their interface for:
- Independent development
- Testing
- Integration preparation

**Mock Data Location**: `backend/agents/[agent_name]/tests/mocks/`

## Versioning

Interfaces are versioned. Current version: **v1**

When breaking changes are needed:
1. Discuss with team
2. Create new version (v2)
3. Maintain backward compatibility during transition
4. Update this document

## Testing Integration

Before integration:
1. Ensure your component's tests pass
2. Verify interface matches this specification
3. Test with mock data from other components
4. Coordinate integration testing with Lead Developer

## Questions?

Contact Lead Developer for interface clarifications or changes.
