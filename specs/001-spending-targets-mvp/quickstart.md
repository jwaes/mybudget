# MyBudget MVP - Developer Quickstart Guide

**Feature**: Spending Targets MVP
**Date**: 2026-01-16
**Target Audience**: Developers setting up local environment

## Prerequisites

### Required
- **Python 3.11+**: Check with `python --version`
- **PostgreSQL 15+**: Local instance or Docker
- **Git**: For version control
- **Node.js 20+**: For frontend development

### Optional
- **Docker & Docker Compose**: For containerized development
- **VS Code**: Recommended IDE with Python + TypeScript extensions

---

## Quick Start (5 minutes)

### 1. Clone and Setup Backend

```bash
# Clone repository
git clone <repository-url>
cd mybudget

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -e ".[dev]"  # Installs from pyproject.toml with dev dependencies
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# DATABASE_URL=postgresql://user:password@localhost:5432/mybudget
# SECRET_KEY=<generate-with-openssl-rand-hex-32>
# ENVIRONMENT=development
```

### 3. Setup Database

```bash
# Create PostgreSQL database
createdb mybudget

# Run migrations
alembic upgrade head

# Optional: Load sample data
python scripts/seed_dev_data.py
```

### 4. Run Backend

```bash
# Start FastAPI dev server
uvicorn mybudget.main:app --reload --host 0.0.0.0 --port 8000

# API available at:
# http://localhost:8000/docs  (Swagger UI)
# http://localhost:8000/redoc (ReDoc)
```

### 5. Run Frontend

```bash
# In new terminal
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Frontend available at:
# http://localhost:5173
```

---

## Running Tests

### Backend Tests (Python + pytest)

```bash
cd backend

# Run all tests with coverage
pytest

# Run unit tests only (fast)
pytest tests/unit -v

# Run integration tests
pytest tests/integration -v

# Run with coverage report
pytest --cov=mybudget --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Frontend Tests (TypeScript + Vitest)

```bash
cd frontend

# Run unit tests
npm run test

# Run with coverage
npm run test:coverage

# Run E2E tests (Playwright)
npm run test:e2e
```

### Test-Driven Development Workflow

Per constitution's TDD principle:

```bash
# 1. Write failing test
pytest tests/unit/test_services/test_target_service.py::test_calculate_underfunded_monthly_needed -v

# 2. See it fail (Red)
# 3. Implement minimal code to pass
# 4. Run test again (Green)
# 5. Refactor while keeping tests green
```

---

## Docker Development (Alternative Setup)

```bash
# Start all services
docker compose up -d

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
# PostgreSQL: localhost:5432

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Run tests in container
docker compose exec backend pytest
docker compose exec frontend npm run test

# Stop services
docker compose down
```

---

## Project Structure

```
mybudget/
├── backend/
│   ├── src/mybudget/          # Source code
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── api/               # FastAPI routes
│   │   └── db/                # Database utilities
│   ├── tests/                 # Test code
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── migrations/            # Alembic migrations
│   └── pyproject.toml         # Dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── services/
│   └── tests/
├── specs/                     # Feature specifications
└── docker-compose.yml
```

---

## Common Development Tasks

### Create Database Migration

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add spending targets table"

# Review generated migration
# Edit migrations/versions/<timestamp>_add_spending_targets_table.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### Add New API Endpoint

```bash
# 1. Write test first (TDD)
# tests/contract/test_targets_api.py

def test_create_target_returns_201():
    response = client.post("/api/targets", json={...})
    assert response.status_code == 201

# 2. Run test (fails - Red)
pytest tests/contract/test_targets_api.py::test_create_target_returns_201 -v

# 3. Implement endpoint
# src/mybudget/api/targets.py

@router.post("/targets", status_code=201)
async def create_target(data: CategoryTargetCreate):
    ...

# 4. Run test (passes - Green)
# 5. Refactor
```

### Run Code Quality Checks

```bash
cd backend

# Linting
ruff check .

# Auto-fix linting issues
ruff check . --fix

# Formatting
black .

# Type checking
mypy src/

# All checks (pre-commit hook)
pre-commit run --all-files
```

---

## Configuration

### Environment Variables

Create `.env` file in backend directory:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/mybudget

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>
ALGORITHM=HS256
SESSION_LIFETIME_MINUTES=30

# Environment
ENVIRONMENT=development  # development | production
DEBUG=true

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173
```

### Generate Secret Key

```bash
openssl rand -hex 32
```

---

## API Documentation

### Access Interactive Docs

Once backend is running:

- **Swagger UI**: http://localhost:8000/docs
  - Interactive API explorer
  - Try endpoints directly in browser

- **ReDoc**: http://localhost:8000/redoc
  - Beautiful API documentation
  - Better for reading, worse for testing

### Example API Calls

```bash
# Create account
curl -X POST http://localhost:8000/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "ING Checking", "account_type": "CHECKING", "initial_balance": "1000.00"}'

# Create spending target
curl -X POST http://localhost:8000/api/targets \
  -H "Content-Type: application/json" \
  -d '{"category_id": "<uuid>", "target_type": "MONTHLY_NEEDED", "amount": "400.00"}'

# Calculate underfunded
curl http://localhost:8000/api/targets/<target-uuid>/underfunded?month=2026-01-01
```

---

## Troubleshooting

### Database Connection Errors

```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql -l | grep mybudget

# Recreate database if corrupted
dropdb mybudget
createdb mybudget
alembic upgrade head
```

### Import Errors

```bash
# Reinstall in editable mode
cd backend
pip install -e ".[dev]"

# Verify mybudget package is installed
pip show mybudget
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use different port
uvicorn mybudget.main:app --reload --port 8001
```

### Migration Conflicts

```bash
# Check migration history
alembic history

# Downgrade to specific revision
alembic downgrade <revision>

# Delete conflict migration file
rm migrations/versions/<conflict-file>.py

# Regenerate
alembic revision --autogenerate -m "Fix migration"
```

---

## Next Steps

1. **Read the spec**: `specs/001-spending-targets-mvp/spec.md`
2. **Review data model**: `specs/001-spending-targets-mvp/data-model.md`
3. **Check API contracts**: `specs/001-spending-targets-mvp/contracts/`
4. **Run tests**: Ensure 100% pass before starting development
5. **Start TDD workflow**: Pick a user story from tasks.md (when generated)

---

## Development Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy 2.0 Docs**: https://docs.sqlalchemy.org/en/20/
- **Pydantic V2 Docs**: https://docs.pydantic.dev/latest/
- **React + TypeScript**: https://react.dev
- **Vitest**: https://vitest.dev
- **Playwright**: https://playwright.dev

---

## Team Collaboration

### Pre-commit Hooks

Install pre-commit hooks to enforce quality gates:

```bash
cd backend
pre-commit install

# Now every commit will run:
# - ruff (linting)
# - black (formatting)
# - mypy (type checking)
# - pytest (tests)
```

### Commit Message Format

Follow Conventional Commits:

```bash
feat: add spending targets API endpoint
fix: correct underfunded calculation for TARGET_BY_DATE
test: add unit tests for target service
docs: update quickstart guide
refactor: extract assignment logic to service
```

---

**Questions?** Check the constitution at `.specify/memory/constitution.md` for development principles.
