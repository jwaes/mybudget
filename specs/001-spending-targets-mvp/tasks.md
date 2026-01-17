# Tasks: MyBudget MVP - Spending Targets

**Input**: Design documents from `/specs/001-spending-targets-mvp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Per constitution's TDD principle, ALL tasks include tests. Red-Green-Refactor is mandatory.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3...)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/mybudget/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Database migrations**: `backend/migrations/versions/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend directory structure per plan.md (src/mybudget with models/, schemas/, services/, api/, lib/, db/)
- [X] T002 [P] Create frontend directory structure (src with components/, pages/, services/, lib/)
- [X] T003 Initialize Python project with pyproject.toml (FastAPI, SQLAlchemy 2.0, Alembic, Pydantic V2, pytest, pytest-cov, pytest-asyncio, Faker, ruff, black, mypy)
- [X] T004 [P] Initialize Node.js project with package.json (React 19, TypeScript 5.8, Vite, React Hook Form, Vitest, React Testing Library, Playwright)
- [X] T005 [P] Create .gitignore for Python and Node.js
- [X] T006 Configure ruff in pyproject.toml (line-length=100, target-version=py311)
- [X] T007 [P] Configure black in pyproject.toml (line-length=100, target-version=py311)
- [X] T008 [P] Configure mypy in pyproject.toml (strict=true, plugins=sqlalchemy.ext.mypy.plugin, pydantic)
- [X] T009 [P] Create pytest.ini with coverage settings (target=90%)
- [X] T010 [P] Create .env.example with required environment variables (DATABASE_URL, SECRET_KEY, FRONTEND_URL)
- [X] T011 Create docker-compose.yml with PostgreSQL 15 service
- [X] T012 [P] Setup pre-commit hooks (.pre-commit-config.yaml with ruff, black, mypy, pytest)
- [X] T013 Create README.md with quickstart instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & ORM Foundation

- [X] T014 Create SQLAlchemy Base in backend/src/mybudget/db/base.py
- [X] T015 [P] Create database session management in backend/src/mybudget/db/session.py
- [X] T016 Initialize Alembic in backend/migrations/ with alembic.ini and env.py
- [X] T017 Create User model in backend/src/mybudget/models/user.py (UUID, email, password_hash, timezone, timestamps)
- [X] T018 [P] Create Pydantic UserCreate schema in backend/src/mybudget/schemas/user.py
- [X] T019 Generate initial Alembic migration for users table
- [X] T020 Test: Write unit test for User model in backend/tests/unit/test_models/test_user.py
- [X] T021 Test: Write migration test ensuring users table created correctly

### Authentication Foundation

- [X] T022 Install fastapi-sessions, fastapi-csrf-protect, pwdlib dependencies
- [X] T023 Create password hashing utility in backend/src/mybudget/lib/auth.py using pwdlib with Argon2id
- [X] T024 Test: Write unit test for password hashing (hash, verify) in backend/tests/unit/test_lib/test_auth.py
- [X] T025 Create session configuration in backend/src/mybudget/config.py (HTTP-only cookies, SameSite=Lax, 30min timeout)
- [X] T026 Create authentication endpoints in backend/src/mybudget/api/auth.py (POST /login, POST /logout, GET /me)
- [X] T027 Test: Write contract tests for auth API in backend/tests/contract/test_auth_api.py
- [ ] T028 Create authentication middleware/dependency for protected routes in backend/src/mybudget/api/dependencies.py
- [ ] T029 Test: Write integration test for login flow in backend/tests/integration/test_auth_flow.py

### FastAPI Application Setup

- [X] T030 Create FastAPI app in backend/src/mybudget/main.py with CORS, exception handlers
- [ ] T031 [P] Register all API routers (accounts, transactions, categories, targets, budget, reconciliation)
- [X] T032 Add OpenAPI/Swagger customization (title, version, description)
- [ ] T033 Test: Write test for FastAPI app startup in backend/tests/test_main.py

### Frontend Foundation

- [ ] T034 Setup React app entry point in frontend/src/main.tsx
- [ ] T035 [P] Create API client utility in frontend/src/services/api.ts (axios with session cookie handling)
- [ ] T036 [P] Create authentication service in frontend/src/services/authService.ts (login, logout, getUser)
- [ ] T037 [P] Create authentication context/hook in frontend/src/lib/auth-context.tsx
- [ ] T038 Test: Write unit tests for authService in frontend/tests/services/test_authService.test.ts

### Shared Utilities

- [X] T039 Create date utilities in backend/src/mybudget/lib/date_utils.py (get_month_first_day, get_month_boundaries, calculate_months_between)
- [X] T040 Test: Write unit tests for date utilities in backend/tests/unit/test_lib/test_date_utils.py
- [X] T041 [P] Create decimal utilities in backend/src/mybudget/lib/decimal_utils.py (safe_decimal, round_currency)
- [X] T042 Test: Write unit tests for decimal utilities in backend/tests/unit/test_lib/test_decimal_utils.py
- [X] T043 [P] Create custom exceptions in backend/src/mybudget/lib/exceptions.py (InsufficientFunds, InvalidTargetDate, ReconciliationError)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Set Up Bank Account and Sync Transactions (Priority: P1) 🎯 MVP

**Goal**: Users can add bank accounts, import transactions via CSV, and approve/categorize them

**Independent Test**: User can create an account with balance, upload CSV transactions, see them in inbox, approve and categorize them, and see account balance + category activity update correctly

### Tests for User Story 1 (TDD - Write These FIRST)

- [ ] T044 [P] [US1] Test: Write contract test for POST /accounts in backend/tests/contract/test_accounts_api.py
- [ ] T045 [P] [US1] Test: Write contract test for GET /accounts in backend/tests/contract/test_accounts_api.py
- [ ] T046 [P] [US1] Test: Write contract test for POST /transactions (CSV import) in backend/tests/contract/test_transactions_api.py
- [ ] T047 [P] [US1] Test: Write contract test for PUT /transactions/{id}/approve in backend/tests/contract/test_transactions_api.py
- [ ] T048 [P] [US1] Test: Write unit test for Account model in backend/tests/unit/test_models/test_account.py
- [ ] T049 [P] [US1] Test: Write unit test for Transaction model in backend/tests/unit/test_models/test_transaction.py
- [ ] T050 [P] [US1] Test: Write unit test for CategorizationRule model in backend/tests/unit/test_models/test_rule.py
- [ ] T051 [US1] Test: Write integration test for user journey (create account → import CSV → approve → verify balance) in backend/tests/integration/test_user_journeys/test_setup_and_sync.py

### Implementation for User Story 1

- [ ] T052 [P] [US1] Create Account model in backend/src/mybudget/models/account.py per data-model.md
- [ ] T053 [P] [US1] Create Transaction model in backend/src/mybudget/models/transaction.py per data-model.md
- [ ] T054 [P] [US1] Create CategorizationRule model in backend/src/mybudget/models/rule.py per data-model.md
- [ ] T055 [US1] Generate Alembic migration for accounts, transactions, categorization_rules tables
- [ ] T056 [P] [US1] Create Pydantic schemas in backend/src/mybudget/schemas/account.py (AccountCreate, AccountResponse)
- [ ] T057 [P] [US1] Create Pydantic schemas in backend/src/mybudget/schemas/transaction.py (TransactionCreate, TransactionApprove, TransactionResponse)
- [ ] T058 [P] [US1] Create Pydantic schemas in backend/src/mybudget/schemas/rule.py (CategorizationRuleCreate, CategorizationRuleResponse)
- [ ] T059 [US1] Implement account service in backend/src/mybudget/services/account_service.py (create_account, get_accounts, update_balance)
- [ ] T060 [US1] Implement transaction service in backend/src/mybudget/services/transaction_service.py (import_csv, get_inbox, approve_transaction, apply_rules)
- [ ] T061 [US1] Implement CSV parser in backend/src/mybudget/lib/csv_parser.py (parse_csv, validate_format)
- [ ] T062 [US1] Test: Write unit test for CSV parser in backend/tests/unit/test_lib/test_csv_parser.py
- [ ] T063 [US1] Implement accounts API endpoints in backend/src/mybudget/api/accounts.py per contracts/accounts.yaml
- [ ] T064 [US1] Implement transactions API endpoints in backend/src/mybudget/api/transactions.py (inbox, import, approve, categorize)
- [ ] T065 [P] [US1] Create AccountList component in frontend/src/components/AccountList.tsx
- [ ] T066 [P] [US1] Create TransactionInbox component in frontend/src/components/TransactionInbox.tsx
- [ ] T067 [P] [US1] Create CSV import component in frontend/src/components/CSVImport.tsx
- [ ] T068 [US1] Create accountService in frontend/src/services/accountService.ts
- [ ] T069 [US1] Create transactionService in frontend/src/services/transactionService.ts
- [ ] T070 [US1] Create Accounts page in frontend/src/pages/Accounts.tsx
- [ ] T071 [US1] Create Transactions page in frontend/src/pages/Transactions.tsx
- [ ] T072 [US1] Test: Write component tests for AccountList in frontend/tests/components/AccountList.test.tsx
- [ ] T073 [US1] Test: Write component tests for TransactionInbox in frontend/tests/components/TransactionInbox.test.tsx

**Checkpoint**: User Story 1 complete - user can create accounts, import transactions, and approve them

---

## Phase 4: User Story 2 - Organize Budget with Categories and Monthly View (Priority: P2)

**Goal**: Users can create category groups and categories, assign funds, and view budget month view

**Independent Test**: User can create category structure, assign funds to categories, see Available/Funded/Activity values, and navigate between months with correct rollover

### Tests for User Story 2 (TDD - Write These FIRST)

- [ ] T074 [P] [US2] Test: Write contract test for POST /category-groups in backend/tests/contract/test_categories_api.py
- [ ] T075 [P] [US2] Test: Write contract test for POST /categories in backend/tests/contract/test_categories_api.py
- [ ] T076 [P] [US2] Test: Write contract test for POST /categories/{id}/assign in backend/tests/contract/test_categories_api.py
- [ ] T077 [P] [US2] Test: Write contract test for GET /budget/{month} in backend/tests/contract/test_budget_api.py
- [ ] T078 [P] [US2] Test: Write unit test for CategoryGroup model in backend/tests/unit/test_models/test_category.py
- [ ] T079 [P] [US2] Test: Write unit test for Category model methods (get_available, get_funded_this_month, get_activity) in backend/tests/unit/test_models/test_category.py
- [ ] T080 [P] [US2] Test: Write unit test for Assignment model in backend/tests/unit/test_models/test_assignment.py
- [ ] T081 [US2] Test: Write integration test for user journey (create categories → assign funds → verify calculations) in backend/tests/integration/test_user_journeys/test_organize_budget.py

### Implementation for User Story 2

- [ ] T082 [P] [US2] Create CategoryGroup model in backend/src/mybudget/models/category.py
- [ ] T083 [P] [US2] Create Category model in backend/src/mybudget/models/category.py with computed methods
- [ ] T084 [P] [US2] Create Assignment model in backend/src/mybudget/models/assignment.py
- [ ] T085 [US2] Generate Alembic migration for category_groups, categories, assignments tables
- [ ] T086 [P] [US2] Create Pydantic schemas in backend/src/mybudget/schemas/category.py
- [ ] T087 [US2] Implement category service in backend/src/mybudget/services/category_service.py (create_group, create_category, assign_funds, calculate_to_assign)
- [ ] T088 [US2] Implement budget service in backend/src/mybudget/services/budget_service.py (get_month_view, calculate_rollover)
- [ ] T089 [US2] Implement categories API endpoints in backend/src/mybudget/api/categories.py
- [ ] T090 [US2] Implement budget API endpoints in backend/src/mybudget/api/budget.py
- [ ] T091 [P] [US2] Create BudgetMonthView component in frontend/src/components/BudgetMonthView.tsx
- [ ] T092 [P] [US2] Create CategoryRow component in frontend/src/components/CategoryRow.tsx (shows Available, Funded, Activity)
- [ ] T093 [P] [US2] Create CategoryGroupSection component in frontend/src/components/CategoryGroupSection.tsx
- [ ] T094 [P] [US2] Create month navigation component in frontend/src/components/MonthNavigator.tsx
- [ ] T095 [US2] Create categoryService in frontend/src/services/categoryService.ts
- [ ] T096 [US2] Create budgetService in frontend/src/services/budgetService.ts
- [ ] T097 [US2] Create Budget page in frontend/src/pages/Budget.tsx
- [ ] T098 [US2] Test: Write component tests for BudgetMonthView in frontend/tests/components/BudgetMonthView.test.tsx

**Checkpoint**: User Story 2 complete - user can organize budget and assign funds

---

## Phase 5: User Story 3 - Reconcile Account Against Statement (Priority: P3)

**Goal**: Users can reconcile accounts against bank statements with discrepancy resolution

**Independent Test**: User can start reconciliation, mark transactions as cleared, create adjustment if needed, and complete reconciliation

### Tests for User Story 3 (TDD - Write These FIRST)

- [ ] T099 [P] [US3] Test: Write contract test for POST /reconciliations in backend/tests/contract/test_reconciliation_api.py
- [ ] T100 [P] [US3] Test: Write contract test for PUT /reconciliations/{id}/mark-cleared in backend/tests/contract/test_reconciliation_api.py
- [ ] T101 [P] [US3] Test: Write contract test for POST /reconciliations/{id}/create-adjustment in backend/tests/contract/test_reconciliation_api.py
- [ ] T102 [P] [US3] Test: Write unit test for Reconciliation model (calculate_cleared_balance, calculate_discrepancy) in backend/tests/unit/test_models/test_reconciliation.py
- [ ] T103 [US3] Test: Write integration test for reconciliation workflow in backend/tests/integration/test_user_journeys/test_reconciliation.py

### Implementation for User Story 3

- [ ] T104 [US3] Create Reconciliation model in backend/src/mybudget/models/reconciliation.py per data-model.md
- [ ] T105 [US3] Generate Alembic migration for reconciliations table
- [ ] T106 [P] [US3] Create Pydantic schemas in backend/src/mybudget/schemas/reconciliation.py
- [ ] T107 [US3] Implement reconciliation service in backend/src/mybudget/services/reconciliation_service.py
- [ ] T108 [US3] Implement reconciliation API endpoints in backend/src/mybudget/api/reconciliation.py
- [ ] T109 [P] [US3] Create ReconcileModal component in frontend/src/components/ReconcileModal.tsx
- [ ] T110 [US3] Create reconciliationService in frontend/src/services/reconciliationService.ts
- [ ] T111 [US3] Integrate reconciliation into Accounts page
- [ ] T112 [US3] Test: Write component tests for ReconcileModal in frontend/tests/components/ReconcileModal.test.tsx

**Checkpoint**: User Story 3 complete - reconciliation workflow functional

---

## Phase 6: User Story 4 - Set Category Spending Target (Priority: P4) 🎯 Core Feature

**Goal**: Users can set three types of spending targets and see accurate underfunded calculations

**Independent Test**: User can set Monthly Needed, Target Balance, and Target by Date targets, and system calculates underfunded correctly per FR-028 formulas

### Tests for User Story 4 (TDD - Write These FIRST)

- [ ] T113 [P] [US4] Test: Write contract test for POST /targets in backend/tests/contract/test_targets_api.py
- [ ] T114 [P] [US4] Test: Write contract test for GET /targets/{id}/underfunded in backend/tests/contract/test_targets_api.py
- [ ] T115 [P] [US4] Test: Write unit test for CategoryTarget model validation (amount > 0, date not in past) in backend/tests/unit/test_models/test_target.py
- [ ] T116 [P] [US4] Test: Write unit test for underfunded calculation - Monthly Needed in backend/tests/unit/test_models/test_target.py
- [ ] T117 [P] [US4] Test: Write unit test for underfunded calculation - Target Balance in backend/tests/unit/test_models/test_target.py
- [ ] T118 [P] [US4] Test: Write unit test for underfunded calculation - Target by Date in backend/tests/unit/test_models/test_target.py
- [ ] T119 [P] [US4] Test: Write unit test for months_left calculation (edge case: current month = target month) in backend/tests/unit/test_models/test_target.py
- [ ] T120 [US4] Test: Write integration test for target CRUD workflow in backend/tests/integration/test_user_journeys/test_set_targets.py

### Implementation for User Story 4

- [ ] T121 [US4] Create CategoryTarget model in backend/src/mybudget/models/target.py with calculate_underfunded method per data-model.md
- [ ] T122 [US4] Generate Alembic migration for category_targets table with CHECK constraints
- [ ] T123 [P] [US4] Create Pydantic schemas in backend/src/mybudget/schemas/target.py per contracts/targets.yaml
- [ ] T124 [US4] Implement target service in backend/src/mybudget/services/target_service.py (create, update, delete, calculate_underfunded)
- [ ] T125 [US4] Implement targets API endpoints in backend/src/mybudget/api/targets.py per contracts/targets.yaml
- [ ] T126 [P] [US4] Create TargetModal component in frontend/src/components/TargetModal.tsx (type selector, amount input, date picker)
- [ ] T127 [P] [US4] Create target badge component in frontend/src/components/TargetBadge.tsx (shows type icon)
- [ ] T128 [US4] Create targetService in frontend/src/services/targetService.ts
- [ ] T129 [US4] Integrate target creation into CategoryRow component (add "Set Target" button)
- [ ] T130 [US4] Update BudgetMonthView to display underfunded indicators
- [ ] T131 [US4] Test: Write component tests for TargetModal in frontend/tests/components/TargetModal.test.tsx

**Checkpoint**: User Story 4 complete - users can set and edit targets with correct calculations

---

## Phase 7: User Story 5 - View Funding Guidance and Fund Underfunded Categories (Priority: P5) 🎯 Core Feature

**Goal**: Users can see total underfunded, filter/sort categories, and use quick-fund buttons

**Independent Test**: User can see underfunded summary, use "Fund Underfunded" on category, and use "Fund All Underfunded" to allocate in priority order

### Tests for User Story 5 (TDD - Write These FIRST)

- [ ] T132 [P] [US5] Test: Write contract test for GET /budget/{month}/underfunded-summary in backend/tests/contract/test_budget_api.py
- [ ] T133 [P] [US5] Test: Write contract test for POST /budget/{month}/fund-underfunded/{category_id} in backend/tests/contract/test_budget_api.py
- [ ] T134 [P] [US5] Test: Write contract test for POST /budget/{month}/fund-all-underfunded in backend/tests/contract/test_budget_api.py
- [ ] T135 [P] [US5] Test: Write unit test for funding service - fund single category in backend/tests/unit/test_services/test_funding_service.py
- [ ] T136 [P] [US5] Test: Write unit test for funding service - fund all with priority order in backend/tests/unit/test_services/test_funding_service.py
- [ ] T137 [P] [US5] Test: Write unit test for funding service - partial funding when To Assign insufficient in backend/tests/unit/test_services/test_funding_service.py
- [ ] T138 [US5] Test: Write integration test for funding workflow in backend/tests/integration/test_user_journeys/test_funding_guidance.py

### Implementation for User Story 5

- [ ] T139 [US5] Implement funding service in backend/src/mybudget/services/funding_service.py (fund_underfunded, fund_all_underfunded, calculate_priority_order)
- [ ] T140 [US5] Add funding endpoints to budget API in backend/src/mybudget/api/budget.py
- [ ] T141 [US5] Update BudgetMonthView component to show underfunded total in top bar
- [ ] T142 [P] [US5] Create "Fund Underfunded" button in CategoryRow component
- [ ] T143 [P] [US5] Create "Fund All Underfunded" button in BudgetMonthView top bar
- [ ] T144 [US5] Implement optimistic UI updates for funding actions (update local state before API response)
- [ ] T145 [US5] Add funding action feedback (toast/snackbar showing "Funded €X to Category")
- [ ] T146 [US5] Test: Write E2E test for full funding workflow in frontend/tests/e2e/funding-workflow.spec.ts

**Checkpoint**: User Story 5 complete - full funding guidance and quick-fund workflow functional

---

## Phase 8: User Story 6 - Month Rollover with Target Persistence (Priority: P6)

**Goal**: Targets behave consistently across month boundaries (Monthly Needed resets, Target Balance persists, Target by Date adjusts)

**Independent Test**: User navigates to next month and verifies each target type behaves per spec (US6 acceptance scenarios)

### Tests for User Story 6 (TDD - Write These FIRST)

- [ ] T147 [P] [US6] Test: Write unit test for Monthly Needed month rollover (funded_this_month resets, underfunded = target) in backend/tests/unit/test_services/test_target_service.py
- [ ] T148 [P] [US6] Test: Write unit test for Target Balance month rollover (target persists, adjusts to current available) in backend/tests/unit/test_services/test_target_service.py
- [ ] T149 [P] [US6] Test: Write unit test for Target by Date month rollover (months_left decreases, suggested_monthly adjusts) in backend/tests/unit/test_services/test_target_service.py
- [ ] T150 [US6] Test: Write integration test for month navigation with targets in backend/tests/integration/test_user_journeys/test_month_rollover.py

### Implementation for User Story 6

- [ ] T151 [US6] Update budget service to handle month navigation correctly (calculate rollover for each category)
- [ ] T152 [US6] Update target service to recalculate underfunded based on new month context
- [ ] T153 [US6] Add month boundary handling in frontend MonthNavigator component
- [ ] T154 [US6] Test: Write E2E test for month navigation with all three target types in frontend/tests/e2e/month-rollover.spec.ts

**Checkpoint**: User Story 6 complete - month rollover behavior is correct and predictable

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T155 [P] Create currency formatter utility in frontend/src/lib/formatters.ts (formatEuro, formatDecimal)
- [ ] T156 [P] Create date formatter utility in frontend/src/lib/formatters.ts (formatMonthYear, formatDate)
- [ ] T157 [P] Add loading states to all async operations (spinner/skeleton components)
- [ ] T158 [P] Add error boundaries in React app for graceful error handling
- [ ] T159 [P] Add error toast/snackbar system for user feedback
- [ ] T160 [P] Implement form validation on all input components (real-time feedback)
- [ ] T161 Create 404 Not Found page in frontend/src/pages/NotFound.tsx
- [ ] T162 [P] Add accessibility attributes (ARIA labels, keyboard navigation)
- [ ] T163 [P] Optimize bundle size (code splitting, lazy loading)
- [ ] T164 Create deployment documentation in docs/DEPLOYMENT.md
- [ ] T165 [P] Add database backup/restore scripts in backend/scripts/
- [ ] T166 [P] Setup GitHub Actions CI/CD pipeline (.github/workflows/ci.yml for backend tests)
- [ ] T167 [P] Setup GitHub Actions CI/CD pipeline (.github/workflows/frontend.yml for frontend tests)
- [ ] T168 Run full test suite and achieve 90%+ code coverage
- [ ] T169 Performance testing: Verify API response times <200ms p95
- [ ] T170 Run quickstart.md validation (ensure new developer can setup in 5 minutes)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4 → P5 → P6)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - No dependencies (categories are independent of accounts/transactions)
- **User Story 3 (P3)**: Requires User Story 1 (needs accounts and transactions to reconcile)
- **User Story 4 (P4)**: Requires User Story 2 (needs categories to set targets on)
- **User Story 5 (P5)**: Requires User Story 4 (needs targets to show funding guidance)
- **User Story 6 (P6)**: Requires User Story 4 (needs targets to test month rollover)

### Critical Path (Sequential MVP)

For solo developer building MVP sequentially:

1. Phase 1: Setup (T001-T013)
2. Phase 2: Foundational (T014-T043) ⚠️ BLOCKS everything
3. Phase 3: User Story 1 (T044-T073) - Accounts & Transactions
4. Phase 4: User Story 2 (T074-T098) - Categories & Budget View
5. Phase 6: User Story 4 (T113-T131) - Spending Targets ⭐ Core Feature
6. Phase 7: User Story 5 (T132-T146) - Funding Guidance ⭐ Core Feature
7. Optional: User Story 3 (T099-T112) - Reconciliation
8. Optional: User Story 6 (T147-T154) - Month Rollover
9. Phase 9: Polish (T155-T170)

**MVP Minimum** (can launch with just these):
- Setup + Foundational + US1 + US2 + US4 + US5 = ~130 tasks
- Delivers: Accounts, transactions, categories, targets, quick-funding
- Time estimate: 4-6 weeks full-time (strict TDD)

### Within Each User Story

TDD Workflow per task:

1. **Tests FIRST** (Red): Write failing tests, verify they fail
2. **Models**: Create database models, run migration
3. **Services**: Implement business logic to make tests pass (Green)
4. **API**: Create endpoints per contracts
5. **Frontend**: Build components and integrate
6. **Refactor**: Clean up code while keeping tests green

### Parallel Opportunities

- **Setup phase**: T002, T004, T005, T007, T008, T009, T010, T012 (frontend + tooling tasks)
- **Foundational phase**: T015, T018, T024, T031, T035-T043 (independent utilities)
- **Within User Story 1**: All test tasks (T044-T051) can run in parallel
- **Within User Story 1**: Models (T052, T053, T054) can be created in parallel
- **Within User Story 1**: Schemas (T056, T057, T058) can be created in parallel
- **Within User Story 1**: Frontend components (T065, T066, T067) can be built in parallel

---

## Parallel Example: User Story 4 (Spending Targets)

```bash
# Step 1: Write all tests in parallel (Red phase)
Task: T113 - Contract test for POST /targets
Task: T114 - Contract test for GET /targets/{id}/underfunded
Task: T115 - Unit test for validation
Task: T116 - Unit test for Monthly Needed calculation
Task: T117 - Unit test for Target Balance calculation
Task: T118 - Unit test for Target by Date calculation
Task: T119 - Unit test for edge cases

# Step 2: Verify all tests fail (Red confirmation)

# Step 3: Implement in sequence (Green phase)
Task: T121 - Create CategoryTarget model
Task: T122 - Generate migration
Task: T123 - Create schemas
Task: T124 - Implement service (makes all calculation tests pass)
Task: T125 - Implement API (makes contract tests pass)

# Step 4: Frontend in parallel
Task: T126 - TargetModal component
Task: T127 - TargetBadge component
Task: T128 - targetService
```

---

## Implementation Strategy

### MVP First (Minimum Viable Product)

**Week 1-2**: Setup + Foundational
1. Complete Phase 1: Setup (13 tasks)
2. Complete Phase 2: Foundational (30 tasks)
3. **STOP and VALIDATE**: All tests pass, dev environment works

**Week 3**: User Story 1 - Accounts & Transactions
1. Complete Phase 3: US1 (30 tasks)
2. **STOP and VALIDATE**: Can create account, import CSV, approve transactions

**Week 4**: User Story 2 - Categories & Budget
1. Complete Phase 4: US2 (25 tasks)
2. **STOP and VALIDATE**: Can create categories, assign funds, see budget view

**Week 5**: User Story 4 - Spending Targets
1. Complete Phase 6: US4 (19 tasks)
2. **STOP and VALIDATE**: Can set all three target types with correct calculations

**Week 6**: User Story 5 - Funding Guidance
1. Complete Phase 7: US5 (15 tasks)
2. **STOP and VALIDATE**: Can fund categories with one tap
3. **LAUNCH MVP**: Basic budgeting with spending targets works end-to-end

### Incremental Delivery After MVP

**Week 7**: Add Reconciliation (US3)
1. Complete Phase 5: US3 (14 tasks)
2. Deploy update

**Week 8**: Add Month Rollover (US6) + Polish
1. Complete Phase 8: US6 (8 tasks)
2. Complete Phase 9: Polish (16 tasks)
3. Deploy final v1.0

---

## Notes

- **[P] tasks** = different files, no dependencies - can run in parallel
- **[Story] labels** = map task to specific user story for traceability
- **TDD is mandatory**: Every feature has tests written FIRST
- **Each user story is independently testable**: Can deploy US1+US2+US4+US5 without US3 or US6
- **Verify tests fail before implementing**: Constitution requires Red-Green-Refactor
- **Commit after each task or logical group**: Keep working tree clean
- **Stop at checkpoints**: Validate story works independently before moving on

**Total Tasks**: 170 tasks
- Setup: 13 tasks
- Foundational: 30 tasks
- User Story 1: 30 tasks
- User Story 2: 25 tasks
- User Story 3: 14 tasks
- User Story 4: 19 tasks
- User Story 5: 15 tasks
- User Story 6: 8 tasks
- Polish: 16 tasks

**MVP Subset**: ~130 tasks (exclude US3, US6, some polish)
**Estimated Time**: 6-8 weeks full-time with strict TDD

---

## Constitution Compliance

✅ **Test-First Development**: All user stories include test tasks written BEFORE implementation
✅ **Comprehensive Unit Testing**: 100% coverage target with unit, integration, contract, and E2E tests
✅ **Type Safety**: All code uses TypeScript (frontend) and type hints (backend)
✅ **Code Quality**: Pre-commit hooks enforce ruff, black, mypy, pytest
✅ **Simplicity First**: No over-engineering - implement only what spec requires
