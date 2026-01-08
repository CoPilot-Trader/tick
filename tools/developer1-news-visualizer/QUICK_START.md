# Quick Start Guide - Troubleshooting "Failed to fetch"

If you're seeing "Failed to connect to backend: Failed to fetch", follow these steps:

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
- http://localhost:8000/health

You should see:
```json
{"status":"healthy"}
```

If this doesn't work, the backend isn't running properly.

## ✅ Step 3: Open Frontend (Choose ONE method)

### Method A: Using Local Server (RECOMMENDED - Avoids CORS issues)

1. Open a **new terminal** (keep backend running in first terminal)
2. Run:
   ```bash
   cd tick/Developer1-News-Sentiment-Agents/frontend-visualizer
   python -m http.server 8080
   ```
3. Open browser: http://localhost:8080

### Method B: Direct File Open (May have CORS issues)

1. Navigate to: `tick/Developer1-News-Sentiment-Agents/frontend-visualizer/`
2. Double-click `index.html`
3. If you see CORS errors, use Method A instead

## ✅ Step 4: Test the Visualizer

1. In the visualizer page, enter a ticker: **AAPL**
2. Click **"🚀 Process Pipeline"**
3. You should see the pipeline steps appear

## 🔧 Common Issues

### Issue 1: "Failed to fetch" Error

**Cause**: Backend not running or wrong URL

**Solution**:
1. Make sure backend is running (Step 1)
2. Check backend is on http://localhost:8000
3. Try opening http://localhost:8000/health in browser
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

## 🧪 Verify Everything Works

Run this test sequence:

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```
   Should return: `{"status":"healthy"}`

2. **Test Pipeline Endpoint**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/news-pipeline/visualize -H "Content-Type: application/json" -d "{\"symbol\":\"AAPL\",\"min_relevance\":0.3,\"max_articles\":5}"
   ```
   Should return JSON with pipeline steps

3. **Open Visualizer**:
   - Use local server (Method A)
   - Enter "AAPL"
   - Click Process
   - Should see 3 steps appear

## 📞 Still Having Issues?

1. Check backend terminal for error messages
2. Check browser console (F12) for detailed error messages
3. Verify all agents are initialized (check backend logs)
4. Make sure you're using Python 3.9+ and all dependencies are installed

---

**Remember**: The backend must be running before you can use the visualizer!

