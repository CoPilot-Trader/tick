# News & Sentiment Agents - Complete Workflow Guide

**Developer**: Developer 1  
**Date**: January 2026  
**Status**: Documentation and Planning

---

## Table of Contents

1. [Your Role as Developer 1](#your-role-as-developer-1)
2. [Files You Need to Work With](#files-you-need-to-work-with)
3. [What's Already Done vs What's Needed](#whats-already-done-vs-whats-needed)
4. [Complete Workflow Explanation](#complete-workflow-explanation)
5. [Flow Charts and Diagrams](#flow-charts-and-diagrams)
6. [Step-by-Step Example: AAPL](#step-by-step-example-aapl)
7. [Understanding the news_agent Folder](#understanding-the-news_agent-folder)
8. [How to Handle 100 Tickers Across Different Sectors?](#how-to-handle-100-tickers-across-different-sectors)
9. [Full Automation Pipeline for News Agents](#full-automation-pipeline-for-news-agents)
10. [Regime Change Detection for News Agents](#regime-change-detection-for-news-agents)
11. [High-Frequency Trading Architecture for News Agents](#high-frequency-trading-architecture-for-news-agents)
12. [Summary](#summary)

---

## Your Role as Developer 1

According to `TEAM.md`, you are responsible for **News & Sentiment Agents**. Your primary areas include:

- News data collection from multiple sources
- LLM-based sentiment analysis (GPT-4)
- Sentiment aggregation
- Semantic caching for cost optimization

### Your Working Directories

- `backend/agents/news_fetch_agent/` - News collection (M3)
- `backend/agents/llm_sentiment_agent/` - GPT-4 sentiment (M3)
- `backend/agents/sentiment_aggregator/` - Sentiment aggregation (M3)

### Your Deliverables

- **News Fetch Agent**: Multi-source news collection
- **LLM Sentiment Agent**: GPT-4 sentiment analysis with semantic caching
- **Sentiment Aggregator**: Multi-source sentiment combination
- **API endpoints** for all components
- **Unit tests** for all components

---

## Files You Need to Work With

You are responsible for **three agents** that work together:

### 1. News Fetch Agent
**Location**: `tick/backend/agents/news_fetch_agent/`

**Files**:
- `agent.py` - Main agent class (skeleton exists)
- `interfaces.py` - Data models (Pydantic models defined)
- `README.md` - Documentation (task list provided)
- `__init__.py` - Package initialization

### 2. LLM Sentiment Agent
**Location**: `tick/backend/agents/llm_sentiment_agent/`

**Files**:
- `agent.py` - Main agent class (skeleton exists)
- `interfaces.py` - Data models (Pydantic models defined)
- `README.md` - Documentation (task list provided)
- `__init__.py` - Package initialization

### 3. Sentiment Aggregator
**Location**: `tick/backend/agents/sentiment_aggregator/`

**Files**:
- `agent.py` - Main agent class (skeleton exists)
- `interfaces.py` - Data models (Pydantic models defined)
- `README.md` - Documentation (task list provided)
- `__init__.py` - Package initialization

---

## What's Already Done vs What's Needed

### ✅ Completed

1. **Agent Class Structure** - All three agents extend `BaseAgent`
2. **Interface Definitions** - Pydantic models are defined:
   - `NewsArticle`, `NewsResponse` (News Fetch)
   - `SentimentScore` (LLM Sentiment)
   - `AggregatedSentiment` (Sentiment Aggregator)
3. **Method Signatures** - All methods are defined with proper docstrings
4. **Health Check Methods** - Basic health checks are implemented
5. **Documentation** - README files with task breakdowns exist

### ❌ Not Done (What You Need to Implement)

- **No actual functionality** - All methods return "not_implemented"
- **No API integrations** - No connections to news APIs or GPT-4
- **No tests written** - Test files don't exist yet
- **No directory structure** - Sub-modules (collectors, filters, etc.) don't exist
- **No API endpoints** - FastAPI routes not created

---

## Complete Workflow Explanation

### High-Level Flow Chart

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT: Stock Symbol (AAPL)                │
│                    Example: "AAPL"                           │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: News Fetch Agent                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Receives: symbol = "AAPL"                        │   │
│  │ 2. Fetches news from multiple sources:              │   │
│  │    - Finnhub API                                    │   │
│  │    - NewsAPI                                        │   │
│  │    - Alpha Vantage (backup)                         │   │
│  │ 3. Filters by relevance to AAPL                     │   │
│  │ 4. Removes duplicates                               │   │
│  │ 5. Scores relevance (0.0 to 1.0)                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  OUTPUT: List of News Articles                               │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: LLM Sentiment Agent                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Receives: News articles from Step 1               │   │
│  │ 2. For each article:                                    │   │
│  │    a. Check semantic cache (similar articles?)        │   │
│  │    b. If cached → return cached sentiment            │   │
│  │    c. If not cached → send to GPT-4 API              │   │
│  │    d. Store result in cache                           │   │
│  │ 3. GPT-4 analyzes sentiment                           │   │
│  │ 4. Returns sentiment score (-1.0 to +1.0)            │   │
│  └──────────────────────────────────────────────────────┘   │
│  OUTPUT: Sentiment Scores for Each Article                    │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Sentiment Aggregator                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. Receives: All sentiment scores from Step 2        │   │
│  │ 2. Applies time-weighting (recent news = more weight) │   │
│  │ 3. Calculates weighted average sentiment             │   │
│  │ 4. Determines impact level:                          │   │
│  │    - High: Strong sentiment + many articles + recent│   │
│  │    - Medium: Moderate sentiment/volume               │   │
│  │    - Low: Weak sentiment or few articles             │   │
│  │ 5. Calculates confidence score                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  OUTPUT: Final Aggregated Sentiment                           │
└────────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL OUTPUT                               │
│  Aggregated Sentiment for AAPL                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Example: AAPL

### Example: Analyzing News Sentiment for AAPL (Apple Inc.)

---

### STEP 1: News Fetch Agent - Collecting News

**Input**:
```json
{
  "symbol": "AAPL",
  "params": {
    "sources": ["finnhub", "newsapi"],
    "limit": 50,
    "date_range": "last_7_days"
  }
}
```

**What Happens**:
1. Agent receives request for "AAPL"
2. Calls multiple news APIs:
   - Finnhub: `GET https://finnhub.io/api/v1/company-news?symbol=AAPL`
   - NewsAPI: `GET https://newsapi.org/v2/everything?q=Apple+OR+AAPL`
   - Alpha Vantage: backup if others fail
3. Collects raw articles (example):
   ```
   Article 1: "Apple Reports Record Q4 Earnings, Stock Surges"
   Article 2: "New iPhone Launch Expected Next Month"
   Article 3: "Tech Stocks Rally Across Market" (less relevant)
   Article 4: "Apple Announces New AI Features"
   ...
   ```
4. Filters and scores relevance:
   - Article 1: relevance_score = 0.95 (directly about Apple)
   - Article 2: relevance_score = 0.88 (about Apple product)
   - Article 3: relevance_score = 0.35 (general tech news)
   - Article 4: relevance_score = 0.92 (Apple-specific)
5. Removes duplicates (same article from multiple sources)
6. Sorts by relevance (highest first)

**Output from News Fetch Agent**:
```json
{
  "symbol": "AAPL",
  "articles": [
    {
      "id": "article_001",
      "title": "Apple Reports Record Q4 Earnings, Stock Surges",
      "source": "Reuters",
      "published_at": "2024-01-15T10:00:00Z",
      "url": "https://reuters.com/apple-earnings",
      "summary": "Apple Inc reported record-breaking Q4 earnings...",
      "content": "Full article text here...",
      "relevance_score": 0.95
    },
    {
      "id": "article_002",
      "title": "Apple Announces New AI Features",
      "source": "TechCrunch",
      "published_at": "2024-01-15T09:30:00Z",
      "url": "https://techcrunch.com/apple-ai",
      "summary": "Apple unveiled new AI capabilities...",
      "content": "Full article text here...",
      "relevance_score": 0.92
    },
    {
      "id": "article_003",
      "title": "New iPhone Launch Expected Next Month",
      "source": "Bloomberg",
      "published_at": "2024-01-14T15:20:00Z",
      "url": "https://bloomberg.com/iphone-launch",
      "summary": "Sources indicate new iPhone model...",
      "content": "Full article text here...",
      "relevance_score": 0.88
    }
    // ... more articles
  ],
  "fetched_at": "2024-01-15T10:30:00Z",
  "total_count": 15,
  "sources": ["finnhub", "newsapi"]
}
```

---

### STEP 2: LLM Sentiment Agent - Analyzing Sentiment

**Input**:
```json
{
  "symbol": "AAPL",
  "articles": [
    // Articles from Step 1
  ]
}
```

**What Happens**:
1. Agent receives articles from News Fetch Agent
2. For each article:
   - **Check semantic cache**:
     - Convert article text to embedding (vector)
     - Search cache for similar articles (cosine similarity > 0.85)
     - If found → return cached sentiment (saves API cost!)
     - If not found → proceed to GPT-4
3. Send to GPT-4 API (if not cached):
   ```
   Prompt to GPT-4:
   "Analyze the sentiment of this financial news article about AAPL:
   
   Title: Apple Reports Record Q4 Earnings, Stock Surges
   Content: Apple Inc reported record-breaking Q4 earnings...
   
   Return sentiment as a number from -1.0 (very negative) to +1.0 (very positive),
   and a label: positive, neutral, or negative."
   ```
4. GPT-4 response:
   ```json
   {
     "sentiment_score": 0.85,
     "sentiment_label": "positive",
     "confidence": 0.92,
     "reasoning": "Article reports record earnings and stock surge, clearly positive"
   }
   ```
5. Store in semantic cache for future similar articles
6. Repeat for all articles

**Output from LLM Sentiment Agent**:
```json
{
  "symbol": "AAPL",
  "sentiment_scores": [
    {
      "article_id": "article_001",
      "sentiment_score": 0.85,
      "sentiment_label": "positive",
      "confidence": 0.92,
      "processed_at": "2024-01-15T10:31:00Z",
      "cached": false
    },
    {
      "article_id": "article_002",
      "sentiment_score": 0.72,
      "sentiment_label": "positive",
      "confidence": 0.88,
      "processed_at": "2024-01-15T10:31:15Z",
      "cached": false
    },
    {
      "article_id": "article_003",
      "sentiment_score": 0.65,
      "sentiment_label": "positive",
      "confidence": 0.85,
      "processed_at": "2024-01-15T10:31:30Z",
      "cached": true  // This was similar to a previous article
    }
    // ... more sentiment scores
  ],
  "cache_stats": {
    "hit_rate": 0.33,  // 5 out of 15 articles were cached
    "total_articles": 15,
    "cached_articles": 5,
    "api_calls_saved": 5
  }
}
```

---

### STEP 3: Sentiment Aggregator - Combining All Sentiments

**Input**:
```json
{
  "symbol": "AAPL",
  "sentiment_scores": [
    // All sentiment scores from Step 2
  ],
  "time_weighted": true
}
```

**What Happens**:
1. Agent receives all sentiment scores
2. Applies time-weighting:
   - Recent articles (last 24 hours) = weight 1.0
   - Older articles (2-7 days) = weight 0.7
   - Very old articles (>7 days) = weight 0.3
3. Calculates weighted average:
   ```
   Article 1: score 0.85, weight 1.0 (published today)
   Article 2: score 0.72, weight 1.0 (published today)
   Article 3: score 0.65, weight 0.7 (published yesterday)
   ...
   
   Weighted Average = (0.85×1.0 + 0.72×1.0 + 0.65×0.7 + ...) / (1.0 + 1.0 + 0.7 + ...)
                    = 0.68
   ```
4. Determines impact level:
   - High: aggregated_sentiment = 0.68 (strong), news_count = 15 (many), recent = yes
   - Result: **"High"** impact
5. Calculates confidence:
   - Based on: number of articles, consistency of scores, recency
   - Result: 0.82 (high confidence)

**Output from Sentiment Aggregator (Final)**:
```json
{
  "symbol": "AAPL",
  "aggregated_sentiment": 0.68,
  "sentiment_label": "positive",
  "confidence": 0.82,
  "impact": "High",
  "news_count": 15,
  "time_weighted": true,
  "aggregated_at": "2024-01-15T10:32:00Z",
  "breakdown": {
    "positive_articles": 12,
    "neutral_articles": 2,
    "negative_articles": 1,
    "average_sentiment": 0.68,
    "sentiment_std": 0.15
  }
}
```

---

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER REQUEST                                 │
│              GET /api/v1/news/sentiment/AAPL                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
        ┌────────────────────────────────────┐
        │   ORCHESTRATOR (Lead Developer)    │
        │   Coordinates all agents            │
        └────────────┬───────────────────────┘
                     │
                     │ Calls News Fetch Agent
                     ▼
┌────────────────────────────────────────────────────────────┐
│  NEWS FETCH AGENT (You - Developer 1)                      │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ collectors/finnhub_collector.py                      │ │
│  │ collectors/newsapi_collector.py                      │ │
│  │ filters/relevance_filter.py                         │ │
│  └──────────────────────────────────────────────────────┘ │
│  Returns: 15 filtered news articles                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ Passes articles to LLM Sentiment
                             ▼
┌────────────────────────────────────────────────────────────┐
│  LLM SENTIMENT AGENT (You - Developer 1)                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ llm/gpt4_client.py                                  │ │
│  │ cache/semantic_cache.py                             │ │
│  │ optimization/cost_optimizer.py                      │ │
│  └──────────────────────────────────────────────────────┘ │
│  Returns: 15 sentiment scores                             │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ Passes scores to Aggregator
                             ▼
┌────────────────────────────────────────────────────────────┐
│  SENTIMENT AGGREGATOR (You - Developer 1)                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ aggregation/time_weighted.py                       │ │
│  │ aggregation/impact_scorer.py                        │ │
│  └──────────────────────────────────────────────────────┘ │
│  Returns: Final aggregated sentiment                      │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ Returns to Orchestrator
                             ▼
        ┌────────────────────────────────────┐
        │   ORCHESTRATOR                     │
        │   Combines with other signals      │
        └────────────┬───────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │   FUSION AGENT (Lead Developer)    │
        │   Creates final trading signal     │
        └────────────────────────────────────┘
```

---

## Understanding the news_agent Folder

### The Situation

There are **two different approaches** in the codebase:

1. **`news_agent`** (older/combined) - Combines news collection AND sentiment analysis in one agent
2. **Three separate agents** (official per TEAM.md):
   - `news_fetch_agent` - Collects news
   - `llm_sentiment_agent` - Analyzes sentiment with GPT-4
   - `sentiment_aggregator` - Combines sentiment scores

### Recommendation

**Use the three-agent architecture** as specified in TEAM.md. The `news_agent` folder appears to be a prototype or alternative approach.

**What to do with `news_agent` folder**:
- **Option 1**: Keep it as reference/backup
- **Option 2**: Migrate useful code to the three-agent structure
- **Option 3**: Remove it if it's obsolete

**My recommendation**: Keep it for now, but focus on implementing the three separate agents as per TEAM.md. You can reference `news_agent` for ideas, but the official architecture uses the three-agent approach.

---

## How to Handle 100 Tickers Across Different Sectors?

### Overview

As Developer 1 (News & Sentiment Agents), you handle news collection and sentiment analysis for **all tickers** across different sectors. Your agents are **universal**—same code for all tickers—but you need to optimize for scale, cost, and efficiency.

---

## What You Need to Do

### 1. News Fetch Agent - Multi-Ticker Handling

#### Batch Processing Strategy

**What to implement:**
- Process multiple tickers in batches (e.g., 10-20 at a time)
- Parallel API calls to news sources
- Rate limit management per API provider
- Error handling that doesn't stop the entire batch

**Example workflow:**
```
100 Tickers → Split into 10 batches of 10 tickers each
    ↓
For each batch:
    - Fetch news for all 10 tickers in parallel
    - Handle rate limits (wait if needed)
    - Store results
    - Move to next batch
```

**Key considerations:**
- API rate limits (Finnhub, NewsAPI, Alpha Vantage have different limits)
- Timeout handling (some tickers may have no news)
- Retry logic for failed requests
- Deduplication across tickers (same news might affect multiple stocks)

#### Sector-Aware News Filtering

**What to implement:**
- Sector metadata tagging (optional, but helpful)
- Relevance scoring that considers sector context
- Filter out irrelevant news more aggressively

**Example:**
- Tech sector (AAPL, MSFT): Filter for tech-related keywords
- Energy sector (XOM, CVX): Filter for oil/energy keywords
- Healthcare (JNJ, PFE): Filter for healthcare/pharma keywords

**Why this matters:**
- Reduces noise in news feeds
- Improves relevance scores
- Saves processing time and API costs

#### Caching Strategy

**What to implement:**
- Cache news articles by ticker
- Cache expiration (e.g., 1 hour for news)
- Cache invalidation when new news arrives
- Share cache across tickers when news is relevant to multiple stocks

**Example:**
```
News: "Tech Sector Rally" → Relevant to AAPL, MSFT, GOOGL
Cache this once, use for all three tickers
```

---

### 2. LLM Sentiment Agent - Cost Optimization

#### Semantic Caching (Critical for 100 Tickers)

**What to implement:**
- Global semantic cache (not per-ticker)
- Similar articles across tickers share sentiment
- Target: 60%+ cache hit rate across all tickers

**Why this is crucial:**
- GPT-4 API costs: ~$0.01-0.03 per article
- 100 tickers × 15 articles each = 1,500 articles
- Without cache: $15-45 per analysis cycle
- With 60% cache: $6-18 per cycle (saves $9-27)

**Implementation strategy:**
```
For each article:
    1. Convert to embedding (vector)
    2. Search global cache for similar articles
    3. If similarity > 0.85 → Use cached sentiment
    4. If not found → Call GPT-4, store in cache
```

#### Batch Processing for GPT-4

**What to implement:**
- Batch multiple articles in one API call (if API supports)
- Process articles in parallel (respect rate limits)
- Queue system for API calls
- Priority queue (recent news first)

**Example:**
```
100 tickers × 15 articles = 1,500 articles
After semantic cache: ~600 articles need GPT-4
Process in batches of 50 articles
Total: 12 batches
Time: ~5-10 minutes (depending on API limits)
```

#### Sector-Specific Prompt Optimization

**What to consider:**
- Different sectors may need slightly different prompts
- Tech news vs financial news vs healthcare news
- Can use sector metadata to adjust prompts

**Example:**
```
Tech sector prompt: "Analyze sentiment for this tech stock news..."
Energy sector prompt: "Analyze sentiment for this energy sector news..."
```

---

### 3. Sentiment Aggregator - Multi-Ticker Processing

#### Parallel Aggregation

**What to implement:**
- Process all tickers in parallel
- Independent aggregation per ticker
- No cross-ticker dependencies

**Why this works:**
- Each ticker's sentiment is independent
- Can process all 100 tickers simultaneously
- Fast execution time

#### Time-Weighting Consistency

**What to implement:**
- Same time-weighting logic for all tickers
- Consistent impact scoring across sectors
- Fair comparison across tickers

**Example:**
```
All tickers use same time weights:
- Last 24 hours: weight 1.0
- 2-7 days: weight 0.7
- >7 days: weight 0.3
```

---

## What You Need to Take Care Of

### 1. API Rate Limits & Costs

**Critical concerns:**
- News API rate limits (e.g., NewsAPI: 1,000 requests/day free tier)
- GPT-4 API rate limits (requests per minute)
- Cost management (GPT-4 is expensive)

**Solutions:**
- Implement rate limiting/throttling
- Use multiple API keys (if allowed)
- Prioritize important tickers
- Cache aggressively
- Monitor API usage and costs

**Example rate limit handling:**
```
NewsAPI: 1,000 requests/day
100 tickers × 1 request = 100 requests
Can fetch 10 times per day (1,000 / 100 = 10)
Or: Use multiple API keys for different batches
```

### 2. Error Handling & Resilience

**What to handle:**
- API failures (network issues, API downtime)
- Missing news for some tickers
- Invalid responses from APIs
- Timeout scenarios

**Solutions:**
- Retry logic with exponential backoff
- Fallback to alternative news sources
- Graceful degradation (return partial results)
- Logging and monitoring

**Example:**
```
If Finnhub fails → Try NewsAPI
If NewsAPI fails → Try Alpha Vantage
If all fail → Return cached news (if available)
If no cache → Return empty result with error message
```

### 3. Performance & Scalability

**Challenges:**
- Processing 100 tickers takes time
- Need to complete within reasonable timeframe
- System should scale if more tickers are added

**Solutions:**
- Parallel processing (multithreading/multiprocessing)
- Async/await for I/O operations
- Database optimization for storage
- Caching to reduce redundant work

**Performance targets:**
```
100 tickers processing:
- News Fetch: < 5 minutes (parallel)
- LLM Sentiment: < 10 minutes (with caching)
- Sentiment Aggregation: < 1 minute (parallel)
Total: < 16 minutes for full cycle
```

### 4. Data Quality & Validation

**What to validate:**
- News article completeness (title, content, date)
- Relevance scores are reasonable (0.0-1.0)
- Sentiment scores are valid (-1.0 to +1.0)
- Timestamps are correct

**Solutions:**
- Input validation for all data
- Data quality checks before processing
- Flag suspicious data for review
- Log validation failures

### 5. Sector-Specific Considerations

**What to be aware of:**
- Different sectors have different news volumes
- Some sectors are more news-heavy (tech, finance)
- Some sectors have less news (utilities, consumer staples)
- News relevance varies by sector

**Solutions:**
- Adjust relevance thresholds per sector (optional)
- Handle low-news tickers gracefully
- Don't penalize tickers with less news
- Consider sector context in filtering

**Example:**
```
Tech sector (AAPL): 20-30 articles per day
Utilities sector (NEE): 2-5 articles per day
Both are valid, don't filter utilities too aggressively
```

### 6. Monitoring & Observability

**What to monitor:**
- API call counts and costs
- Cache hit rates
- Processing times per ticker
- Error rates
- News volume per ticker

**Solutions:**
- Logging for all operations
- Metrics collection (cache hits, API calls, errors)
- Alerts for high error rates
- Dashboard for monitoring (optional)

**Key metrics to track:**
```
- Cache hit rate: Target >60%
- API calls per day: Monitor costs
- Average processing time per ticker
- Error rate: Target <1%
- News articles fetched per ticker
```

---

## Practical Implementation Strategy

### Phase 1: Single Ticker (Start Small)
1. Implement News Fetch Agent for one ticker
2. Implement LLM Sentiment Agent for one ticker
3. Implement Sentiment Aggregator for one ticker
4. Test thoroughly

### Phase 2: Multiple Tickers (Scale Up)
1. Add batch processing
2. Add parallel execution
3. Add error handling
4. Test with 10 tickers

### Phase 3: Full Scale (100 Tickers)
1. Optimize for performance
2. Implement aggressive caching
3. Add monitoring and logging
4. Test with all 100 tickers

### Phase 4: Optimization
1. Fine-tune cache strategies
2. Optimize API usage
3. Improve error handling
4. Monitor and adjust

---

## Example: Processing 100 Tickers

### Step-by-Step Flow

```
1. Receive request: Process 100 tickers
   ↓
2. Split into batches: 10 batches of 10 tickers
   ↓
3. For each batch (parallel):
   a. News Fetch Agent:
      - Fetch news for 10 tickers in parallel
      - Filter and score relevance
      - Store in database
   ↓
4. For all tickers (after news fetch):
   a. LLM Sentiment Agent:
      - Check semantic cache (global)
      - Process uncached articles with GPT-4
      - Store results in cache
   ↓
5. For all tickers (parallel):
   a. Sentiment Aggregator:
      - Aggregate sentiment per ticker
      - Calculate impact levels
      - Store final results
   ↓
6. Return results for all 100 tickers
```

### Time Estimates

```
News Fetch (parallel batches):
- 10 batches × 30 seconds = 5 minutes

LLM Sentiment (with 60% cache):
- 600 articles × 2 seconds = 20 minutes
- With parallel processing: ~10 minutes

Sentiment Aggregation (parallel):
- 100 tickers × 0.5 seconds = 50 seconds

Total: ~16 minutes for 100 tickers
```

---

## Full Automation Pipeline for News Agents

### What You Need to Do

### 1. Scheduled News Fetching

**What to implement:**
- Automated scheduler (cron job, Celery, or similar)
- Periodic news fetching (e.g., every hour, 4 times/day, or daily)
- Automatic trigger for all tickers in watchlist
- Background job processing

**Technologies to use:**
- **Celery** (Python task queue)
- **APScheduler** (Advanced Python Scheduler)
- **Cron jobs** (Linux/Unix)
- **Task scheduler** (Windows)

**Example implementation approach:**
```python
# Scheduler setup (handled by Orchestrator, but you need to make agents ready)
# Your agents should be callable on-demand

# News Fetch Agent should support:
- process(symbol, params)  # Already exists
- batch_process(symbols_list)  # Need to add
- scheduled_fetch()  # Need to add
```

**What to add to News Fetch Agent:**
- `batch_process(symbols: List[str])` method
- Automatic retry logic
- Rate limit handling
- Progress tracking

### 2. Automated Sentiment Analysis

**What to implement:**
- Automatic processing after news fetch
- Queue system for GPT-4 API calls
- Automatic cache management
- Cost monitoring and alerts

**Technologies to use:**
- **Redis Queue (RQ)** or **Celery** for queuing
- **Redis** for semantic cache
- **OpenAI API client**
- **Sentence transformers** for embeddings

**What to add to LLM Sentiment Agent:**
- `batch_analyze(articles: List[Article])` method
- Queue management for API calls
- Automatic cache cleanup (old entries)
- Cost tracking and reporting

### 3. Automated Aggregation

**What to implement:**
- Automatic aggregation after sentiment analysis
- Scheduled aggregation runs
- Automatic result storage
- Alert generation for significant changes

**What to add to Sentiment Aggregator:**
- `batch_aggregate(symbols: List[str])` method
- Automatic result storage
- Change detection (significant sentiment shifts)
- Alert triggers

### What You Need to Take Care Of

**1. API Rate Limits**
- Monitor API usage continuously
- Implement backoff strategies
- Queue management to avoid exceeding limits

**2. Cost Management**
- Track GPT-4 API costs
- Set daily/monthly budgets
- Alerts when approaching limits
- Optimize cache hit rates

**3. Error Handling**
- Graceful failures (one ticker failure shouldn't stop others)
- Retry logic with exponential backoff
- Fallback mechanisms
- Comprehensive logging

**4. Data Freshness**
- Cache expiration policies
- Ensure recent news is prioritized
- Handle stale data

**5. System Monitoring**
- Track processing times
- Monitor success/failure rates
- Alert on anomalies
- Performance metrics

### Automation Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│  SCHEDULER (Every Hour / 4x Daily / Daily)                 │
│  - Triggers news fetch for all tickers                      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  NEWS FETCH AGENT (Automated)                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Receives list of 100 tickers                      │  │
│  │ 2. Processes in batches (10-20 at a time)            │  │
│  │ 3. Fetches news from multiple sources                │  │
│  │ 4. Filters and scores relevance                      │  │
│  │ 5. Stores in database                                 │  │
│  │ 6. Triggers next step automatically                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  LLM SENTIMENT AGENT (Automated)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Receives news articles from News Fetch            │  │
│  │ 2. Checks semantic cache (global)                    │  │
│  │ 3. Processes uncached articles with GPT-4            │  │
│  │ 4. Stores results in cache                            │  │
│  │ 5. Tracks costs and cache hit rate                   │  │
│  │ 6. Triggers next step automatically                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  SENTIMENT AGGREGATOR (Automated)                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Receives sentiment scores                         │  │
│  │ 2. Aggregates per ticker                             │  │
│  │ 3. Calculates impact levels                          │  │
│  │ 4. Stores final results                              │  │
│  │ 5. Detects significant changes                        │  │
│  │ 6. Generates alerts if needed                        │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  RESULT STORAGE & NOTIFICATION                             │
│  - Store in database                                         │
│  - Send to Fusion Agent                                     │
│  - Generate alerts for significant changes                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Regime Change Detection for News Agents

### What You Need to Do

### 1. News Volume Anomaly Detection

**What to implement:**
- Track news volume per ticker over time
- Detect sudden spikes or drops in news volume
- Compare current volume to historical averages
- Flag anomalies

**What to add to News Fetch Agent:**
- `detect_volume_anomaly(symbol: str, current_volume: int, historical_avg: float)` method
- Historical volume tracking
- Anomaly threshold configuration

**Example logic:**
```
If current_volume > 3x historical_average:
    → Regime change detected (high news activity)
If current_volume < 0.3x historical_average:
    → Regime change detected (low news activity)
```

### 2. Sentiment Volatility Detection

**What to implement:**
- Track sentiment score volatility
- Detect sudden sentiment shifts
- Compare recent sentiment to historical patterns
- Flag significant changes

**What to add to Sentiment Aggregator:**
- `detect_sentiment_regime_change(symbol: str, recent_sentiment: float, historical_sentiment: float)` method
- Historical sentiment tracking
- Volatility calculation

**Example logic:**
```
If recent_sentiment - historical_sentiment > 0.5:
    → Positive regime change (sudden positive shift)
If recent_sentiment - historical_sentiment < -0.5:
    → Negative regime change (sudden negative shift)
```

### 3. News Source Diversity Monitoring

**What to implement:**
- Track which news sources are reporting
- Detect changes in source coverage
- Monitor source reliability
- Flag unusual source patterns

**What to add to News Fetch Agent:**
- Source diversity tracking
- Source reliability scoring
- Pattern detection

### What You Need to Take Care Of

**1. False Positives**
- Avoid flagging normal fluctuations
- Use statistical significance tests
- Require multiple confirmations

**2. Historical Data**
- Maintain sufficient historical data
- Use appropriate time windows
- Handle missing data gracefully

**3. Threshold Tuning**
- Adjust thresholds based on sector
- Test and validate thresholds
- Monitor false positive rates

### Regime Change Detection Flow

```
┌─────────────────────────────────────────────────────────────┐
│  NEWS FETCH AGENT                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Fetch news for ticker                             │  │
│  │ 2. Count news volume                                  │  │
│  │ 3. Compare to historical average                      │  │
│  │ 4. Flag if anomaly detected                           │  │
│  │ 5. Pass flag to next agents                           │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  SENTIMENT AGGREGATOR                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Receive sentiment scores                           │  │
│  │ 2. Calculate aggregated sentiment                     │  │
│  │ 3. Compare to historical sentiment                    │  │
│  │ 4. Calculate volatility                                │  │
│  │ 5. Flag if regime change detected                     │  │
│  │ 6. Include flag in output                             │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  REGIME CHANGE OUTPUT                                        │
│  {                                                           │
│    "symbol": "AAPL",                                         │
│    "regime_change_detected": true,                           │
│    "type": "sentiment_shift",                                │
│    "confidence": 0.85,                                       │
│    "details": {                                              │
│      "recent_sentiment": 0.75,                               │
│      "historical_sentiment": 0.45,                          │
│      "change": +0.30                                         │
│    }                                                         │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## High-Frequency Trading Architecture for News Agents

### What You Need to Do

### 1. Real-Time News Streaming

**What to implement:**
- Real-time news feed integration
- WebSocket connections to news APIs
- Immediate processing of breaking news
- Low-latency news ingestion

**Technologies to use:**
- **WebSocket clients** (websockets library)
- **Async/await** for concurrent processing
- **Message queues** (Redis Streams, Kafka)
- **In-memory caching** (Redis)

**What to add to News Fetch Agent:**
- `stream_news(symbol: str)` method (WebSocket connection)
- Real-time news processing
- Immediate relevance filtering
- Priority queue for breaking news

### 2. Fast Sentiment Analysis

**What to implement:**
- Optimized cache lookup (sub-millisecond)
- Parallel GPT-4 API calls
- Pre-computed embeddings
- Fast similarity search

**Technologies to use:**
- **Vector databases** (FAISS, Pinecone, Qdrant) for fast similarity search
- **Redis** for hot cache
- **Async OpenAI client**
- **Batch processing**

**What to add to LLM Sentiment Agent:**
- Fast cache lookup (vector similarity search)
- Async API calls
- Batch processing for multiple articles
- Priority processing for breaking news

### 3. Low-Latency Aggregation

**What to implement:**
- Incremental aggregation (update as new news arrives)
- In-memory aggregation state
- Fast time-weighting calculations
- Real-time impact scoring

**What to add to Sentiment Aggregator:**
- `incremental_aggregate(symbol: str, new_sentiment: float)` method
- In-memory state management
- Fast recalculation
- Real-time updates

### What You Need to Take Care Of

**1. Latency Constraints**
- Target: < 100ms for news processing
- Optimize cache lookups
- Minimize API call latency
- Use async operations

**2. Data Freshness**
- Process news immediately
- Prioritize recent news
- Expire old data quickly
- Real-time updates

**3. System Load**
- Handle burst traffic
- Scale horizontally
- Use load balancing
- Monitor system resources

**4. Cost Management**
- Balance speed vs cost
- Use caching aggressively
- Optimize API usage
- Monitor costs in real-time

### High-Frequency News Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│  REAL-TIME NEWS STREAM (WebSocket)                          │
│  - News arrives every second/millisecond                    │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼ (Target: < 10ms)
┌─────────────────────────────────────────────────────────────┐
│  NEWS FETCH AGENT (Real-Time)                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Receive news via WebSocket                         │  │
│  │ 2. Quick relevance check (< 5ms)                      │  │
│  │ 3. Filter and score                                    │  │
│  │ 4. Pass to sentiment agent immediately                 │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼ (Target: < 50ms)
┌─────────────────────────────────────────────────────────────┐
│  LLM SENTIMENT AGENT (Real-Time)                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Check semantic cache (< 1ms)                       │  │
│  │ 2. If cached → return immediately                      │  │
│  │ 3. If not → async GPT-4 call (< 2 seconds)            │  │
│  │ 4. Store in cache                                      │  │
│  │ 5. Pass to aggregator                                  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼ (Target: < 10ms)
┌─────────────────────────────────────────────────────────────┐
│  SENTIMENT AGGREGATOR (Real-Time)                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. Incremental aggregation                            │  │
│  │ 2. Update existing sentiment                          │  │
│  │ 3. Recalculate impact                                 │  │
│  │ 4. Store result                                        │  │
│  │ 5. Send to Fusion Agent                               │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  TOTAL LATENCY: < 100ms (with cache)                        │
│  TOTAL LATENCY: < 3 seconds (without cache)                │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary: What to Add to Your Agents

### News Fetch Agent - Additional Methods

```python
# For Automation
def batch_process(self, symbols: List[str]) -> Dict[str, Any]
def scheduled_fetch(self, symbols: List[str]) -> Dict[str, Any]

# For Regime Change Detection
def detect_volume_anomaly(self, symbol: str, current_volume: int, historical_avg: float) -> Dict[str, Any]
def track_news_volume(self, symbol: str) -> Dict[str, Any]

# For High-Frequency Trading
def stream_news(self, symbol: str) -> AsyncIterator[Dict[str, Any]]
def process_realtime_news(self, news_item: Dict[str, Any]) -> Dict[str, Any]
```

### LLM Sentiment Agent - Additional Methods

```python
# For Automation
def batch_analyze(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]
def queue_analysis(self, articles: List[Dict[str, Any]]) -> str  # Returns job ID
def get_cost_stats(self) -> Dict[str, Any]

# For High-Frequency Trading
async def analyze_async(self, article: Dict[str, Any]) -> Dict[str, Any]
def fast_cache_lookup(self, article_text: str) -> Optional[Dict[str, Any]]
def batch_cache_lookup(self, articles: List[str]) -> List[Optional[Dict[str, Any]]]
```

### Sentiment Aggregator - Additional Methods

```python
# For Automation
def batch_aggregate(self, symbols: List[str]) -> Dict[str, Any]
def detect_changes(self, symbol: str, threshold: float = 0.3) -> Dict[str, Any]

# For Regime Change Detection
def detect_sentiment_regime_change(self, symbol: str, recent_sentiment: float, historical_sentiment: float) -> Dict[str, Any]
def calculate_sentiment_volatility(self, symbol: str, window: int = 7) -> float

# For High-Frequency Trading
def incremental_aggregate(self, symbol: str, new_sentiment: float) -> Dict[str, Any]
def get_realtime_sentiment(self, symbol: str) -> Dict[str, Any]
```

---

## Technologies & Models You'll Use

### For Automation:
- **Celery** or **APScheduler** (task scheduling)
- **Redis** (caching and queuing)
- **PostgreSQL/TimescaleDB** (data storage)
- **Logging framework** (monitoring)

### For Regime Change Detection:
- **Statistical libraries** (numpy, scipy) for anomaly detection
- **Time-series analysis** (pandas)
- **No additional ML models needed** (statistical methods)

### For High-Frequency Trading:
- **WebSocket libraries** (websockets, aiohttp)
- **Vector databases** (FAISS, Qdrant) for fast similarity search
- **Async/await patterns** (asyncio)
- **In-memory databases** (Redis)
- **Sentence transformers** (for embeddings)

---

## Key Takeaways

### Automation:
- ✅ Make agents batch-processable
- ✅ Add scheduling support
- ✅ Implement robust error handling
- ✅ Monitor costs and performance

### Regime Change Detection:
- ✅ Track historical patterns
- ✅ Detect anomalies in volume and sentiment
- ✅ Flag significant changes
- ✅ Provide confidence scores

### High-Frequency Trading:
- ✅ Optimize for speed (< 100ms target)
- ✅ Use real-time streaming
- ✅ Implement fast caching
- ✅ Support incremental updates

**Your agents should be:**
- **Scalable** (handle 1 or 100 tickers)
- **Fast** (low latency for real-time)
- **Reliable** (robust error handling)
- **Cost-effective** (aggressive caching)
- **Observable** (comprehensive monitoring)

This enables automation, regime change detection, and high-frequency processing while maintaining reliability and cost efficiency.

---

## Key Takeaways for Developer 1

### Must Do:
1. ✅ Implement batch processing for multiple tickers
2. ✅ Implement semantic caching (critical for cost)
3. ✅ Handle API rate limits properly
4. ✅ Process tickers in parallel where possible
5. ✅ Implement robust error handling

### Must Take Care Of:
1. ⚠️ API costs (GPT-4 is expensive)
2. ⚠️ Rate limits (don't exceed API limits)
3. ⚠️ Performance (process 100 tickers efficiently)
4. ⚠️ Data quality (validate all inputs)
5. ⚠️ Monitoring (track metrics and errors)

### Nice to Have:
1. 💡 Sector-specific optimizations
2. 💡 Advanced caching strategies
3. 💡 Performance dashboards
4. 💡 Automated retry mechanisms

---

## Summary

Your agents are **universal**—same code for all tickers. Focus on:
- **Efficiency**: Process multiple tickers in parallel
- **Cost optimization**: Aggressive semantic caching
- **Reliability**: Robust error handling
- **Scalability**: System handles 100+ tickers

The system should work the same way for 1 ticker or 100 tickers—just with more parallel processing and better caching.

---

## Summary

### Overview: What Are News Agents?

As Developer 1, I am responsible for building **three specialized agents** that work together to collect, analyze, and aggregate news sentiment for stock trading decisions:

1. **News Fetch Agent**: Collects financial news from multiple sources
2. **LLM Sentiment Agent**: Analyzes news sentiment using GPT-4
3. **Sentiment Aggregator**: Combines sentiment scores into final trading signals

These agents are **universal**—the same code processes any ticker, from 1 to 100+ stocks across different sectors.

---

### Models Used in News Agents

**Primary Models:**
- **GPT-4 (OpenAI)**: Sentiment analysis model that analyzes news articles and returns sentiment scores (-1.0 to +1.0)
- **Sentence Transformers**: Converts article text to embeddings for semantic similarity matching
- **Vector Databases (FAISS/Qdrant)**: Fast similarity search for semantic caching

**How Agents and Models Interact:**
- **Agents orchestrate**: Agents control workflow, prepare data, and make decisions
- **Models predict**: Models are passive—they receive data and return predictions
- **Agents call models**: Agents load models, pass data, and interpret results
- **Example**: LLM Sentiment Agent loads GPT-4, sends article text, receives sentiment score, then formats the result

---

### End-to-End Process: Input to Output

#### Raw Input Example (5 Tickers, 2 Sectors)

**Initial Request:**
```json
{
  "tickers": ["AAPL", "MSFT", "XOM", "CVX", "JNJ"],
  "sectors": {
    "technology": ["AAPL", "MSFT"],
    "energy": ["XOM", "CVX"],
    "healthcare": ["JNJ"]
  },
  "params": {
    "date_range": "last_7_days",
    "max_articles_per_ticker": 20,
    "sources": ["finnhub", "newsapi"],
    "min_relevance_score": 0.5
  }
}
```

---

#### Step 1: News Fetch Agent

**Agent:** News Fetch Agent  
**Models Called:** None (data collection and filtering only)

**Input Received (Raw):**
```json
{
  "symbol": "AAPL",
  "params": {
    "date_range": "last_7_days",
    "max_articles": 20,
    "sources": ["finnhub", "newsapi"]
  }
}
```

**Agent Processing:**
1. Fetches raw news from APIs (Finnhub, NewsAPI, Alpha Vantage)
2. Filters by relevance to ticker
3. Removes duplicates
4. Scores relevance (0.0 to 1.0)

**Refined Output (After Agent Processing):**
```json
{
  "symbol": "AAPL",
  "articles": [
    {
      "id": "article_001",
      "title": "Apple Reports Record Q4 Earnings, Stock Surges",
      "source": "Reuters",
      "published_at": "2024-01-15T10:00:00Z",
      "url": "https://reuters.com/apple-earnings",
      "summary": "Apple Inc reported record-breaking Q4 earnings...",
      "content": "Full article text here...",
      "relevance_score": 0.95,
      "sector": "technology"
    },
    {
      "id": "article_002",
      "title": "Apple Announces New AI Features",
      "source": "TechCrunch",
      "published_at": "2024-01-15T09:30:00Z",
      "url": "https://techcrunch.com/apple-ai",
      "summary": "Apple unveiled new AI capabilities...",
      "content": "Full article text here...",
      "relevance_score": 0.92,
      "sector": "technology"
    }
    // ... more articles
  ],
  "fetched_at": "2024-01-15T10:30:00Z",
  "total_count": 15,
  "sources": ["finnhub", "newsapi"]
}
```

**This output is passed to → LLM Sentiment Agent**

---

#### Step 2: LLM Sentiment Agent

**Agent:** LLM Sentiment Agent  
**Models Called:**
- **Sentence Transformers** (for embeddings)
- **Vector Database** (FAISS/Qdrant for cache lookup)
- **GPT-4** (OpenAI API for sentiment analysis)

**Input Received (From News Fetch Agent):**
```json
{
  "symbol": "AAPL",
  "articles": [
    {
      "id": "article_001",
      "title": "Apple Reports Record Q4 Earnings, Stock Surges",
      "content": "Full article text here...",
      "relevance_score": 0.95
    }
    // ... more articles
  ]
}
```

**Agent Processing for Each Article:**

**2a. Cache Check (Using Sentence Transformers + Vector DB):**
- Agent calls **Sentence Transformers model** → Converts article text to embedding vector
- Agent queries **Vector Database** → Searches for similar cached articles
- If similarity > 0.85 → Use cached sentiment (skip GPT-4)

**2b. If Not Cached (Calls GPT-4):**

**Input Passed to GPT-4 Model:**
```json
{
  "model": "gpt-4",
  "messages": [
    {
      "role": "system",
      "content": "You are a financial sentiment analyst. Analyze news sentiment for stocks."
    },
    {
      "role": "user",
      "content": "Analyze the sentiment of this financial news article about AAPL:\n\nTitle: Apple Reports Record Q4 Earnings, Stock Surges\n\nContent: Apple Inc reported record-breaking Q4 earnings, exceeding analyst expectations. The stock surged 5% in after-hours trading...\n\nReturn sentiment as a number from -1.0 (very negative) to +1.0 (very positive), and a label: positive, neutral, or negative."
    }
  ]
}
```

**Output Received from GPT-4 Model:**
```json
{
  "sentiment_score": 0.85,
  "sentiment_label": "positive",
  "confidence": 0.92,
  "reasoning": "Article reports record earnings and stock surge, clearly positive sentiment"
}
```

**Agent Output (After Processing All Articles):**
```json
{
  "symbol": "AAPL",
  "sentiment_scores": [
    {
      "article_id": "article_001",
      "sentiment_score": 0.85,
      "sentiment_label": "positive",
      "confidence": 0.92,
      "processed_at": "2024-01-15T10:31:00Z",
      "cached": false,
      "model_used": "gpt-4"
    },
    {
      "article_id": "article_002",
      "sentiment_score": 0.72,
      "sentiment_label": "positive",
      "confidence": 0.88,
      "processed_at": "2024-01-15T10:31:15Z",
      "cached": true,
      "model_used": "cached"
    }
    // ... more sentiment scores
  ],
  "cache_stats": {
    "hit_rate": 0.33,
    "total_articles": 15,
    "cached_articles": 5,
    "api_calls_saved": 5
  }
}
```

**This output is passed to → Sentiment Aggregator**

---

#### Step 3: Sentiment Aggregator

**Agent:** Sentiment Aggregator  
**Models Called:** None (mathematical aggregation only)

**Input Received (From LLM Sentiment Agent):**
```json
{
  "symbol": "AAPL",
  "sentiment_scores": [
    {
      "article_id": "article_001",
      "sentiment_score": 0.85,
      "sentiment_label": "positive",
      "confidence": 0.92,
      "processed_at": "2024-01-15T10:31:00Z"
    },
    {
      "article_id": "article_002",
      "sentiment_score": 0.72,
      "sentiment_label": "positive",
      "confidence": 0.88,
      "processed_at": "2024-01-15T10:31:15Z"
    }
    // ... more sentiment scores
  ]
}
```

**Agent Processing:**
1. Applies time-weighting (recent = weight 1.0, older = weight 0.7)
2. Calculates weighted average sentiment
3. Determines impact level (High/Medium/Low)
4. Calculates confidence score

**Final Output:**
```json
{
  "symbol": "AAPL",
  "aggregated_sentiment": 0.68,
  "sentiment_label": "positive",
  "confidence": 0.82,
  "impact": "High",
  "news_count": 15,
  "time_weighted": true,
  "aggregated_at": "2024-01-15T10:32:00Z",
  "regime_change_detected": false,
  "breakdown": {
    "positive_articles": 12,
    "neutral_articles": 2,
    "negative_articles": 1,
    "average_sentiment": 0.68,
    "sentiment_std": 0.15
  }
}
```

**This output is used by the Fusion Agent (Lead Developer) to create final trading signals.**

---

#### Complete Flow Diagram: Agent → Model Interactions

```
┌─────────────────────────────────────────────────────────────┐
│  RAW INPUT                                                   │
│  {tickers: ["AAPL", "MSFT", "XOM", "CVX", "JNJ"], ...}      │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  NEWS FETCH AGENT                                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Input: Raw request with tickers                        │  │
│  │ Processing: Fetch, filter, score relevance             │  │
│  │ Models Called: NONE                                    │  │
│  │ Output: Refined news articles                          │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼ (Passes refined articles)
┌─────────────────────────────────────────────────────────────┐
│  LLM SENTIMENT AGENT                                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Input: News articles from News Fetch Agent            │  │
│  │                                                       │  │
│  │ Step 1: Check Cache                                   │  │
│  │   ├─ Calls: Sentence Transformers Model              │  │
│  │   │   └─ Output: Article embedding vector            │  │
│  │   ├─ Calls: Vector Database (FAISS/Qdrant)           │  │
│  │   │   └─ Output: Similar articles (if found)         │  │
│  │   └─ If cached → Use cached sentiment                │  │
│  │                                                       │  │
│  │ Step 2: If Not Cached                                 │  │
│  │   ├─ Calls: GPT-4 Model (OpenAI API)                 │  │
│  │   │   Input: Article text + prompt                    │  │
│  │   │   Output: Sentiment score + label                 │  │
│  │   └─ Stores result in cache                          │  │
│  │                                                       │  │
│  │ Output: Sentiment scores for all articles             │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼ (Passes sentiment scores)
┌─────────────────────────────────────────────────────────────┐
│  SENTIMENT AGGREGATOR                                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Input: Sentiment scores from LLM Sentiment Agent      │  │
│  │ Processing: Time-weighting, aggregation, impact calc  │  │
│  │ Models Called: NONE (mathematical operations only)    │  │
│  │ Output: Final aggregated sentiment per ticker         │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  FINAL OUTPUT (Per Ticker)                                  │
│  {                                                           │
│    "symbol": "AAPL",                                         │
│    "aggregated_sentiment": 0.68,                             │
│    "sentiment_label": "positive",                            │
│    "confidence": 0.82,                                       │
│    "impact": "High"                                          │
│  }                                                           │
└─────────────────────────────────────────────────────────────┘
```

---

#### Summary: Agent-Model Interactions

| Agent | Models Called | Purpose | Input to Model | Output from Model |
|-------|--------------|---------|----------------|-------------------|
| **News Fetch Agent** | None | Data collection & filtering | N/A | N/A |
| **LLM Sentiment Agent** | **Sentence Transformers** | Convert text to embeddings | Article text | Embedding vector |
| **LLM Sentiment Agent** | **Vector Database** | Cache lookup | Embedding vector | Similar cached articles |
| **LLM Sentiment Agent** | **GPT-4** | Sentiment analysis | Article text + prompt | Sentiment score + label |
| **Sentiment Aggregator** | None | Mathematical aggregation | N/A | N/A |

**Key Points:**
- **News Fetch Agent**: No models, only data processing
- **LLM Sentiment Agent**: Uses 3 models (Sentence Transformers, Vector DB, GPT-4)
- **Sentiment Aggregator**: No models, only mathematical calculations
- **Data Flow**: Raw input → Refined articles → Sentiment scores → Aggregated sentiment

---

### Challenges and Defined Solutions

After studying the complete system architecture, I have identified key challenges and defined solutions:

#### 1. **Scalability: Handling 100+ Tickers Across Sectors**

**Challenge:** Process news for 100+ tickers efficiently without performance degradation.

**Solution:**
- Batch processing (10-20 tickers per batch)
- Parallel execution across tickers
- Universal agent design (same code for all tickers)
- Sector-aware filtering (optional optimization)

**Performance Target:** < 16 minutes for 100 tickers

---

#### 2. **Cost Management: GPT-4 API Costs**

**Challenge:** GPT-4 API is expensive (~$0.01-0.03 per article). For 100 tickers × 15 articles = $15-45 per cycle.

**Solution:**
- **Semantic caching**: Global cache shared across all tickers
- **Similarity matching**: Cache articles with >85% similarity
- **Target**: 60%+ cache hit rate (reduces costs by 60%)
- **Cost savings**: From $15-45 to $6-18 per cycle

---

#### 3. **Automation: Fully Automated Pipeline**

**Challenge:** System must run automatically without human intervention.

**Solution:**
- Scheduled tasks (Celery/APScheduler) for periodic news fetching
- Queue systems (Redis Queue) for GPT-4 API calls
- Automatic cache management and cleanup
- Error handling with retry logic and fallback mechanisms
- Monitoring and alerting for failures

---

#### 4. **Regime Change Detection: Market Behavior Shifts**

**Challenge:** Detect sudden changes in news volume or sentiment patterns.

**Solution:**
- **Volume anomaly detection**: Track news volume vs historical average
- **Sentiment volatility detection**: Monitor sudden sentiment shifts
- **Statistical thresholds**: Flag anomalies (>3x or <0.3x historical)
- **Confidence scoring**: Provide confidence levels for regime changes

---

#### 5. **High-Frequency Trading: Real-Time Processing**

**Challenge:** Process news in real-time with ultra-low latency (< 100ms target).

**Solution:**
- WebSocket connections for real-time news streaming
- Fast cache lookups using vector databases (FAISS/Qdrant)
- Async/await patterns for concurrent processing
- Incremental aggregation (update as news arrives)
- In-memory state management for fast access

**Latency Targets:**
- With cache: < 100ms total
- Without cache: < 3 seconds (GPT-4 API call)

---

#### 6. **API Rate Limits and Reliability**

**Challenge:** News APIs and GPT-4 have rate limits. System must handle failures gracefully.

**Solution:**
- Rate limiting and throttling per API provider
- Retry logic with exponential backoff
- Fallback to alternative news sources (Finnhub → NewsAPI → Alpha Vantage)
- Graceful degradation (return partial results if some sources fail)
- Comprehensive logging and monitoring

---

#### 7. **Data Quality and Validation**

**Challenge:** Ensure all data is valid and reliable before processing.

**Solution:**
- Input validation for all news articles
- Data quality checks (completeness, timestamps, relevance scores)
- Flag suspicious data for review
- Log validation failures for monitoring

---

### Key Aspects I Will Be Mindful Of

1. **Cost Optimization**: Aggressive semantic caching to minimize GPT-4 API costs
2. **Performance**: Parallel processing and efficient algorithms for speed
3. **Reliability**: Robust error handling and fallback mechanisms
4. **Scalability**: System handles 1 ticker or 100+ tickers seamlessly
5. **Monitoring**: Track cache hit rates, API costs, processing times, error rates
6. **Automation**: Fully automated pipeline with minimal human intervention
7. **Real-Time Capability**: Support for high-frequency trading requirements
8. **Regime Detection**: Monitor and flag significant market behavior changes

---

### Deliverables

- **News Fetch Agent**: Multi-source news collection with relevance filtering
- **LLM Sentiment Agent**: GPT-4 sentiment analysis with 60%+ cache hit rate
- **Sentiment Aggregator**: Time-weighted sentiment aggregation with impact scoring
- **API Endpoints**: RESTful APIs for all three agents
- **Unit Tests**: Comprehensive test coverage
- **Documentation**: Complete technical documentation

---

### Expected Impact

The News & Sentiment Agents will provide:
- **Accurate sentiment analysis** for trading decisions
- **Cost-effective operations** through semantic caching
- **Scalable architecture** supporting 100+ tickers
- **Real-time capabilities** for high-frequency trading
- **Automated pipeline** reducing manual intervention
- **Regime change detection** for adaptive trading strategies

---

## Key Learning Points

### 1. Why Three Separate Agents?

- **Separation of Concerns**: Each agent has one job
- **Easier to Test**: Test each component independently
- **Easier to Maintain**: Fix issues in one agent without affecting others
- **Scalability**: Can scale each agent independently

### 2. Why Semantic Caching?

- **GPT-4 API calls are expensive** (costs money per request)
- **Similar articles get similar sentiment**
- **Cache similar articles** to save money
- **Target: 60%+ cache hit rate** (60% of articles use cached results)

### 3. Why Time-Weighting?

- **Recent news is more relevant** than old news
- **Older news has less impact** on current sentiment
- **Weight recent articles more heavily** in aggregation

---

## Next Steps

1. Review this document thoroughly
2. Understand the workflow and data flow
3. Start implementing News Fetch Agent first
4. Then implement LLM Sentiment Agent
5. Finally implement Sentiment Aggregator
6. Create API endpoints for all three
7. Write unit tests

---

## Questions?

Contact the Lead Developer for:
- Architecture decisions
- Interface clarifications
- Dependency coordination
- Code review requests
- Milestone planning

