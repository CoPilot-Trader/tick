# Branching Strategy

## Branch Structure

### Main Branches

- **`main`**: Production-ready code. Protected branch. Only merged via Pull Requests after code review.

### Feature Branches

Each developer works on their own feature branch:

- **`feature/news-agent`**: Developer 1 - News Agent development
- **`feature/price-prediction-agent`**: Developer 2 - Price Prediction Agent development
- **`feature/[component-name]`**: Developer 3 - [Component to be assigned]
- **`feature/frontend`**: Lead Developer - Frontend development
- **`feature/orchestrator`**: Lead Developer - Agent orchestration

### Branch Naming Convention

```
feature/[component-name]
hotfix/[issue-description]
bugfix/[issue-description]
```

## Workflow

### Starting Work

1. **Ensure you're on main and up to date**:
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Create your feature branch**:
   ```bash
   git checkout -b feature/your-component-name
   ```

3. **Push branch to remote**:
   ```bash
   git push -u origin feature/your-component-name
   ```

### Daily Workflow

1. **Start of day**:
   ```bash
   git checkout feature/your-component-name
   git pull origin main  # Get latest changes from main
   ```

2. **Make changes and commit**:
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   git push origin feature/your-component-name
   ```

### Creating a Pull Request

1. **Ensure your branch is up to date**:
   ```bash
   git checkout feature/your-component-name
   git pull origin main
   git rebase main  # Optional: rebase for cleaner history
   ```

2. **Push your changes**:
   ```bash
   git push origin feature/your-component-name
   ```

3. **Create PR on GitHub**:
   - Go to GitHub repository
   - Click "New Pull Request"
   - Select `main` as base branch
   - Select your feature branch
   - Fill out PR template
   - Request review from Lead Developer

### PR Requirements

- [ ] Code follows style guidelines
- [ ] Unit tests written and passing
- [ ] Component README updated
- [ ] No merge conflicts
- [ ] All linting errors resolved
- [ ] Interface changes documented

### Merging Process

1. **Lead Developer reviews PR**
2. **Address any feedback**
3. **Lead Developer merges to `main`**
4. **Delete feature branch after merge** (optional)

## Conflict Resolution

If you encounter merge conflicts:

1. **Don't panic** - conflicts are normal
2. **Pull latest main**:
   ```bash
   git checkout main
   git pull origin main
   ```
3. **Rebase your branch**:
   ```bash
   git checkout feature/your-component-name
   git rebase main
   ```
4. **Resolve conflicts** in your editor
5. **Continue rebase**:
   ```bash
   git add .
   git rebase --continue
   ```

## Best Practices

### Commit Messages

Use clear, descriptive commit messages:

```
✅ Good: "Add sentiment analysis module to news agent"
✅ Good: "Fix price prediction model accuracy calculation"
❌ Bad: "fix"
❌ Bad: "updates"
```

### Commit Frequency

- Commit often (at least daily)
- Small, logical commits are better than large ones
- Don't commit broken code

### Branch Hygiene

- Keep branches focused on single features
- Don't let branches get too far behind `main`
- Delete merged branches to keep repository clean

## Emergency Hotfixes

For critical production issues:

1. **Create hotfix branch from main**:
   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-issue-description
   ```

2. **Fix the issue and commit**
3. **Create PR and merge immediately** (after review)
4. **Merge hotfix back to your feature branch** if needed

## Branch Protection Rules

The `main` branch is protected with:
- Require pull request reviews
- Require status checks to pass
- Require branches to be up to date
- No force pushes
- No deletion

## Questions?

Contact Lead Developer for branch strategy questions or issues.

