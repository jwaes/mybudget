# API Contracts for MyBudget MVP

This directory contains OpenAPI 3.0 specifications for all MyBudget API endpoints.

## Contract Files

### ✅ auth.yaml (Complete)
Authentication API - user registration, login, logout, session management.

### ✅ targets.yaml (Complete)
Spending targets API - create, update, delete targets, calculate underfunded amounts.

### 📋 Remaining Contracts (To Be Generated)

The following contracts follow the same pattern as `targets.yaml`:

#### accounts.yaml
- `GET /accounts` - List all accounts
- `POST /accounts` - Create account with initial balance
- `GET /accounts/{id}` - Get account details with current balance
- `PUT /accounts/{id}` - Update account name/type
- `DELETE /accounts/{id}` - Delete account

#### transactions.yaml
- `GET /transactions/inbox` - Get unapproved transactions
- `GET /transactions` - List approved transactions (with filters: account, category, date range)
- `POST /transactions` - Create transaction (manual entry or CSV import)
- `PUT /transactions/{id}/approve` - Approve transaction (moves to APPROVED state)
- `PUT /transactions/{id}/categorize` - Set category for transaction
- `DELETE /transactions/{id}` - Delete transaction

#### categories.yaml
- `GET /category-groups` - List category groups
- `POST /category-groups` - Create category group
- `GET /categories` - List categories (with group filter)
- `POST /categories` - Create category
- `POST /categories/{id}/assign` - Assign funds to category (creates Assignment record)
- `GET /categories/{id}/stats` - Get available, funded, activity for month

#### budget.yaml
- `GET /budget/{month}` - Get budget month view (all categories with computed values)
- `GET /budget/{month}/to-assign` - Calculate "To Assign" amount
- `GET /budget/{month}/underfunded-summary` - Total underfunded across all targets
- `POST /budget/{month}/fund-underfunded/{category_id}` - Fund specific underfunded category
- `POST /budget/{month}/fund-all-underfunded` - Fund all underfunded categories in priority order

#### reconciliation.yaml
- `POST /reconciliations` - Start reconciliation (provide statement balance + date)
- `GET /reconciliations/{id}` - Get reconciliation status
- `GET /reconciliations/{id}/transactions` - Get uncleared transactions for reconciliation
- `PUT /reconciliations/{id}/mark-cleared` - Mark transactions as cleared
- `POST /reconciliations/{id}/create-adjustment` - Create adjustment transaction for discrepancy
- `PUT /reconciliations/{id}/complete` - Mark reconciliation complete

#### rules.yaml
- `GET /categorization-rules` - List all rules
- `POST /categorization-rules` - Create rule (payee pattern → category)
- `DELETE /categorization-rules/{id}` - Delete rule

## Contract Testing

All contracts can be tested against the implementation using:

```bash
# Generate request/response validation tests from OpenAPI specs
pytest tests/contract/test_api_contracts.py
```

## Viewing Documentation

FastAPI auto-generates interactive API docs from these schemas:

```bash
# Start dev server
uvicorn mybudget.main:app --reload

# View docs
open http://localhost:8000/docs  # Swagger UI
open http://localhost:8000/redoc # ReDoc
```

## Generating Client SDKs (Future)

OpenAPI specs enable auto-generation of TypeScript clients:

```bash
# Generate TypeScript client for frontend
npx openapi-typescript-codegen --input contracts/ --output frontend/src/api/generated
```

## Validation Rules

All contracts enforce:
- **Financial precision**: Decimal strings (not floats) for all monetary amounts
- **Type safety**: UUID validation, enum constraints
- **Required fields**: Per spec requirements
- **Error responses**: Consistent error format with `detail` and `error_code`
- **Security**: Session cookie authentication on all endpoints
