# TICK M1 Completion Plan: Data Pipeline Foundation

## Executive Summary

This document outlines the comprehensive plan to complete Milestone 1 (Foundation & Data Pipeline) for the TICK Multi-Agent Stock Prediction System. The plan integrates the client's Copilot Signals architecture with our existing codebase.

---

## Current State Analysis

### What We Have (TICK Codebase)

| Component | Status | Notes |
|-----------|--------|-------|
| Data Agent | **Stub** | `agent.py` has TODO placeholders |
| YFinance Collector | **Working** | Full implementation for OHLCV |
| Alpha Vantage Collector | **Partial** | Exists but needs testing |
| Feature Agent | **Stub** | `agent.py` has TODO placeholders |
| Momentum Indicators | **Working** | RSI, MACD, Stochastic, CCI, MFI |
| Volatility Indicators | **Exists** | Need verification |
| Trend Indicators | **Exists** | Need verification |
| Parquet Storage | **Exists** | Basic implementation |

### What Client Has (Copilot Signals)

| Module | Purpose | Type | Data Source | Output Columns |
|--------|---------|------|-------------|----------------|
| MOD06 | Event Calendar | EVENT_BASED | FMP API | days_to_fomc, days_to_cpi, days_to_jobs, event_proximity_score, is_fomc_week |
| MOD09 | Correlation & Macro | MARKET_WIDE | FRED/yfinance | vix_level, vix_percentile, vix_term_structure, yield_2y, yield_10y, yield_spread_2s10s, macro_regime |
| MOD10 | Sentiment | TICKER_SPECIFIC | Alpha Vantage | news_sentiment_score, news_volume_24h, sentiment_momentum, social_buzz_score |
| MOD11 | Sector Rotation | SECTOR_LEVEL | yfinance/ETFs | sector_momentum_5d, sector_momentum_20d, sector_relative_strength, rotation_phase |
| MOD13 | Earnings | TICKER_SPECIFIC | FMP | days_to_earnings, last_surprise_pct, beat_rate_4q, implied_move, is_earnings_week |
| MOD14 | Economic Data | MARKET_WIDE | FRED | cpi_yoy, gas_price, unemployment_rate, consumer_sentiment, fed_funds_rate |
| MOD15 | Options Flow | TICKER_SPECIFIC | Options API | put_call_ratio, unusual_options_activity, iv_percentile, gamma_exposure |

**Client Module Types:**
- `MARKET_WIDE`: Applies to all tickers (VIX, yields, economic data) - merge by timestamp only
- `TICKER_SPECIFIC`: Per-ticker data (sentiment, earnings) - merge by ticker + timestamp
- `SECTOR_LEVEL`: Per-sector data (rotation) - merge via sector lookup
- `EVENT_BASED`: Calendar events - merge by timestamp

### Key Architecture Differences

| Aspect | Client | TICK (Current) | Action Required |
|--------|--------|----------------|-----------------|
| Primary Data Source | Tiingo IEX | yfinance | Add Tiingo collector |
| Fundamentals Source | FMP | None | Add FMP collector |
| Schema | Universal (54 cols) | Basic OHLCV | Extend schema |
| Join Keys | ticker, bar_ts, timeframe | ticker, date | Align schema |
| Storage | Parquet/Pickle | Parquet | Keep, extend |

---

## Phase 1: Data Infrastructure (Week 1-2)

### 1.1 Add Tiingo Data Collector

**Location:** `backend/agents/data_agent/collectors/tiingo_collector.py`

**API Keys Required:**
- Tiingo: `9e7e7ef41ad8cefe4bfa3f57e7bb60b5d81e3d14`

**Features to Implement:**
```python
class TiingoCollector:
    - fetch_historical_eod(ticker, start, end)  # End-of-day prices
    - fetch_iex_historical(ticker, start, end, resample)  # IEX intraday
    - fetch_latest(ticker)  # Real-time quote
    - fetch_metadata(ticker)  # Ticker info
```

**Reference:** Client's `modules/core/price_data.py`

### 1.2 Add FMP (Financial Modeling Prep) Collector

**Location:** `backend/agents/data_agent/collectors/fmp_collector.py`

**API Keys Required:**
- FMP: `W8Qj3LfEWEh5EGBo8gBlCQ4QNT36rZ8j`

**Features to Implement:**
```python
class FMPCollector:
    - fetch_historical_price(ticker, start, end)
    - fetch_earnings_calendar(ticker)  # For MOD06
    - fetch_earnings_surprise(ticker)  # For MOD06
    - fetch_company_profile(ticker)
    - fetch_sector_performance()  # For MOD11
    - fetch_financial_ratios(ticker)
```

### 1.3 Add FRED Data Collector

**Location:** `backend/agents/data_agent/collectors/fred_collector.py`

**Features to Implement:**
```python
class FREDCollector:
    - fetch_series(series_id, start, end)  # Generic FRED series
    - fetch_vix()  # VIX for MOD09
    - fetch_treasury_yields()  # 10Y, 2Y for MOD14
    - fetch_economic_indicators()  # GDP, CPI, etc.
```

---

## Phase 2: Context Modules (Week 2-3)

### 2.1 Implement Universal Schema (from Client's schema_constants.py)

**Location:** `backend/agents/data_agent/schema.py`

**Join Keys (All modules MUST use these for merging):**
```python
JOIN_KEYS = {
    "primary": ["ticker", "timeframe", "timestamp"],
    "ticker_only": ["ticker"],
    "market_wide": ["timeframe", "timestamp"],  # For _MARKET data
    "time_only": ["timestamp"],
}

MARKET_TICKER = "_MARKET"  # Special ticker for market-wide data
```

**Timeframe Normalization:**
```python
SUPPORTED_TIMEFRAMES = ["1min", "5min", "10min", "15min", "30min", "60min", "daily", "weekly"]
```

**Full Schema by Module (Client's exact output columns):**

```python
# MOD06: Events Calendar (prefix: evt_)
MOD06_COLUMNS = [
    "days_to_fomc", "days_to_cpi", "days_to_jobs", "days_to_gdp",
    "event_proximity_score", "is_fomc_week", "is_cpi_week",
    "next_event_type", "next_event_date",
]

# MOD09: Correlation & Macro (prefix: macro_)
MOD09_COLUMNS = [
    "vix_level", "vix_percentile", "vix_term_structure",
    "yield_2y", "yield_10y", "yield_spread_2s10s", "yield_curve_inverted",
    "spx_bond_corr_20d", "spx_vix_corr_20d",
    "macro_regime",  # risk_on, risk_off, transition
    "regime_confidence", "dollar_index", "gold_signal",
]

# MOD10: Sentiment (prefix: sent_)
MOD10_COLUMNS = [
    "news_sentiment_score", "news_volume_24h", "sentiment_momentum",
    "social_buzz_score", "analyst_sentiment", "insider_sentiment",
    "sentiment_divergence",  # price vs sentiment
]

# MOD11: Sector Rotation (prefix: rot_)
MOD11_COLUMNS = [
    "sector", "sector_momentum_5d", "sector_momentum_20d",
    "sector_relative_strength", "sector_flow_score",
    "rotation_phase",  # early_cycle, mid_cycle, late_cycle, recession
    "risk_appetite_score", "defensive_rotation", "cyclical_rotation",
    "sector_rank",
]

# MOD13: Earnings (prefix: earn_)
MOD13_COLUMNS = [
    "days_to_earnings", "earnings_date", "earnings_time",  # BMO, AMC
    "last_surprise_pct", "surprise_history_avg", "beat_rate_4q",
    "guidance_sentiment", "is_earnings_week",
    "implied_move", "historical_earnings_vol",
]

# MOD14: Economic Data (prefix: econ_)
MOD14_COLUMNS = [
    "cpi_yoy", "cpi_mom", "cpi_trend", "core_cpi_yoy",
    "gas_price", "gas_price_change_mom",
    "unemployment_rate", "unemployment_trend",
    "consumer_sentiment", "sentiment_change_mom",
    "economic_surprise_index", "fed_funds_rate", "inflation_expectations",
]

# MOD15: Options Flow (prefix: opt_) - FUTURE
MOD15_COLUMNS = [
    "put_call_ratio", "unusual_options_activity",
    "large_trades_bullish", "large_trades_bearish",
    "implied_vol_rank", "iv_percentile",
    "options_volume_ratio", "gamma_exposure",
]
```

**Sector Mappings (from client's schema):**
```python
SECTOR_ETFS = {
    "XLK": "technology",
    "XLF": "financials",
    "XLV": "healthcare",
    "XLY": "consumer_discretionary",
    "XLP": "consumer_staples",
    "XLE": "energy",
    "XLI": "industrials",
    "XLB": "materials",
    "XLU": "utilities",
    "XLRE": "real_estate",
    "XLC": "communication_services",
}

RISK_ON_SECTORS = ["technology", "consumer_discretionary", "financials", "communication_services"]
RISK_OFF_SECTORS = ["utilities", "consumer_staples", "healthcare", "real_estate"]
CYCLICAL_SECTORS = ["energy", "materials", "industrials"]
```

### 2.2 Implement Context Loader (from Client's context_loader.py)

**Location:** `backend/agents/data_agent/context_loader.py`

**Purpose:** Central orchestrator that joins all context modules with proper merge strategies

**Key Design Patterns from Client:**

```python
class ContextLoader:
    """
    Features from client's implementation:
    - Auto-discovers modules from SchemaRegistry
    - Handles different merge strategies per module type
    - Caches loaded data (5-min TTL)
    - Supports lookback for missing data
    - Validates staleness of context data
    """

    def __init__(self, config: LoaderConfig = None):
        self.config = config or LoaderConfig.from_env()
        self._cache = {}  # {cache_key: (df, timestamp)}

    def enrich_signals(self, signals_df: pd.DataFrame, date: str = None) -> pd.DataFrame:
        """Main entry point - enrich signals with all context modules."""

        # 1. Normalize input signals
        signals_df = normalize_dataframe(signals_df)

        # 2. Add sector column based on ticker
        signals_df = add_sector_column(signals_df)

        # 3. Load all context for the date
        context = self.load_all_context(date)

        # 4. Merge based on module type
        enriched = signals_df.copy()
        for mod_id, context_df in context.items():
            schema = SchemaRegistry.get(mod_id)

            if schema.module_type == ModuleType.MARKET_WIDE:
                # VIX, yields, economic - merge by timestamp only (asof merge)
                enriched = merge_market_wide_context(enriched, context_df, schema.column_prefix)

            elif schema.module_type == ModuleType.TICKER_SPECIFIC:
                # Sentiment, earnings - merge by ticker + timestamp
                enriched = merge_ticker_context(enriched, context_df, schema.column_prefix)

            elif schema.module_type == ModuleType.SECTOR_LEVEL:
                # Sector rotation - merge via sector column
                enriched = self._merge_sector_context(enriched, context_df, schema.column_prefix)

            elif schema.module_type == ModuleType.EVENT_BASED:
                # Calendar events - merge by timestamp
                enriched = merge_market_wide_context(enriched, context_df, schema.column_prefix)

        return enriched
```

**Merge Utilities (from client):**
```python
def merge_market_wide_context(signals_df, context_df, prefix=""):
    """Use pd.merge_asof for time-based merging (most recent context for each signal)."""
    return pd.merge_asof(
        signals_df.sort_values("timestamp"),
        context_df.sort_values("timestamp"),
        on="timestamp",
        direction="backward",  # Get most recent context
    )

def merge_ticker_context(signals_df, context_df, prefix=""):
    """Merge by ticker, then asof on timestamp within each ticker."""
    merged_dfs = []
    for ticker in signals_df["ticker"].unique():
        sig_ticker = signals_df[signals_df["ticker"] == ticker]
        ctx_ticker = context_df[context_df["ticker"] == ticker]
        if len(ctx_ticker) > 0:
            merged = pd.merge_asof(sig_ticker, ctx_ticker, on="timestamp", direction="backward")
            merged_dfs.append(merged)
    return pd.concat(merged_dfs) if merged_dfs else signals_df
```

### 2.3 Individual Context Modules

#### MOD06: Earnings Context

**Location:** `backend/agents/data_agent/context/earnings.py`

```python
class EarningsContext:
    def add_context(self, df):
        # 1. Fetch earnings calendar from FMP
        # 2. Calculate days_to_earnings
        # 3. Fetch historical earnings surprise
        # 4. Add earnings_surprise_pct column
        return df
```

#### MOD09: Macro/VIX Context

**Location:** `backend/agents/data_agent/context/macro_vix.py`

```python
class MacroVIXContext:
    def add_context(self, df):
        # 1. Fetch VIX from yfinance (^VIX)
        # 2. Calculate VIX percentile (rolling 252-day)
        # 3. Determine VIX regime
        return df
```

**VIX Regime Logic (from client's code):**
```python
def get_vix_regime(vix: float, percentile: float) -> str:
    if vix < 15:
        return "low"
    elif vix < 20:
        return "medium"
    elif vix < 30:
        return "high"
    else:
        return "extreme"
```

#### MOD11: Sector Rotation Context

**Location:** `backend/agents/data_agent/context/sector.py`

```python
class SectorContext:
    SECTOR_ETFS = {
        "XLK": "Technology",
        "XLF": "Financials",
        "XLE": "Energy",
        "XLV": "Healthcare",
        "XLI": "Industrials",
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLU": "Utilities",
        "XLB": "Materials",
        "XLRE": "Real Estate",
        "XLC": "Communication Services",
    }

    def add_context(self, df):
        # 1. Get ticker's sector
        # 2. Fetch sector ETF performance
        # 3. Calculate relative strength vs SPY
        # 4. Generate rotation signal
        return df
```

#### MOD14: Economic Context

**Location:** `backend/agents/data_agent/context/economic.py`

```python
class EconomicContext:
    FRED_SERIES = {
        "fed_funds": "FEDFUNDS",
        "treasury_10y": "DGS10",
        "treasury_2y": "DGS2",
        "unemployment": "UNRATE",
        "cpi": "CPIAUCSL",
    }

    def add_context(self, df):
        # 1. Fetch economic indicators from FRED
        # 2. Calculate yield curve spread
        # 3. Forward-fill to match bar_ts
        return df
```

#### MOD10: Sentiment Context (TICKER_SPECIFIC)

**Location:** `backend/agents/data_agent/context/sentiment.py`

```python
class SentimentContext:
    """
    Output columns (prefix: sent_):
    - news_sentiment_score: -1 to 1 sentiment from news
    - news_volume_24h: Number of news articles
    - sentiment_momentum: Change in sentiment
    - social_buzz_score: Social media mentions
    - sentiment_divergence: Price vs sentiment divergence
    """

    def add_context(self, df):
        # 1. Fetch news sentiment from Alpha Vantage
        # 2. Calculate sentiment momentum (rolling change)
        # 3. Detect sentiment-price divergence
        # 4. Join by ticker + timestamp
        return df
```

#### MOD13: Earnings Context (TICKER_SPECIFIC)

**Location:** `backend/agents/data_agent/context/earnings.py`

```python
class EarningsContext:
    """
    Output columns (prefix: earn_):
    - days_to_earnings: Days until next earnings
    - earnings_date: Next earnings date
    - earnings_time: BMO (before market open) or AMC (after market close)
    - last_surprise_pct: Last quarter's surprise percentage
    - beat_rate_4q: Beat rate over last 4 quarters
    - is_earnings_week: Boolean flag
    - implied_move: Expected move from options
    """

    def add_context(self, df):
        # 1. Fetch earnings calendar from FMP
        # 2. Calculate days_to_earnings
        # 3. Fetch historical earnings surprises
        # 4. Calculate beat rate (last 4 quarters)
        # 5. Join by ticker + timestamp
        return df
```

#### MOD15: Options Flow Context (TICKER_SPECIFIC - FUTURE)

**Location:** `backend/agents/data_agent/context/options.py`

```python
class OptionsContext:
    """
    Output columns (prefix: opt_):
    - put_call_ratio: Volume-weighted P/C ratio
    - unusual_options_activity: Boolean flag
    - iv_percentile: Implied volatility percentile
    - gamma_exposure: Market maker gamma exposure

    NOTE: Lower priority - requires options data provider
    """

    def add_context(self, df):
        # 1. Fetch options flow data
        # 2. Calculate put/call ratio
        # 3. Detect unusual activity
        return df
```

---

## Phase 3: Pipeline Integration (Week 3-4)

### 3.1 Historical Pipeline (for Model Training)

**Purpose:** Generate 54-column enriched dataset for training

```
Flow:
  Raw OHLCV (Tiingo/yfinance)
      ↓
  Feature Agent (Technical Indicators)
      ↓
  Context Loader (7 Modules)
      ↓
  Enriched DataFrame (54 columns)
      ↓
  Parquet Storage (partitioned by ticker/date)
```

**Implementation:**

```python
class HistoricalPipeline:
    def __init__(self):
        self.data_agent = DataAgent()
        self.feature_agent = FeatureAgent()
        self.context_loader = ContextLoader()

    async def run(self, tickers: List[str], start: datetime, end: datetime):
        for ticker in tickers:
            # 1. Fetch OHLCV
            ohlcv = await self.data_agent.fetch_historical(ticker, start, end)

            # 2. Calculate features
            features = await self.feature_agent.calculate_all(ohlcv)

            # 3. Enrich with context
            enriched = self.context_loader.enrich(features)

            # 4. Store
            await self.storage.save(enriched, ticker)
```

### 3.2 Real-time Inference Pipeline

**Purpose:** Generate features for live predictions

```
Flow:
  Real-time Price (WebSocket/Tiingo IEX)
      ↓
  Update OHLCV (sliding window)
      ↓
  Feature Agent (incremental)
      ↓
  Context Loader (cached where possible)
      ↓
  Enriched Row (for model inference)
```

**Implementation:**

```python
class RealtimePipeline:
    def __init__(self):
        self.buffer = {}  # ticker -> recent bars
        self.context_cache = ContextCache(ttl=300)  # 5-min cache

    async def process_tick(self, ticker: str, price_data: dict):
        # 1. Update OHLCV buffer
        self.buffer[ticker].append(price_data)

        # 2. Calculate features (only on new data)
        features = self.feature_agent.calculate_incremental(
            self.buffer[ticker]
        )

        # 3. Get cached context (refresh if stale)
        context = await self.context_cache.get_or_refresh(ticker)

        # 4. Merge and return
        return {**features, **context}
```

---

## Phase 4: Wire Up Data Agent (Week 4)

### 4.1 Complete DataAgent Implementation

```python
class DataAgent(BaseAgent):
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(name="data_agent", config=config)

        # Initialize collectors
        self.collectors = {
            "tiingo": TiingoCollector(api_key=config.get("tiingo_api_key")),
            "yfinance": YFinanceCollector(),
            "fmp": FMPCollector(api_key=config.get("fmp_api_key")),
            "fred": FREDCollector(),
        }

        # Initialize context loader
        self.context_loader = ContextLoader()

        # Initialize storage
        self.storage = ParquetStorage(base_path=config.get("data_path"))

    async def fetch_historical(self, ticker, start, end, enriched=False):
        # 1. Try Tiingo first, fallback to yfinance
        result = await self._fetch_with_fallback(ticker, start, end)

        # 2. Optionally enrich with context
        if enriched:
            result = self.context_loader.enrich(result)

        return result

    async def fetch_realtime(self, ticker):
        # Use Tiingo IEX for real-time
        return await self.collectors["tiingo"].fetch_latest(ticker)
```

### 4.2 Complete FeatureAgent Implementation

```python
class FeatureAgent(BaseAgent):
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(name="feature_agent", config=config)

        self.indicator_modules = {
            "momentum": MomentumIndicators(),
            "volatility": VolatilityIndicators(),
            "trend": TrendIndicators(),
            "volume": VolumeIndicators(),
        }

    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators."""
        for name, module in self.indicator_modules.items():
            df = module.calculate(df)
        return df

    def calculate_incremental(self, recent_bars: List[dict]) -> dict:
        """Calculate indicators on recent data (for real-time)."""
        df = pd.DataFrame(recent_bars)
        result = self.calculate_all(df)
        return result.iloc[-1].to_dict()
```

---

## Phase 5: Frontend Data Pipeline Page (Week 4)

### 5.1 Enhance Pipeline Page

The existing `/pipeline/page.tsx` needs enhancements:

1. **Pipeline Status Dashboard**
   - Show status of each data collector (Tiingo, yfinance, FMP, FRED)
   - Display last successful fetch time per ticker
   - Show data freshness indicators

2. **Historical Data Management**
   - Trigger historical data backfill
   - Show backfill progress
   - Preview enriched data (54 columns)

3. **Real-time Pipeline Monitor**
   - WebSocket connection status
   - Ticks per second
   - Latency metrics

---

## API Configuration

### Environment Variables Required

```bash
# .env file
TIINGO_API_KEY=9e7e7ef41ad8cefe4bfa3f57e7bb60b5d81e3d14
FMP_API_KEY=W8Qj3LfEWEh5EGBo8gBlCQ4QNT36rZ8j
FRED_API_KEY=<get_from_fred>  # Free registration
ALPHA_VANTAGE_API_KEY=<existing_or_get_new>
```

### Rate Limits

| API | Rate Limit | Strategy |
|-----|------------|----------|
| Tiingo | 500/hour (free) | Queue + cache |
| FMP | 250/day (free) | Batch + cache |
| FRED | Unlimited | Cache 24h |
| yfinance | Soft limit | Retry + backoff |

---

## Testing Strategy

### Unit Tests

```
tests/
├── agents/
│   ├── data_agent/
│   │   ├── test_tiingo_collector.py
│   │   ├── test_fmp_collector.py
│   │   ├── test_context_loader.py
│   │   └── test_earnings_context.py
│   └── feature_agent/
│       ├── test_momentum.py
│       └── test_volatility.py
```

### Integration Tests

1. **End-to-end Historical Pipeline**
   - Fetch → Calculate → Enrich → Store → Retrieve

2. **Schema Validation**
   - Verify all 54 columns present
   - Validate data types
   - Check for NaN handling

### Test Tickers

Use these for testing (client's recommended):
- `AAPL` - High liquidity
- `TSLA` - High volatility
- `SPY` - ETF/benchmark
- `XLK` - Sector ETF

---

## Deliverables Checklist

### Phase 1: Data Infrastructure
- [ ] Tiingo Collector implemented and tested
- [ ] FMP Collector implemented and tested
- [ ] FRED Collector implemented and tested
- [ ] All collectors integrated into DataAgent

### Phase 2: Context Modules (ALL 7 from Client)
- [ ] Universal Schema defined (JOIN_KEYS, column prefixes)
- [ ] SchemaRegistry pattern implemented
- [ ] Context Loader with merge strategies implemented
- [ ] MOD06 (Events Calendar) - FOMC/CPI/Jobs proximity
- [ ] MOD09 (Macro/VIX) - VIX, yields, regime detection
- [ ] MOD10 (Sentiment) - News sentiment, social buzz (TICKER_SPECIFIC)
- [ ] MOD11 (Sector Rotation) - Sector ETF performance, rotation phase
- [ ] MOD13 (Earnings) - Days to earnings, surprise history (TICKER_SPECIFIC)
- [ ] MOD14 (Economic) - CPI, unemployment, consumer sentiment
- [ ] MOD15 (Options) - P/C ratio, unusual activity (FUTURE - lower priority)

### Phase 3: Pipeline Integration
- [ ] Historical Pipeline working end-to-end
- [ ] Real-time Pipeline working end-to-end
- [ ] Data stored in Parquet format
- [ ] Schema validation passing

### Phase 4: Agent Completion
- [ ] DataAgent fully implemented
- [ ] FeatureAgent fully implemented
- [ ] Both agents have health checks
- [ ] Both agents have proper error handling

### Phase 5: Frontend
- [ ] Pipeline page shows collector status
- [ ] Pipeline page shows data freshness
- [ ] Can trigger manual backfill

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| API rate limits | Data gaps | Implement caching, queue requests |
| Tiingo API changes | Pipeline breaks | Keep yfinance as fallback |
| FMP free tier limits | Missing earnings data | Batch requests, cache aggressively |
| Context calculation slow | Latency in real-time | Pre-compute, cache context |

---

## Notes from Client Training Sessions & Code Analysis

### From Loom Training Videos:
1. **Data must be indexed by `timestamp`** (not arbitrary index, not `bar_ts`)
2. **Always forward-fill economic data** (published monthly/weekly)
3. **VIX regime is crucial** - affects all predictions
4. **Earnings dates need buffer** - fetch 2 weeks before/after
5. **Sector rotation signals** - use 20-day relative strength

### From Client's schema_constants.py:
6. **Column naming convention**: Use prefixes for each module (evt_, macro_, sent_, rot_, earn_, econ_, opt_)
7. **Timeframe normalization**: Always convert to canonical form ("5m" → "5min", "1h" → "60min", "1d" → "daily")
8. **MARKET_TICKER = "_MARKET"**: Special ticker for market-wide data (VIX, yields, etc.)
9. **Sector classification**: Risk-on vs Risk-off sectors affect rotation signals

### From Client's context_loader.py:
10. **Use `pd.merge_asof` for time-based joins** (direction="backward" to get most recent context)
11. **Cache context data with 5-min TTL** for real-time performance
12. **Lookback on missing data**: If today's context not found, try previous days
13. **Staleness warnings**: Alert if context data exceeds max_staleness_hours
14. **Load order matters**: Some modules depend on others (MOD11 depends on MOD09 for yield data)

### Data Paths (Client's convention):
```
/srv/data_lake/
├── context/
│   ├── mod06_events/
│   │   ├── daily/
│   │   └── intraday/
│   ├── mod09_correlation/
│   ├── mod10_sentiment/
│   ├── mod11_rotation/
│   ├── mod13_earnings/
│   └── mod14_economic/
└── signals/
```

---

## Next Steps (Immediate)

1. **Create `.env` file** with API keys
2. **Implement Tiingo Collector** (highest priority)
3. **Test with AAPL** to verify data flow
4. **Implement MOD09 (VIX)** - most impactful context

---

*Document Version: 1.0*
*Created: 2026-01-29*
*Author: Claude Code Agent*
