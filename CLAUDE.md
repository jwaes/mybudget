# mybudget Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-16

## Active Technologies
- Python 3.11 (backend), TypeScript 5.8 (frontend) + FastAPI (async web framework), SQLAlchemy 2.0 (ORM), Alembic (migrations), Pydantic V2 (validation/serialization); React 19, Vite, React Hook Form (frontend) (001-spending-targets-mvp)
- PostgreSQL 15+ (relational database for financial data integrity, ACID transactions) (001-spending-targets-mvp)
- TypeScript 5.8 (frontend) + React 19, shadcn/ui (New York style), Tailwind CSS v3.x, Radix UI primitives, lucide-react (icons), React Router v7 (002-shadcn-ui-migration)
- N/A (frontend-only migration, no data model changes) (002-shadcn-ui-migration)
- Python 3.11 (backend), TypeScript 5.8 (frontend) + FastAPI, SQLAlchemy (backend); React 19, shadcn/ui, Tailwind CSS (frontend) (004-account-deletion)
- PostgreSQL with CASCADE delete on transactions.account_id (004-account-deletion)

- Python 3.11 + FastAPI (async web framework), SQLAlchemy 2.0 (ORM), Alembic (migrations), Pydantic V2 (validation/serialization) (001-spending-targets-mvp)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11: Follow standard conventions

## Recent Changes
- 004-account-deletion: Added Python 3.11 (backend), TypeScript 5.8 (frontend) + FastAPI, SQLAlchemy (backend); React 19, shadcn/ui, Tailwind CSS (frontend)
- 001-spending-targets-mvp: Added Python 3.11 (backend), TypeScript 5.8 (frontend) + FastAPI (async web framework), SQLAlchemy 2.0 (ORM), Alembic (migrations), Pydantic V2 (validation/serialization); React 19, Vite, React Hook Form (frontend)
- 002-shadcn-ui-migration: Added TypeScript 5.8 (frontend) + React 19, shadcn/ui (New York style), Tailwind CSS v3.x, Radix UI primitives, lucide-react (icons), React Router v7


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
