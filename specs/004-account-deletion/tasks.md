# Tasks: Account Deletion

**Input**: Design documents from `/specs/004-account-deletion/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Component tests included per constitution (TDD required).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/mybudget/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Service layer foundation for delete functionality

- [ ] T001 Add delete() method to accountService in frontend/src/services/accountService.ts

**Checkpoint**: Service layer ready for UI components

---

## Phase 2: User Story 1 - Delete Manual Account (Priority: P1) 🎯 MVP

**Goal**: Users can delete manual (non-bank-connected) accounts with a confirmation dialog

**Independent Test**: Create a manual account, click delete, confirm, verify account disappears from list

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T002 [P] [US1] Write component tests for DeleteAccountDialog in frontend/tests/components/DeleteAccountDialog.test.tsx (renders, shows account name, shows transaction warning, handles cancel, handles delete, shows loading, shows error)

### Implementation for User Story 1

- [ ] T003 [US1] Create DeleteAccountDialog component in frontend/src/components/DeleteAccountDialog.tsx (copy pattern from DisconnectConfirmDialog)
- [ ] T004 [US1] Add delete button/menu to account rows in frontend/src/pages/Accounts.tsx
- [ ] T005 [US1] Wire DeleteAccountDialog to Accounts page with state management in frontend/src/pages/Accounts.tsx
- [ ] T006 [US1] Add success toast notification after deletion in frontend/src/pages/Accounts.tsx

**Checkpoint**: Manual account deletion fully functional and testable

---

## Phase 3: User Story 2 - Delete Bank-Connected Account (Priority: P2)

**Goal**: Users can delete bank-connected accounts with appropriate warnings about unlinking

**Independent Test**: Delete a bank-connected account, verify it's removed, verify bank connection remains if other accounts exist

### Tests for User Story 2

- [ ] T007 [P] [US2] Add test cases for bank-connected accounts to DeleteAccountDialog tests in frontend/tests/components/DeleteAccountDialog.test.tsx (shows unlink warning for bank-connected accounts)

### Implementation for User Story 2

- [ ] T008 [US2] Update DeleteAccountDialog to show bank-specific warning when account.linked_account_id is present in frontend/src/components/DeleteAccountDialog.tsx
- [ ] T009 [US2] Ensure Account type includes linked_account_id field in frontend/src/types/account.ts (verify or add)

**Checkpoint**: Bank-connected account deletion works correctly

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and cleanup

- [ ] T010 Manual test: Delete manual account with transactions - verify transactions deleted
- [ ] T011 Manual test: Delete bank-connected account - verify account removed, bank connection preserved
- [ ] T012 Manual test: Cancel deletion - verify account unchanged
- [ ] T013 Run all frontend tests and verify passing
- [ ] T014 Final code review and cleanup

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (US1)**: Depends on Phase 1 (T001 must complete)
- **Phase 3 (US2)**: Depends on Phase 2 (US1 must be complete - builds on same dialog)
- **Phase 4 (Polish)**: Depends on Phase 2 and 3

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Component before page integration
- Core functionality before edge cases

### Parallel Opportunities

- T002 (tests) can start immediately after T001
- T007 (US2 tests) can start as soon as T003 (dialog) exists

---

## Parallel Example: User Story 1

```bash
# After T001 completes, launch test writing:
Task: "Write component tests for DeleteAccountDialog"

# After T002 completes (tests failing), implement:
Task: "Create DeleteAccountDialog component"
Task: "Add delete button to account rows"  # Can start after dialog exists
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: User Story 1 (T002-T006)
3. **STOP and VALIDATE**: Test manual account deletion
4. Deploy/demo if ready - users can delete manual accounts

### Incremental Delivery

1. Setup (T001) → Service layer ready
2. User Story 1 (T002-T006) → Manual deletion works (MVP!)
3. User Story 2 (T007-T009) → Bank-connected deletion works
4. Polish (T010-T014) → Fully tested and reviewed

---

## Notes

- Backend API already exists - no backend tasks needed
- Frontend follows existing DisconnectConfirmDialog pattern
- All deletion is handled by database CASCADE - no manual cleanup needed
- LinkedAccount.account_id set to NULL on delete (preserves bank connection)
