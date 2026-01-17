# Implementation Plan: MyBudget MVP - Spending Targets

**Branch**: `001-spending-targets-mvp` | **Date**: 2026-01-16 (Updated 2026-01-17) | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-spending-targets-mvp/spec.md`

## Summary

Build a bank-sync-first personal budgeting application that helps users manage spending through category-based budgets with intelligent funding guidance. The core feature is "Spending Targets" - a simple yet powerful way for users to set monthly spending intentions and get instant visibility into what needs funding. The MVP supports three target types (Monthly Needed, Target Balance, Target by Date) with one-tap funding actions to meet targets effortlessly.

Technical approach: Python web application with a relational database for transactional data, RESTful API backend, and modern web frontend. Focus on precise financial calculations, data integrity through reconciliation, and fast user workflows (<60 seconds to fully fund a budget).

**Update 2026-01-17**: Added User Story 0 (Authentication UI) - login and registration pages for user authentication before accessing budget features.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.8 (frontend)
**Primary Dependencies**: FastAPI (async web framework), SQLAlchemy 2.0 (ORM), Alembic (migrations), Pydantic V2 (validation/serialization); React 19, Vite, React Hook Form (frontend)
**Storage**: PostgreSQL 15+ (relational database for financial data integrity, ACID transactions)
**Testing**: pytest (test framework), pytest-cov (coverage), pytest-asyncio (async tests), Faker (test data generation); Vitest + React Testing Library (frontend)
**Target Platform**: Web application (browser-based UI + REST API backend)
**Project Type**: Web application (backend API + frontend client)
**Performance Goals**: <2 seconds for all operations (per SC-010 assumption), <200ms API response p95, real-time UI updates for funding actions
**Constraints**:
- Financial precision: all amounts stored as DECIMAL (no floating point)
- Data integrity: reconciliation must catch any balance discrepancies
- Timezone-aware: month boundaries respect user's local timezone
- Single-user MVP: no multi-tenancy complexity
- 30-minute session timeout for security
**Scale/Scope**:
- 1-5 bank accounts per user
- 100-500 transactions/month
- 20-50 budget categories
- Historical data retained indefinitely
- Target: 1,000 users for MVP

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Test-First Development (NON-NEGOTIABLE)

**Status**: ✅ PASS

**Plan**:
- All business logic (target calculations, funding algorithms, reconciliation) will be developed using strict TDD
- Tests written first for each underfunded calculation formula (FR-028)
- Red-Green-Refactor cycle for all services and models
- Contract tests define API behavior before implementation

**Verification**:
- Every model method has corresponding unit test
- Every service function has test coverage showing red→green progression
- Integration tests for user journeys exist before feature implementation

### II. Comprehensive Unit Testing

**Status**: ✅ PASS

**Plan**:
- Target: 100% coverage of business logic (models, services, calculations)
- Unit tests use mocks for database (no real DB in unit tests)
- Fast tests (<10ms each) using in-memory fixtures
- Separate integration tests for database interactions

**Test Organization**:
```
tests/
├── unit/
│   ├── test_models/          # Model business logic (calculations, validation)
│   ├── test_services/        # Service layer (funding algorithms, reconciliation)
│   └── test_lib/             # Utility functions
├── integration/
│   ├── test_api/             # Full HTTP request/response cycles
│   ├── test_database/        # Repository patterns with real DB
│   └── test_user_journeys/   # End-to-end workflows per user story
└── contract/
    └── test_api_contracts/   # OpenAPI schema validation
```

### III. Type Safety

**Status**: ✅ PASS

**Plan**:
- All functions have full type annotations
- Pydantic models for API request/response validation
- SQLAlchemy models with typed columns
- `mypy --strict` in CI/CD pipeline
- decimal.Decimal for all financial amounts (not float)

**Example**:
```python
from decimal import Decimal
from datetime import date

def calculate_underfunded(
    target_type: TargetType,
    target_amount: Decimal,
    funded_this_month: Decimal,
    available_now: Decimal,
    target_date: date | None,
    current_month: date,
) -> Decimal:
    ...
```

### IV. Code Quality Standards

**Status**: ✅ PASS

**Tooling**:
- `ruff` for linting (configured in pyproject.toml)
- `black` for formatting (line length: 100)
- `mypy --strict` for type checking
- `pytest` with pytest-cov for coverage reporting
- Pre-commit hooks enforce all checks locally

**CI/CD Gates**:
- All quality checks in GitHub Actions / GitLab CI
- Coverage threshold: 90% minimum (aiming for 100%)
- No warnings allowed in ruff or mypy
- All tests must pass

### V. Simplicity First (YAGNI)

**Status**: ✅ PASS

**MVP Constraints**:
- No multi-user features (single user only)
- No multi-currency (EUR only per assumption)
- No mobile apps (web only)
- No advanced reporting (basic month view only)
- No custom target priorities (fixed priority order)
- No async job queues (synchronous bank sync for MVP)

**Avoiding Premature Abstraction**:
- Direct SQLAlchemy queries (no repository pattern unless justified)
- Simple FastAPI routes (no complex middleware)
- Inline calculations (no calculation engine abstraction)
- Standard REST patterns (no GraphQL, no custom protocols)

### Constitution Compliance Summary

**PASS** ✅ - All 5 core principles are addressed in the technical approach. No violations identified. Ready to proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/001-spending-targets-mvp/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (completed)
├── research.md          # Phase 0 output (technology decisions) ✅
├── data-model.md        # Phase 1 output (entity designs) ✅
├── quickstart.md        # Phase 1 output (dev setup guide) ✅
├── contracts/           # Phase 1 output (OpenAPI schemas)
│   ├── auth.yaml        # Authentication endpoints (NEW)
│   ├── targets.yaml     # Spending targets ✅
│   └── README.md        # Contract documentation ✅
├── checklists/
│   └── requirements.md  # Spec quality checklist (completed) ✅
└── tasks.md             # Phase 2 output (/speckit.tasks command) - TO BE REGENERATED
```

### Source Code (repository root)

```text
# Web application structure (backend + frontend)

backend/
├── src/mybudget/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings (env vars, DB config)
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── user.py              # User model ✅
│   │   ├── account.py           # Account model ✅
│   │   ├── transaction.py       # Transaction model ✅
│   │   ├── category.py          # Category, CategoryGroup models ✅
│   │   ├── categorization_rule.py # CategorizationRule model ✅
│   │   └── [pending: target, assignment, reconciliation]
│   ├── schemas/                 # Pydantic schemas (API contracts)
│   │   ├── __init__.py
│   │   ├── user.py              # User schemas ✅
│   │   ├── account.py           # Account schemas ✅
│   │   ├── transaction.py       # Transaction schemas ✅
│   │   ├── category.py          # Category schemas ✅
│   │   └── [pending: target, reconciliation]
│   ├── services/                # Business logic layer
│   │   ├── __init__.py
│   │   ├── account_service.py   # ✅
│   │   ├── transaction_service.py # ✅
│   │   ├── category_service.py  # ✅
│   │   └── [pending: target, funding, reconciliation]
│   ├── api/                     # FastAPI routes
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication endpoints ✅
│   │   ├── accounts.py          # Account endpoints ✅
│   │   ├── transactions.py      # Transaction endpoints ✅
│   │   ├── categories.py        # Category endpoints ✅
│   │   └── [pending: targets, budget, reconciliation]
│   ├── lib/                     # Shared utilities
│   │   ├── __init__.py
│   │   ├── auth.py              # Password hashing ✅
│   │   ├── session.py           # Session management ✅
│   │   ├── date_utils.py        # Month boundaries, timezone ✅
│   │   └── exceptions.py        # Custom exceptions ✅
│   └── db/                      # Database utilities
│       ├── __init__.py
│       ├── session.py           # DB session management ✅
│       └── base.py              # SQLAlchemy Base ✅
├── migrations/                  # Alembic migrations ✅
└── tests/
    ├── unit/                    # Unit tests ✅
    ├── integration/             # Integration tests ✅
    └── contract/                # API contract tests ✅

frontend/
├── src/
│   ├── components/
│   │   ├── AccountList.tsx      # ✅
│   │   ├── TransactionInbox.tsx # ✅
│   │   ├── CSVImport.tsx        # ✅
│   │   └── [pending: BudgetMonthView, CategoryRow, TargetModal, ReconcileModal]
│   ├── services/
│   │   ├── api.ts               # API client ✅
│   │   ├── authService.ts       # ✅
│   │   ├── accountService.ts    # ✅
│   │   ├── transactionService.ts # ✅
│   │   ├── categoryService.ts   # ✅
│   │   └── [pending: targetService, budgetService]
│   ├── pages/
│   │   ├── Login.tsx            # PENDING (User Story 0)
│   │   ├── Register.tsx         # PENDING (User Story 0)
│   │   ├── Accounts.tsx         # ✅
│   │   ├── Transactions.tsx     # ✅
│   │   └── [pending: Dashboard, Budget]
│   ├── types/
│   │   ├── auth.ts              # ✅
│   │   ├── account.ts           # ✅
│   │   ├── transaction.ts       # ✅
│   │   ├── category.ts          # ✅
│   │   └── [pending: target, budget]
│   └── lib/
│       └── auth-context.tsx     # ✅
└── tests/
    ├── components/              # Component tests ✅
    └── services/                # Service tests ✅
```

**Structure Decision**: Web application with backend/frontend separation. Backend is a Python FastAPI REST API with PostgreSQL storage. Frontend is React 19 with TypeScript. This structure supports the constitution's testing requirements (unit tests for backend logic, contract tests for API, integration tests for full workflows, E2E tests for UI).

## Implementation Status

### Completed

**Phase 2 (Foundation)** - ✅ Complete:
- User model, authentication endpoints (POST /register, POST /login, POST /logout, GET /me)
- Password hashing (Argon2id via pwdlib)
- Session management (itsdangerous signed cookies)
- Frontend auth service and context
- 91 backend tests, 10 frontend tests

**Phase 3 (User Story 1)** - ✅ Complete:
- Account, Transaction, Category, CategoryGroup, CategorizationRule models
- All API endpoints for accounts, transactions, categories
- Frontend services and components (AccountList, TransactionInbox, CSVImport)
- Frontend pages (Accounts, Transactions)
- 164 backend tests, 30 frontend tests passing (194 total)

### Pending

**User Story 0 - Authentication UI** (NEW - Added 2026-01-17):
- Login page with email/password form (FR-AUTH-001)
- Registration page with email/password/timezone form (FR-AUTH-002)
- Error handling for invalid credentials (FR-AUTH-004)
- Redirect logic after successful login (FR-AUTH-005)
- Logout functionality (FR-AUTH-006)

**User Stories 2-6** - Pending:
- Budget month view (User Story 2)
- Reconciliation workflow (User Story 3)
- Spending targets (User Story 4)
- Funding guidance (User Story 5)
- Month rollover (User Story 6)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations identified. All complexity is justified by functional requirements and aligns with constitution principles.*

## Phase 0: Research & Technology Decisions

**Status**: ✅ Complete

Research findings documented in [research.md](./research.md):

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Frontend Framework | React 19 + TypeScript | Best-in-class form handling, enterprise component ecosystem |
| Bank Sync | CSV Import for MVP | API costs prohibitive, validate core value first |
| Authentication | Session-based with HTTP-only cookies | XSS protection, simplicity for single-user MVP |
| Password Hashing | Argon2id (pwdlib) | OWASP 2026 standard |
| Decimal Precision | Python decimal.Decimal | Standard library, financial precision |
| Database Migrations | Alembic | Standard for SQLAlchemy |
| API Documentation | FastAPI OpenAPI/Swagger | Auto-generated, interactive docs |

## Phase 1: Design Artifacts

**Status**: ✅ Complete

### Data Model (data-model.md)

Documented entities with full schema details:

1. **User** - email, password_hash, timezone ✅
2. **Account** (FR-001, FR-002, FR-003) - name, type, balance ✅
3. **Transaction** (FR-005, FR-006, FR-007, FR-010) - date, payee, amount, state ✅
4. **CategoryGroup** (FR-011) - name, display_order ✅
5. **Category** (FR-012, FR-013, FR-014, FR-015) - name, group ✅
6. **CategorizationRule** (FR-008, FR-009) - payee_pattern, category ✅
7. **CategoryTarget** (FR-026, FR-027, FR-028) - Pending
8. **Assignment** (FR-037 - audit trail) - Pending
9. **Reconciliation** (FR-021, FR-025) - Pending

### API Contracts (contracts/)

- **auth.yaml**: Authentication endpoints (NEW - to be added)
- **targets.yaml**: Target CRUD, underfunded calculations ✅
- **README.md**: Contract documentation ✅

### Quickstart Guide (quickstart.md)

✅ Complete - includes dev environment setup, testing commands, Docker configuration.

---

**Status**: Plan updated 2026-01-17. Ready for `/speckit.tasks` to generate tasks for User Story 0 (Authentication UI).
