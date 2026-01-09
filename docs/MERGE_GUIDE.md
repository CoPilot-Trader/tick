# Branch Merge Guide for TICK Project

## Current Branch Overview

| Branch | Owner | Description | Status |
|--------|-------|-------------|--------|
| `main` | - | Base branch with initial setup | Production-ready base |
| `frontend` | You | Frontend rapid prototype | Ready to merge |
| `feature/news-agent` | Salim | News & Sentiment Agents | Ready to merge |

---

## 🚀 Quick Merge Steps (For Tomorrow's Demo)

### Step 1: Make sure everything is committed and pushed

```bash
# Check status on each branch
git checkout frontend
git status
git push origin frontend

git checkout feature/news-agent
git status
git push origin feature/news-agent
```

### Step 2: Update main with frontend work first

```bash
# Switch to main
git checkout main

# Merge frontend into main
git merge frontend -m "Merge frontend: rapid prototype v1"

# Push to remote
git push origin main
```

### Step 3: Then merge the news-agent into main

```bash
# Still on main, merge news-agent
git merge feature/news-agent -m "Merge feature/news-agent: News & Sentiment Agents implementation"

# Push the combined main
git push origin main
```

### Step 4: Handle any merge conflicts (if they occur)

If you see conflict messages:

```bash
# See which files have conflicts
git status

# Open conflicted files - look for these markers:
# <<<<<<< HEAD
# (your code)
# =======
# (incoming code)
# >>>>>>> feature/news-agent

# Edit the files to keep what you want, then:
git add <resolved-file>
git commit -m "Resolve merge conflicts"
```

---

## 📋 Detailed Workflow for Multiple Developers

### A. Before Starting Any Merge

```bash
# 1. Fetch latest from remote
git fetch origin

# 2. Check all branches
git branch -a

# 3. See what's different between branches
git log main..origin/frontend --oneline    # Commits in frontend not in main
git log main..feature/news-agent --oneline # Commits in news-agent not in main
```

### B. Creating a Clean Integration Branch (Safer Approach)

If you want to test the merge before touching `main`:

```bash
# Create a new integration branch from main
git checkout main
git checkout -b integration/demo-v1

# Merge frontend
git merge frontend -m "Integrate frontend prototype"

# Merge news-agent
git merge feature/news-agent -m "Integrate news & sentiment agents"

# Test everything works...

# If happy, fast-forward main to integration
git checkout main
git merge integration/demo-v1
git push origin main
```

### C. Post-Merge: Update Your Working Branch

After merging to main, update your working branch with main changes:

```bash
git checkout frontend
git merge main -m "Sync with main after integration"
git push origin frontend
```

---

## 🔧 Common Scenarios

### Scenario 1: "I want to see what Salim changed"

```bash
# View commits
git log feature/news-agent --oneline -10

# View file changes
git diff main..feature/news-agent --stat

# View specific file changes
git diff main..feature/news-agent -- backend/agents/news_agent/
```

### Scenario 2: "I want to test news-agent on my frontend branch first"

```bash
git checkout frontend
git merge feature/news-agent -m "Test: integrate news-agent with frontend"
# Test locally, then push if happy
```

### Scenario 3: "The merge broke something, I need to undo"

```bash
# If you haven't pushed yet:
git reset --hard HEAD~1

# If you already pushed (creates a new commit that undoes):
git revert -m 1 HEAD
git push origin main
```

### Scenario 4: "I want to pick only specific commits"

```bash
# Cherry-pick specific commits
git checkout main
git cherry-pick <commit-hash>
```

---

## 📁 Expected File Structure After Merge

After merging both branches, `main` should have:

```
tick/
├── frontend/           # From 'frontend' branch
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   └── lib/
│   └── ...
├── backend/
│   ├── agents/
│   │   ├── news_agent/        # From 'feature/news-agent'
│   │   ├── news_fetch_agent/  # From 'feature/news-agent'
│   │   ├── llm_sentiment_agent/
│   │   └── ...
│   └── api/
└── tools/
    └── developer1-news-visualizer/  # From 'feature/news-agent'
```

---

## ✅ Pre-Demo Checklist

- [ ] All branches pushed to remote
- [ ] Frontend builds without errors: `cd frontend && npm run build`
- [ ] Backend runs without errors: `cd backend && python -m uvicorn api.main:app`
- [ ] News visualizer tool works: `cd tools/developer1-news-visualizer && python -m http.server 8080`
- [ ] Main branch has all merged content
- [ ] Demo walkthrough practiced

---

## 🆘 Emergency Commands

```bash
# Abort a merge in progress
git merge --abort

# See current state
git status

# View recent commits on current branch
git log --oneline -10

# Check which branch you're on
git branch

# Stash uncommitted changes temporarily
git stash
git stash pop  # To restore
```

---

## Team Branch Naming Convention

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/<name>` | `feature/news-agent` |
| Bugfix | `bugfix/<name>` | `bugfix/api-timeout` |
| Hotfix | `hotfix/<name>` | `hotfix/critical-error` |
| Integration | `integration/<version>` | `integration/demo-v1` |

---

*Last updated: January 10, 2026*

