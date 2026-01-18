# Tasks: MyBudget MVP - Spending Targets

**Input**: Design documents from `/specs/001-spending-targets-mvp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md
**Last Updated**: 2026-01-18

**Tests**: Per constitution's TDD principle, ALL tasks include tests. Red-Green-Refactor is mandatory.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US0, US1, US2...)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/mybudget/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Database migrations**: `backend/migrations/versions/`

---

## Phase 1: Setup (Shared Infrastructure) ✅ COMPLETE

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

## Phase 2: Foundational (Blocking Prerequisites) ✅ COMPLETE

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

### Database & ORM Foundation

- [X] T014 Create SQLAlchemy Base in backend/src/mybudget/db/base.py
- [X] T015 [P] Create database session management in backend/src/mybudget/db/session.py
- [X] T016 Initialize Alembic in backend/migrations/ with alembic.ini and env.py
- [X] T017 Create User model in backend/src/mybudget/models/user.py (UUID, email, password_hash, timezone, timestamps)
- [X] T018 [P] Create Pydantic UserCreate schema in backend/src/mybudget/schemas/user.py
- [X] T019 Generate initial Alembic migration for users table
- [X] T020 Test: Write unit test for User model in backend/tests/unit/test_models/test_user.py
- [X] T021 Test: Write migration test ensuring users table created correctly

### Authentication Foundation (Backend)

- [X] T022 Install fastapi-sessions, fastapi-csrf-protect, pwdlib dependencies
- [X] T023 Create password hashing utility in backend/src/mybudget/lib/auth.py using pwdlib with Argon2id
- [X] T024 Test: Write unit test for password hashing (hash, verify) in backend/tests/unit/test_lib/test_auth.py
- [X] T025 Create session configuration in backend/src/mybudget/config.py (HTTP-only cookies, SameSite=Lax, 30min timeout)
- [X] T026 Create authentication endpoints in backend/src/mybudget/api/auth.py (POST /register, POST /login, POST /logout, GET /me)
- [X] T027 Test: Write contract tests for auth API in backend/tests/contract/test_auth_api.py
- [X] T028 Create authentication middleware/dependency for protected routes in backend/src/mybudget/api/dependencies.py
- [X] T029 Test: Write integration test for login flow in backend/tests/integration/test_auth_flow.py

### FastAPI Application Setup

- [X] T030 Create FastAPI app in backend/src/mybudget/main.py with CORS, exception handlers
- [X] T031 [P] Register all API routers (accounts, transactions, categories, targets, budget, reconciliation)
- [X] T032 Add OpenAPI/Swagger customization (title, version, description)
- [X] T033 Test: Write test for FastAPI app startup in backend/tests/test_main.py

### Frontend Foundation (Services Only)

- [X] T034 Setup React app entry point in frontend/src/main.tsx
- [X] T035 [P] Create API client utility in frontend/src/services/api.ts (fetch with session cookie handling)
- [X] T036 [P] Create authentication service in frontend/src/services/authService.ts (login, logout, getUser)
- [X] T037 [P] Create authentication context/hook in frontend/src/lib/auth-context.tsx
- [X] T038 Test: Write unit tests for authService in frontend/tests/services/authService.test.ts

### Shared Utilities

- [X] T039 Create date utilities in backend/src/mybudget/lib/date_utils.py (get_month_first_day, get_month_boundaries, calculate_months_between)
- [X] T040 Test: Write unit tests for date utilities in backend/tests/unit/test_lib/test_date_utils.py
- [X] T041 [P] Create decimal utilities in backend/src/mybudget/lib/decimal_utils.py (safe_decimal, round_currency)
- [X] T042 Test: Write unit tests for decimal utilities in backend/tests/unit/test_lib/test_decimal_utils.py
- [X] T043 [P] Create custom exceptions in backend/src/mybudget/lib/exceptions.py (InsufficientFunds, InvalidTargetDate, ReconciliationError)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 2.5: User Story 0 - Authentication UI (Priority: P0) ✅ COMPLETE

**Goal**: Users can register, log in, and access protected pages. This is the gateway to ALL other features.

**Independent Test**: User can visit the app, register a new account, log in with credentials, access protected budget pages, and log out.

**Dependencies**: Requires Phase 2 (Foundational) to be complete (auth backend, auth service, auth context exist)

### Tests for User Story 0 (TDD)

- [X] T044 [P] [US0] Test: Write component test for Login page in frontend/tests/components/Login.test.tsx (renders form, submits credentials, shows errors, redirects on success)
- [X] T045 [P] [US0] Test: Write component test for Register page in frontend/tests/components/Register.test.tsx (renders form with email/password/timezone, validates inputs, submits, shows errors)
- [X] T046 [US0] Test: Write E2E test for login flow in frontend/tests/e2e/auth.spec.ts (visit protected route → redirect to login → login → access granted)
- [X] T047 [US0] Test: Write E2E test for registration flow in frontend/tests/e2e/auth.spec.ts (register → auto-login → access dashboard)

### Implementation for User Story 0

- [X] T048 [US0] Create Login page in frontend/src/pages/Login.tsx per FR-AUTH-001, FR-AUTH-003, FR-AUTH-004, FR-AUTH-005
  - Email and password form fields
  - Form validation (email format, required fields)
  - Error message display for invalid credentials
  - "Register" link to registration page
  - Redirect to dashboard on success
  - Use authService.login() from existing service
- [X] T049 [US0] Create Register page in frontend/src/pages/Register.tsx per FR-AUTH-002, FR-AUTH-008, FR-AUTH-009
  - Email, password, confirm password, and timezone fields
  - Password strength validation (min 8 characters per spec)
  - Timezone selector (populate with IANA timezones)
  - Error message display for validation/duplicate email
  - "Login" link for existing users
  - Auto-login after successful registration
- [X] T050 [US0] Create ProtectedRoute component in frontend/src/components/ProtectedRoute.tsx per FR-AUTH-003
  - Wrapper for authenticated-only routes
  - Redirect to /login if not authenticated
  - Show loading state while checking auth status
- [X] T051 [US0] Add logout button to app layout/header per FR-AUTH-006
  - Visible when user is authenticated
  - Calls authService.logout()
  - Redirects to login page after logout
- [X] T052 [US0] Update App.tsx routing to integrate Login, Register, and ProtectedRoute
  - Public routes: /login, /register
  - Protected routes: /dashboard, /accounts, /transactions, /budget
  - Default redirect: unauthenticated → /login, authenticated → /dashboard
- [X] T053 [US0] Handle session expiry gracefully per FR-AUTH-007
  - Detect 401 responses from API
  - Clear local auth state
  - Redirect to login with "Session expired" message

**Checkpoint**: User Story 0 complete - users can register, log in, and access protected pages

---

## Phase 3: User Story 1 - Set Up Bank Account and Sync Transactions (Priority: P1) ✅ COMPLETE

**Goal**: Users can add bank accounts, import transactions via CSV, and approve/categorize them

**Independent Test**: User can create an account with balance, upload CSV transactions, see them in inbox, approve and categorize them, and see account balance + category activity update correctly

### Tests for User Story 1 (TDD)

- [X] T054 [P] [US1] Test: Write contract test for POST /accounts in backend/tests/contract/test_accounts_api.py
- [X] T055 [P] [US1] Test: Write contract test for GET /accounts in backend/tests/contract/test_accounts_api.py
- [X] T056 [P] [US1] Test: Write contract test for POST /transactions (CSV import) in backend/tests/contract/test_transactions_api.py
- [X] T057 [P] [US1] Test: Write contract test for PUT /transactions/{id}/approve in backend/tests/contract/test_transactions_api.py
- [X] T058 [P] [US1] Test: Write unit test for Account model in backend/tests/unit/test_models/test_account.py
- [X] T059 [P] [US1] Test: Write unit test for Transaction model in backend/tests/unit/test_models/test_transaction.py
- [X] T060 [P] [US1] Test: Write unit test for CategorizationRule model in backend/tests/unit/test_models/test_rule.py
- [X] T061 [US1] Test: Write integration test for user journey (create account → import CSV → approve → verify balance) in backend/tests/integration/test_user_journeys/test_setup_and_sync.py

### Implementation for User Story 1

- [X] T062 [P] [US1] Create Account model in backend/src/mybudget/models/account.py per data-model.md
- [X] T063 [P] [US1] Create Transaction model in backend/src/mybudget/models/transaction.py per data-model.md
- [X] T064 [P] [US1] Create CategorizationRule model in backend/src/mybudget/models/categorization_rule.py per data-model.md
- [X] T065 [US1] Generate Alembic migration for accounts, transactions, categorization_rules tables
- [X] T066 [P] [US1] Create Pydantic schemas in backend/src/mybudget/schemas/account.py (AccountCreate, AccountResponse)
- [X] T067 [P] [US1] Create Pydantic schemas in backend/src/mybudget/schemas/transaction.py (TransactionCreate, TransactionApprove, TransactionResponse)
- [X] T068 [P] [US1] Create Pydantic schemas in backend/src/mybudget/schemas/categorization_rule.py (CategorizationRuleCreate, CategorizationRuleResponse)
- [X] T069 [US1] Implement account service in backend/src/mybudget/services/account_service.py (create_account, get_accounts, update_balance)
- [X] T070 [US1] Implement transaction service in backend/src/mybudget/services/transaction_service.py (import_csv, get_inbox, approve_transaction, apply_rules)
- [X] T071 [US1] Implement CSV parser in backend/src/mybudget/lib/csv_parser.py (parse_csv, validate_format)
- [X] T072 [US1] Test: Write unit test for CSV parser in backend/tests/unit/test_lib/test_csv_parser.py
- [X] T073 [US1] Implement accounts API endpoints in backend/src/mybudget/api/accounts.py per contracts/accounts.yaml
- [X] T074 [US1] Implement transactions API endpoints in backend/src/mybudget/api/transactions.py (inbox, import, approve, categorize)
- [X] T075 [P] [US1] Create AccountList component in frontend/src/components/AccountList.tsx
- [X] T076 [P] [US1] Create TransactionInbox component in frontend/src/components/TransactionInbox.tsx
- [X] T077 [P] [US1] Create CSV import component in frontend/src/components/CSVImport.tsx
- [X] T078 [US1] Create accountService in frontend/src/services/accountService.ts
- [X] T079 [US1] Create transactionService in frontend/src/services/transactionService.ts
- [X] T080 [US1] Create Accounts page in frontend/src/pages/Accounts.tsx
- [X] T081 [US1] Create Transactions page in frontend/src/pages/Transactions.tsx
- [X] T082 [US1] Test: Write component tests for AccountList in frontend/tests/components/AccountList.test.tsx
- [X] T083 [US1] Test: Write component tests for TransactionInbox in frontend/tests/components/TransactionInbox.test.tsx

**Checkpoint**: User Story 1 complete - user can create accounts, import transactions, and approve them

---

## Phase 4: User Story 2 - Organize Budget with Categories and Monthly View (Priority: P2) ✅ COMPLETE

**Goal**: Users can create category groups and categories, assign funds, and view budget month view

**Independent Test**: User can create category structure, assign funds to categories, see Available/Funded/Activity values, and navigate between months with correct rollover

### Tests for User Story 2 (TDD - Write These FIRST)

- [X] T084 [P] [US2] Test: Write contract test for POST /category-groups in backend/tests/contract/test_categories_api.py
- [X] T085 [P] [US2] Test: Write contract test for POST /categories in backend/tests/contract/test_categories_api.py
- [X] T086 [P] [US2] Test: Write contract test for POST /categories/{id}/assign in backend/tests/contract/test_categories_api.py
- [X] T087 [P] [US2] Test: Write contract test for GET /budget/{month} in backend/tests/contract/test_budget_api.py
- [X] T088 [P] [US2] Test: Write unit test for CategoryGroup model in backend/tests/unit/test_models/test_category.py
- [X] T089 [P] [US2] Test: Write unit test for Category model methods (get_available, get_funded_this_month, get_activity) in backend/tests/unit/test_models/test_category.py
- [X] T090 [P] [US2] Test: Write unit test for Assignment model in backend/tests/unit/test_models/test_assignment.py
- [X] T091 [US2] Test: Write integration test for user journey (create categories → assign funds → verify calculations) in backend/tests/integration/test_budget_flow.py

### Implementation for User Story 2

- [X] T092 [P] [US2] Create CategoryGroup model in backend/src/mybudget/models/category.py
- [X] T093 [P] [US2] Create Category model in backend/src/mybudget/models/category.py with computed methods
- [X] T094 [P] [US2] Create Assignment model in backend/src/mybudget/models/assignment.py
- [X] T095 [US2] Generate Alembic migration for category_groups, categories, assignments tables
- [X] T096 [P] [US2] Create Pydantic schemas in backend/src/mybudget/schemas/category.py
- [X] T097 [US2] Implement category service in backend/src/mybudget/services/category_service.py (create_group, create_category, assign_funds, calculate_to_assign)
- [X] T098 [US2] Implement budget service in backend/src/mybudget/services/budget_service.py (get_month_view, calculate_rollover)
- [X] T099 [US2] Implement categories API endpoints in backend/src/mybudget/api/categories.py
- [X] T100 [US2] Implement budget API endpoints in backend/src/mybudget/api/budget.py
- [X] T101 [P] [US2] Create BudgetMonthView component in frontend/src/components/BudgetMonthView.tsx
- [X] T102 [P] [US2] Create CategoryRow component in frontend/src/components/CategoryRow.tsx (shows Available, Funded, Activity)
- [X] T103 [P] [US2] Create CategoryGroupSection component in frontend/src/components/CategoryGroupSection.tsx
- [X] T104 [P] [US2] Create month navigation component in frontend/src/components/MonthNavigator.tsx
- [X] T105 [US2] Create categoryService in frontend/src/services/categoryService.ts
- [X] T106 [US2] Create budgetService in frontend/src/services/budgetService.ts
- [X] T107 [US2] Create Budget page in frontend/src/pages/Budget.tsx
- [X] T108 [US2] Test: Write component tests for BudgetMonthView in frontend/tests/components/BudgetMonthView.test.tsx

### Category Management UI (Missing from Original Tasks)

- [X] T108a [P] [US2] Test: Write component tests for CategoryGroupModal in frontend/tests/components/CategoryGroupModal.test.tsx
- [X] T108b [P] [US2] Test: Write component tests for CategoryModal in frontend/tests/components/CategoryModal.test.tsx
- [X] T108c [P] [US2] Create CategoryGroupModal component in frontend/src/components/CategoryGroupModal.tsx (name input, create/edit/delete)
- [X] T108d [P] [US2] Create CategoryModal component in frontend/src/components/CategoryModal.tsx (name input, group selector for create, edit/delete)
- [X] T108e [US2] Add "Add Group" button to BudgetMonthView component (opens CategoryGroupModal)
- [X] T108f [US2] Add "Add Category" button to CategoryGroupSection component (opens CategoryModal)
- [X] T108g [US2] Add edit/delete functionality to category groups (click group name to edit)
- [X] T108h [US2] Add edit/delete functionality to categories (click category name to edit)

**Checkpoint**: User Story 2 complete - user can organize budget and assign funds

---

## Phase 5: User Story 3 - Reconcile Account Against Statement (Priority: P3) ✅ COMPLETE

**Goal**: Users can reconcile accounts against bank statements with discrepancy resolution

**Independent Test**: User can start reconciliation, mark transactions as cleared, create adjustment if needed, and complete reconciliation

### Tests for User Story 3 (TDD - Write These FIRST)

- [X] T109 [P] [US3] Test: Write contract test for POST /reconciliations in backend/tests/contract/test_reconciliation_api.py
- [X] T110 [P] [US3] Test: Write contract test for PUT /reconciliations/{id}/mark-cleared in backend/tests/contract/test_reconciliation_api.py
- [X] T111 [P] [US3] Test: Write contract test for POST /reconciliations/{id}/create-adjustment in backend/tests/contract/test_reconciliation_api.py
- [X] T112 [P] [US3] Test: Write unit test for Reconciliation model (calculate_cleared_balance, calculate_discrepancy) in backend/tests/unit/test_models/test_reconciliation.py
- [X] T113 [US3] Test: Write integration test for reconciliation workflow in backend/tests/integration/test_reconciliation_flow.py

### Implementation for User Story 3

- [X] T114 [US3] Create Reconciliation model in backend/src/mybudget/models/reconciliation.py per data-model.md
- [X] T115 [US3] Generate Alembic migration for reconciliations table
- [X] T116 [P] [US3] Create Pydantic schemas in backend/src/mybudget/schemas/reconciliation.py
- [X] T117 [US3] Implement reconciliation service in backend/src/mybudget/services/reconciliation_service.py
- [X] T118 [US3] Implement reconciliation API endpoints in backend/src/mybudget/api/reconciliation.py
- [X] T119 [P] [US3] Create ReconcileModal component in frontend/src/components/ReconcileModal.tsx → Use shadcn Dialog ✅ Completed with 002-shadcn-ui-migration
- [X] T120 [US3] Create reconciliationService in frontend/src/services/reconciliationService.ts ✅ Completed 2026-01-17
- [X] T121 [US3] Integrate reconciliation into Accounts page ✅ Completed 2026-01-17
- [X] T122 [US3] Test: Write component tests for ReconcileModal in frontend/tests/components/ReconcileModal.test.tsx ✅ Completed 2026-01-17

**Checkpoint**: User Story 3 complete - full reconciliation workflow functional

---

## Phase 6: User Story 4 - Set Category Spending Target (Priority: P4) 🎯 Core Feature ✅ COMPLETE

**Goal**: Users can set three types of spending targets and see accurate underfunded calculations

**Independent Test**: User can set Monthly Needed, Target Balance, and Target by Date targets, and system calculates underfunded correctly per FR-028 formulas

### Tests for User Story 4 (TDD - Write These FIRST)

- [X] T123 [P] [US4] Test: Write contract test for POST /targets in backend/tests/contract/test_targets_api.py
- [X] T124 [P] [US4] Test: Write contract test for GET /targets/{id}/underfunded in backend/tests/contract/test_targets_api.py
- [X] T125 [P] [US4] Test: Write unit test for CategoryTarget model validation (amount > 0, date not in past) in backend/tests/unit/test_models/test_target.py
- [X] T126 [P] [US4] Test: Write unit test for underfunded calculation - Monthly Needed in backend/tests/unit/test_models/test_target.py
- [X] T127 [P] [US4] Test: Write unit test for underfunded calculation - Target Balance in backend/tests/unit/test_models/test_target.py
- [X] T128 [P] [US4] Test: Write unit test for underfunded calculation - Target by Date in backend/tests/unit/test_models/test_target.py
- [X] T129 [P] [US4] Test: Write unit test for months_left calculation (edge case: current month = target month) in backend/tests/unit/test_models/test_target.py
- [X] T130 [US4] Test: Write integration test for target CRUD workflow in backend/tests/integration/test_user_journeys/test_set_targets.py

### Implementation for User Story 4

- [X] T131 [US4] Create CategoryTarget model in backend/src/mybudget/models/target.py with calculate_underfunded method per data-model.md
- [X] T132 [US4] Generate Alembic migration for category_targets table with CHECK constraints
- [X] T133 [P] [US4] Create Pydantic schemas in backend/src/mybudget/schemas/target.py per contracts/targets.yaml
- [X] T134 [US4] Implement target service in backend/src/mybudget/services/target_service.py (create, update, delete, calculate_underfunded)
- [X] T135 [US4] Implement targets API endpoints in backend/src/mybudget/api/targets.py per contracts/targets.yaml
- [X] T136 [P] [US4] Create TargetModal component in frontend/src/components/TargetModal.tsx (type selector, amount input, date picker)
- [X] T137 [P] [US4] Create target badge component in frontend/src/components/TargetBadge.tsx (shows type icon)
- [X] T138 [US4] Create targetService in frontend/src/services/targetService.ts
- [X] T139 [US4] Integrate target creation into CategoryRow component (add "Set Target" button)
- [X] T140 [US4] Update BudgetMonthView to display underfunded indicators
- [X] T141 [US4] Test: Write component tests for TargetModal in frontend/tests/components/TargetModal.test.tsx

**Checkpoint**: User Story 4 complete - users can set and edit targets with correct calculations

---

## Phase 7: User Story 5 - View Funding Guidance and Fund Underfunded Categories (Priority: P5) 🎯 Core Feature ✅ COMPLETE

**Goal**: Users can see total underfunded, filter/sort categories, and use quick-fund buttons

**Independent Test**: User can see underfunded summary, use "Fund Underfunded" on category, and use "Fund All Underfunded" to allocate in priority order

### Tests for User Story 5 (TDD - Write These FIRST)

- [X] T142 [P] [US5] Test: Write contract test for GET /budget/{month}/underfunded-summary in backend/tests/contract/test_budget_api.py
- [X] T143 [P] [US5] Test: Write contract test for POST /budget/{month}/fund-underfunded/{category_id} in backend/tests/contract/test_budget_api.py
- [X] T144 [P] [US5] Test: Write contract test for POST /budget/{month}/fund-all-underfunded in backend/tests/contract/test_budget_api.py
- [X] T145 [P] [US5] Test: Write unit test for funding service - fund single category in backend/tests/unit/test_services/test_funding_service.py
- [X] T146 [P] [US5] Test: Write unit test for funding service - fund all with priority order in backend/tests/unit/test_services/test_funding_service.py
- [X] T147 [P] [US5] Test: Write unit test for funding service - partial funding when To Assign insufficient in backend/tests/unit/test_services/test_funding_service.py
- [X] T148 [US5] Test: Write integration test for funding workflow in backend/tests/integration/test_budget_flow.py

### Implementation for User Story 5

- [X] T149 [US5] Implement funding service in backend/src/mybudget/services/funding_service.py (fund_underfunded, fund_all_underfunded, calculate_priority_order)
- [X] T150 [US5] Add funding endpoints to budget API in backend/src/mybudget/api/budget.py
- [X] T151 [US5] Update BudgetMonthView component to show underfunded total in top bar
- [X] T152 [P] [US5] Create "Fund Underfunded" button in CategoryRow component
- [X] T153 [P] [US5] Create "Fund All Underfunded" button in BudgetMonthView top bar
- [X] T154 [US5] Implement optimistic UI updates for funding actions (update local state before API response)
- [X] T155 [US5] Add funding action feedback (toast/snackbar showing "Funded €X to Category")
- [X] T156 [US5] Test: Write E2E test for full funding workflow in frontend/tests/e2e/funding-workflow.spec.ts ✅ Completed 2026-01-17

**Checkpoint**: User Story 5 complete - full funding guidance and quick-fund workflow functional

---

## Phase 8: User Story 6 - Month Rollover with Target Persistence (Priority: P6) ✅ COMPLETE

**Goal**: Targets behave consistently across month boundaries (Monthly Needed resets, Target Balance persists, Target by Date adjusts)

**Independent Test**: User navigates to next month and verifies each target type behaves per spec (US6 acceptance scenarios)

### Tests for User Story 6 (TDD - Write These FIRST)

- [X] T157 [P] [US6] Test: Write unit test for Monthly Needed month rollover (funded_this_month resets, underfunded = target) in backend/tests/unit/test_services/test_target_service.py ✅ Completed 2026-01-17
- [X] T158 [P] [US6] Test: Write unit test for Target Balance month rollover (target persists, adjusts to current available) in backend/tests/unit/test_services/test_target_service.py ✅ Completed 2026-01-17
- [X] T159 [P] [US6] Test: Write unit test for Target by Date month rollover (months_left decreases, suggested_monthly adjusts) in backend/tests/unit/test_services/test_target_service.py ✅ Completed 2026-01-17
- [X] T160 [US6] Test: Write integration test for month navigation with targets in backend/tests/integration/test_user_journeys/test_month_rollover.py ✅ Completed 2026-01-17

### Implementation for User Story 6

- [X] T161 [US6] Update budget service to handle month navigation correctly (calculate rollover for each category) ✅ Already implemented in budget_service.py
- [X] T162 [US6] Update target service to recalculate underfunded based on new month context ✅ Already implemented in target_service.py
- [X] T163 [US6] Add month boundary handling in frontend MonthNavigator component ✅ Already implemented
- [X] T164 [US6] Test: Write E2E test for month navigation with all three target types in frontend/tests/e2e/month-rollover.spec.ts ✅ Completed 2026-01-17

**Checkpoint**: User Story 6 complete - month rollover behavior is correct and predictable

---

## Phase 9: Transaction Search and Filtering (FR-046 to FR-053)

**Goal**: Users can search and filter transactions efficiently

**Dependencies**: User Story 1 (COMPLETE - transactions exist)

**Added**: 2026-01-18 from clarification session updates to spec.md

### Tests for Transaction Search (TDD)

- [ ] T181 [P] Test: Write unit test for transaction search by payee in backend/tests/unit/test_services/test_transaction_service.py
- [ ] T182 [P] Test: Write unit test for transaction search by memo in backend/tests/unit/test_services/test_transaction_service.py
- [ ] T183 [P] Test: Write unit test for transaction filtering (date, amount, category, account, status) in backend/tests/unit/test_services/test_transaction_service.py
- [ ] T184 [P] Test: Write contract test for GET /transactions with search/filter params in backend/tests/contract/test_transactions_api.py

### Implementation for Transaction Search

- [ ] T185 Add transaction search by payee (FR-046, partial match, case-insensitive) to backend/src/mybudget/services/transaction_service.py
- [ ] T186 Add transaction search by memo (FR-047, partial match, case-insensitive) to backend/src/mybudget/services/transaction_service.py
- [ ] T187 Add transaction filtering by date range (FR-048) to backend/src/mybudget/services/transaction_service.py
- [ ] T188 Add transaction filtering by amount range (FR-049) to backend/src/mybudget/services/transaction_service.py
- [ ] T189 Add transaction filtering by category (FR-050) including uncategorized to backend/src/mybudget/services/transaction_service.py
- [ ] T190 Add transaction filtering by account (FR-051) to backend/src/mybudget/services/transaction_service.py
- [ ] T191 Add transaction filtering by status (FR-052) to backend/src/mybudget/services/transaction_service.py
- [ ] T192 Update GET /transactions endpoint with search/filter query params in backend/src/mybudget/api/transactions.py
- [ ] T193 [P] Create TransactionSearch component in frontend/src/components/TransactionSearch.tsx
- [ ] T194 [P] Create TransactionFilters component in frontend/src/components/TransactionFilters.tsx
- [ ] T195 Add uncategorized transaction count badge to navigation (FR-053) in frontend/src/components/layout/
- [ ] T196 Integrate search/filter into Transactions page in frontend/src/pages/Transactions.tsx
- [ ] T197 Test: Write component test for TransactionSearch in frontend/tests/components/TransactionSearch.test.tsx
- [ ] T198 Test: Write component test for TransactionFilters in frontend/tests/components/TransactionFilters.test.tsx

**Checkpoint**: Transaction search and filtering complete - users can find transactions quickly

---

## Phase 10: Observability (FR-OBS-001 to FR-OBS-004)

**Goal**: Production-ready monitoring with structured logging, Prometheus metrics, and health checks

**Dependencies**: None (cross-cutting concern, can start anytime)

**Added**: 2026-01-18 from clarification session - decided on full observability stack

### Implementation for Observability

- [ ] T199 Add structlog and prometheus-fastapi-instrumentator to backend/pyproject.toml
- [ ] T200 Configure structlog for JSON logging in backend/src/mybudget/lib/logging.py
- [ ] T201 Create health check endpoint (FR-OBS-003) returning system status in backend/src/mybudget/api/health.py
- [ ] T202 Setup Prometheus metrics endpoint (FR-OBS-002) using prometheus-fastapi-instrumentator in backend/src/mybudget/main.py
- [ ] T203 Add logging for key user actions (FR-OBS-001): login, logout, transaction approval, funding operations
- [ ] T204 Configure metrics for latency, error rates, sessions, transaction counts (FR-OBS-004)
- [ ] T205 Test: Write test for health check endpoint in backend/tests/contract/test_health_api.py
- [ ] T206 Test: Write test for metrics endpoint accessibility in backend/tests/contract/test_health_api.py

**Checkpoint**: Observability infrastructure complete - ready for production monitoring

---

## Phase 11: Bank Sync Status (FR-010a, FR-010b)

**Goal**: Users have visibility into bank sync status and can retry failed syncs

**Dependencies**: User Story 1 (COMPLETE - accounts exist)

**Added**: 2026-01-18 from clarification session - decided on status indicator + manual retry

### Implementation for Bank Sync Status

- [ ] T207 Add sync_status, last_sync_at, sync_error fields to Account model in backend/src/mybudget/models/account.py
- [ ] T208 Generate Alembic migration for account sync status fields
- [ ] T209 Add sync status update logic to CSV import (simulate sync) in backend/src/mybudget/services/transaction_service.py
- [ ] T210 Create POST /accounts/{id}/retry-sync endpoint in backend/src/mybudget/api/accounts.py
- [ ] T211 Add sync status indicator (FR-010a) per account in frontend/src/components/AccountList.tsx
- [ ] T212 Add manual retry button (FR-010b) for failed syncs in frontend/src/components/AccountList.tsx
- [ ] T213 Test: Write component test for sync status display in frontend/tests/components/AccountList.test.tsx

**Checkpoint**: Bank sync status visibility complete - users know when sync fails

---

## Phase 12: Categorization Extensibility (FR-043 to FR-045)

**Goal**: Transaction categorization interface supports future ML integration

**Dependencies**: User Story 1 (COMPLETE - transactions exist)

**Added**: 2026-01-18 from spec updates - ML-ready interface

### Implementation for Categorization Extensibility

- [ ] T214 Add categorization_source enum (MANUAL, RULE, ML_SUGGESTED) to Transaction model in backend/src/mybudget/models/transaction.py
- [ ] T215 Add confidence_score (nullable, 0.0-1.0) field to Transaction model
- [ ] T216 Generate Alembic migration for categorization fields
- [ ] T217 Update transaction approval workflow to set categorization_source = MANUAL
- [ ] T218 Update rule-based categorization to set categorization_source = RULE
- [ ] T219 Add batch approval endpoint (FR-045) for multiple transactions in backend/src/mybudget/api/transactions.py
- [ ] T220 Add batch approval UI in TransactionInbox component (select multiple, approve all with same category)
- [ ] T221 Test: Write unit test for categorization source tracking in backend/tests/unit/test_services/test_transaction_service.py
- [ ] T222 Test: Write contract test for batch approval endpoint in backend/tests/contract/test_transactions_api.py

**Checkpoint**: Categorization extensibility complete - ready for future ML integration

---

## Phase 13: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

**⚠️ NOTE**: Many polish tasks are superseded by 002-shadcn-ui-migration. Complete 002 first, then return here for remaining tasks. Tasks T167, T168, T170, T172, T173 are handled by shadcn components.

- [x] T165 [P] Create currency formatter utility in frontend/src/lib/formatters.ts (formatCurrency, formatDecimal) ✅ Created 2026-01-17
- [x] T166 [P] Create date formatter utility in frontend/src/lib/formatters.ts (formatMonthYear, formatDate) ✅ Created 2026-01-17
- [X] T167 [P] Add loading states to all async operations (spinner/skeleton components) → Used shadcn Skeleton in 002-shadcn-ui-migration ✅
- [X] T168 [P] Add error boundaries in React app for graceful error handling ✅ Created ErrorBoundary.tsx 2026-01-17
- [x] T169 [P] Add error toast/snackbar system for user feedback ✅ Enhanced Toast.tsx 2026-01-17
- [ ] T170 [P] Implement form validation on all input components (real-time feedback) → Use shadcn Form after 002
- [X] T171 Create 404 Not Found page in frontend/src/pages/NotFound.tsx ✅ Created 2026-01-17
- [X] T172 [P] Add accessibility attributes (ARIA labels, keyboard navigation) → Handled by Radix UI in 002-shadcn-ui-migration ✅
- [ ] T173 [P] Optimize bundle size (code splitting, lazy loading) → Do after 002 migration complete
- [ ] T174 Create deployment documentation in docs/DEPLOYMENT.md
- [ ] T175 [P] Add database backup/restore scripts in backend/scripts/
- [X] T176 [P] Setup GitHub Actions CI/CD pipeline (.github/workflows/backend.yml for backend tests) ✅ Created 2026-01-17
- [X] T177 [P] Setup GitHub Actions CI/CD pipeline (.github/workflows/frontend.yml for frontend tests) ✅ Created 2026-01-17
- [ ] T178 Run full test suite and achieve 90%+ code coverage
- [ ] T179 Performance testing: Verify API response times <200ms p95
- [ ] T180 Run quickstart.md validation (ensure new developer can setup in 5 minutes)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: ✅ COMPLETE
- **Foundational (Phase 2)**: ✅ COMPLETE
- **User Story 0 (Phase 2.5)**: Depends on Foundational - BLOCKS user access to all features
- **User Story 1 (Phase 3)**: ✅ COMPLETE
- **User Stories 2-6 (Phase 4-8)**: All depend on User Story 0 for user access
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P2 → P3 → P4 → P5 → P6)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 0 (P0)**: Can start after Foundational - GATEWAY to all features
- **User Story 1 (P1)**: ✅ COMPLETE
- **User Story 2 (P2)**: Can start after US0 - No dependencies (categories are independent of accounts/transactions)
- **User Story 3 (P3)**: Requires User Story 1 (needs accounts and transactions to reconcile)
- **User Story 4 (P4)**: Requires User Story 2 (needs categories to set targets on)
- **User Story 5 (P5)**: Requires User Story 4 (needs targets to show funding guidance)
- **User Story 6 (P6)**: Requires User Story 4 (needs targets to test month rollover)

### Critical Path (Next Steps)

Current state: Phases 1-8 COMPLETE. 172 tasks completed, 50 remaining.

**Completed**:
- Phase 1: Setup ✅
- Phase 2: Foundation ✅
- Phase 2.5: User Story 0 (Auth UI) ✅
- Phase 3: User Story 1 (Accounts & Transactions) ✅
- Phase 4: User Story 2 (Categories & Budget View) ✅
- Phase 5: User Story 3 (Reconciliation) ✅
- Phase 6: User Story 4 (Spending Targets) ✅ Core Feature
- Phase 7: User Story 5 (Funding Guidance) ✅
- Phase 8: User Story 6 (Month Rollover) ✅

**Next Steps** (new features from 2026-01-18 clarification):
1. **Phase 9: Transaction Search/Filtering** - FR-046 to FR-053 (18 tasks)
2. **Phase 10: Observability** - FR-OBS-001 to FR-OBS-004 (8 tasks)
3. **Phase 11: Bank Sync Status** - FR-010a, FR-010b (7 tasks)
4. **Phase 12: Categorization Extensibility** - FR-043 to FR-045 (9 tasks)
5. **Phase 13: Polish** - Remaining cross-cutting concerns (8 tasks)

---

## Notes

- **[P] tasks** = different files, no dependencies - can run in parallel
- **[Story] labels** = map task to specific user story for traceability
- **TDD is mandatory**: Every feature has tests written FIRST
- **Each user story is independently testable**: Can deploy incrementally
- **Verify tests fail before implementing**: Constitution requires Red-Green-Refactor
- **Commit after each task or logical group**: Keep working tree clean
- **Stop at checkpoints**: Validate story works independently before moving on

**Total Tasks**: 222 tasks
- Setup: 13 tasks (COMPLETE)
- Foundational: 30 tasks (COMPLETE)
- User Story 0: 10 tasks (COMPLETE)
- User Story 1: 30 tasks (COMPLETE)
- User Story 2: 33 tasks (COMPLETE)
- User Story 3: 14 tasks (COMPLETE)
- User Story 4: 19 tasks (COMPLETE)
- User Story 5: 15 tasks (COMPLETE)
- User Story 6: 8 tasks (COMPLETE)
- Transaction Search: 18 tasks (NEW - 2026-01-18)
- Observability: 8 tasks (NEW - 2026-01-18)
- Bank Sync Status: 7 tasks (NEW - 2026-01-18)
- Categorization Extensibility: 9 tasks (NEW - 2026-01-18)
- Polish: 16 tasks

**Completed**: 172 tasks (Phases 1-8 + partial Phase 13)
**Remaining**: 50 tasks (Phases 9-12 new features + remaining Phase 13 polish)

---

## Constitution Compliance

✅ **Test-First Development**: All user stories include test tasks written BEFORE implementation
✅ **Comprehensive Unit Testing**: 100% coverage target with unit, integration, contract, and E2E tests
✅ **Type Safety**: All code uses TypeScript (frontend) and type hints (backend)
✅ **Code Quality**: Pre-commit hooks enforce ruff, black, mypy, pytest
✅ **Simplicity First**: No over-engineering - implement only what spec requires
