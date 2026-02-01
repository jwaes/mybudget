# Feature Specification: Account Deletion

**Feature Branch**: `004-account-deletion`
**Created**: 2026-02-01
**Status**: Draft
**Input**: User description: "Delete account with confirmation dialog"

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Delete Manual Account (Priority: P1)

A user wants to remove an account they no longer use from their budget. They click a delete option for the account, see a confirmation dialog warning them about the consequences, and confirm the deletion.

**Why this priority**: Account deletion is fundamental account management functionality. Users need to clean up accounts they no longer use to maintain an organized budget.

**Independent Test**: Can be fully tested by creating an account, then deleting it via the UI, and verifying it no longer appears in the account list.

**Acceptance Scenarios**:

1. **Given** a user has a manual (non-bank-connected) account, **When** they click the delete option, **Then** they see a confirmation dialog
2. **Given** the confirmation dialog is displayed, **When** the user confirms deletion, **Then** the account is removed from the account list
3. **Given** the confirmation dialog is displayed, **When** the user cancels, **Then** the account remains unchanged
4. **Given** the account has associated transactions, **When** viewing the confirmation dialog, **Then** the user is warned that transactions will be deleted

---

### User Story 2 - Delete Bank-Connected Account (Priority: P2)

A user wants to delete an account that was created from a bank connection. The system handles this by removing the account from their budget while preserving the bank connection if other accounts exist.

**Why this priority**: Bank-connected accounts have additional complexity since they're linked to external bank connections. Users may want to remove specific accounts without disconnecting entirely.

**Independent Test**: Can be fully tested by deleting a bank-connected account and verifying it's removed while the bank connection remains if other accounts exist.

**Acceptance Scenarios**:

1. **Given** a bank-connected account, **When** the user clicks delete, **Then** they see a confirmation dialog explaining this will unlink the account
2. **Given** the bank connection has multiple accounts, **When** the user deletes one account, **Then** only that account is removed (bank connection and other accounts remain)
3. **Given** the bank connection has only one account, **When** the user deletes it, **Then** the account is removed (bank connection handling follows existing disconnect flow from 003)

---

### Edge Cases

- What happens when trying to delete an account while a sync is in progress? The system allows deletion; any in-progress sync will complete but new transactions won't be associated.
- What happens to transactions already in the inbox from this account? Inbox transactions are deleted with the account.
- What happens to categorized transactions from this account? All transactions belonging to the account are deleted.
- What happens if the user tries to delete their last account? The system allows it - users may want to start fresh.
- What happens if deletion fails due to a network error? The user sees an error message and can retry.

---

## Requirements *(mandatory)*

### Functional Requirements

**Delete Option**

- **FR-001**: System MUST provide a delete option for each account in the account list
- **FR-002**: Delete option MUST be accessible via a button, icon, or menu in the account row

**Confirmation Dialog**

- **FR-003**: System MUST display a confirmation dialog before deleting any account
- **FR-004**: Confirmation dialog MUST clearly identify which account will be deleted
- **FR-005**: Confirmation dialog MUST warn users that associated transactions will be deleted
- **FR-006**: Confirmation dialog MUST provide "Cancel" and "Delete" actions
- **FR-007**: The "Delete" action MUST be visually distinct (destructive styling) to prevent accidental clicks

**Deletion Behavior**

- **FR-008**: System MUST remove the account from the database upon confirmed deletion
- **FR-009**: System MUST delete all transactions associated with the deleted account
- **FR-010**: System MUST update the account list immediately after successful deletion
- **FR-011**: System MUST show a success message after deletion completes
- **FR-012**: System MUST show an error message if deletion fails

**Bank-Connected Accounts**

- **FR-013**: For bank-connected accounts, system MUST unlink the account from the bank connection
- **FR-014**: System MUST preserve the bank connection if other linked accounts exist

### Key Entities

- **Account**: Existing entity representing a financial account; deletion removes the account and cascades to related transactions
- **Transaction**: Existing entity; transactions are deleted when their parent account is deleted
- **LinkedAccount**: Existing entity (from 003); link is removed when account is deleted

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can delete an account in under 10 seconds (including confirmation)
- **SC-002**: Zero accidental deletions due to confirmation dialog protecting user actions
- **SC-003**: 100% of deletion attempts either succeed with confirmation or fail with clear error message
- **SC-004**: Account list updates immediately after deletion (no page refresh required)

---

## Assumptions

- The backend already supports account deletion via DELETE /api/accounts/{id} endpoint
- Transaction cascade deletion is handled at the database level
- Users understand that deletion is permanent and cannot be undone
- The confirmation dialog pattern follows existing app conventions (e.g., disconnect bank dialog from 003)

---

## Dependencies

- Existing account management backend API (from 001-spending-targets-mvp)
- Existing frontend account list component
- Existing AlertDialog component from shadcn/ui (from 002-shadcn-ui-migration)
