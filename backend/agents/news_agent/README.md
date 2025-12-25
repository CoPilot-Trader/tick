# News Agent

**Developer**: Developer 1  
**Branch**: `feature/news-agent`  
**Status**: 🚧 In Development

## Overview

The News Agent is responsible for:
- Collecting news articles related to stocks
- Performing sentiment analysis on news
- Filtering and ranking news by relevance
- Providing news sentiment scores

## Directory Structure

```
news_agent/
├── __init__.py
├── agent.py              # Main agent class
├── interfaces.py         # Public interface definitions
├── collectors/          # News collection modules
│   ├── __init__.py
│   └── news_api.py      # News API integration
├── analyzers/           # Analysis modules
│   ├── __init__.py
│   └── sentiment.py     # Sentiment analysis
├── filters/             # Filtering modules
│   ├── __init__.py
│   └── relevance.py     # Relevance filtering
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── mocks/           # Mock data
└── README.md            # This file
```

## Interface

### Provides

**Sentiment Data**:
```python
{
    "symbol": "AAPL",
    "timestamp": "2024-01-15T10:30:00Z",
    "sentiment_score": 0.75,
    "sentiment_label": "positive",
    "confidence": 0.85,
    "news_count": 15
}
```

**Filtered News Articles**:
```python
{
    "articles": [...],
    "symbol": "AAPL",
    "filtered_at": "2024-01-15T10:30:00Z"
}
```

### API Endpoints

- `GET /api/v1/news/sentiment/{symbol}` - Get sentiment
- `GET /api/v1/news/articles/{symbol}` - Get articles
- `POST /api/v1/news/analyze` - Analyze news

## Development Tasks

### Phase 1: Core Structure
- [ ] Set up agent class structure
- [ ] Implement base agent interface
- [ ] Create directory structure
- [ ] Set up testing framework

### Phase 2: News Collection
- [ ] Integrate news API
- [ ] Implement news fetching
- [ ] Add error handling
- [ ] Write unit tests

### Phase 3: Sentiment Analysis
- [ ] Implement sentiment analysis
- [ ] Add confidence scoring
- [ ] Optimize performance
- [ ] Write unit tests

### Phase 4: Filtering
- [ ] Implement relevance filtering
- [ ] Add ranking algorithm
- [ ] Write unit tests

### Phase 5: API Integration
- [ ] Create FastAPI endpoints
- [ ] Add request validation
- [ ] Write integration tests

## Dependencies

### Required
- News API access (API key needed)
- Sentiment analysis library (e.g., transformers, textblob)

### Optional
- None

## Testing

```bash
# Run tests
pytest agents/news_agent/tests/

# With coverage
pytest agents/news_agent/tests/ --cov=agents.news_agent
```

## Mock Data

Mock data for development/testing available in `tests/mocks/`.

## Notes

- Keep news API rate limits in mind
- Cache news data appropriately
- Handle API failures gracefully

## Questions?

Contact Lead Developer for questions or clarifications.

