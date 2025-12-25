# Backend - Multi-Agent Stock Prediction System

Python-based backend for the multi-agent stock prediction system.

## Structure

```
backend/
├── api/                    # API endpoints and routes
├── core/                   # Core system components
├── agents/                 # Individual agent modules
│   ├── news_agent/        # Developer 1
│   ├── price_prediction_agent/  # Developer 2
│   └── orchestrator/      # Lead Developer
├── data/                   # Data sources and utilities
├── models/                 # ML models (if shared)
├── utils/                  # Shared utilities
├── tests/                  # Integration tests
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Setup

### Prerequisites

- Python 3.9+
- pip or poetry

### Installation

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Development

### Running the API

```bash
# Development server
python -m uvicorn api.main:app --reload

# Production
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# All tests
pytest

# Specific agent tests
pytest agents/news_agent/tests/
pytest agents/price_prediction_agent/tests/
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all functions and classes
- Maximum line length: 100 characters

## Agent Development

Each agent is self-contained in its own directory. See individual agent READMEs:
- [News Agent](./agents/news_agent/README.md)
- [Price Prediction Agent](./agents/price_prediction_agent/README.md)

## API Documentation

Once running, API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Environment Variables

See `.env.example` for required environment variables.

## Questions?

Contact Lead Developer for backend architecture questions.

