# Quickstart: Account Deletion

**Feature**: 004-account-deletion
**Estimated Effort**: 2-4 hours

## Overview

Add a delete button to accounts with a confirmation dialog. Backend API already exists.

## Prerequisites

- Backend running with existing `/api/accounts/{id}` DELETE endpoint
- Frontend with shadcn/ui AlertDialog component installed

## Implementation Steps

### Step 1: Add delete method to accountService (5 min)

```typescript
// frontend/src/services/accountService.ts
async delete(id: string): Promise<void> {
  await api.delete(`/accounts/${id}`)
}
```

### Step 2: Create DeleteAccountDialog component (30 min)

Copy pattern from `DisconnectConfirmDialog.tsx`:

```typescript
// frontend/src/components/DeleteAccountDialog.tsx
interface DeleteAccountDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  account: { id: string; name: string; transactionCount?: number }
  onDeleted?: () => void
}
```

Key elements:
- AlertDialog from shadcn/ui
- Warning about permanent deletion
- Show transaction count if available
- Destructive button styling
- Loading state during deletion

### Step 3: Add delete button to Accounts page (15 min)

Options:
- Trash icon button in account row
- Dropdown menu with Delete option
- Both

Connect to DeleteAccountDialog.

### Step 4: Write tests (30-60 min)

Component tests for DeleteAccountDialog:
- Renders with account name
- Shows transaction count warning
- Calls onDeleted after successful deletion
- Shows error on failure
- Cancel closes dialog without deleting

## Testing Checklist

- [ ] Can delete manual account
- [ ] Transactions are removed after deletion
- [ ] Can delete bank-connected account
- [ ] LinkedAccount preserved (can re-link)
- [ ] Cancel button works
- [ ] Error handling works
- [ ] Success message shown

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/services/accountService.ts` | MODIFY | Add delete() method |
| `frontend/src/components/DeleteAccountDialog.tsx` | CREATE | Confirmation dialog |
| `frontend/src/pages/Accounts.tsx` | MODIFY | Add delete button |
| `frontend/tests/components/DeleteAccountDialog.test.tsx` | CREATE | Component tests |
