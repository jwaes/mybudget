# MyBudget MVP

A bank-sync budgeting application with intelligent spending targets. Built with Python FastAPI backend and React TypeScript frontend.

## Features

- **Spending Targets**: Three target types to fit your budgeting style
  - Monthly Needed: Fund €X each month
  - Target Balance: Maintain €X available always
  - Target by Date: Reach €X by specific date
- **Bank Account Management**: Track multiple accounts with reconciliation
- **Transaction Organization**: Categorize and approve transactions
- **Funding Guidance**: Automatic underfunded target calculations

## Quick Start

See [specs/001-spending-targets-mvp/quickstart.md](specs/001-spending-targets-mvp/quickstart.md) for detailed setup instructions.

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Node.js 20+
- Git

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd mybudget

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your settings

# Create database
createdb mybudget
alembic upgrade head

# Start backend
uvicorn mybudget.main:app --reload

# Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

Visit:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Docker Development

```bash
docker compose up -d
```

## Testing

```bash
# Backend tests
cd backend
pytest                    # All tests
pytest tests/unit -v      # Unit tests only
pytest --cov=mybudget     # With coverage

# Frontend tests
cd frontend
npm run test              # Unit tests
npm run test:coverage     # With coverage
npm run test:e2e          # E2E tests
```

## Project Structure

```
mybudget/
├── backend/              # Python FastAPI backend
│   ├── src/mybudget/     # Source code
│   ├── tests/            # Test code
│   └── migrations/       # Database migrations
├── frontend/             # React TypeScript frontend
│   ├── src/              # Source code
│   └── tests/            # Test code
└── specs/                # Feature specifications
```

## Documentation

- [Feature Specification](specs/001-spending-targets-mvp/spec.md)
- [Data Model](specs/001-spending-targets-mvp/data-model.md)
- [API Contracts](specs/001-spending-targets-mvp/contracts/)
- [Quickstart Guide](specs/001-spending-targets-mvp/quickstart.md)
- [Project Constitution](.specify/memory/constitution.md)

## Tech Stack

**Backend:**
- Python 3.11, FastAPI, SQLAlchemy 2.0, PostgreSQL 15+
- Alembic, Pydantic V2, pytest

**Frontend:**
- React 19, TypeScript 5.8, Vite
- React Hook Form, Vitest, Playwright

## Development Principles

This project follows strict Test-Driven Development (TDD):
- Write tests before implementation
- 100% test coverage goal
- Type safety with mypy strict mode

See [constitution](.specify/memory/constitution.md) for complete development principles.

## License

MIT
