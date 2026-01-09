# Developer 1 - News Pipeline Visualizer

Frontend visualization tool for the News & Sentiment Agents pipeline.

## Purpose

This tool provides a step-by-step visualization of:
- **News Fetch Agent** - News collection from multiple sources
- **LLM Sentiment Agent** - Sentiment analysis with caching
- **Sentiment Aggregator** - Sentiment aggregation

## Features

- Real-time pipeline visualization
- API usage tracking display
- Detailed metrics for each step
- Error reporting with stack traces
- Support for multiple stock tickers

## Quick Start

See `QUICK_START.md` for detailed setup instructions.

### Quick Setup

1. **Start the backend server:**
   ```bash
   cd backend
   python -m uvicorn api.main:app --reload
   ```

2. **Open the visualizer:**
   - Option A: Use local server (recommended)
     ```bash
     cd tools/developer1-news-visualizer
     python -m http.server 8080
     ```
     Then open: http://localhost:8080
   
   - Option B: Open `index.html` directly (may have CORS issues)

3. **Use the visualizer:**
   - Select a stock ticker from dropdown
   - Set Min Relevance and Max Articles
   - Click "Process Pipeline"
   - View step-by-step results

## Files

- `index.html` - Main HTML file
- `app.js` - Frontend JavaScript (API calls, rendering)
- `styles.css` - Styling
- `README.md` - This file
- `QUICK_START.md` - Detailed setup and troubleshooting

## API Endpoint

The visualizer connects to:
```
POST http://localhost:8000/api/v1/news-pipeline/visualize
```

## Features Displayed

### Step 1: News Fetch Agent
- Raw articles count
- Final articles count (after filtering)
- Sources used
- Data source (Mock/Real API)
- API usage for each source (remaining calls, limits)

### Step 2: LLM Sentiment Agent
- Articles processed
- Cache hits/misses
- Cache hit rate
- Sentiment scores

### Step 3: Sentiment Aggregator
- Aggregated sentiment score
- Impact level
- Time-weighted aggregation details

## Troubleshooting

See `QUICK_START.md` for common issues and solutions.

## Notes

- This is a **development tool** for visualizing the pipeline
- Requires backend server to be running
- Not part of the main production frontend
- Useful for debugging and development

## Developer

**Developer 1** - News & Sentiment Agents
