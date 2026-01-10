# Client Component Mapping
## What We Use vs What We Don't Use

**Date:** January 10, 2026  
**Client Repo:** `_client-repo/` (copilot-signals)  
**Purpose:** Identify extractable components for M1 delivery

---

## 🔍 Key Discovery: Their Indicators Are STUBS!

**Important Finding:** The file `signals/indicators.py` contains only function signatures:
```python
def ema(series, n): ...
def atr(df, n=14): ...
def vwap(df): ...
def rel_volume(df, window=20): ...
```

**The REAL implementations are scattered across:**
- `modules/swing_scalp_classifier.py` → ATR, Volume Ratio, Session Phase
- `modules/level_exhaustion.py` → RSI, EMAs, Level calculations
- `analysis/spx_move_discovery.py` → Feature engineering, VWAP
- `signals/volume.py` → Volume features

---

## ✅ Components We WILL Use

### 1. ATR (Average True Range)
**Source:** `modules/swing_scalp_classifier.py:103-116`
**Use Case:** Both Historical & Inference

```python
# EXTRACTING THIS:
def calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    df = df.copy()
    df['prev_close'] = df['close'].shift(1)
    df['prev_close'] = df['prev_close'].fillna(df['close'])
    
    hl = df['high'] - df['low']
    hpc = (df['high'] - df['prev_close']).abs()
    lpc = (df['low'] - df['prev_close']).abs()
    
    tr = pd.concat([hl, hpc, lpc], axis=1).max(axis=1)
    atr = tr.rolling(window=period, min_periods=1).mean()
    
    return atr
```

| Pipeline | Usage |
|----------|-------|
| Historical | Batch feature generation |
| Inference | Real-time volatility tracking |

---

### 2. RSI (Relative Strength Index)
**Source:** `modules/level_exhaustion.py:747-759`
**Use Case:** Both Historical & Inference

```python
# EXTRACTING THIS:
def calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi
```

| Pipeline | Usage |
|----------|-------|
| Historical | Training features |
| Inference | Momentum signals |

---

### 3. Volume Ratio (Relative Volume)
**Source:** `modules/swing_scalp_classifier.py:135-146`
**Use Case:** Both Historical & Inference

```python
# EXTRACTING THIS:
def calc_volume_ratio(df: pd.DataFrame, lookback: int = 20) -> float:
    """Current volume vs average volume. Returns ratio (1.0 = normal)."""
    if len(df) < lookback or 'volume' not in df.columns:
        return 1.0
    
    current_vol = df['volume'].iloc[-1]
    avg_vol = df['volume'].iloc[-lookback:].mean()
    
    if avg_vol == 0 or pd.isna(avg_vol) or pd.isna(current_vol):
        return 1.0
    
    return round(current_vol / avg_vol, 2)
```

| Pipeline | Usage |
|----------|-------|
| Historical | Volume-based features |
| Inference | Unusual activity detection |

---

### 4. Session Phase Detection
**Source:** `modules/swing_scalp_classifier.py:149-177`
**Use Case:** Inference only (time-based)

```python
# EXTRACTING THIS:
def get_session_phase(timestamp: Optional[datetime] = None) -> str:
    """Determine current trading session phase."""
    # Returns: pre_open, open_drive, morning, midday, afternoon, close, after_hours
```

| Pipeline | Usage |
|----------|-------|
| Historical | Time-bucketed features |
| Inference | Time-aware predictions |

---

### 5. VWAP (Volume-Weighted Average Price)
**Source:** `analysis/spx_move_discovery.py:208-218`
**Use Case:** Both Historical & Inference

```python
# EXTRACTING THIS:
def calc_vwap(df: pd.DataFrame) -> pd.Series:
    """Calculate intraday VWAP"""
    typical = (df['high'] + df['low'] + df['close']) / 3
    vol_price = typical * df['volume']
    
    vwap = vol_price.groupby(df.index.date).cumsum() / \
           df['volume'].groupby(df.index.date).cumsum()
    
    return vwap
```

| Pipeline | Usage |
|----------|-------|
| Historical | Institutional activity features |
| Inference | Price vs VWAP signals |

---

### 6. Volume Features (Acceleration/Pivots)
**Source:** `signals/volume.py` (entire file)
**Use Case:** Both Historical & Inference

```python
# EXTRACTING THIS:
def tag_reversal_with_accel(df: pd.DataFrame, rvol_lb: int = 20, ...) -> pd.DataFrame:
    """
    Outputs: VOL_RVOL, VOL_ACCEL, PIVOT_LOW/HIGH, REVERSAL_ACCEL_BULL/BEAR
    """
```

| Pipeline | Usage |
|----------|-------|
| Historical | Pattern detection features |
| Inference | Reversal signals |

---

### 7. Moving Averages (SMA/EMA)
**Source:** `modules/level_exhaustion.py:366-410`
**Use Case:** Both Historical & Inference

```python
# PATTERN TO USE:
ma_configs = {
    '10m': [('20ema', 20, 'ema')],
    '60m': [('20ema', 20, 'ema'), ('50sma', 50, 'sma')],
    'daily': [
        ('9ema', 9, 'ema'),
        ('20ema', 20, 'ema'),
        ('50sma', 50, 'sma'),
        ('200sma', 200, 'sma')
    ],
}
```

| Pipeline | Usage |
|----------|-------|
| Historical | Trend features |
| Inference | Trend direction |

---

### 8. Feature Engineering Patterns
**Source:** `analysis/spx_move_discovery.py:130-233`
**Use Case:** Historical (training features)

Key patterns to extract:
- Price position in N-bar range
- Bar microstructure (range, body, direction)
- Momentum/velocity calculations
- Compression/expansion metrics
- Volume dynamics
- Time-based features

---

### 9. Data Schema Standard
**Source:** `docs/DATA_LAKE_SCHEMA_STANDARD.md`
**Use Case:** Both (schema consistency)

Key conventions:
- Column names: `open, high, low, close, volume` (not o,h,l,c,v)
- Join keys: `ticker, timeframe, bar_ts`
- Timeframes: `10m, 60m, daily` (not 10min, 1h, 1d)

---

## ❌ Components We WILL NOT Use

### 1. Data Sources (Tiingo)
**Files:** `scripts/raw_backfill.py`, `scripts/raw_backfill_daily.py`
**Reason:** SoW specifies yfinance + Alpha Vantage

```python
# THEY USE:
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY")
url = f"https://api.tiingo.com/iex/{ticker}/prices?..."

# WE USE:
import yfinance as yf
df = yf.download(symbol, start=start_date, end=end_date)
```

---

### 2. Universal Data Loader
**File:** `universal_data_loader.py`
**Reason:** Tied to their data lake structure (`/srv/data_lake/raw`)

```python
# THEY HAVE:
DATA_ROOT = Path('/srv/data_lake/raw')  # Server-specific path

# WE BUILD:
# Local parquet storage + TimescaleDB
```

---

### 3. Context Enricher (Mod 6/9/11/13)
**File:** `scripts/context_enricher.py`
**Reason:** Depends on their data lake structure + we don't have their context data

---

### 4. Entry/Exit Timing
**Files:** `modules/entry_timing.py`, `modules/exit_signals.py`, `modules/exit_phase_detector.py`
**Reason:** Trading execution logic, NOT data pipeline

---

### 5. Pattern Discovery/Clustering
**Files:** `discovery/*.py`, `forward_test/*.py`, `scripts/build_embeddings.py`
**Reason:** ML clustering, Phase 2+ scope

---

### 6. Level Exhaustion Engine (Full)
**File:** `modules/level_exhaustion.py` (full engine)
**Reason:** Too complex for M1, uses SQLite database for tracking

**What we DO extract:** Individual helper functions (RSI, EMAs)
**What we DON'T use:** The full `LevelExhaustionEngine` class

---

### 7. Swing/Scalp Classifier (Full)
**File:** `modules/swing_scalp_classifier.py` (full classifier)
**Reason:** Trading classification, NOT data pipeline

**What we DO extract:** Helper functions (ATR, volume ratio, session phase)
**What we DON'T use:** The full `SwingScalpClassifier` class

---

### 8. Scanner Scripts
**Files:** `forward_test/`, `analysis/*_scanner.py`
**Reason:** Real-time pattern scanning, Phase 2+ scope

---

## 📊 Summary Table: Client Components

| Component | Source File | Extract? | Use in Historical | Use in Inference |
|-----------|-------------|----------|-------------------|------------------|
| ATR | swing_scalp_classifier.py | ✅ YES | ✅ Features | ✅ Volatility |
| RSI | level_exhaustion.py | ✅ YES | ✅ Features | ✅ Momentum |
| Volume Ratio | swing_scalp_classifier.py | ✅ YES | ✅ Features | ✅ Activity |
| Session Phase | swing_scalp_classifier.py | ✅ YES | ⚠️ Optional | ✅ Time-aware |
| VWAP | spx_move_discovery.py | ✅ YES | ✅ Features | ✅ Institutional |
| Volume Features | volume.py | ✅ YES | ✅ Features | ✅ Reversals |
| MA Config | level_exhaustion.py | ✅ YES | ✅ Trends | ✅ Trends |
| Feature Patterns | spx_move_discovery.py | ✅ YES | ✅ Training | ⚠️ Optional |
| Schema Standard | docs/ | ✅ Reference | ✅ Consistency | ✅ Consistency |
| Tiingo Data | raw_backfill.py | ❌ NO | N/A | N/A |
| Data Loader | universal_data_loader.py | ❌ NO | N/A | N/A |
| Context Enricher | context_enricher.py | ❌ NO | N/A | N/A |
| Entry Timing | entry_timing.py | ❌ NO | N/A | N/A |
| Exit Signals | exit_signals.py | ❌ NO | N/A | N/A |
| Full Level Engine | level_exhaustion.py | ❌ NO | N/A | N/A |
| Full Classifier | swing_scalp_classifier.py | ❌ NO | N/A | N/A |
| Pattern Discovery | discovery/*.py | ❌ NO | N/A | N/A |
| Scanners | forward_test/*.py | ❌ NO | N/A | N/A |

---

## 🔄 How Components Translate: Historical → Inference

| Function | Historical (Batch) | Inference (Live) |
|----------|-------------------|------------------|
| `calc_atr()` | Full history calculation | Rolling window update |
| `calc_rsi()` | Full history calculation | Incremental update |
| `calc_volume_ratio()` | Per-bar calculation | Real-time spike detection |
| `calc_vwap()` | Daily reset | Intraday cumulative |
| `calc_moving_averages()` | Full series | Last N bars only |
| `engineer_features()` | All features for training | Subset for inference |

---

## 🎯 Client Communication Points

### What We're Using:
> "We're extracting 8 core indicator/feature calculation components from your existing codebase:
> - ATR, RSI, VWAP, Volume Ratio, Session Phase
> - Moving Average configurations
> - Volume acceleration/pivot detection
> - Feature engineering patterns
> 
> These ensure consistency between your existing historical analysis and our new inference pipeline."

### What We're NOT Using (and Why):
> "We're NOT using several components that are either:
> 1. **Data source specific** (Tiingo) - SoW specifies yfinance/Alpha Vantage
> 2. **Trading execution logic** - Entry/exit timing is Phase 2+
> 3. **Pattern discovery/ML** - Clustering is Phase 2+
> 4. **Infrastructure-tied** - Your data lake paths are server-specific
> 
> This keeps M1 focused on the data pipeline foundation, not trading signals."

### The Value-Add:
> "What's NEW that your existing repo doesn't have:
> 1. **Inference pipeline** - Real-time data streaming + caching
> 2. **API layer** - FastAPI endpoints for live predictions
> 3. **Clean separation** - Historical vs Inference clearly architected
> 4. **Portability** - Not tied to /srv/data_lake/ server structure"

