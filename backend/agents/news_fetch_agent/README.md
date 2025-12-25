# News Fetch Agent

**Developer**: Developer 1  
**Branch**: `feature/news-fetch-agent`  
**Status**: 🚧 In Development  
**Milestone**: M3 - Sentiment & Fusion

## Overview

The News Fetch Agent is responsible for:
- Collecting financial news from multiple sources (Finnhub, NewsAPI, Alpha Vantage)
- News filtering and relevance scoring
- Historical news data collection
- Real-time news monitoring
- Providing news articles to LLM Sentiment Agent

## Directory Structure

```
news_fetch_agent/
├── __init__.py
├── agent.py              # Main agent class
├── interfaces.py         # Public interface definitions
├── collectors/          # News collection modules
│   ├── __init__.py
│   ├── finnhub_collector.py
│   ├── newsapi_collector.py
│   └── alpha_vantage_collector.py
├── filters/             # News filtering
│   ├── __init__.py
│   └── relevance_filter.py
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── mocks/
└── README.md            # This file
```

## Interface

### Provides

**News Articles**:
```python
{
    "symbol": "AAPL",
    "articles": [
        {
            "id": "article_123",
            "title": "Apple Reports Strong Q4 Earnings",
            "source": "Reuters",
            "published_at": "2024-01-15T10:00:00Z",
            "url": "https://...",
            "summary": "Apple Inc reported...",
            "relevance_score": 0.92
        }
    ],
    "fetched_at": "2024-01-15T10:30:00Z",
    "total_count": 15
}
```

### API Endpoints

- `GET /api/v1/news/{symbol}` - Get news for symbol
- `POST /api/v1/news/fetch` - Trigger news fetch
- `GET /api/v1/news/sources` - Get available sources

## Development Tasks

### Phase 1: Core Structure
- [x] Set up agent class structure
- [x] Implement base agent interface
- [ ] Create directory structure
- [ ] Set up testing framework

### Phase 2: News Collection
- [ ] Integrate Finnhub API
- [ ] Integrate NewsAPI
- [ ] Integrate Alpha Vantage (fallback)
- [ ] Add error handling
- [ ] Write unit tests

### Phase 3: Filtering
- [ ] Implement relevance scoring
- [ ] Add news filtering
- [ ] Add duplicate detection
- [ ] Write unit tests

### Phase 4: Real-time Monitoring
- [ ] Implement real-time news monitoring
- [ ] Add news streaming
- [ ] Write unit tests

## Dependencies

- requests/httpx
- finnhub-python (optional)
- newsapi-python (optional)

## Acceptance Criteria (Milestone 3)

- News Fetch Agent collects news from 2+ sources for target tickers
- News collection operational for all target tickers
- Relevance scoring functional
- Real-time news monitoring operational
- API endpoints return valid JSON responses

## Notes

- Use multiple sources for redundancy
- Filter news by relevance to stock symbol
- Handle API rate limits
- Cache news data appropriately
- Remove duplicates across sources

