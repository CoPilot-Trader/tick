# Milestone 1 Delivery Plan
## Foundation & Data Pipeline - $900 (15%)

**Date:** January 10, 2026  
**Branch:** `data-part-v1`  
**Objective:** Deliver M1 with clean separation of Historical vs Inference pipelines

---

## 🎯 Strategic Approach

### The Two-Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        TICK DATA ARCHITECTURE                                │
├─────────────────────────────────────┬───────────────────────────────────────┤
│      HISTORICAL PIPELINE            │       INFERENCE PIPELINE              │
│      (Training / Batch)             │       (Real-time / Live)              │
├─────────────────────────────────────┼───────────────────────────────────────┤
│                                     │                                       │
│  ┌─────────────────────────┐        │  ┌─────────────────────────┐          │
│  │  Historical Data Agent  │        │  │  Real-time Data Agent   │          │
│  │  - Batch OHLCV fetch    │        │  │  - 5-min streaming      │          │
│  │  - 2+ years history     │        │  │  - WebSocket updates    │          │
│  │  - yfinance/AlphaVantage│        │  │  - Live price feeds     │          │
│  └───────────┬─────────────┘        │  └───────────┬─────────────┘          │
│              │                      │              │                        │
│              ▼                      │              ▼                        │
│  ┌─────────────────────────┐        │  ┌─────────────────────────┐          │
│  │  Feature Agent (Batch)  │        │  │  Feature Agent (Live)   │          │
│  │  - 20+ indicators       │        │  │  - Same indicators      │          │
│  │  - Full history calc    │        │  │  - Incremental calc     │          │
│  │  - Feature store        │        │  │  - Redis cache          │          │
│  └───────────┬─────────────┘        │  └───────────┬─────────────┘          │
│              │                      │              │                        │
│              ▼                      │              ▼                        │
│  ┌─────────────────────────┐        │  ┌─────────────────────────┐          │
│  │   Storage (Parquet)     │        │  │   Storage (TimescaleDB) │          │
│  │  - Training datasets    │        │  │  - Live time-series     │          │
│  │  - Feature matrices     │        │  │  - Query-optimized      │          │
│  └─────────────────────────┘        │  └─────────────────────────┘          │
│                                     │              │                        │
│  Used for: Model Training           │              ▼                        │
│  (Client has existing work here)    │  ┌─────────────────────────┐          │
│                                     │  │   Prediction Agents     │          │
│                                     │  │  - News Agent ✅ READY  │          │
│                                     │  │  - Price Forecast       │          │
│                                     │  │  - Trend Classification │          │
│                                     │  └─────────────────────────┘          │
│                                     │                                       │
│                                     │  Used for: Live Predictions           │
│                                     │  (We are building this)               │
└─────────────────────────────────────┴───────────────────────────────────────┘
```

---

## 📋 M1 Deliverables Mapping

| SoW Requirement | Historical Pipeline | Inference Pipeline | Status |
|-----------------|--------------------|--------------------|--------|
| Dev Environment (Docker, DB, Redis) | ✅ Shared | ✅ Shared | TO BUILD |
| Historical data ingestion (2+ years) | ✅ Primary | Reference only | TO BUILD |
| Real-time streaming (5-min bars) | N/A | ✅ Primary | TO BUILD |
| 20+ Technical indicators | ✅ Batch mode | ✅ Incremental mode | TO BUILD |
| Data validation | ✅ Batch | ✅ Live | TO BUILD |
| TimescaleDB storage | Archive | ✅ Primary | TO BUILD |
| Redis caching | N/A | ✅ Feature cache | TO BUILD |
| FastAPI endpoints | Health check | ✅ Full API | TO BUILD |

---

## 🏗️ Implementation Plan

### Phase 1: Shared Infrastructure (Day 1-2)

**1.1 Docker Environment**
```yaml
# docker-compose.yml
services:
  postgres:
    image: timescale/timescaledb:latest-pg15
    # TimescaleDB for time-series storage
    
  redis:
    image: redis:7-alpine
    # Feature caching for inference
    
  backend:
    build: ./backend
    # FastAPI application
```

**1.2 Database Schema**
```sql
-- Inference pipeline tables (TimescaleDB)
CREATE TABLE ohlcv_live (
    ticker VARCHAR(10),
    timeframe VARCHAR(10),
    bar_ts TIMESTAMPTZ,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume BIGINT,
    PRIMARY KEY (ticker, timeframe, bar_ts)
);
SELECT create_hypertable('ohlcv_live', 'bar_ts');

-- Features table
CREATE TABLE features_live (
    ticker VARCHAR(10),
    timeframe VARCHAR(10),
    bar_ts TIMESTAMPTZ,
    features JSONB,  -- Flexible feature storage
    PRIMARY KEY (ticker, timeframe, bar_ts)
);
SELECT create_hypertable('features_live', 'bar_ts');
```

**1.3 Project Structure**
```
backend/
├── agents/
│   ├── data_agent/
│   │   ├── historical.py      # Historical pipeline (batch)
│   │   ├── realtime.py        # Inference pipeline (live)
│   │   ├── interfaces.py
│   │   └── agent.py           # Unified interface
│   │
│   ├── feature_agent/
│   │   ├── indicators.py      # Shared indicator calculations
│   │   ├── batch.py           # Historical feature generation
│   │   ├── incremental.py     # Live feature updates
│   │   └── agent.py
│   │
├── infrastructure/
│   ├── database.py            # TimescaleDB connection
│   ├── cache.py               # Redis connection
│   └── config.py              # Environment config
│
├── api/
│   ├── main.py
│   └── routers/
│       ├── health.py          # Health check endpoints
│       ├── data.py            # Data endpoints
│       └── features.py        # Feature endpoints
│
└── storage/
    └── historical/            # Parquet files for training data
        ├── raw/
        └── features/
```

---

### Phase 2: Historical Pipeline (Day 2-3)

**Purpose:** Satisfy M1 requirement for "2+ years historical data"

**2.1 Historical Data Agent**
```python
# backend/agents/data_agent/historical.py

class HistoricalDataAgent:
    """
    Batch data ingestion for training pipeline.
    
    - Fetches 2+ years of OHLCV data
    - Stores as Parquet (training) + TimescaleDB (reference)
    - Runs on-demand or scheduled
    """
    
    def fetch_historical(
        self, 
        symbol: str, 
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1d"
    ) -> pd.DataFrame:
        """Fetch historical data from yfinance/Alpha Vantage"""
        
    def validate_data(self, df: pd.DataFrame) -> ValidationResult:
        """Validate data quality (>98% accuracy requirement)"""
        
    def store_parquet(self, df: pd.DataFrame, path: Path):
        """Store for training pipeline"""
        
    def store_timescale(self, df: pd.DataFrame):
        """Store in TimescaleDB for reference"""
```

**2.2 Deliverable Output**
```
storage/historical/
├── raw/
│   ├── AAPL/
│   │   ├── daily_2022-01-01_2026-01-10.parquet
│   │   ├── hourly_2024-01-01_2026-01-10.parquet
│   │   └── 5min_2025-11-01_2026-01-10.parquet
│   ├── TSLA/
│   ├── MSFT/
│   ├── GOOGL/
│   └── SPY/
└── features/
    └── ... (generated features for training)
```

**Client's Existing Work Reference:**
- Their `universal_data_loader.py` shows how to load multi-file parquet
- Their schema conventions from `DATA_LAKE_SCHEMA_STANDARD.md`
- We can reference their approach but build our own clean implementation

---

### Phase 3: Inference Pipeline (Day 3-4)

**Purpose:** Real-time data for live predictions (NEW - client hasn't built this)

**3.1 Real-time Data Agent**
```python
# backend/agents/data_agent/realtime.py

class RealtimeDataAgent:
    """
    Live data streaming for inference pipeline.
    
    - 5-minute update cycle
    - Stores in TimescaleDB
    - Triggers feature recalculation
    """
    
    async def start_streaming(self, symbols: List[str]):
        """Start real-time data collection"""
        
    async def fetch_latest(self, symbol: str, timeframe: str) -> pd.DataFrame:
        """Get latest bars for inference"""
        
    def get_realtime_quote(self, symbol: str) -> Quote:
        """Get current price (for immediate inference)"""
```

**3.2 Integration with News Agent**
```python
# The inference pipeline connects to existing news agents
from agents.news_fetch_agent import NewsFetchAgent
from agents.llm_sentiment_agent import LLMSentimentAgent

# Real-time data flows:
# 1. Price data (from RealtimeDataAgent) 
# 2. News data (from NewsFetchAgent - ALREADY BUILT)
# 3. Features (from FeatureAgent)
# → All feed into prediction agents
```

---

### Phase 4: Feature Agent (Day 4-5)

**Purpose:** Calculate 20+ technical indicators (shared between pipelines)

**4.1 Indicator Implementation**
```python
# backend/agents/feature_agent/indicators.py

class TechnicalIndicators:
    """
    Shared indicator calculations.
    Used by both historical and inference pipelines.
    """
    
    # Trend Indicators
    def sma(self, series: pd.Series, period: int) -> pd.Series
    def ema(self, series: pd.Series, period: int) -> pd.Series
    def macd(self, series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]
    
    # Momentum Indicators
    def rsi(self, series: pd.Series, period: int = 14) -> pd.Series
    def stochastic(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]
    def cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series
    
    # Volatility Indicators
    def atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series
    def bollinger_bands(self, series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]
    def historical_volatility(self, series: pd.Series) -> pd.Series
    
    # Volume Indicators
    def obv(self, df: pd.DataFrame) -> pd.Series
    def vwap(self, df: pd.DataFrame) -> pd.Series
    def relative_volume(self, df: pd.DataFrame) -> pd.Series
    
    # Trend Strength
    def adx(self, df: pd.DataFrame) -> pd.Series
    def plus_di(self, df: pd.DataFrame) -> pd.Series
    def minus_di(self, df: pd.DataFrame) -> pd.Series
```

**4.2 Full 20+ Indicator List**
| # | Indicator | Category | Implementation |
|---|-----------|----------|----------------|
| 1 | SMA(20) | Trend | pandas rolling |
| 2 | SMA(50) | Trend | pandas rolling |
| 3 | SMA(200) | Trend | pandas rolling |
| 4 | EMA(9) | Trend | pandas ewm |
| 5 | EMA(21) | Trend | pandas ewm |
| 6 | RSI(14) | Momentum | Custom (from client) |
| 7 | MACD | Momentum | pandas ewm |
| 8 | Stochastic %K | Momentum | Custom |
| 9 | Stochastic %D | Momentum | Custom |
| 10 | ATR(14) | Volatility | Custom (from client) |
| 11 | Bollinger Upper | Volatility | pandas rolling |
| 12 | Bollinger Lower | Volatility | pandas rolling |
| 13 | Historical Vol | Volatility | pandas rolling std |
| 14 | OBV | Volume | cumsum |
| 15 | VWAP | Volume | Custom |
| 16 | Relative Volume | Volume | Custom (from client) |
| 17 | ADX | Trend Strength | pandas-ta |
| 18 | +DI | Trend Strength | pandas-ta |
| 19 | -DI | Trend Strength | pandas-ta |
| 20 | CCI | Momentum | pandas-ta |
| 21 | Williams %R | Momentum | Custom |
| 22 | MFI | Volume | Custom |

---

### Phase 5: API Foundation (Day 5-6)

**5.1 FastAPI Structure**
```python
# backend/api/main.py

app = FastAPI(title="TICK API", version="1.0.0")

# Health endpoints
@app.get("/health")
@app.get("/health/db")
@app.get("/health/cache")

# Data endpoints
@app.get("/api/v1/data/{symbol}/historical")
@app.get("/api/v1/data/{symbol}/latest")
@app.post("/api/v1/data/backfill")

# Feature endpoints
@app.get("/api/v1/features/{symbol}")
@app.get("/api/v1/features/{symbol}/indicators")
```

**5.2 Performance Target**
- API response < 500ms ✅
- Feature calculation < 2 seconds per ticker ✅

---

## 📦 M1 Deliverables Checklist

### Development Environment Setup
- [ ] Docker Compose with TimescaleDB + Redis
- [ ] Environment configuration (.env template)
- [ ] Database schema migrations
- [ ] Development setup documentation

### Data Agent Implementation
- [ ] Historical data ingestion (yfinance primary, Alpha Vantage fallback)
- [ ] 2+ years data for: AAPL, TSLA, MSFT, GOOGL, SPY
- [ ] Real-time streaming capability (5-min bars)
- [ ] Data validation (>98% accuracy checks)
- [ ] TimescaleDB storage

### Feature Agent Foundation
- [ ] 20+ technical indicators implemented
- [ ] Batch calculation for historical data
- [ ] Incremental calculation for live data
- [ ] Redis caching for inference features

### API Foundation
- [ ] FastAPI project structure
- [ ] Health check endpoints
- [ ] Data retrieval endpoints
- [ ] Feature calculation endpoints
- [ ] Error handling framework

### Documentation
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Development environment guide
- [ ] Data pipeline architecture doc

---

## 🔗 How This Connects to Client's Existing Work

### What We Reference (Not Copy)
| Client's Work | Our Approach |
|---------------|--------------|
| `universal_data_loader.py` | Inspired our parquet loading pattern |
| `DATA_LAKE_SCHEMA_STANDARD.md` | Referenced for schema consistency |
| `calc_atr()` from modules | Extracted and cleaned up |
| `_calculate_rsi()` from modules | Extracted and cleaned up |
| Volume features from signals | Adapted for our use |

### What Client Can Do With Their Historical Work
- Client's existing `copilot-signals` repo handles their historical training pipeline
- Our M1 delivers the **foundation** that can work with their data OR our data
- The **inference pipeline** is entirely new (client hasn't built this)

### Clean Separation
```
Client's Repo (copilot-signals)     Our Repo (tick)
────────────────────────────────    ────────────────────────────────
Historical data collection          Historical + Inference pipelines
Pattern discovery                   Data Agent (both modes)
Training data generation            Feature Agent (both modes)
                                    API Foundation ← NEW
                                    Inference Pipeline ← NEW
                                    News Agent ← DONE
```

---

## 📊 Demo for M1 Acceptance

### What to Show Client
1. **Docker environment running** (TimescaleDB + Redis + API)
2. **Historical data loaded** (2+ years for 5 tickers)
3. **Real-time updates working** (show 5-min bars updating)
4. **20+ indicators calculated** (show feature DataFrame)
5. **API responding** (Swagger UI with < 500ms response)
6. **Data quality report** (show >98% validation)

### Sample Demo Script
```bash
# 1. Start environment
docker-compose up -d

# 2. Run historical backfill
python -m backend.agents.data_agent.cli backfill --symbols AAPL,TSLA,MSFT,GOOGL,SPY

# 3. Show data quality
python -m backend.agents.data_agent.cli validate --symbol AAPL

# 4. Start real-time streaming
python -m backend.agents.data_agent.cli stream --symbols AAPL,TSLA

# 5. Calculate features
python -m backend.agents.feature_agent.cli calculate --symbol AAPL

# 6. Test API
curl http://localhost:8000/api/v1/data/AAPL/latest
curl http://localhost:8000/api/v1/features/AAPL
```

---

## ⏱️ Timeline

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Docker + DB setup | Infrastructure running |
| 2 | Historical Data Agent | 2+ years data fetched |
| 3 | Real-time Data Agent | 5-min streaming working |
| 4 | Feature Agent (indicators) | 20+ indicators working |
| 5 | API endpoints | FastAPI responding |
| 6 | Testing + Documentation | M1 ready for demo |

---

## 💡 Key Points for Client Communication

### What You're Delivering
> "M1 provides the **foundation** for both training and inference. The Data Agent can fetch historical data for model training AND stream real-time data for live predictions. This architecture allows you to leverage your existing historical work while we build the inference pipeline you need."

### How It Connects to Their Work
> "Your existing copilot-signals repository has excellent historical data engineering. Our M1 Data Agent is designed to either **work with your existing data** OR **fetch fresh data** - giving you flexibility. The Feature Agent uses the same indicator calculations, ensuring consistency."

### The Value-Add
> "What's NEW in M1 is the **inference pipeline foundation** - the real-time streaming, Redis caching, and API layer that your existing repo doesn't have. This is what enables live predictions."

---

## Next Steps

1. **Approve this plan** → I'll start implementation
2. **Clarify any requirements** → Adjust before building
3. **Start Phase 1** → Docker + infrastructure setup

