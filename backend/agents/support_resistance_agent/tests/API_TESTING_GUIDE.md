# Testing Support/Resistance Agent API Endpoints

## Quick Start

### Step 1: Start the Server

Open a terminal and run:

```bash
cd tick/backend
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at: `http://localhost:8000`

### Step 2: Test the Endpoints

You can test the endpoints using:

1. **Python script** (recommended):
   ```bash
   python -m agents.support_resistance_agent.tests.test_api_integration
   ```

2. **cURL commands** (see below)

3. **Browser** (for GET endpoints):
   - Health: http://localhost:8000/api/v1/levels/health
   - Get Levels: http://localhost:8000/api/v1/levels/AAPL?min_strength=50&max_levels=5

## Available Endpoints

### 1. Health Check
**GET** `/api/v1/levels/health`

Check if the agent is healthy and initialized.

**Example:**
```bash
curl http://localhost:8000/api/v1/levels/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "agent_status": "healthy",
  "agent_initialized": true,
  "cache_size": 0,
  "components_initialized": {...}
}
```

---

### 2. Get Levels (GET)
**GET** `/api/v1/levels/{symbol}`

Get support and resistance levels for a symbol.

**Parameters:**
- `symbol` (path): Stock symbol (e.g., AAPL)
- `min_strength` (query, optional): Minimum strength score (0-100), default: 50
- `max_levels` (query, optional): Maximum levels per type, default: 5
- `timeframe` (query, optional): Data timeframe (1m, 1h, 1d, 1w, 1mo, 1y), default: 1d
- `project_future` (query, optional): Predict future levels, default: false
- `projection_periods` (query, optional): Number of periods ahead to project, default: 20
- `lookback_days` (query, optional): Custom lookback period in days

**Example:**
```bash
curl "http://localhost:8000/api/v1/levels/AAPL?min_strength=50&max_levels=5&timeframe=1d&project_future=true"
```

**Expected Response:**
```json
{
  "symbol": "AAPL",
  "timestamp": "2026-01-20T08:00:00Z",
  "current_price": 150.25,
  "support_levels": [
    {
      "price": 142.73,
      "strength": 52,
      "type": "support",
      "touches": 2,
      "validated": true,
      "breakout_probability": 45.2,
      "volume": 1500000,
      "has_volume_confirmation": true,
      "first_touch": "2024-01-15T10:00:00Z",
      "last_touch": "2024-12-20T10:00:00Z",
      "projected_valid_until": "2024-03-15T00:00:00Z"
    }
  ],
  "resistance_levels": [...],
  "total_levels": 4,
  "predicted_future_levels": [...],
  "processing_time_seconds": 0.4,
  "api_metadata": {...}
}
```

---

### 3. Detect Levels (POST)
**POST** `/api/v1/levels/detect`

Detect support and resistance levels (POST request with body).

**Request Body:**
```json
{
  "symbol": "TSLA",
  "min_strength": 50,
  "max_levels": 5,
  "timeframe": "1d",
  "project_future": false,
  "projection_periods": 20,
  "lookback_days": null
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/levels/detect \
  -H "Content-Type: application/json" \
  -d '{"symbol": "TSLA", "min_strength": 50, "max_levels": 5, "timeframe": "1d", "project_future": true}'
```

---

### 4. Get Nearest Levels
**GET** `/api/v1/levels/{symbol}/nearest`

Get the nearest support and resistance levels.

**Parameters:**
- `symbol` (path): Stock symbol
- `min_strength` (query, optional): Minimum strength score, default: 50

**Example:**
```bash
curl "http://localhost:8000/api/v1/levels/MSFT/nearest?min_strength=50"
```

**Expected Response:**
```json
{
  "symbol": "MSFT",
  "current_price": 380.50,
  "nearest_support": 375.00,
  "nearest_resistance": 385.00,
  "api_metadata": {...}
}
```

---

### 5. Batch Detection
**POST** `/api/v1/levels/batch`

Detect levels for multiple symbols at once.

**Request Body:**
```json
{
  "symbols": ["AAPL", "TSLA", "GOOGL"],
  "min_strength": 50,
  "max_levels": 3,
  "timeframe": "1d",
  "project_future": false,
  "projection_periods": 20,
  "lookback_days": null,
  "use_parallel": false
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/levels/batch \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["AAPL", "TSLA", "GOOGL"], "min_strength": 50, "max_levels": 3, "use_parallel": false}'
```

**Expected Response:**
```json
{
  "results": {
    "AAPL": {...},
    "TSLA": {...},
    "GOOGL": {...}
  },
  "api_metadata": {
    "endpoint": "/api/v1/levels/batch",
    "symbols_processed": 3,
    "processing_time_seconds": 0.87,
    "use_parallel": false
  }
}
```

---

## Testing Checklist

- [ ] Health check returns `"status": "healthy"`
- [ ] GET `/api/v1/levels/AAPL` returns levels
- [ ] POST `/api/v1/levels/detect` works with request body
- [ ] GET `/api/v1/levels/MSFT/nearest` returns nearest levels
- [ ] POST `/api/v1/levels/batch` processes multiple symbols
- [ ] All endpoints return proper JSON
- [ ] Error handling works (try invalid symbol)
- [ ] Multi-timeframe support works (test different timeframes)
- [ ] Future level prediction works (test with `project_future=true`)

## Running Tests

### Integration Tests

```bash
# From project root
python -m agents.support_resistance_agent.tests.test_api_integration
```

### Direct Agent Tests

```bash
# From project root
python -m agents.support_resistance_agent.tests.test_agent_integration
```

### Diagnostic Tests

```bash
# Test yfinance connectivity
python -m agents.support_resistance_agent.tests.test_yfinance_diagnostic

# Test direct agent (bypassing API)
python -m agents.support_resistance_agent.tests.test_direct
```

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check for import errors in the console

### Endpoints return errors
- Verify the agent is initialized (check health endpoint)
- Check that mock data exists: `tick/backend/agents/support_resistance_agent/tests/mocks/ohlcv_mock_data.json`
- Look at server logs for detailed error messages

### Connection refused
- Make sure the server is running
- Check the port number (default: 8000)
- Verify firewall settings

### yfinance not working
- Run diagnostic: `python -m agents.support_resistance_agent.tests.test_yfinance_diagnostic`
- Check network connectivity
- Verify yfinance is installed: `pip install yfinance`

## Expected Performance

- Single symbol: ~0.4 seconds
- Batch (5 symbols): ~0.87 seconds
- Cached results: <0.001 seconds
