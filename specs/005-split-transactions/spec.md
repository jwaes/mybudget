# Feature Specification: Split Transactions

**Feature Branch**: `005-split-transactions`
**Created**: 2026-01-18
**Status**: Draft
**Input**: Split Transactions - Split single transaction across multiple categories. Features: Split a transaction into 2+ category allocations, maintain original transaction integrity (total of splits equals original amount), display split breakdown in transaction list, support editing split allocations, support unsplitting (reverting to single category).

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Split a Transaction into Multiple Categories (Priority: P1)

A user has a transaction (e.g., a grocery store purchase of $150) that contains items belonging to different budget categories (e.g., $100 groceries, $30 household supplies, $20 personal care). They split the single transaction into multiple category allocations while maintaining the original total.

**Why this priority**: This is the core functionality - without splitting, users cannot accurately track spending when a single purchase spans multiple categories.

**Independent Test**: Can be fully tested by splitting a transaction and verifying each split appears with the correct category and amount, and that the splits sum to the original amount.

**Acceptance Scenarios**:

1. **Given** a user has an uncategorized transaction for $150, **When** they click "Split Transaction", **Then** they see a split editor with fields to add multiple category allocations
2. **Given** the split editor is open, **When** the user adds allocations for Groceries ($100), Household ($30), and Personal Care ($20), **Then** the system shows the remaining amount as $0 (fully allocated)
3. **Given** all splits are entered and the total equals the original amount, **When** the user saves, **Then** the transaction is marked as split and each allocation is recorded
4. **Given** the splits do not equal the original amount, **When** the user tries to save, **Then** the system shows an error indicating the discrepancy

---

### User Story 2 - View Split Breakdown in Transaction List (Priority: P1)

A user viewing their transaction list can easily see which transactions are split and view the breakdown of categories without opening each transaction.

**Why this priority**: Users need visibility into split transactions to understand their spending at a glance without extra clicks.

**Independent Test**: Can be fully tested by viewing a transaction list containing split transactions and verifying the split indicator and breakdown are visible.

**Acceptance Scenarios**:

1. **Given** a transaction has been split, **When** viewing the transaction list, **Then** the transaction shows a visual indicator that it is split
2. **Given** a split transaction is in the list, **When** the user expands or hovers over it, **Then** they see all category allocations with their amounts
3. **Given** a split transaction is in the list, **When** viewing the category column, **Then** it shows "Multiple Categories" or a summary like "Groceries + 2 more"

---

### User Story 3 - Edit Split Allocations (Priority: P2)

A user realizes they made an error in how they split a transaction and needs to adjust the allocations - changing amounts or categories while maintaining the original total.

**Why this priority**: Users frequently need to correct mistakes or adjust allocations as they better understand their spending.

**Independent Test**: Can be fully tested by editing an existing split transaction and verifying the changes are saved correctly.

**Acceptance Scenarios**:

1. **Given** a split transaction, **When** the user clicks "Edit Split", **Then** they see the current allocations in an editable form
2. **Given** the split editor is open with existing allocations, **When** the user changes an amount from $100 to $80 for Groceries, **Then** the remaining unallocated amount updates to show $20
3. **Given** the user has modified allocations, **When** they save and the total equals the original, **Then** the updated splits are saved
4. **Given** the user is editing splits, **When** they add a new category allocation, **Then** the new allocation is added to the existing splits

---

### User Story 4 - Unsplit a Transaction (Priority: P2)

A user decides they no longer want a transaction split and wants to revert it to a single category assignment.

**Why this priority**: Users need the ability to undo splits, whether due to errors or changing how they want to categorize.

**Independent Test**: Can be fully tested by unsplitting a transaction and verifying it reverts to a single-category transaction.

**Acceptance Scenarios**:

1. **Given** a split transaction, **When** the user clicks "Unsplit", **Then** they see a confirmation dialog explaining the action
2. **Given** the user confirms unsplit, **When** the action completes, **Then** all split allocations are removed and the transaction becomes a single uncategorized transaction
3. **Given** a transaction has been unsplit, **When** viewing the transaction list, **Then** the split indicator is removed and the transaction can be categorized normally

---

### User Story 5 - Delete a Single Split Allocation (Priority: P3)

A user wants to remove one allocation from a split transaction without unsplitting entirely, redistributing that amount to other categories.

**Why this priority**: Provides finer control over split management without requiring a complete redo.

**Independent Test**: Can be fully tested by deleting one allocation from a split and verifying the remaining allocations are intact.

**Acceptance Scenarios**:

1. **Given** a split transaction with 3 allocations, **When** the user deletes one allocation, **Then** the remaining amount shows as unallocated
2. **Given** an allocation is deleted and amount is unallocated, **When** the user distributes the amount to remaining categories and saves, **Then** the split is updated with the new allocations
3. **Given** a split has only 2 allocations, **When** the user deletes one, **Then** the system prompts to either add another split or unsplit entirely

---

### Edge Cases

- What happens when a user tries to split a transaction to just one category? The system requires at least 2 allocations for a split; otherwise, suggest regular categorization.
- What happens when a split allocation amount is zero? The system prevents zero-amount allocations and shows a validation error.
- What happens when a user enters amounts that exceed the original transaction? The system shows a clear error and prevents saving.
- What happens when rounding causes splits to not exactly equal the original (e.g., $100 split 3 ways)? The system allows a 1-cent variance and assigns the remainder to the last allocation.
- What happens when a split transaction is from a bank sync and a new sync arrives? The original transaction is not modified; splits are preserved.
- What happens when the user wants to split an already-categorized transaction? The existing category becomes the first allocation with the full amount, which can then be adjusted.

---

## Requirements *(mandatory)*

### Functional Requirements

**Creating Splits**

- **FR-001**: System MUST allow users to split a single transaction into 2 or more category allocations
- **FR-002**: System MUST require the sum of all split allocations to equal the original transaction amount
- **FR-003**: System MUST prevent saving splits that do not balance (with allowance for 1-cent rounding variance)
- **FR-004**: System MUST show the remaining unallocated amount in real-time as users enter splits
- **FR-005**: System MUST allow a maximum of 10 split allocations per transaction
- **FR-006**: System MUST allow splitting transactions regardless of their current state (inbox, approved, cleared)

**Displaying Splits**

- **FR-007**: System MUST display a visual indicator on split transactions in all transaction views
- **FR-008**: System MUST show the full breakdown of categories when a user expands or inspects a split transaction
- **FR-009**: System MUST display "Multiple Categories" or similar summary text in compact list views
- **FR-010**: System MUST include all split allocations in category spending reports with their respective amounts

**Editing Splits**

- **FR-011**: System MUST allow users to edit existing split allocations
- **FR-012**: System MUST allow users to add new allocations to an existing split
- **FR-013**: System MUST allow users to remove allocations from an existing split (minimum 2 must remain)
- **FR-014**: System MUST recalculate and display remaining unallocated amount during editing

**Unsplitting**

- **FR-015**: System MUST allow users to unsplit a transaction, reverting to a single uncategorized transaction
- **FR-016**: System MUST require confirmation before unsplitting
- **FR-017**: System MUST remove all split allocation records when a transaction is unsplit

**Data Integrity**

- **FR-018**: System MUST maintain the original transaction amount unchanged regardless of splits
- **FR-019**: System MUST preserve splits when transactions are synced from bank connections
- **FR-020**: System MUST include split transactions correctly in all budget calculations and reports

### Key Entities

- **Transaction**: Extended to include a "split" flag indicating whether the transaction has multiple category allocations; original amount remains unchanged
- **SplitAllocation**: Represents one portion of a split transaction; attributes include parent transaction reference, category, amount, optional memo for the allocation
- **SplitGroup**: Logical grouping of allocations for a single transaction; ensures total always equals parent transaction amount

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can split a transaction into multiple categories in under 1 minute
- **SC-002**: 100% of split transactions have allocations that sum exactly to the original amount (within 1-cent tolerance)
- **SC-003**: Users can identify split transactions in the transaction list within 2 seconds (visual indicator is clear)
- **SC-004**: Budget reports accurately reflect split allocations (each split amount appears in its respective category)
- **SC-005**: 90% of users who attempt to split a transaction successfully complete the action on first try
- **SC-006**: Users can unsplit a transaction in under 30 seconds

---

## Assumptions

- Users have categories defined before splitting transactions
- Split transactions are relatively rare (estimated <10% of all transactions)
- Most splits will have 2-3 allocations; 10-allocation limit is sufficient
- Splits should be preserved across bank sync operations
- A 1-cent rounding variance is acceptable for splits (e.g., $100 split 3 ways = $33.33 + $33.33 + $33.34)
- Memo/notes can optionally be added to individual split allocations for clarity

---

## Dependencies

- Existing transaction system (from 001-spending-targets-mvp) for base transaction handling
- Existing category system (from 001-spending-targets-mvp) for category selection
- Existing budget calculations (from 001-spending-targets-mvp) must be updated to handle split allocations
- Reporting system (from 004-reporting) must correctly aggregate split amounts by category
