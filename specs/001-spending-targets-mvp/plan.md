# Implementation Plan: MyBudget MVP - Spending Targets

**Branch**: `001-spending-targets-mvp` | **Date**: 2026-01-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-spending-targets-mvp/spec.md`

## Summary

Build a bank-sync-first personal budgeting application that helps users manage spending through category-based budgets with intelligent funding guidance. The core feature is "Spending Targets" - a simple yet powerful way for users to set monthly spending intentions and get instant visibility into what needs funding. The MVP supports three target types (Monthly Needed, Target Balance, Target by Date) with one-tap funding actions to meet targets effortlessly.

Technical approach: Python web application with a relational database for transactional data, RESTful API backend, and modern web frontend. Focus on precise financial calculations, data integrity through reconciliation, and fast user workflows (<60 seconds to fully fund a budget).

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI (async web framework), SQLAlchemy 2.0 (ORM), Alembic (migrations), Pydantic V2 (validation/serialization)
**Storage**: PostgreSQL 15+ (relational database for financial data integrity, ACID transactions)
**Testing**: pytest (test framework), pytest-cov (coverage), pytest-asyncio (async tests), Faker (test data generation)
**Target Platform**: Web application (browser-based UI + REST API backend)
**Project Type**: Web application (backend API + frontend client)
**Performance Goals**: <2 seconds for all operations (per SC-010 assumption), <200ms API response p95, real-time UI updates for funding actions
**Constraints**:
- Financial precision: all amounts stored as DECIMAL (no floating point)
- Data integrity: reconciliation must catch any balance discrepancies
- Timezone-aware: month boundaries respect user's local timezone
- Single-user MVP: no multi-tenancy complexity
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
├── research.md          # Phase 0 output (technology decisions)
├── data-model.md        # Phase 1 output (entity designs)
├── quickstart.md        # Phase 1 output (dev setup guide)
├── contracts/           # Phase 1 output (OpenAPI schemas)
│   ├── accounts.yaml
│   ├── transactions.yaml
│   ├── categories.yaml
│   ├── targets.yaml
│   └── reconciliation.yaml
├── checklists/
│   └── requirements.md  # Spec quality checklist (completed)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
# Web application structure (backend + frontend)

backend/
├── src/
│   ├── mybudget/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Settings (env vars, DB config)
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── account.py           # Account model
│   │   │   ├── transaction.py       # Transaction model
│   │   │   ├── category.py          # Category, CategoryGroup models
│   │   │   ├── target.py            # CategoryTarget model
│   │   │   ├── assignment.py        # Assignment model (audit trail)
│   │   │   ├── rule.py              # CategorizationRule model
│   │   │   └── reconciliation.py    # Reconciliation model
│   │   ├── schemas/                 # Pydantic schemas (API contracts)
│   │   │   ├── __init__.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── category.py
│   │   │   ├── target.py
│   │   │   └── reconciliation.py
│   │   ├── services/                # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── account_service.py
│   │   │   ├── transaction_service.py
│   │   │   ├── category_service.py
│   │   │   ├── target_service.py    # Underfunded calculations
│   │   │   ├── funding_service.py   # Fund underfunded logic
│   │   │   ├── reconciliation_service.py
│   │   │   └── sync_service.py      # Bank sync integration
│   │   ├── api/                     # FastAPI routes
│   │   │   ├── __init__.py
│   │   │   ├── accounts.py
│   │   │   ├── transactions.py
│   │   │   ├── categories.py
│   │   │   ├── targets.py
│   │   │   ├── budget.py            # Month view endpoint
│   │   │   └── reconciliation.py
│   │   ├── lib/                     # Shared utilities
│   │   │   ├── __init__.py
│   │   │   ├── date_utils.py        # Month boundaries, timezone
│   │   │   ├── decimal_utils.py     # Financial precision helpers
│   │   │   └── exceptions.py        # Custom exceptions
│   │   └── db/                      # Database utilities
│   │       ├── __init__.py
│   │       ├── session.py           # DB session management
│   │       └── base.py              # SQLAlchemy Base
│   └── migrations/                  # Alembic migrations
│       ├── alembic.ini
│       ├── env.py
│       └── versions/
└── tests/
    ├── unit/
    │   ├── test_models/
    │   │   ├── test_account.py
    │   │   ├── test_transaction.py
    │   │   ├── test_category.py
    │   │   └── test_target.py       # Test underfunded calculations
    │   ├── test_services/
    │   │   ├── test_target_service.py
    │   │   ├── test_funding_service.py
    │   │   └── test_reconciliation_service.py
    │   └── test_lib/
    │       └── test_date_utils.py
    ├── integration/
    │   ├── test_api/
    │   │   ├── test_accounts_api.py
    │   │   ├── test_transactions_api.py
    │   │   ├── test_categories_api.py
    │   │   ├── test_targets_api.py
    │   │   └── test_budget_api.py
    │   ├── test_database/
    │   │   └── test_repositories.py
    │   └── test_user_journeys/
    │       ├── test_setup_and_sync.py      # User Story 1
    │       ├── test_organize_budget.py     # User Story 2
    │       ├── test_reconciliation.py      # User Story 3
    │       ├── test_set_targets.py         # User Story 4
    │       ├── test_funding_guidance.py    # User Story 5
    │       └── test_month_rollover.py      # User Story 6
    └── contract/
        └── test_api_contracts.py

frontend/
├── src/
│   ├── components/
│   │   ├── AccountList.tsx          # Account overview
│   │   ├── TransactionInbox.tsx     # Approve/categorize transactions
│   │   ├── BudgetMonthView.tsx      # Main budget screen
│   │   ├── CategoryRow.tsx          # Category with targets/underfunded
│   │   ├── TargetModal.tsx          # Set/edit targets
│   │   └── ReconcileModal.tsx       # Reconciliation workflow
│   ├── services/
│   │   ├── api.ts                   # API client
│   │   ├── accountService.ts
│   │   ├── transactionService.ts
│   │   ├── categoryService.ts
│   │   ├── targetService.ts
│   │   └── budgetService.ts
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Accounts.tsx
│   │   ├── Transactions.tsx
│   │   └── Budget.tsx               # Budget month view
│   └── lib/
│       ├── formatters.ts            # Currency, date formatting
│       └── calculations.ts          # Client-side calculations
└── tests/
    ├── components/
    ├── services/
    └── e2e/                         # End-to-end tests (Playwright/Cypress)

pyproject.toml                       # Python dependencies & tool config
docker-compose.yml                   # Local dev environment (Postgres, etc.)
.env.example                         # Environment variables template
.gitignore
README.md
```

**Structure Decision**: Web application with backend/frontend separation. Backend is a Python FastAPI REST API with PostgreSQL storage. Frontend is a modern web client (React/Vue/Svelte TBD in Phase 0 research). This structure supports the constitution's testing requirements (unit tests for backend logic, contract tests for API, integration tests for full workflows, E2E tests for UI).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*No violations identified. All complexity is justified by functional requirements and aligns with constitution principles.*

## Phase 0: Research & Technology Decisions

### Research Topics

1. **Frontend Framework Selection**
   - Decision: NEEDS CLARIFICATION
   - Options: React, Vue 3, Svelte
   - Criteria: TypeScript support, form handling, testing ecosystem, bundle size
   - Outcome: Will research and document in research.md

2. **Bank Sync Integration**
   - Decision: NEEDS CLARIFICATION
   - Options: Plaid, TrueLayer (Open Banking), mock/manual for MVP
   - Criteria: Cost, compliance, ease of integration, European bank support
   - Outcome: Will research and document in research.md

3. **Authentication Strategy**
   - Decision: NEEDS CLARIFICATION
   - Options: Session-based (cookies), JWT, OAuth2
   - Criteria: Security, simplicity, single-user MVP constraints
   - Outcome: Will research and document in research.md

4. **Decimal Precision Library**
   - Decision: Python's built-in `decimal.Decimal`
   - Rationale: Standard library, precise financial calculations, no external dependency
   - Alternatives: None needed (standard choice for financial apps)

5. **Database Migration Strategy**
   - Decision: Alembic
   - Rationale: Standard for SQLAlchemy, version-controlled schema changes
   - Alternatives: None (de facto standard)

6. **API Documentation**
   - Decision: FastAPI's built-in OpenAPI/Swagger
   - Rationale: Auto-generated from code, interactive docs, aligns with contract testing
   - Alternatives: None needed (FastAPI includes this)

### Research Outputs

Research findings will be documented in `research.md` with the following structure:

```markdown
# Technology Research: MyBudget MVP

## Frontend Framework
- **Decision**: [React/Vue/Svelte]
- **Rationale**: [why chosen]
- **Alternatives Considered**: [what else was evaluated]
- **Trade-offs**: [what we're gaining/losing]

## Bank Sync Integration
- **Decision**: [Plaid/TrueLayer/Mock]
- **Rationale**: [why chosen]
- **Alternatives Considered**: [what else was evaluated]
- **MVP Approach**: [mock vs real integration]

## Authentication
- **Decision**: [Session/JWT]
- **Rationale**: [why chosen]
- **Alternatives Considered**: [what else was evaluated]
- **Security Considerations**: [HTTPS, CSRF, etc.]
```

## Phase 1: Design Artifacts

### Data Model (data-model.md)

Will document the following entities with full schema details:

1. **Account** (FR-001, FR-002, FR-003)
2. **Transaction** (FR-005, FR-006, FR-007, FR-010)
3. **CategoryGroup** (FR-011)
4. **Category** (FR-012, FR-013, FR-014, FR-015)
5. **CategoryTarget** (FR-026, FR-027, FR-028)
6. **Assignment** (FR-037 - audit trail)
7. **CategorizationRule** (FR-008, FR-009)
8. **Reconciliation** (FR-021, FR-025)

Each entity will include:
- Field definitions with types (PostgreSQL types + Python types)
- Constraints (NOT NULL, UNIQUE, CHECK constraints)
- Indexes for query performance
- Relationships (foreign keys)
- Validation rules from spec
- State transitions where applicable

### API Contracts (contracts/)

Will generate OpenAPI 3.0 schemas for:

1. **accounts.yaml**: Account CRUD, balance queries
2. **transactions.yaml**: Transaction inbox, approval, categorization, rules
3. **categories.yaml**: Category/group CRUD, assignments
4. **targets.yaml**: Target CRUD, underfunded calculations
5. **budget.yaml**: Month view, funding actions (Fund Underfunded, Fund All)
6. **reconciliation.yaml**: Reconciliation workflow

Each contract will include:
- Endpoint paths and HTTP methods
- Request/response schemas
- Validation rules
- Error responses
- Example payloads

### Quickstart Guide (quickstart.md)

Will provide:
- Prerequisites (Python 3.11, PostgreSQL, Docker optional)
- Environment setup (virtualenv, dependencies)
- Database setup (create DB, run migrations)
- Running tests (pytest commands)
- Running dev server (uvicorn)
- Running frontend dev server
- API documentation URL (FastAPI /docs)
- Sample data loading (optional fixtures)

### Agent Context Update

After completing Phase 1 artifacts, will run:
```bash
.specify/scripts/bash/update-agent-context.sh claude
```

This will update the Claude-specific context file with:
- Technology stack decisions (FastAPI, PostgreSQL, frontend framework)
- Project structure overview
- Key architectural patterns
- Testing approach

## Next Steps

1. **Phase 0**: Execute research for the 3 NEEDS CLARIFICATION items
2. **Phase 1**: Generate data-model.md, contracts/, quickstart.md
3. **Phase 1**: Update agent context
4. **Re-check Constitution**: Verify no violations introduced during design
5. **Phase 2**: Ready for `/speckit.tasks` to generate implementation tasks

---

**Status**: Phase 0 research pending. Will begin with frontend framework, bank sync, and authentication research.
