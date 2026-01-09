# LLM Sentiment Agent

**Developer**: Developer 1  
**Branch**: `feature/llm-sentiment-agent`  
**Status**: ✅ Production Ready (Mock GPT-4) | 🚧 Pending Real GPT-4 API  
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
├── __init__.py                    # Package initialization
├── agent.py                        # Main agent class (LLMSentimentAgent)
├── interfaces.py                   # Pydantic models (SentimentScore)
├── README.md                       # This file
│
├── llm/                            # LLM integration
│   ├── __init__.py                # Package exports
│   ├── gpt4_client.py             # OpenAI GPT-4 API client
│   ├── mock_gpt4_client.py        # Mock GPT-4 client for testing
│   └── prompt_templates.py        # Sentiment analysis prompts
│
├── cache/                          # Semantic caching
│   ├── __init__.py                # Package exports
│   ├── semantic_cache.py          # Semantic similarity using Sentence Transformers
│   ├── cache_manager.py            # High-level cache management
│   └── vector_store.py             # Vector storage for embeddings
│
├── optimization/                   # Cost optimization
│   ├── __init__.py                # Package exports
│   └── cost_optimizer.py          # Batching, cost tracking, optimization
│
└── tests/                          # Unit tests
    ├── __init__.py                # Test package initialization
    ├── test_agent.py              # Tests for main agent class
    ├── test_end_to_end.py         # End-to-end integration tests
    └── mocks/                     # Mock data for testing
        ├── __init__.py            # Mock package initialization
        └── gpt4_mock_responses.json # Mock GPT-4 responses
```

### Component Overview

#### LLM Module (`llm/`)
- **Purpose**: GPT-4 integration and prompt management
- **GPT4Client**: Real OpenAI GPT-4 API client (stub, ready for implementation)
- **MockGPT4Client**: ✅ Fully implemented with content-based sentiment generation
- **PromptTemplates**: ✅ Sentiment analysis prompts optimized for GPT-4
- **Why Separate**: Easy to switch models, test independently, manage prompts

#### Cache Module (`cache/`)
- **Purpose**: Semantic caching to reduce API costs
- **SemanticCache**: Uses Sentence Transformers for similarity detection
- **CacheManager**: High-level cache operations and statistics
- **VectorStore**: In-memory vector storage (can be replaced with Redis/Pinecone)
- **Why Separate**: Reusable caching logic, easy to test, scalable

#### Optimization Module (`optimization/`)
- **Purpose**: Cost optimization strategies
- **CostOptimizer**: Batching, cost tracking, request optimization
- **Why Separate**: Centralized cost management, easy to extend

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

### Phase 1: Core Structure ✅
- [x] Set up agent class structure
- [x] Implement base agent interface
- [x] Create directory structure
- [x] Set up testing framework
- [x] Create all component files with docstrings

### Phase 2: GPT-4 Integration ✅
- [x] Create prompt templates
- [x] Implement mock GPT-4 client (content-based sentiment)
- [x] Create GPT-4 client stub (ready for real API)
- [x] Implement sentiment extraction logic
- [x] Add error handling
- [ ] Integrate real OpenAI GPT-4 API (pending - ready to implement)
- [ ] Write unit tests for real API

### Phase 3: Semantic Caching ✅
- [x] Implement semantic similarity detection (Sentence Transformers)
- [x] Add vector store (in-memory for testing)
- [x] Implement cache lookup
- [x] Implement cache storage
- [x] Cache manager with statistics
- [ ] Add Redis backend (for production)
- [ ] Write unit tests

### Phase 4: Cost Optimization ✅
- [x] Implement batching strategies
- [x] Add cost tracking
- [x] Request optimization
- [x] Cost estimation
- [ ] Write unit tests

## Dependencies

### Required for Testing (Mock Data)
- `numpy` - For vector operations
- `pydantic` - Data validation (already in project)

### Required for Production
- `openai>=1.0.0` - GPT-4 API client
- `sentence-transformers` - For semantic similarity (pre-trained models)
- `numpy` - For vector operations

### Optional (for Production Caching)
- `redis` - For persistent cache storage (currently using in-memory)

### Installation
```bash
# For testing (mock data works without these)
pip install numpy

# For production
pip install openai sentence-transformers numpy

# Optional: For Redis caching
pip install redis
```

## Mock Data

The agent includes mock data for testing and development:

**Location**: `tests/mocks/gpt4_mock_responses.json`

**Contents**:
- Mock GPT-4 responses for 20+ articles
- Sentiment scores, labels, confidence, reasoning
- Matches real GPT-4 response format

**Usage**:
```python
from agents.llm_sentiment_agent.agent import LLMSentimentAgent

agent = LLMSentimentAgent(config={"use_mock_data": True})
agent.initialize()
result = agent.analyze_sentiment(article, "AAPL")
```

## Acceptance Criteria (Milestone 3)

- LLM Sentiment Agent processes news with GPT-4 and returns sentiment scores
- Sentiment scores generated within 5 seconds per news item (with caching)
- Semantic caching reduces API calls by >60%
- Cache hit rate >60% for repeated or similar news queries
- Cost optimization strategies implemented

## Component Details

### LLM Module

#### GPT4Client
- **Status**: 🚧 Stub created, ready for OpenAI API integration
- API: https://platform.openai.com/docs/api-reference
- Requires: OpenAI API key
- Model: gpt-4 (configurable)
- Structure complete, needs API integration

#### MockGPT4Client
- **Status**: ✅ Fully Implemented
- Returns mock responses from JSON file or generates sentiment from content
- Content-based sentiment generation for articles not in mock data
- Simulates API delay
- Used for testing without API costs
- Provides realistic sentiment scores

#### PromptTemplates
- **Status**: ✅ Fully Implemented
- Optimized prompts for sentiment analysis
- Extracts: sentiment_score, sentiment_label, confidence, reasoning
- Supports single and batch analysis

### Cache Module

#### SemanticCache
- **Status**: ✅ Fully Implemented
- Uses Sentence Transformers (pre-trained model: all-MiniLM-L6-v2)
- Generates embeddings for articles
- Finds similar articles using cosine similarity
- Similarity threshold: 0.85 (configurable)

#### CacheManager
- **Status**: ✅ Fully Implemented
- High-level cache operations
- Tracks cache statistics (hits, misses, hit rate)
- Can enable/disable caching

#### VectorStore
- **Status**: ✅ Fully Implemented (in-memory)
- Stores embeddings and metadata
- Fast similarity search
- Can be replaced with Redis/Pinecone for production

### Optimization Module

#### CostOptimizer
- **Status**: ✅ Fully Implemented
- Estimates API costs
- Creates batches for processing
- Tracks cost statistics
- Optimizes prompts

### Main Agent

#### LLMSentimentAgent
- **Status**: ✅ Fully Implemented
- Complete pipeline: cache check → GPT-4 analysis → cache store
- Integrates all components
- Returns sentiment scores in standard format

## Usage Examples

### Basic Usage (Mock Data)
```python
from agents.llm_sentiment_agent.agent import LLMSentimentAgent

# Initialize agent with mock data
agent = LLMSentimentAgent(config={
    "use_mock_data": True,
    "use_cache": True
})
agent.initialize()

# Analyze single article
article = {
    "id": "article_123",
    "title": "Apple Reports Earnings",
    "content": "Apple Inc reported strong earnings..."
}
result = agent.analyze_sentiment(article, "AAPL")
print(f"Sentiment: {result['sentiment_score']:.2f}")

# Batch analyze
articles = [article1, article2, article3]
results = agent.batch_analyze(articles, "AAPL")

# Get cache stats
stats = agent.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
```

### Integration with News Fetch Agent
```python
from agents.news_fetch_agent.agent import NewsFetchAgent
from agents.llm_sentiment_agent.agent import LLMSentimentAgent

# Fetch news
news_agent = NewsFetchAgent(config={"use_mock_data": True})
news_agent.initialize()
news_result = news_agent.process("AAPL", params={"limit": 10})

# Analyze sentiment
sentiment_agent = LLMSentimentAgent(config={"use_mock_data": True})
sentiment_agent.initialize()
sentiment_result = sentiment_agent.process("AAPL", params={
    "articles": news_result["articles"]
})

# Get results
for score in sentiment_result["sentiment_scores"]:
    print(f"Article: {score['article_id']}")
    print(f"Sentiment: {score['sentiment_score']:.2f} ({score['sentiment_label']})")
    print(f"Cached: {score['cached']}")
```

## Development Workflow

1. **Start with Mock Data**: Use `MockGPT4Client` for initial development
2. **Test Semantic Cache**: Verify cache hit rate with similar articles
3. **Test Integration**: Test with News Fetch Agent output
4. **Add Real API**: Switch to real GPT-4 when ready
5. **Optimize**: Tune cache threshold and batch sizes

## Status

### ✅ Completed Features

- **Mock GPT-4 Client**: Fully implemented with content-based sentiment generation
- **Semantic Caching**: Complete implementation with Sentence Transformers
- **Cache Management**: High-level cache operations with statistics tracking
- **Cost Optimization**: Batching, cost tracking, and optimization strategies
- **Prompt Templates**: Optimized prompts for sentiment analysis
- **Agent Pipeline**: Complete pipeline with cache check → analysis → cache store
- **Error Handling**: Comprehensive error handling

### 🚧 Pending

- **Real GPT-4 API Integration**: Stub ready, needs OpenAI API key configuration
- **Production Cache Backend**: Currently in-memory, can be upgraded to Redis/Pinecone

## Notes

- Use GPT-4 for high-quality sentiment analysis
- Semantic caching critical for cost reduction (target: 60%+ hit rate)
- Sentiment scale: -1.0 (very negative) to +1.0 (very positive)
- Cache similar news articles to avoid redundant API calls
- Monitor API usage and costs
- Sentence Transformers model is pre-trained, no training needed
- Mock data allows development without API keys
- Mock client generates realistic sentiment from article content
- All components have docstrings explaining purpose and usage

