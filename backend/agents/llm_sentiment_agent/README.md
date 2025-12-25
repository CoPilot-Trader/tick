# LLM Sentiment Agent

**Developer**: Developer 1  
**Branch**: `feature/llm-sentiment-agent`  
**Status**: 🚧 In Development  
**Milestone**: M3 - Sentiment & Fusion

## Overview

The LLM Sentiment Agent is responsible for:
- Processing news using GPT-4 API
- Sentiment scoring pipeline (-1 to +1 scale)
- Semantic caching implementation (60%+ cache hit rate target)
- Cost optimization strategies
- Providing sentiment scores to Sentiment Aggregator

## Directory Structure

```
llm_sentiment_agent/
├── __init__.py
├── agent.py              # Main agent class
├── interfaces.py         # Public interface definitions
├── llm/                 # LLM integration
│   ├── __init__.py
│   ├── gpt4_client.py
│   └── prompt_templates.py
├── cache/               # Semantic caching
│   ├── __init__.py
│   ├── semantic_cache.py
│   └── cache_manager.py
├── optimization/        # Cost optimization
│   ├── __init__.py
│   └── cost_optimizer.py
├── tests/               # Unit tests
│   ├── __init__.py
│   ├── test_agent.py
│   └── mocks/
└── README.md            # This file
```

## Interface

### Requires

- News articles from News Fetch Agent

### Provides

**Sentiment Scores**:
```python
{
    "symbol": "AAPL",
    "article_id": "article_123",
    "sentiment_score": 0.75,  # -1.0 to +1.0
    "sentiment_label": "positive",  # positive, neutral, negative
    "confidence": 0.85,
    "processed_at": "2024-01-15T10:30:00Z",
    "cached": False
}
```

### API Endpoints

- `POST /api/v1/sentiment/analyze` - Analyze news sentiment
- `GET /api/v1/sentiment/cache/stats` - Get cache statistics
- `POST /api/v1/sentiment/batch` - Batch sentiment analysis

## Development Tasks

### Phase 1: Core Structure
- [x] Set up agent class structure
- [x] Implement base agent interface
- [ ] Create directory structure
- [ ] Set up testing framework

### Phase 2: GPT-4 Integration
- [ ] Integrate OpenAI GPT-4 API
- [ ] Create prompt templates
- [ ] Implement sentiment extraction
- [ ] Add error handling
- [ ] Write unit tests

### Phase 3: Semantic Caching
- [ ] Implement semantic similarity detection
- [ ] Add cache storage (Redis/vector DB)
- [ ] Implement cache lookup
- [ ] Target: 60%+ cache hit rate
- [ ] Write unit tests

### Phase 4: Cost Optimization
- [ ] Implement batching strategies
- [ ] Add request optimization
- [ ] Monitor API costs
- [ ] Write unit tests

## Dependencies

- openai (GPT-4 API)
- sentence-transformers (for semantic similarity)
- Redis (for caching)
- numpy

## Acceptance Criteria (Milestone 3)

- LLM Sentiment Agent processes news with GPT-4 and returns sentiment scores
- Sentiment scores generated within 5 seconds per news item (with caching)
- Semantic caching reduces API calls by >60%
- Cache hit rate >60% for repeated or similar news queries
- Cost optimization strategies implemented

## Notes

- Use GPT-4 for high-quality sentiment analysis
- Semantic caching critical for cost reduction
- Sentiment scale: -1.0 (very negative) to +1.0 (very positive)
- Cache similar news articles to avoid redundant API calls
- Monitor API usage and costs

