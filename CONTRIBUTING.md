# Contributing Guide

## Getting Started

1. **Read the documentation**:
   - [README.md](./README.md) - Project overview
   - [TEAM.md](./TEAM.md) - Team structure and responsibilities
   - [BRANCHING.md](./BRANCHING.md) - Git workflow
   - [Component Dependencies](./docs/COMPONENT_DEPENDENCIES.md) - Interface definitions

2. **Set up your development environment**:
   - Follow setup instructions in component-specific READMEs
   - Ensure you have the required tools installed

3. **Create your feature branch**:
   ```bash
   git checkout -b feature/your-component-name
   ```

## Development Workflow

### Before You Start

- [ ] Read your component's README
- [ ] Understand the interface requirements
- [ ] Check dependencies with other components
- [ ] Set up your development environment

### During Development

- [ ] Work only in your assigned directory
- [ ] Follow code style guidelines
- [ ] Write unit tests as you develop
- [ ] Update your component's README with progress
- [ ] Commit frequently with clear messages

### Before Submitting

- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] No linting errors
- [ ] Component README is updated
- [ ] Interface matches specification
- [ ] No sensitive data committed

## Code Style

### Python (Backend)

- Follow PEP 8
- Use type hints
- Write docstrings
- Maximum line length: 100 characters
- Use `black` for formatting

### TypeScript (Frontend)

- Use TypeScript strict mode
- Follow React best practices
- Use functional components
- Write JSDoc comments for complex functions

## Testing

- Write unit tests for all new functionality
- Aim for >80% code coverage
- Test edge cases and error conditions
- Use mock data for external dependencies

## Pull Request Process

1. **Create PR** from your feature branch to `main`
2. **Fill out PR template**:
   - Description of changes
   - Related issues
   - Testing done
   - Checklist items
3. **Request review** from Lead Developer
4. **Address feedback** promptly
5. **Wait for approval** before merging

## Communication

- Use clear commit messages
- Document interface changes early
- Communicate blockers immediately
- Ask questions if unclear

## Questions?

Contact Lead Developer for:
- Architecture decisions
- Interface clarifications
- Code review requests
- Any blockers or questions

