# Team Collaboration Guide

## Team Members & Responsibilities

### Lead Developer
**Role**: Project Lead, Prototyping, Frontend Development, Backend Integration, Agent Orchestration
**Primary Areas**:
- Frontend development (Next.js/TypeScript)
- Backend API design and integration
- Agent orchestration and coordination
- Code review and merge management
- Overall system architecture
- Data Agent, Feature Agent, Fusion Agent, Backtesting Agent, Orchestrator

**Working Directories**:
- `frontend/` - Full access
- `backend/api/` - API endpoints and orchestration
- `backend/core/` - Core system components
- `backend/agents/orchestrator/` - Agent coordination
- `backend/agents/data_agent/` - Data ingestion (M1)
- `backend/agents/feature_agent/` - Technical indicators (M1)
- `backend/agents/fusion_agent/` - Signal fusion (M3)
- `backend/agents/backtesting_agent/` - Backtesting (M4)

---

### Developer 1: News & Sentiment Agents
**Role**: News Collection and Sentiment Analysis
**Primary Areas**:
- News data collection from multiple sources
- LLM-based sentiment analysis (GPT-4)
- Sentiment aggregation
- Semantic caching for cost optimization

**Working Directories**:
- `backend/agents/news_fetch_agent/` - News collection (M3)
- `backend/agents/llm_sentiment_agent/` - GPT-4 sentiment (M3)
- `backend/agents/sentiment_aggregator/` - Sentiment aggregation (M3)

**Branches**:
- `feature/news-fetch-agent`
- `feature/llm-sentiment-agent`
- `feature/sentiment-aggregator`

**Dependencies**:
- Requires: None (standalone agents)
- Provides: News articles, sentiment scores, aggregated sentiment
- Interfaces: See individual agent READMEs

**Deliverables**:
- News Fetch Agent: Multi-source news collection
- LLM Sentiment Agent: GPT-4 sentiment analysis with semantic caching
- Sentiment Aggregator: Multi-source sentiment combination
- API endpoints for all components
- Unit tests

---

### Developer 2: Prediction & Analysis Agents
**Role**: Price Prediction, Trend Classification, Support/Resistance
**Primary Areas**:
- Multi-horizon price forecasting (Prophet + LSTM)
- Trend classification (LightGBM/XGBoost)
- Support/resistance level detection
- Model training and validation

**Working Directories**:
- `backend/agents/price_forecast_agent/` - Price predictions (M2)
- `backend/agents/trend_classification_agent/` - Trend signals (M2)
- `backend/agents/support_resistance_agent/` - Level detection (M2)

**Branches**:
- `feature/price-forecast-agent`
- `feature/trend-classification-agent`
- `feature/support-resistance-agent`

**Dependencies**:
- Requires: OHLCV data (Data Agent), Features (Feature Agent)
- Provides: Price forecasts, trend signals, support/resistance levels
- Interfaces: See individual agent READMEs

**Deliverables**:
- Price Forecast Agent: Multi-horizon predictions (1h, 4h, 1d, 1w)
- Trend Classification Agent: BUY/SELL/HOLD signals
- Support/Resistance Agent: Key price levels with strength scores
- Model training pipelines
- API endpoints for all components
- Unit tests

---

## Component Dependencies

### Dependency Graph

```
┌─────────────────┐
│   Data Agent    │ (Lead Developer - M1)
│   (OHLCV Data)  │
└────────┬────────┘
         │
         ├─→ Feature Agent (Lead Developer - M1)
         │   └─→ Technical Indicators
         │
         ├─→ Price Forecast Agent (Developer 2 - M2)
         ├─→ Trend Classification Agent (Developer 2 - M2)
         └─→ Support/Resistance Agent (Developer 2 - M2)
         
┌─────────────────┐
│ News Fetch      │ (Developer 1 - M3)
│ Agent           │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Sentiment   │ (Developer 1 - M3)
│ Agent (GPT-4)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Sentiment       │ (Developer 1 - M3)
│ Aggregator      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fusion Agent   │ (Lead Developer - M3)
│                 │
└────────┬────────┘
         │ Combines all signals
         │
         ▼
┌─────────────────┐
│ Backtesting     │ (Lead Developer - M4)
│ Agent           │
└─────────────────┘
```

### Milestone Breakdown

**M1 - Foundation & Data Pipeline** (Weeks 1-2)
- Lead Developer: Data Agent, Feature Agent

**M2 - Core Prediction Models** (Weeks 3-5)
- Developer 2: Price Forecast Agent, Trend Classification Agent, Support/Resistance Agent

**M3 - Sentiment & Fusion** (Weeks 6-7)
- Developer 1: News Fetch Agent, LLM Sentiment Agent, Sentiment Aggregator
- Lead Developer: Fusion Agent

**M4 - Backtesting & Integration** (Weeks 8-9)
- Lead Developer: Backtesting Agent, System Integration

## Communication Protocol

### Daily Standups
- Brief updates on progress
- Blockers and dependencies
- Interface changes
- Milestone progress

### Code Review Process
1. Create PR from feature branch
2. Request review from Lead Developer
3. Address feedback
4. Lead Developer merges to `main`

### Dependency Communication

If your component requires data/output from another component:

1. **Check the Interface**: Review the providing component's README for interface definition
2. **Use Mock Data**: Develop with mock data matching the interface
3. **Coordinate**: Communicate with the providing developer about timeline
4. **Integration**: Test integration once the providing component is ready

## Working Guidelines

### DO ✅
- Work only in your assigned directory
- Follow the established code style
- Write unit tests for your components
- Update your component's README as you develop
- Communicate interface changes early
- Use the standard logging framework
- Follow the error handling patterns
- Track milestone progress

### DON'T ❌
- Modify other developers' code without permission
- Push directly to `main` branch
- Change interfaces without team discussion
- Skip code reviews
- Ignore linting errors
- Commit sensitive data (API keys, passwords)
- Miss milestone deadlines without communication

## Progress Tracking

Each developer should maintain:
- Component README with current status
- List of completed features
- Known issues and TODOs
- Integration points ready for testing
- Milestone progress tracking

## Milestone Responsibilities

### Developer 1 (M3)
- News Fetch Agent: Collect news from 2+ sources
- LLM Sentiment Agent: GPT-4 integration with 60%+ cache hit rate
- Sentiment Aggregator: Multi-source combination

### Developer 2 (M2)
- Price Forecast Agent: Multi-horizon predictions (1h, 4h, 1d, 1w)
- Trend Classification Agent: >55% accuracy target
- Support/Resistance Agent: 3-5 levels per ticker, >60% validation

### Lead Developer
- M1: Data Agent, Feature Agent
- M3: Fusion Agent
- M4: Backtesting Agent, System Integration
- All Milestones: Orchestrator, API, Frontend

## Questions?

Contact the Lead Developer for:
- Architecture decisions
- Interface clarifications
- Dependency coordination
- Code review requests
- Milestone planning
