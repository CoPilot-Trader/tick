# Quick Start Guide - Level Detection Visualizer

If you're seeing "Failed to fetch" or connection errors, follow these steps:

## ✅ Step 1: Start the Backend Server

Open a terminal and run:

```bash
cd tick/backend
python -m uvicorn api.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Keep this terminal open!** The backend must be running.

## ✅ Step 2: Test Backend Connection

Open your browser and go to:
- http://localhost:8000/api/v1/levels/health

You should see:
```json
{
  "status": "healthy",
  "agent_status": "healthy",
  "agent_initialized": true,
  ...
}
```

If this doesn't work, the backend isn't running properly.

## ✅ Step 3: Test Level Detection API

Test the API endpoint directly:
```bash
curl "http://localhost:8000/api/v1/levels/AAPL?min_strength=50&max_levels=5"
```

You should see JSON with support/resistance levels.

## ✅ Step 4: Open Frontend (Choose ONE method)

### Method A: Using Local Server (RECOMMENDED - Avoids CORS issues)

1. Open a **new terminal** (keep backend running in first terminal)
2. Run:
   ```bash
   cd tick/tools/developer2-level-detection-visualizer
   python -m http.server 8080
   ```
3. Open browser: http://localhost:8080

### Method B: Direct File Open (May have CORS issues)

1. Navigate to: `tick/tools/developer2-level-detection-visualizer/`
2. Double-click `index.html`
3. If you see CORS errors, use Method A instead

## ✅ Step 5: Test the Visualizer

1. In the visualizer page, select a ticker: **AAPL**
2. Set Min Strength: **50**
3. Set Max Levels: **5**
4. Click **"🔍 Detect Levels"**
5. You should see:
   - Current price
   - Nearest support and resistance levels
   - Support levels list (green)
   - Resistance levels list (red)
   - Processing metadata

## 🔧 Common Issues

### Issue 1: "Failed to fetch" Error

**Cause**: Backend not running or wrong URL

**Solution**:
1. Make sure backend is running (Step 1)
2. Check backend is on http://localhost:8000
3. Try opening http://localhost:8000/api/v1/levels/health in browser
4. If health check fails, check backend terminal for errors

### Issue 2: CORS Error

**Cause**: Opening HTML file directly (file:// protocol)

**Solution**: Use Method A (local server) instead of direct file open

### Issue 3: Backend Import Errors

**Cause**: Missing dependencies or wrong Python path

**Solution**:
```bash
cd tick/backend
pip install -r requirements.txt
python -m uvicorn api.main:app --reload
```

### Issue 4: Port Already in Use

**Error**: `Address already in use`

**Solution**: 
1. Find and close the process using port 8000
2. Or change port: `uvicorn api.main:app --reload --port 8001`
3. Update `API_BASE_URL` in `app.js` to match

### Issue 5: "No levels detected" or Empty Results

**Cause**: 
- Min strength too high
- No data available for symbol
- Mock data not generated

**Solution**:
1. Try lowering Min Strength to 30 or 20
2. Try a different symbol (AAPL, TSLA, MSFT, GOOGL, SPY)
3. Check backend logs for data loading errors
4. Verify mock data exists: `tick/backend/agents/support_resistance_agent/tests/mocks/ohlcv_mock_data.json`

### Issue 6: Levels Not Showing Correctly

**Cause**: API response format mismatch

**Solution**:
1. Check browser console (F12) for JavaScript errors
2. Verify API response format matches expected structure
3. Check backend logs for any errors during level detection

## 🧪 Verify Everything Works

Run this test sequence:

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/api/v1/levels/health
   ```
   Should return: `{"status":"healthy",...}`

2. **Test Level Detection Endpoint**:
   ```bash
   curl "http://localhost:8000/api/v1/levels/AAPL?min_strength=50&max_levels=5"
   ```
   Should return JSON with `support_levels` and `resistance_levels` arrays

3. **Open Visualizer**:
   - Use local server (Method A)
   - Select "AAPL"
   - Set Min Strength: 50
   - Set Max Levels: 5
   - Click Detect Levels
   - Should see:
     - Current price display
     - Nearest support/resistance
     - At least 1-2 support levels (green)
     - At least 1-2 resistance levels (red)
     - Processing metadata

## 📊 Understanding the Results

### Current Price
- Shows the latest closing price from the data

### Nearest Support
- The highest support level below current price
- Distance shown as percentage below current price

### Nearest Resistance
- The lowest resistance level above current price
- Distance shown as percentage above current price

### Support/Resistance Levels
- **Price**: The detected level price
- **Strength**: 0-100 score (higher = more reliable)
- **Touches**: Number of times price touched this level
- **Validated**: Whether historical data confirms the level
- **Dates**: First and last time price touched this level

### Strength Score Meaning
- **80-100**: Very strong level (highly reliable)
- **60-79**: Strong level (reliable)
- **40-59**: Moderate level (somewhat reliable)
- **20-39**: Weak level (less reliable)
- **0-19**: Very weak level (questionable)

## 📞 Still Having Issues?

1. Check backend terminal for error messages
2. Check browser console (F12) for detailed error messages
3. Verify Support/Resistance Agent is initialized (check backend logs)
4. Make sure you're using Python 3.9+ and all dependencies are installed
5. Verify mock data file exists and has data for your selected symbol

---

**Remember**: The backend must be running before you can use the visualizer!

**Testing**: If you see empty results, try:
- Lowering Min Strength to 20-30
- Trying different symbols (AAPL, TSLA, MSFT, GOOGL, SPY)
- Checking backend logs for data loading issues
