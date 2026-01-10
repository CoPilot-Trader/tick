# Client Repository Analysis & Extraction Plan
## CoPilot-Signals Repository → TICK Data Pipeline

**Date:** January 10, 2026  
**Branch:** `data-part-v1`  
**Goal:** Extract useful components for historical data pipeline without over-engineering

---

## 1. SOW Requirements for Data Pipeline (M1)

Based on the SoW, **Milestone 1: Foundation & Data Pipeline** requires:

| Requirement | SoW Deliverable | Priority |
|-------------|-----------------|----------|
| Historical data ingestion | 2+ years OHLCV for 3-5 tickers | HIGH |
| Data sources | yfinance, Alpha Vantage | HIGH |
| Timeframes | 5-minute, 1-hour, daily bars | HIGH |
| Technical indicators | 20+ indicators | HIGH |
| Feature engineering | Returns, volatility, MAs | HIGH |
| Data validation | >98% accuracy, quality checks | MEDIUM |
| Storage | TimescaleDB (or Parquet for MVP) | MEDIUM |
| Caching | Redis for performance | LOW |

---

## 2. Client Repository Overview

**Repository:** `copilot-signals`  
**Size:** ~15,000 files (includes venv, heavy with analysis notebooks)  
**Architecture:** Monolithic Python scripts, no clear agent abstraction

### Directory Structure
```
copilot-signals/
├── analysis/          # Analysis scripts (SPX discovery, VIX regimes)
├── discovery/         # Pattern discovery & clustering
├── docs/              # Documentation (schemas, architecture)
├── forward_test/      # Live scanners
├── modules/           # Core logic modules
│   ├── entry_timing.py
│   ├── exit_signals.py
│   ├── level_exhaustion.py
│   ├── swing_scalp_classifier.py
│   └── ...
├── scripts/           # ETL & backfill scripts
├── signals/           # Feature calculation modules
│   ├── indicators.py  # STUB - not implemented!
│   ├── volume.py      # Volume features
│   ├── levels.py      # STUB
│   └── ...
├── universal_data_loader.py
└── requirements.txt
```

---

## 3. What's USEFUL to Extract

### ✅ Recommended for Extraction

| Component | File | What It Does | Why Useful |
|-----------|------|--------------|------------|
| **ATR Calculation** | `modules/swing_scalp_classifier.py:103-116` | Clean ATR implementation | Standard indicator |
| **Volume Features** | `signals/volume.py` | RVol, acceleration, pivots | Feature engineering |
| **Level Calculation** | `modules/level_exhaustion.py:228-410` | MAs, swing points, session levels | Support/Resistance |
| **Data Schema** | `docs/DATA_LAKE_SCHEMA_STANDARD.md` | Schema conventions | Consistency |
| **Data Loading** | `universal_data_loader.py` | Multi-file parquet loading | Pattern reference |
| **Feature Engineering** | `analysis/spx_move_discovery.py:130-233` | 30+ features | Good feature list |
| **RSI Calculation** | `modules/level_exhaustion.py:747-759` | Standard RSI | Indicator |

### ❌ NOT Recommended (Out of Scope / Over-Engineering)

| Component | Reason |
|-----------|--------|
| `modules/entry_timing.py` | Trading execution logic, not needed for data pipeline |
| `modules/exit_signals.py` | Signal generation, not data ingestion |
| `discovery/*.py` | Pattern discovery, ML clustering - Phase 2+ |
| `forward_test/*.py` | Real-time scanners - Not in M1 scope |
| `scripts/build_embeddings.py` | NLP embeddings - Not needed |
| Tiingo API integration | They use Tiingo, we use yfinance/Alpha Vantage per SoW |

---

## 4. Feature List to Implement (SoW: 20+ indicators)

Based on client's `spx_move_discovery.py` and SOW requirements:

### Technical Indicators (Core 20)
1. **Moving Averages:** SMA(20), SMA(50), SMA(200), EMA(9), EMA(21)
2. **Momentum:** RSI(14), MACD(12,26,9), Stochastic(14,3)
3. **Volatility:** ATR(14), Bollinger Bands(20,2), Historical Volatility
4. **Volume:** OBV, VWAP, Relative Volume, Volume MA
5. **Trend:** ADX, Plus/Minus DI, Parabolic SAR

### Engineered Features (From Client's Discovery)
- Price position in N-bar range
- Bar range vs average
- Velocity/momentum (1,2,3,5-bar moves)
- Compression indicators
- Session-based features (time of day)
- VWAP distance

---

## 5. Implementation Strategy

### Phase 1: Data Agent (Week 1)

```python
# backend/agents/data_agent/agent.py

class DataAgent:
    """
    Data ingestion from yfinance (primary) and Alpha Vantage (fallback)
    
    Methods:
    - fetch_historical(symbol, start_date, end_date, timeframe)
    - validate_data_quality(df)
    - store_to_parquet(df, path)
    """
```

**Data Sources:**
- **yfinance:** Free, reliable, 2+ years history for daily/hourly
- **Alpha Vantage:** API key in .env, fallback for intraday

**Storage Format:**
- Parquet files (lightweight, fast, no DB dependency for MVP)
- Schema: `ticker, timeframe, bar_ts, open, high, low, close, volume`

### Phase 2: Feature Agent (Week 1-2)

```python
# backend/agents/feature_agent/agent.py

class FeatureAgent:
    """
    Calculate 20+ technical indicators
    
    Methods:
    - calculate_indicators(ohlcv_df) -> dict of indicators
    - engineer_features(ohlcv_df, indicators) -> feature DataFrame
    """
```

**Indicators to Extract from Client:**
- `calc_atr()` from `swing_scalp_classifier.py`
- `_calculate_rsi()` from `level_exhaustion.py`
- `_calculate_emas()` from `entry_timing.py`

**Indicators to Implement Fresh:**
- Use `pandas-ta` library (clean, maintained, no TA-Lib dependency issues)

---

## 6. What We WON'T Do (Scope Control)

Per the SoW and fixed-price nature:

| Feature | Status | Reason |
|---------|--------|--------|
| Tiingo integration | ❌ Skip | SoW specifies yfinance/Alpha Vantage |
| TimescaleDB | ❌ Skip for MVP | Parquet sufficient, add later |
| Real-time streaming | ⚠️ Basic only | Complex, save for M4 |
| Redis caching | ⚠️ Optional | Nice-to-have, not critical |
| Pattern discovery | ❌ Skip | Phase 2+ |
| Entry/Exit timing | ❌ Skip | Not data pipeline |

---

## 7. Extracted Code Snippets

### ATR (from client)
```python
def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    df = df.copy()
    df['prev_close'] = df['close'].shift(1).fillna(df['close'])
    hl = df['high'] - df['low']
    hpc = (df['high'] - df['prev_close']).abs()
    lpc = (df['low'] - df['prev_close']).abs()
    tr = pd.concat([hl, hpc, lpc], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()
```

### RSI (from client)
```python
def calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
```

### Volume Features (from client)
```python
def calc_relative_volume(df: pd.DataFrame, lookback: int = 20) -> pd.Series:
    return df['volume'] / df['volume'].rolling(lookback, min_periods=3).mean()

def calc_volume_acceleration(df: pd.DataFrame, ema_span: int = 5) -> pd.Series:
    vol_ema = df['volume'].ewm(span=ema_span, adjust=False).mean()
    return vol_ema.diff()
```

---

## 8. Recommended Dependencies

```txt
# Data
pandas>=2.0.0
numpy>=1.24.0
pyarrow>=14.0.0  # Parquet support

# Data Sources
yfinance>=0.2.36
alpha_vantage>=2.3.1

# Indicators (cleaner than TA-Lib)
pandas-ta>=0.3.14b

# Validation
pydantic>=2.0.0
```

---

## 9. Next Steps

1. **Implement Data Agent** with yfinance/Alpha Vantage
2. **Implement Feature Agent** with pandas-ta + extracted helpers
3. **Create data validation** quality checks
4. **Test pipeline** with 3-5 tickers (AAPL, TSLA, MSFT, GOOGL, SPY)
5. **Store as Parquet** files for training

---

## 10. File References

Key files from client repo for reference:
- `/tick/_client-repo/modules/swing_scalp_classifier.py` - ATR, volume helpers
- `/tick/_client-repo/modules/level_exhaustion.py` - Levels, RSI, EMA
- `/tick/_client-repo/signals/volume.py` - Volume features
- `/tick/_client-repo/analysis/spx_move_discovery.py` - Feature engineering patterns
- `/tick/_client-repo/docs/DATA_LAKE_SCHEMA_STANDARD.md` - Schema reference

