# Quick Reference Guide

Quick reference for common tasks and information.

## Team Members & Components

| Developer | Component | Branch | Directory |
|-----------|-----------|--------|-----------|
| Lead | Frontend | `feature/frontend` | `frontend/` |
| Lead | Orchestrator | `feature/orchestrator` | `backend/agents/orchestrator/` |
| Developer 1 | News Agent | `feature/news-agent` | `backend/agents/news_agent/` |
| Developer 2 | Price Prediction Agent | `feature/price-prediction-agent` | `backend/agents/price_prediction_agent/` |
| Developer 3 | [TBD] | `feature/[component]` | `backend/agents/[component]/` |

## Common Commands

### Git Workflow
```bash
# Start new feature
git checkout main
git pull origin main
git checkout -b feature/your-component-name

# Daily work
git checkout feature/your-component-name
git pull origin main
# ... make changes ...
git add .
git commit -m "Description"
git push origin feature/your-component-name
```

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest agents/your_agent/tests/
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## File Locations

### Documentation
- Main README: `README.md`
- Team guide: `TEAM.md`
- Branching: `BRANCHING.md`
- Dependencies: `docs/COMPONENT_DEPENDENCIES.md`
- Getting started: `docs/GETTING_STARTED.md`

### Code
- Base agent interface: `backend/core/interfaces/base_agent.py`
- API entry: `backend/api/main.py`
- Frontend entry: `frontend/src/app/page.tsx`

### Configuration
- Backend deps: `backend/requirements.txt`
- Frontend deps: `frontend/package.json`
- Git ignore: `.gitignore`

## Interface Quick Reference

### News Agent Provides
- Sentiment data: `{symbol, sentiment_score, sentiment_label, confidence}`
- News articles: `{articles: [...], symbol, filtered_at}`

### Price Prediction Agent Provides
- Predictions: `{symbol, current_price, predictions: [...], technical_indicators}`

## API Endpoints

### News Agent
- `GET /api/v1/news/sentiment/{symbol}`
- `GET /api/v1/news/articles/{symbol}`
- `POST /api/v1/news/analyze`

### Price Prediction Agent
- `GET /api/v1/predictions/{symbol}`
- `GET /api/v1/predictions/{symbol}/indicators`
- `POST /api/v1/predictions/batch`

## Checklist Before PR

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Component README updated
- [ ] No linting errors
- [ ] Interface matches specification
- [ ] No sensitive data committed
- [ ] PR template filled out

## Contact

- **Lead Developer**: For architecture, reviews, questions
- **Component READMEs**: For component-specific questions
- **Interface Docs**: `docs/COMPONENT_DEPENDENCIES.md`

## Status Indicators

- 🚧 In Development
- ✅ Complete
- ⚠️ Needs Attention
- 📝 Documentation

