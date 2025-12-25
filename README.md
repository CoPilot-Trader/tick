# TICK - Time-Indexed Composite Knowledge for Markets

> A multi-agent AI system for stock market analysis, prediction, and trading signal generation. Combines price forecasting, sentiment analysis, trend classification, and support/resistance detection into unified trading signals.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3+-blue.svg)](https://www.typescriptlang.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14+-black.svg)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)

## Overview

**TICK** is a comprehensive multi-agent stock market prediction system that leverages specialized AI agents to deliver actionable trading signals. The system integrates:

- **Price Forecasting**: Multi-horizon predictions (1h, 4h, 1d, 1w) using Prophet and LSTM models
- **Trend Classification**: BUY/SELL/HOLD signals with confidence scores using LightGBM/XGBoost
- **Support/Resistance Detection**: Key price levels with strength scoring using DBSCAN clustering
- **News Sentiment Analysis**: GPT-4 powered sentiment scoring with semantic caching
- **Signal Fusion**: Rule-based combination of all signals into unified trading recommendations
- **Backtesting**: Historical performance simulation with comprehensive metrics

## Architecture

The system consists of 10 specialized agents working in coordination:

```
Data Agent → Feature Agent
    ↓
    ├─→ Price Forecast Agent
    ├─→ Trend Classification Agent
    └─→ Support/Resistance Agent

News Fetch Agent → LLM Sentiment Agent → Sentiment Aggregator

All Agents → Fusion Agent → Backtesting Agent
```

## Project Structure

```
codebase/
├── backend/              # Python-based multi-agent system
│   ├── agents/         # 10 specialized agents
│   ├── api/           # FastAPI REST endpoints
│   ├── core/          # Core interfaces and utilities
│   └── tests/         # Integration tests
├── frontend/           # Next.js/TypeScript dashboard
│   ├── src/
│   │   ├── app/       # Next.js app router
│   │   ├── components/# React components
│   │   └── lib/      # Utilities and API clients
│   └── public/        # Static assets
└── docs/              # Project documentation
    ├── SoW_Multi_Agent_Stock_Prediction_System_v2.pdf
    ├── COMPONENT_DEPENDENCIES.md
    └── AGENTS_SUMMARY.md
```

## Key Features

- 🤖 **10 Specialized AI Agents**: Each agent handles a specific aspect of market analysis
- 📊 **Multi-Horizon Predictions**: Forecast prices for 1h, 4h, 1d, and 1w timeframes
- 📈 **Technical Analysis**: 20+ technical indicators and engineered features
- 🗞️ **News Sentiment**: GPT-4 powered sentiment analysis with 60%+ cache hit rate
- 🎯 **Unified Signals**: Fusion agent combines all predictions into actionable signals
- 📉 **Backtesting**: Historical performance validation with PnL, Sharpe ratio, and drawdown metrics
- 🚀 **Real-time Updates**: WebSocket support for live market data and predictions
- 📱 **Modern Dashboard**: Next.js frontend with interactive charts and visualizations

## Team Structure

- **Lead Developer**: Data Agent, Feature Agent, Fusion Agent, Backtesting Agent, Orchestrator, Frontend
- **Developer 1**: News Fetch Agent, LLM Sentiment Agent, Sentiment Aggregator
- **Developer 2**: Price Forecast Agent, Trend Classification Agent, Support/Resistance Agent

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- npm or yarn
- PostgreSQL with TimescaleDB (for data storage)
- Redis (for caching)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd codebase
   ```

2. **Set up Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Set up Frontend**
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Run the application**
   ```bash
   # Backend (from backend directory)
   python -m uvicorn api.main:app --reload
   
   # Frontend (from frontend directory)
   npm run dev
   ```

## Development Workflow

1. **Branch Strategy**: Each developer works on their own feature branch
   - `feature/data-agent` - Data ingestion
   - `feature/price-forecast-agent` - Price predictions
   - `feature/news-fetch-agent` - News collection
   - `main` - Production-ready code (protected)

2. **Code Review**: All changes must be reviewed before merging to `main`

3. **Dependencies**: See [TEAM.md](./TEAM.md) for component dependencies and interfaces

## Documentation

- 📖 [Team Collaboration Guide](./TEAM.md) - Team roles, responsibilities, and workflows
- 🌿 [Branching Strategy](./BRANCHING.md) - Git workflow and branch management
- 🔗 [Component Dependencies](./docs/COMPONENT_DEPENDENCIES.md) - Interface definitions and dependencies
- 🚀 [Getting Started Guide](./docs/GETTING_STARTED.md) - Setup instructions
- 📋 [Agents Summary](./docs/AGENTS_SUMMARY.md) - Complete agent overview
- 📐 [Project Structure](./docs/PROJECT_STRUCTURE.md) - Detailed structure documentation

## Milestones

- **M1**: Foundation & Data Pipeline (Weeks 1-2)
- **M2**: Core Prediction Models (Weeks 3-5)
- **M3**: Sentiment & Fusion (Weeks 6-7)
- **M4**: Backtesting & Integration (Weeks 8-9)
- **M5**: Frontend & Testing (Weeks 10-11)
- **M6**: Documentation & Delivery (Week 12)

## Technology Stack

### Backend
- **Python 3.9+**
- **FastAPI** - REST API framework
- **Prophet** - Time series forecasting (baseline)
- **TensorFlow/Keras** - LSTM models
- **LightGBM/XGBoost** - Trend classification
- **scikit-learn** - DBSCAN clustering
- **OpenAI GPT-4** - Sentiment analysis
- **PostgreSQL + TimescaleDB** - Time-series data storage
- **Redis** - Caching layer

### Frontend
- **Next.js 14+** - React framework
- **TypeScript** - Type safety
- **TradingView Lightweight Charts** - Price visualization
- **Tailwind CSS** - Styling

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on contributing to the project.

## License

[To be determined]

---

**TICK** - Time-Indexed Composite Knowledge for Markets | Built with ❤️ by the TICK Team
