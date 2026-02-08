# TICK M2 Implementation Plan: Core Prediction Models

## Executive Summary

Milestone 2 focuses on implementing the core prediction models. Based on our assessment:

| Agent | Status | Work Required |
|-------|--------|---------------|
| Support/Resistance Agent | **COMPLETE** | Already implemented by Dev 2 |
| Price Forecast Agent | **STUB** | Full implementation needed |
| Trend Classification Agent | **STUB** | Full implementation needed |

**Payment:** $1,200 (20% of $6,000)

---

## Current State Analysis

### Support/Resistance Agent - ALREADY COMPLETE

Developer 2 has already implemented:
- DBSCAN clustering for level detection
- Local extrema detection algorithm
- Level strength scoring (0-100)
- Volume profile analysis
- Level validation
- Batch processing
- Caching system
- ML-based level prediction

**No work needed - ready for signoff.**

### Price Forecast Agent - NEEDS IMPLEMENTATION

Current: Stub with TODO placeholders
Required:
- Prophet model (baseline)
- LSTM model (primary)
- Multi-horizon predictions (1h, 4h, 1d, 1w)
- Confidence intervals
- Walk-forward validation

### Trend Classification Agent - NEEDS IMPLEMENTATION

Current: Stub with TODO placeholders
Required:
- LightGBM/XGBoost classifier
- Feature engineering for classification
- BUY/SELL/HOLD with probability scores
- Multi-timeframe support (1h, 1d)
- >55% accuracy target

---

## Implementation Plan

### Phase 1: Price Forecast Agent

#### 1.1 Prophet Model (Baseline)

```
backend/agents/price_forecast_agent/
├── agent.py                    # Main agent (rewrite)
├── models/
│   ├── __init__.py
│   ├── prophet_model.py        # NEW - Prophet forecasting
│   ├── lstm_model.py           # NEW - LSTM forecasting
│   └── model_registry.py       # NEW - Model versioning
├── training/
│   ├── __init__.py
│   ├── trainer.py              # NEW - Training pipeline
│   └── walk_forward.py         # NEW - Walk-forward validation
└── utils/
    ├── __init__.py
    └── data_prep.py            # NEW - Data preparation
```

**Prophet Model Features:**
- Automatic seasonality detection (daily, weekly)
- Holiday effects
- Trend changepoints
- Uncertainty intervals

#### 1.2 LSTM Model (Primary)

**LSTM Architecture:**
- Input: 60 time steps of features
- Layers: 2 LSTM layers (128, 64 units)
- Dropout: 0.2 for regularization
- Output: Price prediction + confidence

**Features for LSTM:**
- OHLCV data (normalized)
- Technical indicators (from Feature Agent)
- Lagged returns
- Volatility measures

#### 1.3 Multi-Horizon Predictions

| Horizon | Description | Use Case |
|---------|-------------|----------|
| 1h | 1-hour ahead | Day trading |
| 4h | 4-hour ahead | Swing trading |
| 1d | 1-day ahead | Position trading |
| 1w | 1-week ahead | Investment |

### Phase 2: Trend Classification Agent

#### 2.1 LightGBM Classifier

```
backend/agents/trend_classification_agent/
├── agent.py                    # Main agent (rewrite)
├── models/
│   ├── __init__.py
│   ├── lightgbm_classifier.py  # NEW - LightGBM model
│   └── xgboost_classifier.py   # NEW - XGBoost alternative
├── features/
│   ├── __init__.py
│   └── feature_builder.py      # NEW - Classification features
└── training/
    ├── __init__.py
    └── trainer.py              # NEW - Training pipeline
```

**Classification Labels:**
- BUY: Price increases >1% in horizon
- SELL: Price decreases >1% in horizon
- HOLD: Price changes <1% in horizon

**Features for Classification:**
- Technical indicators (RSI, MACD, etc.)
- Price momentum
- Volume features
- Trend features
- Context features (from M1)

#### 2.2 Multi-Timeframe Support

| Timeframe | Training Data | Prediction |
|-----------|---------------|------------|
| 1h | 6 months hourly | Next hour direction |
| 1d | 2 years daily | Next day direction |

### Phase 3: Model Serving Infrastructure

#### 3.1 Model Registry

```python
class ModelRegistry:
    """
    Simple model registry for versioning and deployment.

    Features:
    - Save trained models with metadata
    - Load latest or specific version
    - Track model performance
    """

    def save_model(self, model, name, version, metrics):
        pass

    def load_model(self, name, version="latest"):
        pass

    def get_model_info(self, name):
        pass
```

#### 3.2 Inference API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/forecast/{ticker}` | GET | Get price forecast |
| `/api/v1/forecast/{ticker}/train` | POST | Train models |
| `/api/v1/trend/{ticker}` | GET | Get trend classification |
| `/api/v1/trend/{ticker}/train` | POST | Train classifier |
| `/api/v1/levels/{ticker}` | GET | Get S/R levels (existing) |

---

## Technical Specifications

### Price Forecast Agent

**Prophet Model:**
```python
def train_prophet(df, horizon_days):
    model = Prophet(
        seasonality_mode='multiplicative',
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,  # For daily data
        changepoint_prior_scale=0.05
    )
    model.fit(df[['ds', 'y']])
    future = model.make_future_dataframe(periods=horizon_days)
    forecast = model.predict(future)
    return forecast
```

**LSTM Model:**
```python
def build_lstm_model(input_shape, output_size=1):
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=input_shape),
        Dropout(0.2),
        LSTM(64, return_sequences=False),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(output_size)
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model
```

### Trend Classification Agent

**LightGBM Classifier:**
```python
def train_lightgbm(X_train, y_train):
    params = {
        'objective': 'multiclass',
        'num_class': 3,  # BUY, SELL, HOLD
        'metric': 'multi_logloss',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.9
    }
    train_data = lgb.Dataset(X_train, label=y_train)
    model = lgb.train(params, train_data, num_boost_round=100)
    return model
```

---

## Definition of Done (from SoW)

- [ ] Price Forecast Agent generates predictions for all timeframes with confidence intervals
- [ ] Trend Classification Agent achieves >55% directional accuracy on validation set
- [ ] Support/Resistance Agent identifies 3-5 key levels per ticker with strength scores (**DONE**)
- [ ] All models can be trained and deployed via API
- [ ] Model inference completes in <3 seconds per ticker
- [ ] Walk-forward validation framework operational

---

## Acceptance Criteria (from SoW)

- [ ] Price predictions within 10% of actual price for 1-day horizon (50% of test cases)
- [ ] Trend classification accuracy >55% on out-of-sample data
- [ ] Support/resistance levels validated: >60% show price reactions (**DONE**)
- [ ] Model training pipeline runs without errors
- [ ] API endpoints return predictions in expected format

---

## Dependencies

### Python Packages Required

```
prophet>=1.1.1
tensorflow>=2.13.0
lightgbm>=4.0.0
xgboost>=2.0.0
scikit-learn>=1.3.0
joblib>=1.3.0
```

### Data Dependencies

- Feature Agent (M1) - for technical indicators
- Data Agent (M1) - for OHLCV data
- Context modules (M1) - for market context

---

## Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Price Forecast Agent - Prophet | 1-2 days |
| 1 | Price Forecast Agent - LSTM | 2-3 days |
| 2 | Trend Classification Agent | 2-3 days |
| 3 | Model Serving Infrastructure | 1 day |
| 4 | Testing & Validation | 1-2 days |

---

## Files to Create

```
backend/agents/
├── price_forecast_agent/
│   ├── agent.py                    # REWRITE
│   ├── models/
│   │   ├── __init__.py             # NEW
│   │   ├── prophet_model.py        # NEW
│   │   ├── lstm_model.py           # NEW
│   │   └── model_registry.py       # NEW
│   ├── training/
│   │   ├── __init__.py             # NEW
│   │   ├── trainer.py              # NEW
│   │   └── walk_forward.py         # NEW
│   └── utils/
│       ├── __init__.py             # NEW
│       └── data_prep.py            # NEW
│
├── trend_classification_agent/
│   ├── agent.py                    # REWRITE
│   ├── models/
│   │   ├── __init__.py             # NEW
│   │   ├── lightgbm_classifier.py  # NEW
│   │   └── xgboost_classifier.py   # NEW
│   ├── features/
│   │   ├── __init__.py             # NEW
│   │   └── feature_builder.py      # NEW
│   └── training/
│       ├── __init__.py             # NEW
│       └── trainer.py              # NEW
│
└── api/routes/
    ├── forecast.py                 # NEW
    └── trend.py                    # NEW
```

---

*Document Version: 1.0*
*Created: January 29, 2026*
