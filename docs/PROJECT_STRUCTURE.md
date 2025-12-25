# Project Structure Overview

This document provides a comprehensive overview of the project structure.

## Root Structure

```
codebase/
├── backend/              # Python backend
├── frontend/             # Next.js/TypeScript frontend
├── docs/                 # Project documentation
├── .github/              # GitHub templates and workflows
├── .gitignore           # Git ignore rules
├── README.md            # Main project README
├── TEAM.md              # Team collaboration guide
├── BRANCHING.md         # Git branching strategy
├── CONTRIBUTING.md      # Contribution guidelines
└── docs/
    ├── COMPONENT_DEPENDENCIES.md  # Interface definitions
    └── PROJECT_STRUCTURE.md       # This file
```

## Backend Structure

```
backend/
├── api/                  # API endpoints (Lead Developer)
│   ├── main.py          # FastAPI application
│   └── routers/         # API route modules
├── core/                # Core system components
│   └── interfaces/      # Base interfaces
│       └── base_agent.py
├── agents/              # Agent modules
│   ├── news_agent/      # Developer 1
│   │   ├── agent.py
│   │   ├── interfaces.py
│   │   ├── collectors/
│   │   ├── analyzers/
│   │   ├── filters/
│   │   └── tests/
│   ├── price_prediction_agent/  # Developer 2
│   │   ├── agent.py
│   │   ├── interfaces.py
│   │   ├── data/
│   │   ├── models/
│   │   ├── indicators/
│   │   └── tests/
│   └── orchestrator/    # Lead Developer
├── data/                 # Data sources
├── models/              # Shared ML models
├── utils/               # Shared utilities
├── tests/               # Integration tests
├── requirements.txt     # Python dependencies
└── README.md
```

## Frontend Structure

```
frontend/
├── src/
│   ├── app/             # Next.js app directory
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/      # React components
│   │   ├── common/
│   │   ├── news/
│   │   └── predictions/
│   ├── lib/             # Utilities
│   │   └── api/         # API client
│   ├── types/           # TypeScript types
│   └── hooks/           # Custom hooks
├── public/              # Static assets
├── package.json
├── tsconfig.json
├── next.config.js
└── README.md
```

## Developer Assignments

### Lead Developer
- `frontend/` - Full access
- `backend/api/` - API endpoints
- `backend/core/` - Core components
- `backend/agents/orchestrator/` - Agent coordination

### Developer 1 (News Agent)
- `backend/agents/news_agent/` - News agent development

### Developer 2 (Price Prediction Agent)
- `backend/agents/price_prediction_agent/` - Price prediction agent

### Developer 3
- [To be assigned]

## Key Files

### Documentation
- `README.md` - Project overview
- `TEAM.md` - Team structure and workflows
- `BRANCHING.md` - Git workflow
- `CONTRIBUTING.md` - Contribution guidelines
- `docs/COMPONENT_DEPENDENCIES.md` - Interface specifications

### Configuration
- `.gitignore` - Git ignore rules
- `backend/requirements.txt` - Python dependencies
- `frontend/package.json` - Node.js dependencies
- `backend/.env.example` - Backend environment template
- `frontend/.env.example` - Frontend environment template

### Code
- `backend/core/interfaces/base_agent.py` - Base agent interface
- `backend/api/main.py` - FastAPI application entry point
- `frontend/src/app/page.tsx` - Frontend entry point

## Branch Structure

- `main` - Production-ready code
- `feature/news-agent` - Developer 1
- `feature/price-prediction-agent` - Developer 2
- `feature/frontend` - Lead Developer
- `feature/orchestrator` - Lead Developer

## Questions?

Refer to individual component READMEs or contact Lead Developer.

