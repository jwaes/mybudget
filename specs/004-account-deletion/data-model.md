# Data Model: Account Deletion

**Feature**: 004-account-deletion
**Date**: 2026-02-01

## Entity Changes

### No New Entities

This feature uses existing entities only.

### Affected Entities

#### Account (existing)

No schema changes. Deletion behavior:

```
Account deletion → CASCADE to:
  - Transaction (all transactions for account deleted)
  - Reconciliation (all reconciliations for account deleted)

Account deletion → SET NULL on:
  - LinkedAccount.account_id (link broken, record preserved)
```

#### Transaction (existing)

No schema changes. Automatically deleted when parent Account is deleted due to:

```python
account_id: Mapped[UUID] = mapped_column(
    ForeignKey("accounts.id", ondelete="CASCADE"),
)
```

#### LinkedAccount (existing)

No schema changes. When linked Account is deleted:

```python
account_id: Mapped[UUID | None] = mapped_column(
    ForeignKey("accounts.id", ondelete="SET NULL"),
)
```

The LinkedAccount record remains (preserving bank connection), but `account_id` becomes NULL.

## State Transitions

### Account Deletion Flow

```
[Account Exists]
    │
    ▼ User clicks Delete
[Confirmation Dialog Shown]
    │
    ├─ User clicks Cancel → [Account Exists] (no change)
    │
    └─ User clicks Delete
        │
        ▼
[Deletion In Progress]
    │
    ├─ Success → [Account Deleted]
    │              ├─ Transactions: CASCADE deleted
    │              └─ LinkedAccount.account_id: SET NULL
    │
    └─ Failure → [Error Displayed] → [Account Exists]
```

## Validation Rules

### Pre-deletion Checks

1. **Ownership**: Account must belong to authenticated user
2. **Existence**: Account must exist (404 if not found)

### No Blocking Conditions

Per spec edge cases, deletion is always allowed:
- Even if account is the user's last account
- Even if sync is in progress
- Even if account has transactions in any state
