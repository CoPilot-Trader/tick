# Developer 1 - Development Scripts

This directory contains development and testing scripts for Developer 1's News & Sentiment Agents.

## Purpose

These scripts are used for:
- Testing API key detection and configuration
- Verifying API usage tracking functionality
- Testing collector initialization
- Debugging and development

## Scripts

### `test_api_keys.py`
Verifies API key detection and collector initialization.

**Usage:**
```bash
python backend/developer1/scripts/test_api_keys.py
```

**What it does:**
- Checks environment variables for API keys
- Verifies `.env` file configuration
- Tests agent initialization with API keys
- Reports which collectors are initialized

---

### `test_api_usage_tracking.py`
Tests API usage tracking through the pipeline endpoint.

**Usage:**
```bash
python backend/developer1/scripts/test_api_usage_tracking.py
```

**What it does:**
- Makes multiple API calls to the pipeline
- Verifies that API usage counters decrease correctly
- Tests all three APIs (Finnhub, NewsAPI, Alpha Vantage)

---

### `test_collector_init.py`
Tests collector initialization with API keys.

**Usage:**
```bash
python backend/developer1/scripts/test_collector_init.py
```

**What it does:**
- Checks API key status
- Initializes News Fetch Agent
- Reports which collectors were initialized
- Shows API usage info for each collector

---

### `test_collector_tracking.py`
Tests API usage tracking for individual collectors.

**Usage:**
```bash
python backend/developer1/scripts/test_collector_tracking.py
```

**What it does:**
- Tests each collector individually
- Verifies counter increments on each call
- Tests reset logic for rate limits
- Reports pass/fail status

---

### `test_direct_collector.py`
Direct collector testing without going through the agent.

**Usage:**
```bash
python backend/developer1/scripts/test_direct_collector.py
```

**What it does:**
- Tests collectors directly
- Shows usage before and after each call
- Useful for debugging collector-specific issues

---

### `verify_api_tracking.py`
Comprehensive verification of API tracking through the full pipeline.

**Usage:**
```bash
python backend/developer1/scripts/verify_api_tracking.py
```

**What it does:**
- Makes multiple pipeline requests
- Verifies API usage tracking across all requests
- Compares remaining calls between requests
- Provides detailed test results

## Requirements

- Backend server must be running (for scripts that test API endpoints)
- API keys in `.env` file (for real API testing)
- Python dependencies from `backend/requirements.txt`

## Notes

- These scripts are for **development and testing purposes only**
- They are **not required** for production deployment
- Some scripts require the backend server to be running
- Scripts that test real APIs will consume API quota

## Integration with Main Project

These scripts are Developer 1's development tools and are separate from the main project test suite in `backend/tests/`.

