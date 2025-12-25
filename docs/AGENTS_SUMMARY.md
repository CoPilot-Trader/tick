# Agents Summary

Complete list of all agents created based on the SoW (Scope of Work) document.

## Total Agents: 10

### Milestone 1: Foundation & Data Pipeline (Weeks 1-2)

1. **Data Agent** (`backend/agents/data_agent/`)
   - **Developer**: Lead Developer
   - **Purpose**: Ingests and manages historical and real-time OHLCV data
   - **Key Features**: 
     - Historical data ingestion (2+ years)
     - Real-time data streaming (5-minute, 1-hour, daily bars)
     - Data validation and quality checks
     - TimescaleDB storage

2. **Feature Agent** (`backend/agents/feature_agent/`)
   - **Developer**: Lead Developer
   - **Purpose**: Computes technical indicators and engineered features
   - **Key Features**:
     - 20+ technical indicators (TA-Lib integration)
     - Feature engineering (returns, volatility, moving averages)
     - Feature caching mechanism

### Milestone 2: Core Prediction Models (Weeks 3-5)

3. **Price Forecast Agent** (`backend/agents/price_forecast_agent/`)
   - **Developer**: Developer 2
   - **Purpose**: Multi-horizon price prediction
   - **Key Features**:
     - Prophet model (baseline)
     - LSTM model (primary)
     - Multi-horizon: 1h, 4h, 1d, 1w
     - Confidence intervals
     - Walk-forward validation

4. **Trend Classification Agent** (`backend/agents/trend_classification_agent/`)
   - **Developer**: Developer 2
   - **Purpose**: Directional signals (BUY/SELL/HOLD)
   - **Key Features**:
     - LightGBM/XGBoost classifier
     - Multi-timeframe support (1h, 1d)
     - Probability scores
     - Target: >55% accuracy

5. **Support/Resistance Agent** (`backend/agents/support_resistance_agent/`)
   - **Developer**: Developer 2
   - **Purpose**: Identifies key price levels
   - **Key Features**:
     - DBSCAN clustering
     - Local extrema detection
     - Strength scoring (0-100)
     - Target: 3-5 levels per ticker, >60% validation

### Milestone 3: Sentiment & Fusion (Weeks 6-7)

6. **News Fetch Agent** (`backend/agents/news_fetch_agent/`)
   - **Developer**: Developer 1
   - **Purpose**: Collects financial news from multiple sources
   - **Key Features**:
     - Finnhub, NewsAPI, Alpha Vantage integration
     - News filtering and relevance scoring
     - Historical and real-time news collection

7. **LLM Sentiment Agent** (`backend/agents/llm_sentiment_agent/`)
   - **Developer**: Developer 1
   - **Purpose**: Processes news using GPT-4 for sentiment scoring
   - **Key Features**:
     - GPT-4 API integration
     - Sentiment scoring (-1 to +1 scale)
     - Semantic caching (60%+ cache hit rate target)
     - Cost optimization

8. **Sentiment Aggregator** (`backend/agents/sentiment_aggregator/`)
   - **Developer**: Developer 1
   - **Purpose**: Combines multiple sentiment outputs
   - **Key Features**:
     - Multi-source sentiment combination
     - Time-weighted aggregation
     - Impact scoring (High/Medium/Low)

9. **Fusion Agent** (`backend/agents/fusion_agent/`)
   - **Developer**: Lead Developer
   - **Purpose**: Combines all predictions into unified trading signals
   - **Key Features**:
     - Rule-based signal fusion
     - Weighted combination of all signals
     - Final BUY/SELL/HOLD signal generation
     - Confidence score calculation

### Milestone 4: Backtesting & Integration (Weeks 8-9)

10. **Backtesting Agent** (`backend/agents/backtesting_agent/`)
    - **Developer**: Lead Developer
    - **Purpose**: Simulates historical performance with PnL metrics
    - **Key Features**:
      - Historical simulation engine
      - Trade execution logic
      - Performance metrics (PnL, Sharpe ratio, drawdown, win rate)
      - Walk-forward validation framework

## Additional Components

11. **Orchestrator** (`backend/agents/orchestrator/`)
    - **Developer**: Lead Developer
    - **Purpose**: Coordinates all agents and manages workflow
    - **Key Features**:
      - Agent initialization
      - Workflow coordination
      - Error handling
      - Result aggregation

## Agent Structure

Each agent follows this structure:
```
agent_name/
├── __init__.py
├── agent.py              # Main agent class (implements BaseAgent)
├── interfaces.py         # Public interface definitions (Pydantic models)
├── README.md            # Component documentation
├── [subdirectories]/    # Agent-specific modules
└── tests/               # Unit tests
    ├── __init__.py
    ├── test_agent.py
    └── mocks/           # Mock data
```

## Interface Standards

All agents:
- Implement `BaseAgent` interface from `backend/core/interfaces/base_agent.py`
- Provide `initialize()`, `process()`, and `health_check()` methods
- Define public interfaces using Pydantic models in `interfaces.py`
- Include comprehensive README with development tasks
- Have unit tests in `tests/` directory

## Dependencies Flow

```
Data Agent → Feature Agent
    ↓
    ├─→ Price Forecast Agent
    ├─→ Trend Classification Agent
    └─→ Support/Resistance Agent

News Fetch Agent → LLM Sentiment Agent → Sentiment Aggregator

All Agents → Fusion Agent → Backtesting Agent
```

## Next Steps

1. Each developer should review their assigned agents' READMEs
2. Set up development environment
3. Begin implementation following the milestone schedule
4. Use mock data for independent development
5. Coordinate integration testing with Lead Developer

## References

- [SoW Document](../docs/SoW_Multi_Agent_Stock_Prediction_System_v2.pdf)
- [Team Guide](../TEAM.md)
- [Component Dependencies](./COMPONENT_DEPENDENCIES.md)
- [Getting Started](./GETTING_STARTED.md)

