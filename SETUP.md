# TICK - Setup & Run Guide

Single-source setup document. Follow these steps to get the entire system running.

## Prerequisites

- **Docker Desktop** installed and running
- **Git** to clone the repository
- Ports **3000**, **5433**, **6380**, **8000** available on your machine

## 1. Clone & Navigate

```bash
git clone https://github.com/CoPilot-Trader/tick.git
cd tick
git checkout feature/level-detection
```

## 2. Environment Variables

The system ships with default API keys in `docker-compose.yml`. To use your own keys, create a `.env` file in the project root:

```bash
# .env (optional - defaults are provided in docker-compose.yml)

# News & Sentiment data sources
FINNHUB_API_KEY=d5d3rmpr01qvl80nhh40d5d3rmpr01qvl80nhh4g
NEWSAPI_KEY=6fd53b5d6c584a2d9052bcf48988d9be
ALPHA_VANTAGE_API_KEY=2JSGRZ6R9VRMW7OL

# Price data sources
TIINGO_API_KEY=9e7e7ef41ad8cefe4bfa3f57e7bb60b5d81e3d14
FMP_API_KEY=W8Qj3LfEWEh5EGBo8gBlCQ4QNT36rZ8j
```

These are auto-loaded by Docker Compose. If you don't create a `.env` file, the defaults above are used.

**Internal variables (set automatically, no action needed):**

| Variable | Value | Purpose |
|----------|-------|---------|
| `DATABASE_URL` | `postgresql://tick_user:tick_password@timescaledb:5432/tick_db` | TimescaleDB connection |
| `REDIS_URL` | `redis://redis:6379/0` | Redis cache connection |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend -> Backend URL |

## 3. Start Everything

```bash
docker compose up --build -d
```

This starts 4 containers:

| Container | Port | Purpose |
|-----------|------|---------|
| `tick-db` | 5433 | TimescaleDB (time-series PostgreSQL) |
| `tick-redis` | 6380 | Redis (caching layer) |
| `tick-backend` | 8000 | FastAPI backend (12 AI agents) |
| `tick-frontend` | 3000 | Next.js dashboard |

First build takes ~5 minutes (downloads dependencies). Subsequent starts are fast.

## 4. Verify

Wait ~30 seconds for all services to initialize, then:

```bash
# Backend health
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Real OHLCV data (last trading day, 5-min bars)
curl "http://localhost:8000/api/v1/data/AAPL/ohlcv?timeframe=5m&days=1"

# Price forecast
curl "http://localhost:8000/api/v1/forecast/AAPL?horizons=1h&use_baseline=true&use_ensemble=false"

# Support/Resistance levels
curl "http://localhost:8000/api/v1/levels/AAPL"
```

Open the dashboard: **http://localhost:3000**

## 5. What You'll See

### Dashboard (http://localhost:3000)
- Select a stock ticker (AAPL, TSLA, MSFT, GOOGL, SPY)
- Price chart with real 5-minute intraday data from the last trading day
- Predicted price line extending 1 hour into the future
- Support/resistance levels as horizontal reference lines

### Other Pages
| Page | URL | What It Shows |
|------|-----|---------------|
| Levels | http://localhost:3000/levels | Support & resistance level detection |
| Pipeline | http://localhost:3000/pipeline | Live news fetch & sentiment analysis |
| Fusion | http://localhost:3000/fusion | Combined trading signal (BUY/SELL/HOLD) |
| Backtest | http://localhost:3000/backtest | Historical strategy simulation |
| Alerts | http://localhost:3000/alerts | Alert rules & triggered alerts |

## 6. API Endpoints Reference

All endpoints are at `http://localhost:8000`. Key ones:

```
GET  /health                                        System health
GET  /api/v1/data/{symbol}/ohlcv?timeframe=5m&days=1   OHLCV price data
GET  /api/v1/forecast/{symbol}?horizons=1h              Price prediction
GET  /api/v1/trend/{symbol}?timeframe=1d                Trend classification
GET  /api/v1/levels/{symbol}                            Support/resistance
GET  /api/v1/sentiment/{symbol}                         Sentiment analysis
GET  /api/v1/fusion/{symbol}/quick                      Fused trading signal
GET  /api/v1/backtest/{symbol}/quick?days=180           Quick backtest
GET  /api/v1/alerts                                     List alerts
GET  /api/v1/alerts/rules                               Alert rules
POST /api/v1/news-pipeline/visualize                    News pipeline
     Body: {"symbol":"AAPL","min_relevance":0.3,"max_articles":5}
```

## 7. Stop & Clean Up

```bash
# Stop all containers
docker compose down

# Stop and remove data volumes (full reset)
docker compose down -v
```

## Troubleshooting

**Port conflict on 5433:** Local PostgreSQL may use 5432. We map to 5433 to avoid this. If 5433 is also taken, edit the port in `docker-compose.yml`.

**Backend shows "mock data":** On first start, yfinance may take a moment to initialize. Restart the backend container: `docker compose restart backend`

**Build fails with network errors:** Docker needs internet access to pull base images and pip/npm packages. Check your connection and retry.

**Old containers conflict:** If you see containers named `tick_timescaledb` or `tick_redis` from a previous setup: `docker rm -f tick_timescaledb tick_redis` then retry.
