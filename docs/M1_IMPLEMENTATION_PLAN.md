# M1 Implementation Plan (Revised)
## 6-Day Delivery Schedule with Component Extraction

**Date:** January 10, 2026  
**Payment:** $900 (15% of $6,000)

---

## Day 1: Infrastructure + Component Extraction

### Morning: Infrastructure Setup
```bash
# Create docker-compose.yml with TimescaleDB + Redis
# Set up database schema
# Configure environment variables
```

**Deliverables:**
- [ ] `docker-compose.yml` with TimescaleDB + Redis
- [ ] Database schema for `ohlcv_live` and `features_live` tables
- [ ] `.env.example` with configuration template
- [ ] `backend/infrastructure/database.py` - TimescaleDB connection
- [ ] `backend/infrastructure/cache.py` - Redis connection
- [ ] `backend/infrastructure/config.py` - Environment config

### Afternoon: Extract Client Components

**From `modules/swing_scalp_classifier.py`:**
```python
# Extract to: backend/agents/feature_agent/indicators/volatility.py
def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series
def calc_atr_percentile(df: pd.DataFrame, period: int = 14, lookback: int = 20) -> float

# Extract to: backend/agents/feature_agent/indicators/volume.py  
def calc_volume_ratio(df: pd.DataFrame, lookback: int = 20) -> float

# Extract to: backend/agents/feature_agent/indicators/time.py
def get_session_phase(timestamp: Optional[datetime] = None) -> str
```

**From `modules/level_exhaustion.py`:**
```python
# Extract to: backend/agents/feature_agent/indicators/momentum.py
def calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series
```

**From `signals/volume.py`:**
```python
# Extract to: backend/agents/feature_agent/indicators/volume.py
def tag_reversal_with_accel(df: pd.DataFrame, ...) -> pd.DataFrame
```

**From `analysis/spx_move_discovery.py`:**
```python
# Extract to: backend/agents/feature_agent/indicators/price.py
def calc_vwap(df: pd.DataFrame) -> pd.Series

# Extract PATTERN to: backend/agents/feature_agent/features.py
def engineer_base_features(df: pd.DataFrame) -> pd.DataFrame  # Adapt for our use
```

**Deliverables:**
- [ ] `backend/agents/feature_agent/indicators/__init__.py`
- [ ] `backend/agents/feature_agent/indicators/volatility.py` - ATR
- [ ] `backend/agents/feature_agent/indicators/momentum.py` - RSI
- [ ] `backend/agents/feature_agent/indicators/volume.py` - Volume features
- [ ] `backend/agents/feature_agent/indicators/trend.py` - MAs
- [ ] `backend/agents/feature_agent/indicators/price.py` - VWAP
- [ ] `backend/agents/feature_agent/indicators/time.py` - Session phase

---

## Day 2: Data Agent - Historical Pipeline

### Morning: yfinance Integration
```python
# backend/agents/data_agent/sources/yfinance_source.py
class YFinanceSource:
    def fetch_historical(self, symbol: str, start: date, end: date, interval: str) -> pd.DataFrame
    def fetch_quote(self, symbol: str) -> dict
```

### Afternoon: Alpha Vantage Fallback
```python
# backend/agents/data_agent/sources/alphavantage_source.py
class AlphaVantageSource:
    def fetch_historical(self, symbol: str, start: date, end: date, interval: str) -> pd.DataFrame
    def fetch_intraday(self, symbol: str, interval: str) -> pd.DataFrame
```

### Evening: Historical Data Agent
```python
# backend/agents/data_agent/historical.py
class HistoricalDataAgent:
    def __init__(self, primary_source: str = "yfinance")
    def fetch_historical(self, symbol: str, years: int = 2, timeframe: str = "daily") -> pd.DataFrame
    def backfill_ticker(self, symbol: str) -> BackfillResult
    def backfill_all(self, symbols: List[str]) -> Dict[str, BackfillResult]
    def validate_data(self, df: pd.DataFrame) -> ValidationResult
    def store_parquet(self, df: pd.DataFrame, path: Path)
    def store_timescale(self, df: pd.DataFrame)
```

**Deliverables:**
- [ ] `backend/agents/data_agent/sources/__init__.py`
- [ ] `backend/agents/data_agent/sources/yfinance_source.py`
- [ ] `backend/agents/data_agent/sources/alphavantage_source.py`
- [ ] `backend/agents/data_agent/historical.py`
- [ ] `backend/agents/data_agent/validation.py`
- [ ] Historical data fetched for AAPL, TSLA, MSFT, GOOGL, SPY (2+ years)
- [ ] Data stored in `storage/historical/raw/`

---

## Day 3: Data Agent - Inference Pipeline (Real-time)

### Morning: Real-time Data Agent
```python
# backend/agents/data_agent/realtime.py
class RealtimeDataAgent:
    def __init__(self, db: Database, cache: Cache)
    async def start_streaming(self, symbols: List[str], interval: str = "5m")
    async def stop_streaming(self)
    async def fetch_latest(self, symbol: str, bars: int = 100) -> pd.DataFrame
    def get_current_price(self, symbol: str) -> float
```

### Afternoon: Unified Data Agent Interface
```python
# backend/agents/data_agent/agent.py
class DataAgent:
    """Unified interface for both historical and real-time data"""
    
    def __init__(self, config: DataAgentConfig)
    
    # Historical methods
    def fetch_historical(self, symbol: str, **kwargs) -> pd.DataFrame
    def backfill(self, symbols: List[str]) -> Dict[str, BackfillResult]
    
    # Real-time methods  
    async def start_streaming(self, symbols: List[str])
    async def get_latest(self, symbol: str) -> pd.DataFrame
    
    # Shared methods
    def validate(self, df: pd.DataFrame) -> ValidationResult
    def health_check(self) -> HealthStatus
```

### Evening: Background Streaming Setup
```python
# backend/agents/data_agent/streaming.py
class StreamingManager:
    """Manages background data streaming"""
    def __init__(self, agent: RealtimeDataAgent)
    async def run_forever(self, symbols: List[str])
    async def update_once(self, symbols: List[str])
```

**Deliverables:**
- [ ] `backend/agents/data_agent/realtime.py`
- [ ] `backend/agents/data_agent/streaming.py`
- [ ] `backend/agents/data_agent/agent.py` (unified interface)
- [ ] Real-time streaming tested with 5-minute updates
- [ ] Data flowing into TimescaleDB

---

## Day 4: Feature Agent - Full Implementation

### Morning: Core Indicator Implementation
```python
# backend/agents/feature_agent/indicators/trend.py
class TrendIndicators:
    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series
    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series
    @staticmethod
    def macd(series: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]
    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> pd.Series
```

### Afternoon: Additional Indicators (20+ total)
```python
# Complete indicator set:
# Trend (5): SMA(20), SMA(50), SMA(200), EMA(9), EMA(21)
# Momentum (5): RSI(14), MACD, Stochastic %K, Stochastic %D, CCI
# Volatility (4): ATR(14), BB Upper, BB Lower, Historical Vol
# Volume (4): OBV, VWAP, Relative Volume, Volume MA
# Trend Strength (3): ADX, +DI, -DI
# Total: 21 indicators ✅
```

### Evening: Feature Agent Implementation
```python
# backend/agents/feature_agent/agent.py
class FeatureAgent:
    def __init__(self, config: FeatureAgentConfig)
    
    # Batch mode (historical)
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame
    def generate_feature_matrix(self, symbol: str) -> pd.DataFrame
    
    # Incremental mode (inference)
    def update_features(self, symbol: str, new_bar: pd.Series) -> Dict[str, float]
    def get_cached_features(self, symbol: str) -> Optional[Dict[str, float]]
    
    # Shared
    def health_check(self) -> HealthStatus
```

**Deliverables:**
- [ ] `backend/agents/feature_agent/indicators/trend.py`
- [ ] `backend/agents/feature_agent/indicators/momentum.py` (complete)
- [ ] `backend/agents/feature_agent/indicators/volatility.py` (complete)
- [ ] `backend/agents/feature_agent/indicators/volume.py` (complete)
- [ ] `backend/agents/feature_agent/agent.py`
- [ ] `backend/agents/feature_agent/features.py` (feature engineering)
- [ ] All 21+ indicators tested
- [ ] Feature generation < 2 seconds per ticker

---

## Day 5: API Foundation + Integration

### Morning: FastAPI Setup
```python
# backend/api/main.py
app = FastAPI(
    title="TICK API",
    description="Multi-Agent Stock Prediction System",
    version="1.0.0"
)

# Include routers
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(data_router, prefix="/api/v1/data", tags=["Data"])
app.include_router(features_router, prefix="/api/v1/features", tags=["Features"])
```

### Afternoon: API Endpoints
```python
# backend/api/routers/health.py
@router.get("/")
@router.get("/db")
@router.get("/cache")
@router.get("/agents")

# backend/api/routers/data.py
@router.get("/{symbol}/historical")
@router.get("/{symbol}/latest")
@router.post("/backfill")
@router.get("/{symbol}/validate")

# backend/api/routers/features.py
@router.get("/{symbol}")
@router.get("/{symbol}/indicators")
@router.get("/{symbol}/indicators/{indicator_name}")
```

### Evening: Integration Testing
```python
# Test all endpoints
# Verify < 500ms response time
# Test feature calculation < 2 seconds
```

**Deliverables:**
- [ ] `backend/api/main.py`
- [ ] `backend/api/routers/health.py`
- [ ] `backend/api/routers/data.py`
- [ ] `backend/api/routers/features.py`
- [ ] `backend/api/deps.py` (dependencies)
- [ ] API responding < 500ms
- [ ] Swagger documentation auto-generated

---

## Day 6: Documentation + Demo Prep

### Morning: Documentation
```markdown
# Create:
- backend/README.md
- backend/agents/data_agent/README.md
- backend/agents/feature_agent/README.md
- docs/ARCHITECTURE.md
- docs/API_REFERENCE.md
```

### Afternoon: CLI Tools
```python
# backend/cli.py
@click.group()
def cli():
    pass

@cli.command()
def backfill(symbols, years):
    """Backfill historical data"""

@cli.command()
def stream(symbols):
    """Start real-time streaming"""

@cli.command()
def features(symbol):
    """Calculate features for a symbol"""

@cli.command()
def validate(symbol):
    """Validate data quality"""
```

### Evening: Demo Script
```bash
#!/bin/bash
# demo.sh

# 1. Start services
docker-compose up -d

# 2. Show data backfill
python -m backend.cli backfill --symbols AAPL,TSLA,MSFT,GOOGL,SPY --years 2

# 3. Show data validation
python -m backend.cli validate --symbol AAPL

# 4. Start API
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 &

# 5. Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/data/AAPL/latest
curl http://localhost:8000/api/v1/features/AAPL

# 6. Show feature calculation timing
python -m backend.cli features --symbol AAPL --time
```

**Deliverables:**
- [ ] All README files
- [ ] CLI tool
- [ ] Demo script
- [ ] M1 ready for client demo

---

## 📁 Final Project Structure

```
backend/
├── agents/
│   ├── data_agent/
│   │   ├── __init__.py
│   │   ├── agent.py              # Unified interface
│   │   ├── historical.py         # Historical pipeline
│   │   ├── realtime.py          # Inference pipeline
│   │   ├── streaming.py         # Background streaming
│   │   ├── validation.py        # Data quality checks
│   │   ├── interfaces.py        # Type definitions
│   │   ├── README.md
│   │   └── sources/
│   │       ├── __init__.py
│   │       ├── yfinance_source.py
│   │       └── alphavantage_source.py
│   │
│   ├── feature_agent/
│   │   ├── __init__.py
│   │   ├── agent.py              # Unified interface
│   │   ├── features.py           # Feature engineering
│   │   ├── interfaces.py
│   │   ├── README.md
│   │   └── indicators/
│   │       ├── __init__.py
│   │       ├── trend.py          # SMA, EMA, MACD, ADX
│   │       ├── momentum.py       # RSI, Stochastic, CCI
│   │       ├── volatility.py     # ATR, Bollinger
│   │       ├── volume.py         # OBV, VWAP, RVol
│   │       ├── price.py          # Price-based features
│   │       └── time.py           # Session phase
│   │
│   └── [existing agents...]
│
├── infrastructure/
│   ├── __init__.py
│   ├── database.py               # TimescaleDB
│   ├── cache.py                  # Redis
│   └── config.py                 # Environment
│
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── deps.py
│   └── routers/
│       ├── __init__.py
│       ├── health.py
│       ├── data.py
│       └── features.py
│
├── storage/
│   └── historical/
│       ├── raw/                  # OHLCV parquet files
│       └── features/             # Feature parquet files
│
├── cli.py
├── requirements.txt
└── README.md

docker-compose.yml
.env.example
```

---

## ✅ M1 Acceptance Criteria Checklist

| Criteria | Target | How We Meet It |
|----------|--------|----------------|
| Historical data (2+ years) | 5 tickers | yfinance + parquet storage |
| Real-time streaming | 5-min updates | Background streaming + TimescaleDB |
| Technical indicators | 20+ | 21 indicators implemented |
| Data validation | >98% accuracy | Validation checks in Data Agent |
| Feature calculation | <2 sec/ticker | Optimized pandas operations |
| API latency | <500ms | FastAPI + Redis caching |
| Documentation | Complete | README + Swagger |

---

## 🗣️ Client Communication Script

### Day 1 Update:
> "Infrastructure is set up. I've extracted 8 core components from your existing codebase (ATR, RSI, VWAP, Volume Ratio, etc.) to ensure consistency."

### Day 3 Update:
> "Historical pipeline complete - 2+ years of data for all 5 tickers. Starting the inference (real-time) pipeline now."

### Day 5 Update:
> "API is live. All 21 indicators working. Response time under 500ms. Ready for demo tomorrow."

### Day 6 Demo:
> "Here's what M1 delivers:
> 1. Your existing indicator logic (extracted and cleaned)
> 2. NEW inference pipeline (streaming + caching)
> 3. NEW API layer (FastAPI + Swagger)
> 4. Clean historical vs inference separation"

