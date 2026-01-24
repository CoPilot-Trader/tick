# Level Detection Visualizer - Frontend Guide

**Complete Guide to Understanding the Frontend Interface**  
**Version**: 1.0  
**Last Updated**: January 2026

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Input Section - Parameters Explained](#input-section---parameters-explained)
3. [Output Sections - What You See](#output-sections---what-you-see)
4. [Level Card Details - Field by Field](#level-card-details---field-by-field)
5. [Color Coding & Visual Indicators](#color-coding--visual-indicators)
6. [Data Source Indicator](#data-source-indicator)
7. [How to Interpret Results](#how-to-interpret-results)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### What is the Visualizer?

The Level Detection Visualizer is a **standalone web tool** that provides a user-friendly interface to interact with the Level Detection backend API. It displays support and resistance levels detected for any stock symbol in an easy-to-understand format.

### Purpose

- **Visualize** detected support/resistance levels
- **Understand** level strength and reliability
- **Analyze** breakout probabilities
- **View** predicted future levels
- **Monitor** data source (real-time vs mock data)

### How It Works

1. **User Input**: Select stock, set parameters, click "Detect Levels"
2. **API Request**: Frontend sends request to backend API
3. **Backend Processing**: Backend analyzes historical data and detects levels
4. **Response Display**: Frontend displays results in organized, color-coded cards

---

## Input Section - Parameters Explained

### 1. Stock Ticker

**What it is:**
- Dropdown menu with 30+ popular stock symbols
- Includes major tech, energy, healthcare, finance, and consumer stocks

**Why it's important:**
- Determines which stock to analyze
- Each stock has different price patterns and levels

**How to use:**
- Select a stock from the dropdown (e.g., "AAPL - Apple Inc.")
- The symbol (AAPL) is sent to the backend

**Example:**
```
Selected: "AAPL - Apple Inc."
Backend receives: "AAPL"
```

---

### 2. Min Strength (0-100)

**What it is:**
- Minimum strength score required for a level to be displayed
- Range: 0 to 100
- Default: 50

**What it means:**
- **Strength Score** = Reliability of the level (0-100)
  - 80-100: Very strong level (highly reliable)
  - 60-79: Strong level (reliable)
  - 40-59: Moderate level (somewhat reliable)
  - 20-39: Weak level (less reliable)
  - 0-19: Very weak level (unreliable)

**Why it's important:**
- Filters out weak/unreliable levels
- Focuses on the most important levels
- Higher min strength = fewer but more reliable levels

**How to use:**
- **Lower value (30-40)**: Shows more levels, including weaker ones
- **Default (50)**: Balanced view, shows moderate+ strength levels
- **Higher value (70-80)**: Shows only the strongest, most reliable levels

**Example:**
```
Min Strength: 50
Result: Shows levels with strength ≥ 50
- $145.00 (Strength: 94) ✅ Shown
- $142.50 (Strength: 78) ✅ Shown
- $140.00 (Strength: 45) ❌ Hidden (below 50)
```

---

### 3. Max Levels (1-20)

**What it is:**
- Maximum number of levels to show per type (support or resistance)
- Range: 1 to 20
- Default: 5

**What it means:**
- Limits the number of support levels shown
- Limits the number of resistance levels shown
- Levels are sorted by strength (highest first)

**Why it's important:**
- Prevents information overload
- Focuses on the most important levels
- Keeps the display clean and readable

**How to use:**
- **Lower value (1-3)**: Shows only the top 1-3 strongest levels
- **Default (5)**: Shows top 5 levels (balanced view)
- **Higher value (10-20)**: Shows more levels for detailed analysis

**Example:**
```
Max Levels: 5
Result: Shows top 5 support levels and top 5 resistance levels
- Support: Top 5 strongest support levels
- Resistance: Top 5 strongest resistance levels
```

---

### 4. Timeframe

**What it is:**
- The time interval for each data point
- Options: 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w, 1mo, 1y
- Default: 1d (1 day)

**What it means:**
- **1m**: 1-minute candles (for day traders)
- **5m, 15m, 30m**: 5/15/30-minute candles (for intraday traders)
- **1h, 4h**: 1-hour and 4-hour candles (for swing traders)
- **1d**: Daily candles (for position traders)
- **1w, 1mo, 1y**: Weekly/monthly/yearly candles (for investors)

**Why it's important:**
- Different timeframes show different levels
- Short-term timeframes (1m-1h): Show intraday levels
- Long-term timeframes (1d-1y): Show major support/resistance levels
- Affects lookback period automatically

**How to use:**
- **Day Trading**: Use 1m, 5m, 15m, 30m
- **Swing Trading**: Use 1h, 4h, 1d
- **Investing**: Use 1d, 1w, 1mo, 1y

**Example:**
```
Timeframe: 1d
Lookback: 730 days (2 years) - automatic
Result: Daily price levels over 2 years
```

---

### 5. Predict Future Levels (Checkbox)

**What it is:**
- Checkbox to enable future level prediction
- Default: Unchecked (disabled)

**What it means:**
- When enabled, the system predicts where new support/resistance levels might form
- Uses multiple methods:
  - **Fibonacci Retracements**: Mathematical levels (23.6%, 38.2%, 50%, 61.8%, 78.6%)
  - **Round Numbers**: Psychological levels ($100, $150, $200, etc.)
  - **Spacing Patterns**: Based on historical level spacing

**Why it's important:**
- Helps identify potential future trading opportunities
- Shows where price might find support/resistance in the future
- Useful for planning entry/exit points

**How to use:**
- Check the box to enable predictions
- When checked, "Projection Periods" input appears
- Predictions appear in a separate "Predicted Future Levels" section

**Example:**
```
Predict Future Levels: ✅ Checked
Projection Periods: 20
Result: Shows predicted levels for next 20 periods
```

---

### 6. Projection Periods (1-100)

**What it is:**
- Number of periods ahead to predict
- Range: 1 to 100
- Default: 20
- Only visible when "Predict Future Levels" is checked

**What it means:**
- **For 1d timeframe**: 20 periods = 20 days ahead
- **For 1h timeframe**: 20 periods = 20 hours ahead
- **For 1m timeframe**: 20 periods = 20 minutes ahead

**Why it's important:**
- Determines how far into the future to predict
- Longer periods = less accurate but longer-term view
- Shorter periods = more accurate but shorter-term view

**How to use:**
- **Short-term (5-10)**: Predictions for next few periods (more accurate)
- **Medium-term (20-30)**: Balanced view (default)
- **Long-term (50-100)**: Long-range predictions (less accurate)

**Example:**
```
Timeframe: 1d
Projection Periods: 20
Result: Predicts levels for next 20 days
```

---

### 7. Lookback Days (Optional)

**What it is:**
- Custom historical data range (in days)
- Range: 1 to 3,650 days (10 years)
- Optional: Leave empty to use default based on timeframe

**What it means:**
- **If empty**: Uses default lookback based on timeframe
  - 1m, 5m, 15m, 30m: 30 days
  - 1h, 4h: 90 days
  - 1d: 730 days (2 years)
  - 1w: 1,095 days (3 years)
  - 1mo: 1,825 days (5 years)
  - 1y: 3,650 days (10 years)
- **If specified**: Uses your custom value

**Why it's important:**
- More data = more accurate levels (usually)
- But: Too much data can slow down processing
- Minute-level data: Limited to 5-7 days (yfinance restriction)

**How to use:**
- **Leave empty**: Use default (recommended for most cases)
- **Specify value**: When you need specific time period
  - Example: 100 days for recent analysis
  - Example: 1825 days for 5-year analysis

**Example:**
```
Timeframe: 1d
Lookback Days: (empty)
Result: Uses default 730 days (2 years)

Timeframe: 1d
Lookback Days: 100
Result: Uses 100 days (custom)
```

---

## Output Sections - What You See

### 1. Current Price & Nearest Levels

**What it shows:**
- **Current Price**: Current market price of the stock
- **Nearest Support**: Closest support level below current price
- **Nearest Resistance**: Closest resistance level above current price
- **Distance**: Percentage distance from current price

**Why it's important:**
- Quick reference for current market position
- Shows immediate support/resistance levels
- Helps with quick trading decisions

**Example Display:**
```
Current Price: $150.00 (AAPL)

Nearest Support: $145.00
3.33% below

Nearest Resistance: $155.00
3.33% above
```

**What it means:**
- Price is currently at $150.00
- If price drops, $145.00 is the nearest support (3.33% below)
- If price rises, $155.00 is the nearest resistance (3.33% above)

---

### 2. Support Levels Section

**What it shows:**
- List of all detected support levels
- Sorted by price (highest to lowest)
- Each level displayed in a card with detailed information

**Why it's important:**
- Support levels = Price floors (where price bounces up)
- Useful for:
  - Setting stop-loss orders (below support)
  - Finding entry points (near support)
  - Identifying risk levels

**Visual Indicators:**
- 🟢 Green badge: "Support"
- Green color scheme throughout the card

---

### 3. Resistance Levels Section

**What it shows:**
- List of all detected resistance levels
- Sorted by price (lowest to highest)
- Each level displayed in a card with detailed information

**Why it's important:**
- Resistance levels = Price ceilings (where price bounces down)
- Useful for:
  - Setting take-profit targets (at resistance)
  - Finding exit points (near resistance)
  - Identifying profit levels

**Visual Indicators:**
- 🔴 Red badge: "Resistance"
- Red color scheme throughout the card

---

### 4. Predicted Future Levels Section

**What it shows:**
- Predicted support levels (future)
- Predicted resistance levels (future)
- Only appears when "Predict Future Levels" is checked

**Why it's important:**
- Shows where new levels might form
- Helps plan future trading strategies
- Identifies potential entry/exit points

**Visual Indicators:**
- 🔮 Blue badge: "PREDICTED"
- Shows confidence percentage
- Shows source (fibonacci, round_number, spacing_pattern)

**Example:**
```
Predicted Support: $225.00
Confidence: 50.0%
Source: round number
Timeframe: 20 periods
```

---

### 5. Processing Information (Metadata)

**What it shows:**
- Total Levels: Total number of levels detected
- Support Levels: Count of support levels
- Resistance Levels: Count of resistance levels
- Timeframe: Selected timeframe
- Lookback Days: Actual lookback used (with source indicator)
- Data Source: Real-time or mock data indicator
- Peaks Detected: Number of peaks found
- Valleys Detected: Number of valleys found
- Data Points: Number of historical data points analyzed
- Processing Time: Time taken to detect levels
- API Response Time: Total API call time

**Why it's important:**
- Transparency about the analysis
- Shows data quality (data points, data source)
- Performance metrics (processing time)
- Validation of results (peaks/valleys detected)

---

## Level Card Details - Field by Field

Each level is displayed in a card with the following information:

### 1. Price

**What it is:**
- The exact price level (e.g., $145.00)
- Displayed prominently at the top of the card

**Why it's important:**
- The key information: where the level is
- Used for setting orders and targets

**Example:**
```
$145.00
```

---

### 2. Strength (0-100)

**What it is:**
- Reliability score of the level (0-100)
- Displayed as: "Strength: 64/100"
- Visual progress bar with color coding

**What it means:**
- **80-100**: Very strong level (highly reliable) 🟢
- **60-79**: Strong level (reliable) 🟡
- **40-59**: Moderate level (somewhat reliable) 🟠
- **20-39**: Weak level (less reliable) 🔴
- **0-19**: Very weak level (unreliable) 🔴

**Why it's important:**
- Higher strength = more reliable level
- Helps prioritize which levels to use
- Stronger levels are more likely to hold

**Example:**
```
Strength: 64/100
[████████████████░░░░] 64%
Color: Light green (moderate-strong)
```

---

### 3. Breakout Probability (0-100%)

**What it is:**
- Probability that price will break through this level
- Displayed as: "Breakout Probability: 55.6%"
- Visual progress bar with color coding

**What it means:**
- **0-30%**: Low probability (level likely to hold) 🟢
- **30-50%**: Moderate probability (level might break) 🟡
- **50-70%**: High probability (level likely to break) 🟠
- **70-100%**: Very high probability (level will break) 🔴

**Why it's important:**
- **For Support**: Low breakout probability = strong support (good for buying)
- **For Resistance**: High breakout probability = weak resistance (price might break through)
- Helps assess risk and opportunity

**Example:**
```
Breakout Probability: 55.6%
[██████████████████░░] 55.6%
Color: Orange (moderate-high probability)
```

---

### 4. Touches

**What it is:**
- Number of times price has touched this level
- Displayed as: "Touches: 362"

**What it means:**
- More touches = more significant level
- Shows how often price reacted at this level
- Higher touch count = stronger level (usually)

**Why it's important:**
- Validates the level's importance
- More touches = more reliable level
- Helps confirm level strength

**Example:**
```
Touches: 362
Meaning: Price touched this level 362 times in the historical data
```

---

### 5. Validated (Yes/No)

**What it is:**
- Whether the level has been validated against historical data
- Displayed as: "✓ Yes" (green) or "✗ No" (red)

**What it means:**
- **Yes**: Price actually reacted at this level in the past
  - Support: Price bounced UP after touching
  - Resistance: Price bounced DOWN after touching
- **No**: Level detected but not validated (may be less reliable)

**Why it's important:**
- Validated levels are more reliable
- Shows the level actually worked in the past
- Helps filter out false signals

**Example:**
```
Validated: ✓ Yes
Meaning: Historical data confirms this level worked (price reacted)
```

---

### 6. Validation Rate (0-100%)

**What it is:**
- Percentage of successful reactions at this level
- Displayed as: "Validation Rate: 50%"
- Only shown if validation rate > 0

**What it means:**
- **80-100%**: Excellent validation (level works very well)
- **60-79%**: Good validation (level works well)
- **40-59%**: Moderate validation (level works sometimes)
- **0-39%**: Poor validation (level doesn't work well)

**Why it's important:**
- Higher validation rate = more reliable level
- Shows how consistently the level worked
- Helps assess level quality

**Example:**
```
Validation Rate: 50%
Meaning: 50% of touches resulted in price reactions
```

---

### 7. Volume Information

**What it shows:**
- **Volume Percentile**: Ranking of volume at this level (0-100%)
- **Volume**: Actual trading volume at this level
- **Confirmed Badge**: If volume confirms the level

**What it means:**
- **High Volume Percentile (80-100%)**: Lots of trading at this level
- **Low Volume Percentile (0-40%)**: Less trading at this level
- **Confirmed**: High volume confirms this is a significant level

**Why it's important:**
- High volume = more significant level
- Volume confirmation adds reliability
- Helps identify major support/resistance zones

**Example:**
```
Volume Information:
📊 Volume Percentile: 95.1%
Volume: 35.4M
✓ Confirmed
Meaning: Very high trading volume at this level (top 5%)
```

---

### 8. First Touch & Last Touch

**What it is:**
- **First Touch**: Date when price first touched this level
- **Last Touch**: Date when price last touched this level
- Displayed as formatted dates (e.g., "Jan 15, 2023")

**What it means:**
- Shows the time span of this level
- Recent last touch = level is still active
- Old last touch = level might be outdated

**Why it's important:**
- Recent touches = more relevant level
- Time span shows level's history
- Helps assess if level is still valid

**Example:**
```
First Touch: Jan 15, 2023
Last Touch: Dec 5, 2023
Meaning: Level was active from Jan 2023 to Dec 2023
```

---

### 9. Level Projection (If Enabled)

**What it shows:**
- **Valid Until**: Estimated date when level becomes invalid
- **Validity Probability**: Probability level is still valid (0-100%)
- **Projected Strength**: Estimated future strength score

**What it means:**
- Predicts how long the level will remain valid
- Estimates future reliability
- Helps plan long-term strategies

**Why it's important:**
- Levels don't last forever
- Helps identify when levels might expire
- Useful for longer-term trading

**Example:**
```
⏱️ Level Projection
Valid Until: Mar 15, 2024
Validity Probability: 85.5%
Projected Strength: 89.2/100
Meaning: Level should remain valid until March 2024 with 85.5% probability
```

---

## Color Coding & Visual Indicators

### Strength Colors

- **🟢 Green (80-100)**: Very strong level
- **🟡 Light Green (60-79)**: Strong level
- **🟠 Amber (40-59)**: Moderate level
- **🔴 Orange (20-39)**: Weak level
- **🔴 Red (0-19)**: Very weak level

### Breakout Probability Colors

- **🟢 Green (0-30%)**: Low probability (level likely to hold)
- **🟡 Amber (30-50%)**: Moderate probability
- **🟠 Orange (50-70%)**: High probability (level might break)
- **🔴 Red (70-100%)**: Very high probability (level will break)

### Level Type Badges

- **🟢 Green "Support"**: Support level (price bounces up)
- **🔴 Red "Resistance"**: Resistance level (price bounces down)
- **🔮 Blue "PREDICTED"**: Predicted future level

### Validation Status

- **✓ Yes (Green)**: Level validated (confirmed by history)
- **✗ No (Red)**: Level not validated (may be less reliable)

---

## Data Source Indicator

### What It Shows

The metadata section displays the data source with an icon and label:

- **🌐 Green "Yahoo Finance (Real-time)"**: Using real-time data from yfinance
- **🔗 Green "Data Agent (Internal)"**: Using internal data service
- **📊 Orange "Mock Data (Test)"**: Using test/mock data

### Why It's Important

- **Real-time data**: More accurate, current market data
- **Mock data**: Test data, may not reflect current market
- Helps you know if results are based on real or test data

### How to Interpret

- **Green indicators**: Real-time data (preferred)
- **Orange indicators**: Mock/test data (for development/testing)

---

## How to Interpret Results

### Scenario 1: Strong Support Level

**What you see:**
```
Support Level: $145.00
Strength: 94/100 (Very Strong 🟢)
Breakout Probability: 25.5% (Low 🟢)
Touches: 362
Validated: ✓ Yes
```

**What it means:**
- Very reliable support level
- Low chance of breaking through
- Good entry point for buying
- Set stop-loss below $145.00

**Trading Action:**
- ✅ **Buy** near $145.00
- ✅ **Stop-Loss** at $142.50 (below support)
- ✅ **Take-Profit** at nearest resistance

---

### Scenario 2: Weak Resistance Level

**What you see:**
```
Resistance Level: $155.00
Strength: 45/100 (Moderate 🟠)
Breakout Probability: 75.2% (High 🔴)
Touches: 12
Validated: ✗ No
```

**What it means:**
- Weak resistance level
- High chance of breaking through
- Price might break above this level
- Not a good take-profit target

**Trading Action:**
- ⚠️ **Don't** set take-profit at $155.00
- ✅ **Watch** for breakout above $155.00
- ✅ **Target** higher resistance level

---

### Scenario 3: Predicted Future Level

**What you see:**
```
Predicted Support: $225.00
Confidence: 50.0%
Source: round number
Timeframe: 20 periods
```

**What it means:**
- Potential future support level
- Based on round number (psychological level)
- 50% confidence (moderate)
- Might form in next 20 periods

**Trading Action:**
- ⚠️ **Monitor** price approaching $225.00
- ✅ **Prepare** to buy if price reaches this level
- ⚠️ **Don't** rely solely on predictions (use with caution)

---

## Troubleshooting

### Issue: "No levels detected with current filters"

**Possible Causes:**
1. **Min Strength too high**: Lower the min strength (try 30-40)
2. **Insufficient data**: Check data source and lookback days
3. **No valid levels**: Stock might not have clear support/resistance

**Solution:**
- Lower "Min Strength" to 30-40
- Check "Data Points" in metadata (should be >100)
- Try a different stock symbol

---

### Issue: "Failed to fetch" Error

**Possible Causes:**
1. **Backend not running**: Backend server is not started
2. **Wrong API URL**: Check if backend is on port 8000
3. **Network issue**: Check internet connection

**Solution:**
1. Start backend server: `cd tick/backend && uvicorn api.main:app --reload`
2. Check browser console for detailed error
3. Verify backend is accessible at `http://localhost:8000`

---

### Issue: Frontend keeps reloading / No results

**Possible Causes:**
1. **Large lookback period**: Too much data to process
2. **Timeout**: Request taking too long (>60 seconds)
3. **Backend error**: Check backend logs

**Solution:**
1. Reduce "Lookback Days" (try 30-100 days)
2. Check backend terminal for errors
3. Try a shorter timeframe (1d instead of 1y)

---

### Issue: Shows "Mock Data" but want real data

**Possible Causes:**
1. **yfinance not installed**: Backend can't fetch real data
2. **yfinance failed**: API error or rate limit
3. **Data Agent not available**: Internal data service not ready

**Solution:**
1. Install yfinance: `pip install yfinance`
2. Check backend logs for yfinance errors
3. Wait for Data Agent integration (when ready)

---

### Issue: Predicted levels not showing

**Possible Causes:**
1. **Checkbox not checked**: "Predict Future Levels" must be enabled
2. **No predictions available**: System couldn't predict levels
3. **Projection periods too short**: Try increasing projection periods

**Solution:**
1. Check "Predict Future Levels" checkbox
2. Increase "Projection Periods" to 20-30
3. Check if timeframe has enough data

---

## Summary

### Key Takeaways

1. **Input Parameters**: Control what levels are detected and displayed
2. **Strength Score**: Higher = more reliable level
3. **Breakout Probability**: Lower for support = better, higher for resistance = might break
4. **Validation**: Validated levels are more reliable
5. **Data Source**: Green = real data, Orange = mock data
6. **Color Coding**: Green = good, Red = warning

### Best Practices

- **Start with defaults**: Min Strength 50, Max Levels 5, Timeframe 1d
- **Adjust gradually**: Change one parameter at a time
- **Check data source**: Ensure you're using real data for trading
- **Validate levels**: Prefer validated levels (✓ Yes)
- **Consider strength**: Focus on levels with strength ≥ 60

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Status**: Complete ✅
