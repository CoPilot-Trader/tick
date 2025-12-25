# Getting Started Guide

This guide will help you get started with the project.

## For All Team Members

1. **Read the documentation**:
   - [README.md](../README.md) - Project overview
   - [TEAM.md](../TEAM.md) - Your role and responsibilities
   - [BRANCHING.md](../BRANCHING.md) - Git workflow
   - [Component Dependencies](./COMPONENT_DEPENDENCIES.md) - Interface definitions

2. **Set up Git**:
   ```bash
   git clone <repository-url>
   cd codebase
   ```

3. **Create your feature branch**:
   ```bash
   git checkout -b feature/your-component-name
   ```

## For Backend Developers

### Setup

1. **Navigate to backend**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Read your component README**:
   - News Agent: `backend/agents/news_agent/README.md`
   - Price Prediction Agent: `backend/agents/price_prediction_agent/README.md`

### Development

1. **Work in your assigned directory**:
   - News Agent: `backend/agents/news_agent/`
   - Price Prediction Agent: `backend/agents/price_prediction_agent/`

2. **Run tests**:
   ```bash
   pytest agents/your_agent/tests/
   ```

3. **Follow the interface**:
   - Implement `BaseAgent` interface
   - Follow interface specifications in your component README
   - See `docs/COMPONENT_DEPENDENCIES.md` for interface contracts

## For Frontend Developer (Lead)

### Setup

1. **Navigate to frontend**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Run development server**:
   ```bash
   npm run dev
   ```

5. **Open browser**: `http://localhost:3000`

## Daily Workflow

1. **Start of day**:
   ```bash
   git checkout feature/your-component-name
   git pull origin main  # Get latest changes
   ```

2. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   git push origin feature/your-component-name
   ```

3. **Create PR when ready**:
   - Push your changes
   - Create Pull Request on GitHub
   - Request review from Lead Developer

## Important Reminders

- ✅ Work only in your assigned directory
- ✅ Follow code style guidelines
- ✅ Write unit tests
- ✅ Update component README as you progress
- ✅ Communicate interface changes early
- ❌ Don't modify other developers' code
- ❌ Don't push directly to `main`
- ❌ Don't commit sensitive data

## Need Help?

- **Architecture questions**: Contact Lead Developer
- **Interface clarifications**: See `docs/COMPONENT_DEPENDENCIES.md`
- **Git workflow**: See `BRANCHING.md`
- **Component-specific**: See your component's README

## Next Steps

1. Set up your development environment
2. Read your component's README
3. Understand the interface requirements
4. Start implementing Phase 1 tasks from your component README

Good luck! 🚀

