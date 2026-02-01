# Implementation Plan: Account Deletion

**Branch**: `004-account-deletion` | **Date**: 2026-02-01 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-account-deletion/spec.md`

## Summary

Implement account deletion functionality with a confirmation dialog. The backend already supports `DELETE /api/accounts/{id}` with cascade deletion of transactions. This feature adds a frontend confirmation dialog following the same pattern as `DisconnectConfirmDialog`, with appropriate warnings about data loss.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.8 (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy (backend); React 19, shadcn/ui, Tailwind CSS (frontend)
**Storage**: PostgreSQL with CASCADE delete on transactions.account_id
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Web application (desktop and mobile responsive)
**Project Type**: Web (backend + frontend)
**Performance Goals**: Deletion completes in < 1 second
**Constraints**: Must show confirmation dialog; must handle bank-connected accounts
**Scale/Scope**: Small feature - 1 new component, minor service additions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Test-First Development | PASS | Will write tests before implementation |
| II. Comprehensive Unit Testing | PASS | Component and service tests required |
| III. Type Safety | PASS | Full TypeScript and Python type hints |
| IV. Code Quality Standards | PASS | Ruff, black, mypy, eslint |
| V. Simplicity First | PASS | Minimal implementation - reuse existing patterns |
| VI. Consistent UI with shadcn/ui | PASS | Use AlertDialog from shadcn/ui (same as DisconnectConfirmDialog) |
| VII. Responsive Design | PASS | AlertDialog is responsive by default |

**Gate Status**: PASS - No violations, proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/004-account-deletion/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API already exists)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
backend/
├── src/mybudget/
│   ├── api/accounts.py           # DELETE endpoint (EXISTS)
│   └── services/account_service.py  # delete_account (EXISTS)
└── tests/
    └── unit/test_services/       # Account service tests (EXISTS)

frontend/
├── src/
│   ├── components/
│   │   └── DeleteAccountDialog.tsx  # NEW - confirmation dialog
│   ├── pages/
│   │   └── Accounts.tsx             # UPDATE - add delete button
│   └── services/
│       └── accountService.ts        # UPDATE - add delete method
└── tests/
    └── components/                   # Component tests
```

**Structure Decision**: Web application structure. Backend API already complete - only frontend changes needed.

## Complexity Tracking

> No violations - feature is straightforward.

| Aspect | Complexity | Justification |
|--------|------------|---------------|
| Backend | Minimal | API already exists with cascade delete |
| Frontend | Low | Copy pattern from DisconnectConfirmDialog |
| Testing | Standard | Unit tests for component and service |

## Key Findings from Codebase Analysis

### Backend (Already Complete)
- `DELETE /api/accounts/{account_id}` endpoint exists at `backend/src/mybudget/api/accounts.py:90`
- `AccountService.delete_account()` implemented at `backend/src/mybudget/services/account_service.py:204`
- Transactions have `ForeignKey("accounts.id", ondelete="CASCADE")` - auto-deleted
- LinkedAccounts have `ForeignKey("accounts.id", ondelete="SET NULL")` - unlinked but preserved

### Frontend (Needs Implementation)
- `accountService.ts` needs `delete(id)` method
- `DisconnectConfirmDialog.tsx` provides the exact pattern to follow
- `Accounts.tsx` needs delete button/menu option

### Existing Pattern (DisconnectConfirmDialog)
- Uses shadcn/ui `AlertDialog` component
- Warning icon with yellow background
- Bullet list of consequences
- Cancel and destructive Delete buttons
- Loading state during operation
- Error handling and display
