# Research: Account Deletion

**Feature**: 004-account-deletion
**Date**: 2026-02-01

## Research Summary

This feature has minimal unknowns since it builds on existing patterns and infrastructure.

## Findings

### 1. Backend API Status

**Decision**: Use existing `DELETE /api/accounts/{id}` endpoint - no backend changes needed.

**Rationale**:
- Endpoint already exists at `backend/src/mybudget/api/accounts.py:90`
- Returns 204 No Content on success, 404 if not found
- Service layer handles deletion at `account_service.py:204`

**Alternatives Considered**:
- Soft delete (add `deleted_at` column) - Rejected: YAGNI, not in spec
- Archive endpoint - Rejected: Not requested, adds complexity

### 2. Cascade Deletion Behavior

**Decision**: Rely on database CASCADE constraints for transaction deletion.

**Rationale**:
- `transactions.account_id` has `ondelete="CASCADE"`
- Database handles deletion atomically
- No orphaned records possible

**Findings from schema**:
```python
# Transaction model
account_id: Mapped[UUID] = mapped_column(
    ForeignKey("accounts.id", ondelete="CASCADE"),
)

# LinkedAccount model
account_id: Mapped[UUID | None] = mapped_column(
    ForeignKey("accounts.id", ondelete="SET NULL"),
)
```

**Behavior**:
- Transactions: Automatically deleted with account
- LinkedAccounts: `account_id` set to NULL (link broken but record preserved)

### 3. Bank-Connected Account Handling

**Decision**: Allow deletion of bank-connected accounts; LinkedAccount record preserved with null account_id.

**Rationale**:
- User may want to remove account from budget without disconnecting bank
- LinkedAccount stays in bank connection (can re-link later)
- Follows principle of least surprise

**Edge cases handled**:
- Deleting bank-connected account: Works, sync continues but transactions go nowhere until re-linked
- Deleting during sync: Allowed, in-flight transactions will fail gracefully

### 4. Frontend Dialog Pattern

**Decision**: Copy `DisconnectConfirmDialog` pattern exactly for consistency.

**Rationale**:
- Proven pattern already in codebase
- Uses shadcn/ui AlertDialog (Constitution Principle VI)
- Handles loading, errors, and cancellation
- Destructive button styling matches design system

**Pattern elements**:
- AlertDialog with AlertDialogContent
- Warning icon (AlertTriangle) with yellow background
- Clear title identifying the item being deleted
- Bullet list of consequences
- Cancel and Delete buttons (Delete is destructive variant)
- Loading spinner during async operation

### 5. Transaction Count Display

**Decision**: Show transaction count in confirmation dialog.

**Rationale**:
- User should understand scope of deletion
- Spec FR-005 requires warning about transaction deletion
- Count provides concrete information

**Implementation**:
- Fetch transaction count when opening dialog
- Or pass from parent if already known
- Display: "X transactions will be permanently deleted"

## Unresolved Questions

None - all technical decisions are clear.

## Dependencies Verified

| Dependency | Status | Notes |
|------------|--------|-------|
| DELETE /api/accounts/{id} | EXISTS | backend/src/mybudget/api/accounts.py:90 |
| AccountService.delete_account | EXISTS | backend/src/mybudget/services/account_service.py:204 |
| AlertDialog component | EXISTS | frontend/src/components/ui/alert-dialog.tsx |
| DisconnectConfirmDialog | EXISTS | Pattern reference at frontend/src/components/DisconnectConfirmDialog.tsx |
| accountService.ts | EXISTS | Needs delete() method added |
