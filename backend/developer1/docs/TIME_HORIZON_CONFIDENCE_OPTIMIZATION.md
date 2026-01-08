# Time Horizon & Confidence Score Optimization

**Date**: January 2026  
**Developer**: Developer 1  
**Status**: ✅ Implementation Guide

## Overview

This document explains how the News & Sentiment Agents select appropriate date ranges based on user-selected time horizons and how the system optimizes for maximum confidence scores in predictions.

## How Time Horizon Selection Works

### 1. User Selection → Date Range Calculation

When a user selects a time horizon in the overall project interface:

```
User selects: "1 minute" → time_horizon = "1m"
```

The system automatically:

1. **Calculates Date Range** (`DateRangeCalculator`)
   - Maps time horizon to appropriate news window
   - Fetches news from that window only
   - Ensures news is relevant to the prediction timeframe

2. **Applies Time Weighting** (`TimeWeightedAggregator`)
   - Adjusts decay rates based on horizon
   - Weights recent news more heavily
   - Filters out outdated news

3. **Calculates Confidence** (`ImpactScorer` + `TimeWeightedAggregator`)
   - Considers news recency
   - Considers news volume
   - Considers sentiment strength
   - Considers time alignment with horizon

---

## Time Horizon → Date Range Mapping

| User Selection | Time Horizon | News Window | Rationale |
|----------------|-------------|-------------|-----------|
| **1 second** | `1s` | Last 5 minutes | Breaking news only - flash events |
| **1 minute** | `1m` | Last 15 minutes | Very recent news - real-time trading |
| **1 hour** | `1h` | Last 6 hours | Intraday news - hourly predictions |
| **1 day** | `1d` | Last 3 days | Daily news cycle - daily predictions |
| **1 week** | `1w` | Last 7 days | Weekly trends - weekly predictions |
| **1 month** | `1mo` | Last 30 days | Monthly trends - monthly predictions |
| **1 year** | `1y` | Last 365 days | Long-term trends - yearly predictions |

### Why These Windows?

**Short Horizons (1s, 1m, 1h):**
- Need very recent news (last few minutes/hours)
- Old news is irrelevant for immediate predictions
- Market reacts quickly to breaking news

**Medium Horizons (1d, 1w):**
- Need recent news but can include slightly older articles
- Daily/weekly patterns matter
- News from 2-3 days ago can still be relevant

**Long Horizons (1mo, 1y):**
- Need broader news window
- Long-term trends matter more than daily fluctuations
- Historical context is important

---

## Confidence Score Calculation

### Current Implementation

The confidence score is calculated using multiple factors:

#### 1. **Time Alignment** (Automatic)
```python
# TimeWeightedAggregator adjusts based on horizon
if time_horizon == "1m":
    half_life = 0.1 hours  # 6 minutes - very fast decay
    max_age = 0.5 hours    # 30 minutes max
elif time_horizon == "1d":
    half_life = 24 hours   # 1 day - moderate decay
    max_age = 72 hours     # 3 days max
```

**How it works:**
- Recent articles get higher weights (closer to 1.0)
- Older articles get lower weights (closer to 0.0)
- Articles beyond `max_age` are excluded (weight = 0.0)

#### 2. **Recency Score** (ImpactScorer)
```python
recency_score = average(time_weights)
# Higher recency = higher confidence
```

**Factors:**
- Average time weight of all articles
- 1.0 = All articles are very recent
- 0.0 = All articles are very old

#### 3. **News Volume** (ImpactScorer)
```python
volume_score = min(news_count / 20.0, 1.0)
# More news = higher confidence (up to 20 articles)
```

**Rationale:**
- More articles = more data points = higher confidence
- But diminishing returns after ~20 articles

#### 4. **Sentiment Strength** (ImpactScorer)
```python
sentiment_strength = abs(aggregated_sentiment)
# Stronger sentiment = higher confidence
```

**Rationale:**
- Clear positive/negative sentiment = higher confidence
- Neutral sentiment = lower confidence

#### 5. **Final Confidence Calculation**
```python
confidence = weighted_average(individual_confidences * time_weights)
```

**Formula:**
```
confidence = Σ(confidence_i × weight_i) / Σ(weight_i)
```

Where:
- `confidence_i` = Individual article confidence from LLM
- `weight_i` = Time weight based on recency and horizon

---

## What's Currently Implemented ✅

### 1. **Automatic Date Range Selection** ✅ IMPLEMENTED
   - System automatically selects appropriate window
   - No manual configuration needed
   - Optimized for each time horizon
   - **Location**: `DateRangeCalculator.calculate()`

### 2. **Time-Weighted Aggregation** ✅ IMPLEMENTED
   - Recent news weighted more heavily
   - Outdated news filtered out
   - Horizon-specific decay rates
   - **Location**: `TimeWeightedAggregator._adjust_for_horizon()`

### 3. **Time-Weighted Confidence** ✅ IMPLEMENTED
   - Confidence scores weighted by time (recent = higher weight)
   - Formula: `confidence = Σ(confidence_i × time_weight_i) / Σ(time_weight_i)`
   - **Location**: `TimeWeightedAggregator.aggregate()`

### 4. **Impact Scoring** ✅ IMPLEMENTED
   - Considers sentiment strength, volume, recency, confidence
   - Returns High/Medium/Low impact
   - **Location**: `ImpactScorer.calculate_impact()`

### 5. **Horizon-Aware Processing** ✅ IMPLEMENTED
   - All agents accept and use `time_horizon` parameter
   - Date ranges calculated automatically
   - Time weighting adjusted per horizon
   - **Location**: All three agents (News Fetch, LLM Sentiment, Aggregator)

---

## Implemented Optimizations ✅

The following optimizations are **NOW IMPLEMENTED** and active in the codebase:

#### 1. **Dynamic Window Adjustment** ✅ IMPLEMENTED

**Status:** ✅ **IMPLEMENTED** in `DateRangeCalculator.expand_window()` and `NewsFetchAgent.process()`

**How it works:**
- If initial fetch returns fewer than `min(limit, 10)` articles, the window is automatically expanded by 50%
- Maximum of 2 expansions to prevent excessive API calls
- Duplicate articles are filtered out during expansion

**Location:**
- `tick/backend/agents/news_fetch_agent/utils/date_range_calculator.py` - `expand_window()` method
- `tick/backend/agents/news_fetch_agent/agent.py` - Dynamic adjustment logic in `process()`

**Benefit:** Ensures sufficient news for accurate predictions, even if recent news is sparse.

#### 2. **Confidence-Based Filtering** ✅ IMPLEMENTED

**Status:** ✅ **IMPLEMENTED** in `LLMSentimentAgent.process()` and `SentimentAggregator.process()`

**How it works:**
- After sentiment analysis, articles with confidence below the horizon-specific threshold are filtered out
- Thresholds are automatically adjusted based on time horizon (stricter for short-term, lenient for long-term)
- Filtering happens in both LLM Sentiment Agent and Sentiment Aggregator for double protection

**Location:**
- `tick/backend/agents/llm_sentiment_agent/agent.py` - Confidence filtering in `process()` method
- `tick/backend/agents/sentiment_aggregator/agent.py` - Additional filtering in `process()` method

**Benefit:** Only high-confidence articles contribute to sentiment, improving prediction accuracy.

#### 3. **Horizon-Specific Confidence Thresholds** ✅ IMPLEMENTED

**Status:** ✅ **IMPLEMENTED** in `LLMSentimentAgent._get_confidence_threshold()` and `SentimentAggregator._get_horizon_thresholds()`

**How it works:**
- Each time horizon has its own confidence threshold and minimum article requirement
- Short-term predictions (1s, 1m) require higher confidence (0.8, 0.75) and fewer articles (3, 5)
- Long-term predictions (1mo, 1y) are more lenient (0.55, 0.5) and require more articles (20, 25)

**Current Thresholds:**
```python
{
    "1s": (0.8, 3),   # Very strict for 1-second predictions
    "1m": (0.75, 5),  # Strict for 1-minute predictions
    "1h": (0.7, 8),   # Moderate for hourly predictions
    "1d": (0.65, 10), # Moderate for daily predictions
    "1w": (0.6, 15),  # Lenient for weekly predictions
    "1mo": (0.55, 20), # More lenient for monthly predictions
    "1y": (0.5, 25)   # Most lenient for yearly predictions
}
```

**Location:**
- `tick/backend/agents/llm_sentiment_agent/agent.py` - `_get_confidence_threshold()` method
- `tick/backend/agents/sentiment_aggregator/agent.py` - `_get_horizon_thresholds()` method

**Benefit:** Short-term predictions require higher confidence, long-term can be more lenient, optimizing for each prediction type.

#### 4. **Source Quality Weighting** (Future Enhancement)

**Current:** All sources weighted equally  
**Improvement:** Weight sources by reliability

```python
SOURCE_WEIGHTS = {
    "Reuters": 1.0,      # High reliability
    "Bloomberg": 1.0,
    "Financial Times": 1.0,
    "MarketWatch": 0.8,  # Medium reliability
    "Yahoo Finance": 0.7,
    "Unknown": 0.5       # Low reliability
}

# Apply source weight to confidence
adjusted_confidence = base_confidence * source_weight
```

**Benefit:** More reliable sources contribute more to confidence.

#### 5. **Sentiment Agreement Scoring** (Future Enhancement)

**Current:** Simple average of sentiment scores  
**Improvement:** Higher confidence when articles agree

```python
# Calculate agreement (variance)
sentiment_scores = [0.7, 0.75, 0.68, 0.72]  # High agreement
variance = calculate_variance(sentiment_scores)  # Low variance

# High agreement = higher confidence
agreement_boost = 1.0 - (variance * 0.5)  # Reduce confidence if high variance
adjusted_confidence = base_confidence * agreement_boost
```

**Benefit:** When multiple articles agree, confidence increases.

---

## Complete Flow for Maximum Confidence

### Step-by-Step Process

1. **User Selects Time Horizon**
   ```
   User: "I want prediction for 1 day"
   → time_horizon = "1d"
   ```

2. **Calculate Optimal Date Range**
   ```python
   from_date, to_date = DateRangeCalculator.calculate("1d")
   # Returns: (3 days ago, now)
   ```

3. **Fetch News from Date Range**
   ```python
   articles = fetch_news(symbol, from_date, to_date)
   # Only fetches articles from last 3 days
   ```

4. **Filter by Relevance & Confidence** ✅
   ```python
   # Filter by relevance (News Fetch Agent)
   relevant = filter_by_relevance(articles, min_relevance=0.3)
   
   # Filter by confidence (LLM Sentiment Agent + Sentiment Aggregator)
   # Automatically filters based on time horizon threshold
   high_confidence = filter_by_confidence(relevant, min_confidence=0.65)  # For "1d"
   ```

5. **Dynamic Window Adjustment** ✅ (if needed)
   ```python
   # If not enough articles, automatically expand window
   if len(articles) < min_articles_required:
       from_date, to_date = DateRangeCalculator.expand_window(
           time_horizon, from_date, to_date, multiplier=1.5
       )
       # Retry fetch with expanded window
   ```

5. **Dynamic Window Adjustment** ✅ (if needed)
   ```python
   # If not enough articles, automatically expand window
   if len(articles) < min_articles_required:
       from_date, to_date = DateRangeCalculator.expand_window(
           time_horizon, from_date, to_date, multiplier=1.5
       )
       # Retry fetch with expanded window
   ```

6. **Apply Time Weighting** ✅
   ```python
   # Adjust decay for 1d horizon
   aggregator = TimeWeightedAggregator(config={
       "time_horizon": "1d",
       "half_life_hours": 24,  # 1 day decay
       "max_age_hours": 72      # 3 days max
   })
   
   # Weight articles by recency
   weighted_sentiment = aggregator.aggregate(sentiment_scores)
   ```

6. **Calculate Final Confidence**
   ```python
   # Multi-factor confidence
   confidence = calculate_confidence(
       sentiment_strength=abs(aggregated_sentiment),
       news_count=len(articles),
       recency=avg_time_weight,
       individual_confidences=article_confidences,
       time_weights=time_weights
   )
   ```

7. **Return Optimized Result**
   ```python
   {
       "aggregated_sentiment": 0.68,
       "confidence": 0.82,  # High confidence due to:
                            # - Recent news (high time weights)
                            # - Multiple articles (volume)
                            # - Strong sentiment (0.68)
                            # - Time-aligned with horizon
       "time_horizon": "1d",
       "date_range": {"from": "3 days ago", "to": "now"}
   }
   ```

---

## Confidence Score Formula (Current)

```
confidence = weighted_average(individual_confidences × time_weights)

Where:
- individual_confidences = [0.85, 0.80, 0.90, ...] from LLM
- time_weights = [0.95, 0.88, 0.92, ...] based on recency
- weight_i = time_weight_i (recent articles weighted more)
```

**Example:**
```
Articles:
  Article 1: confidence=0.85, time_weight=0.95 (very recent)
  Article 2: confidence=0.80, time_weight=0.88 (recent)
  Article 3: confidence=0.90, time_weight=0.75 (older)

confidence = (0.85×0.95 + 0.80×0.88 + 0.90×0.75) / (0.95+0.88+0.75)
          = (0.8075 + 0.704 + 0.675) / 2.58
          = 2.1865 / 2.58
          = 0.847 (84.7% confidence)
```

---

## Recommendations for Production

### Immediate Improvements

1. **Add Confidence Threshold Filtering**
   - Filter out articles with confidence < 0.6
   - Improves overall confidence

2. **Dynamic Window Adjustment**
   - Expand window if not enough articles
   - Ensures minimum data for confidence

3. **Horizon-Specific Thresholds**
   - Stricter for short-term, lenient for long-term
   - Optimizes confidence per horizon

### Future Enhancements

1. **Source Quality Weighting**
   - Weight by source reliability
   - Higher quality sources = higher confidence

2. **Sentiment Agreement Scoring**
   - Higher confidence when articles agree
   - Lower confidence when articles disagree

3. **Volume Optimization**
   - Optimal article count per horizon
   - Too few = low confidence, too many = diminishing returns

---

## Testing Confidence Optimization

### Test Cases

1. **Short Horizon (1m) with Recent News**
   - Expected: High confidence (0.8+)
   - Reason: Recent news, high time weights

2. **Short Horizon (1m) with Old News**
   - Expected: Low confidence (0.5-)
   - Reason: Old news, low time weights

3. **Long Horizon (1y) with Diverse News**
   - Expected: Medium confidence (0.6-0.7)
   - Reason: Diverse news, moderate weights

4. **High Agreement Scenario**
   - Expected: High confidence
   - Reason: Multiple articles agree

5. **Low Agreement Scenario**
   - Expected: Lower confidence
   - Reason: Articles disagree

---

## Summary

### How It Works Now

1. **User selects time horizon** → System calculates date range
2. **Fetches news from date range** → Only relevant news
3. **Applies time weighting** → Recent news weighted more
4. **Calculates confidence** → Multi-factor calculation
5. **Returns optimized result** → High confidence when conditions are met

### Key Points

- ✅ **Automatic**: No manual configuration needed
- ✅ **Horizon-Aware**: Adjusts for each time horizon
- ✅ **Time-Weighted**: Recent news prioritized
- ✅ **Multi-Factor**: Considers recency, volume, sentiment, confidence
- ✅ **Optimized**: Designed for maximum confidence

### Current Confidence Factors

1. **Time Alignment** (40%): How well news aligns with horizon
2. **News Volume** (30%): Number of articles
3. **Recency** (20%): How recent the news is
4. **Sentiment Strength** (10%): How strong the sentiment is
5. **Individual Confidence** (Weighted): LLM confidence scores

---

## Implementation Status

### ✅ Core Features (Implemented)

1. **Date Range Calculation** - Automatically selects news window based on time horizon
2. **Time-Weighted Aggregation** - Weights recent news more heavily
3. **Time-Weighted Confidence** - Confidence scores weighted by article recency
4. **Impact Scoring** - Multi-factor impact calculation
5. **Horizon-Aware Processing** - All agents adjust for time horizon

### ✅ Optimizations (Newly Implemented)

1. **Confidence Threshold Filtering** ✅ - Filters out low-confidence articles in both LLM Sentiment Agent and Sentiment Aggregator
2. **Dynamic Window Adjustment** ✅ - Automatically expands date window if not enough articles found
3. **Horizon-Specific Confidence Thresholds** ✅ - Different confidence thresholds and minimum article requirements per time horizon

### 🚧 Future Enhancements (Optional)

1. **Source Quality Weighting** - Weight by source reliability (e.g., Reuters > MarketWatch)
2. **Sentiment Agreement Scoring** - Boost confidence when multiple articles agree on sentiment

---

**Last Updated**: January 2026  
**Status**: ✅ Core Implementation Complete | ✅ Optimizations Implemented | 🚧 Future Enhancements Available

