# Developer 2 - Level Detection Visualizer

Frontend visualization tool for the Support/Resistance Level Detection Agent.

## Purpose

This tool provides visualization of:
- **Support Levels** - Price levels where stocks tend to find support (bounce up)
- **Resistance Levels** - Price levels where stocks tend to find resistance (bounce down)
- **Strength Scores** - Reliability scores (0-100) for each detected level
- **Nearest Levels** - Closest support and resistance levels to current price
- **Processing Metadata** - Detection pipeline statistics

## Features

- Real-time level detection visualization
- Support and resistance level display with strength scores
- Nearest levels calculation and display
- Current price tracking
- Visual strength indicators (color-coded progress bars)
- Level validation status
- Touch count tracking (number of times price touched each level)
- Processing time and metadata display
- Support for multiple stock tickers

## Quick Start

See `QUICK_START.md` for detailed setup instructions.

### Quick Setup

1. **Start the backend server:**
   ```bash
   cd tick/backend
   python -m uvicorn api.main:app --reload
   ```

2. **Open the visualizer:**
   - Option A: Use local server (recommended)
     ```bash
     cd tick/tools/developer2-level-detection-visualizer
     python -m http.server 8080
     ```
     Then open: http://localhost:8080
   
   - Option B: Open `index.html` directly (may have CORS issues)

3. **Use the visualizer:**
   - Select a stock ticker from dropdown
   - Set Min Strength (0-100) and Max Levels (1-20)
   - Click "Detect Levels"
   - View support/resistance levels with strength scores

## Files

- `index.html` - Main HTML file
- `app.js` - Frontend JavaScript (API calls, rendering)
- `styles.css` - Styling
- `README.md` - This file
- `QUICK_START.md` - Detailed setup and troubleshooting

## API Endpoint

The visualizer connects to:
```
GET http://localhost:8000/api/v1/levels/{symbol}?min_strength=50&max_levels=5
```

## Features Displayed

### Current Price & Nearest Levels
- Current stock price
- Nearest support level (below current price)
- Nearest resistance level (above current price)
- Distance from current price (as percentage)

### Support Levels
- Price level (in USD)
- Strength score (0-100) with visual bar
- Touch count (number of times price touched this level)
- Validation status (verified by historical data)
- First and last touch dates

### Resistance Levels
- Same information as support levels
- Displayed separately in red theme

### Processing Metadata
- Total levels detected
- Support/Resistance level counts
- Peaks and valleys detected during analysis
- Data points analyzed
- Processing time (seconds)
- API response time

## Color Coding

- **Support Levels**: Green theme (#4CAF50)
- **Resistance Levels**: Red theme (#f44336)
- **Strength Scores**: 
  - 80-100: Dark green (Very strong)
  - 60-79: Light green (Strong)
  - 40-59: Amber (Moderate)
  - 20-39: Orange (Weak)
  - 0-19: Red (Very weak)

## Troubleshooting

See `QUICK_START.md` for common issues and solutions.

## Notes

- This is a **development tool** for visualizing level detection
- Requires backend server to be running
- Not part of the main production frontend
- Useful for debugging and development
- Uses mock data for testing (when Data Agent is not available)

## Developer

**Developer 2** - Level Detection & Prediction Agents
