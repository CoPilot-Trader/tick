# News Fetch Agent

**Developer**: Developer 1  
**Branch**: `feature/news-fetch-agent`  
**Status**: ✅ Production Ready  
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
├── __init__.py                    # Package initialization
├── agent.py                        # Main agent class (NewsFetchAgent)
├── interfaces.py                   # Pydantic models (NewsArticle, NewsResponse)
├── README.md                       # This file
│
├── collectors/                     # News collection modules
│   ├── __init__.py                # Package exports
│   ├── base_collector.py          # Abstract base class for all collectors
│   ├── finnhub_collector.py       # Finnhub API integration
│   ├── newsapi_collector.py       # NewsAPI integration
│   ├── alpha_vantage_collector.py # Alpha Vantage API integration
│   └── mock_collector.py           # Mock data collector for testing
│
├── filters/                        # News filtering logic
│   ├── __init__.py                # Package exports
│   ├── relevance_filter.py        # Relevance scoring and filtering
│   └── duplicate_filter.py        # Duplicate detection and removal
│
├── utils/                          # Utility functions
│   ├── __init__.py                # Package exports
│   ├── data_normalizer.py         # Normalize different API formats
│   ├── sector_mapper.py           # Map tickers to sectors
│   ├── date_range_calculator.py   # Calculate date ranges for time horizons
│   ├── logger.py                  # Logging utility
│   └── retry.py                   # Retry logic with exponential backoff
│
└── tests/                          # Unit tests
    ├── __init__.py                # Test package initialization
    ├── test_agent.py              # Tests for main agent class
    ├── test_collectors.py         # Tests for news collectors
    ├── test_filters.py            # Tests for filtering logic
    └── mocks/                     # Mock data for testing
        ├── __init__.py            # Mock package initialization
        └── news_mock_data.json    # Mock news articles (10 tickers, 100 articles)
```

### Component Overview

#### Collectors (`collectors/`)
- **Purpose**: Fetch news from various APIs
- **Base Class**: `BaseNewsCollector` - Defines interface for all collectors
- **Real Collectors**: ✅ Finnhub, NewsAPI, Alpha Vantage (fully implemented)
- **Mock Collector**: `MockNewsCollector` - Returns mock data for testing
- **Why Separate**: Easy to add new sources, test independently, handle API-specific logic

#### Filters (`filters/`)
- **Purpose**: Process and filter news articles
- **RelevanceFilter**: Calculates relevance scores (0.0-1.0) and filters by threshold
- **DuplicateFilter**: Detects and removes duplicate articles from multiple sources
- **Why Separate**: Reusable logic, easy to test, can add new filters (spam, quality, etc.)

#### Utils (`utils/`)
- **Purpose**: Shared utility functions
- **DataNormalizer**: Converts different API formats to standard format
- **SectorMapper**: Maps ticker symbols to sectors (technology, energy, healthcare, finance)
- **Why Separate**: Reusable across modules, keeps agent code clean

#### Tests (`tests/`)
- **Purpose**: Unit tests for all components
- **Test Files**: Separate test files for agent, collectors, and filters
- **Mock Data**: JSON file with 10 tickers across 4 sectors (100 articles total)
- **Why Separate**: Organized testing, easy to run, mock data separate from code

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

### Phase 1: Core Structure ✅
- [x] Set up agent class structure
- [x] Implement base agent interface
- [x] Create directory structure
- [x] Set up testing framework
- [x] Create all collector files with docstrings
- [x] Create all filter files with docstrings
- [x] Create utility files with docstrings
- [x] Create test files structure
- [x] Create mock data (10 tickers, 100 articles)

### Phase 2: News Collection ✅
- [x] Integrate Finnhub API
- [x] Integrate NewsAPI
- [x] Integrate Alpha Vantage (fallback)
- [x] Add error handling
- [x] Write unit tests
- [x] API usage tracking
- [x] Time horizon support

### Phase 3: Filtering ✅
- [x] Implement relevance scoring
- [x] Add news filtering
- [x] Add duplicate detection
- [x] Write unit tests

### Phase 4: Real-time Monitoring
- [ ] Implement real-time news monitoring
- [ ] Add news streaming
- [ ] Write unit tests

## Dependencies

### Required
- `requests` or `httpx` - HTTP client for API calls
- `pydantic` - Data validation (already in project)
- `python-dateutil` - Date parsing (if needed)

### Optional (for specific collectors)
- `finnhub-python` - Finnhub API client (optional, can use requests)
- `newsapi-python` - NewsAPI client (optional, can use requests)

### Testing
- `pytest` - Testing framework
- `unittest.mock` - Mocking (built-in)

## Mock Data

The agent includes mock data for testing and development:

**Location**: `tests/mocks/news_mock_data.json`

**Contents**:
- **10 Tickers** across 4 sectors:
  - Technology: AAPL, MSFT, GOOGL (3 tickers)
  - Energy: XOM, CVX (2 tickers)
  - Healthcare: JNJ, PFE (2 tickers)
  - Finance: JPM, BAC, GS (3 tickers)
- **100 Articles** total (10 articles per ticker)
- **Format**: Standard JSON with id, title, source, published_at, url, summary, content

**Usage**:
```python
from news_fetch_agent.collectors import MockNewsCollector

collector = MockNewsCollector()
articles = collector.fetch_news("AAPL")
```

## Component Details

### Collectors

#### BaseNewsCollector (Abstract Base Class)
- Defines interface: `fetch_news(symbol, params) -> List[Dict]`
- Provides: `normalize_response()`, `health_check()`, `get_source_name()`
- All collectors must inherit from this class

#### MockNewsCollector
- **Status**: ✅ Implemented (stub with mock data loading)
- Loads articles from `tests/mocks/news_mock_data.json`
- Returns articles in standard format
- Used for testing without API dependencies

#### FinnhubCollector
- **Status**: ✅ Fully Implemented
- API: https://finnhub.io/docs/api/company-news
- Free tier: 60 calls/minute
- Features: Real API integration, usage tracking, rate limit management
- Requires: API key (falls back to mock if not provided)

#### NewsAPICollector
- **Status**: ✅ Fully Implemented
- API: https://newsapi.org/docs
- Free tier: 1,000 requests/day
- Features: Real API integration, usage tracking, daily limit management
- Requires: API key (falls back to mock if not provided)

#### AlphaVantageCollector
- **Status**: ✅ Fully Implemented
- API: https://www.alphavantage.co/documentation/
- Free tier: 5 calls/minute, 500 calls/day
- Features: Real API integration, usage tracking, dual limit management
- Requires: API key (falls back to mock if not provided)

### Filters

#### RelevanceFilter
- **Status**: ✅ Fully Implemented
- Calculates relevance score (0.0-1.0) for articles
- Filters articles by minimum threshold
- Sorts articles by relevance
- Factors: keyword matching, title relevance, content analysis
- Supports 25+ tickers with keyword mapping

#### DuplicateFilter
- **Status**: ✅ Fully Implemented
- Detects duplicates by: URL match, title similarity, content similarity
- Removes duplicates, keeps preferred source
- Uses SequenceMatcher for similarity calculation
- Tested and working correctly

### Utils

#### DataNormalizer
- **Status**: ✅ Fully Implemented
- Normalizes different API formats to standard format
- Methods: `normalize_finnhub()`, `normalize_newsapi()`, `normalize_alpha_vantage()`
- Handles: timestamp conversion, field mapping, missing fields
- All three API formats fully supported

#### SectorMapper
- **Status**: ✅ Implemented (basic version)
- Maps tickers to sectors (technology, energy, healthcare, finance, consumer)
- Methods: `get_sector()`, `get_tickers_by_sector()`, `add_ticker()`
- Currently includes 25+ tickers, can be extended

## Acceptance Criteria (Milestone 3)

- News Fetch Agent collects news from 2+ sources for target tickers
- News collection operational for all target tickers
- Relevance scoring functional
- Real-time news monitoring operational
- API endpoints return valid JSON responses

## Usage Examples

### Using Mock Collector (Testing)
```python
from news_fetch_agent.collectors import MockNewsCollector

# Create mock collector
collector = MockNewsCollector()

# Fetch news for a ticker
articles = collector.fetch_news("AAPL", {"limit": 5})

# Articles are in standard format
for article in articles:
    print(f"{article['title']} - {article['source']}")
```

### Using Filters
```python
from news_fetch_agent.filters import RelevanceFilter, DuplicateFilter

# Score articles by relevance
relevance_filter = RelevanceFilter()
scored_articles = relevance_filter.score_articles(articles, "AAPL")

# Filter by threshold
filtered = relevance_filter.filter_by_threshold(scored_articles, min_score=0.5)

# Remove duplicates
duplicate_filter = DuplicateFilter()
unique_articles = duplicate_filter.remove_duplicates(filtered)
```

### Using Sector Mapper
```python
from news_fetch_agent.utils import SectorMapper

mapper = SectorMapper()
sector = mapper.get_sector("AAPL")  # Returns: "technology"
tech_tickers = mapper.get_tickers_by_sector("technology")  # Returns: ["AAPL", "MSFT", ...]
```

## Development Workflow

1. **Start with Mock Data**: Use `MockNewsCollector` for initial development
2. **Implement Filters**: Test relevance and duplicate filtering with mock data
3. **Implement Real Collectors**: Add API integrations one by one
4. **Test Integration**: Test full pipeline with mock data first
5. **Add Real Data**: Switch to real APIs once everything works

## Status

### ✅ Completed Features

- **Real API Integration**: Finnhub, NewsAPI, Alpha Vantage fully integrated
- **Time Horizon Support**: Supports 1s, 1m, 1h, 1d, 1w, 1mo, 1y time windows
- **API Usage Tracking**: Real-time tracking of API calls and remaining quotas
- **Relevance Filtering**: Advanced relevance scoring with keyword matching
- **Duplicate Detection**: Multi-method duplicate detection (URL, title, content)
- **Data Normalization**: Complete normalization for all three API formats
- **Error Handling**: Comprehensive error handling and fallback mechanisms
- **Mock Data Support**: Full mock data support for testing without API keys

### 🚧 Future Enhancements

- Real-time news monitoring
- News streaming capabilities
- Advanced caching strategies

## Notes

- Use multiple sources for redundancy
- Filter news by relevance to stock symbol
- Handle API rate limits (automatically tracked)
- Remove duplicates across sources
- Mock data allows development without API keys
- All components have docstrings explaining purpose and usage
- Agent automatically falls back to mock data if API keys are not provided

