# Feature Specification: MyBudget MVP - Spending Targets

**Feature Branch**: `001-spending-targets-mvp`
**Created**: 2026-01-16
**Status**: Draft
**Input**: MVP for bank-account-only, sync-first, reconcile against statements, with easy spending targets as the first real feature

## User Scenarios & Testing *(mandatory)*

### User Story 0 - User Authentication (Priority: P0)

Users must be able to create an account and log in before accessing any budget features.

**Why this priority**: Authentication is the gateway to all other features - without logging in, users cannot access their accounts, transactions, or budget data.

**Independent Test**: User can register a new account, log in with credentials, access protected budget pages, and log out.

**Acceptance Scenarios**:

1. **Given** an unauthenticated visitor, **When** they access any budget page, **Then** they are redirected to the login page
2. **Given** the login page, **When** a new user clicks "Register", **Then** they see a registration form with email, password, and timezone fields
3. **Given** the registration form, **When** the user submits valid credentials, **Then** their account is created and they are automatically logged in
4. **Given** the login page, **When** a returning user enters valid email and password, **Then** they are authenticated and redirected to the dashboard
5. **Given** the login page, **When** a user enters invalid credentials, **Then** they see an error message and remain on the login page
6. **Given** an authenticated user, **When** they click "Log out", **Then** their session ends and they are redirected to the login page
7. **Given** an authenticated session, **When** the session expires (30 minutes of inactivity), **Then** the user is redirected to login on their next action

---

### User Story 1 - Set Up Bank Account and Sync Transactions (Priority: P1)

Users need to connect their bank accounts and import transactions before they can manage their budget.

**Why this priority**: This is foundational infrastructure - without synced transactions, no budgeting features work. This must be the absolute first capability.

**Independent Test**: User can connect a bank account, see imported transactions in the inbox, and approve/categorize them. The system correctly maintains account balances.

**Acceptance Scenarios**:

1. **Given** a new user with no accounts, **When** they add a checking account with a starting balance of €1,000, **Then** the account appears in their account list with the correct balance and "To Assign" shows €1,000
2. **Given** a connected bank account, **When** new transactions are imported from the bank, **Then** they appear in the transaction inbox awaiting approval
3. **Given** transactions in the inbox, **When** the user approves a transaction and assigns it to a category, **Then** the transaction moves to approved status, the category's "Activity" increases, and "Available" for that category decreases accordingly
4. **Given** multiple transactions from the same payee, **When** the user creates a categorization rule, **Then** future transactions from that payee are auto-categorized but still require approval

---

### User Story 2 - Organize Budget with Categories and Monthly View (Priority: P2)

Users need to organize their budget into meaningful categories and category groups to track spending across different areas of life.

**Why this priority**: Categories are required before spending targets can be set. This provides the structure for the budget.

**Independent Test**: User can create category groups (e.g., "Monthly Bills", "Daily Living"), add categories within groups (e.g., "Groceries", "Rent"), view the budget month view with all categories, and see accurate "Available" amounts per category.

**Acceptance Scenarios**:

1. **Given** a new budget, **When** the user creates a category group "Monthly Bills" and adds categories "Rent" (€800) and "Utilities" (€100), **Then** both categories appear in the budget month view under "Monthly Bills"
2. **Given** categories exist, **When** the user assigns €400 to "Groceries" from "To Assign", **Then** "Groceries" shows €400 Available and "To Assign" decreases by €400
3. **Given** a category with Available funds, **When** approved transactions reduce available funds below zero, **Then** the category shows negative available (overspent) in a warning state
4. **Given** the current month with assigned funds, **When** the user navigates to the next month, **Then** leftover Available amounts roll over to the new month and "To Assign" resets based on new account activity

---

### User Story 3 - Reconcile Account Against Statement (Priority: P3)

Users need to verify their budget matches their actual bank balance by reconciling against official bank statements.

**Why this priority**: Reconciliation ensures data integrity and catches discrepancies. While important, users can budget effectively without this initially.

**Independent Test**: User can enter a statement balance and date, mark transactions as cleared, and resolve any discrepancies with adjustment transactions.

**Acceptance Scenarios**:

1. **Given** a bank account with approved transactions, **When** the user starts reconciliation with statement balance €950 on Jan 31, **Then** the system shows all uncleared transactions and calculates the difference between statement balance and cleared balance
2. **Given** a reconciliation in progress, **When** the user marks transactions as cleared and the cleared balance matches the statement balance, **Then** the reconciliation completes successfully
3. **Given** a reconciliation with a €10 discrepancy, **When** the user creates an adjustment transaction, **Then** the discrepancy resolves and reconciliation completes

---

### User Story 4 - Set Category Spending Target (Priority: P4)

Users need to set spending intentions on categories to guide monthly funding decisions.

**Why this priority**: This is the first "smart budgeting" feature that provides value beyond basic transaction tracking. It's the foundation of the MyBudget experience.

**Independent Test**: User can set a Monthly Needed target (€400 for Groceries), a Target Balance (€1,000 Emergency Fund), and a Target by Date (€600 Insurance by Oct 31), and see accurate underfunded calculations for each.

**Acceptance Scenarios**:

1. **Given** a category "Groceries" with €0 assigned, **When** the user sets a Monthly Needed target of €400, **Then** the category shows "Underfunded €400" and displays a target badge
2. **Given** a category "Emergency Fund" with €300 available, **When** the user sets a Target Balance of €1,000, **Then** the category shows "Underfunded €700"
3. **Given** a category "Insurance" with €0 available and today is July 1, **When** the user sets a Target by Date of €600 by Oct 31, **Then** the system calculates 4 months remaining and suggests €150/month, showing "Underfunded €150"
4. **Given** an existing target, **When** the user edits the target amount or removes the target, **Then** underfunded calculations update immediately

---

### User Story 5 - View Funding Guidance and Fund Underfunded Categories (Priority: P5)

Users need a clear view of what categories need funding and the ability to fund them quickly.

**Why this priority**: This completes the "easy targets" workflow - seeing what needs funding and acting on it with minimal friction.

**Independent Test**: User can view the budget month screen showing total underfunded amount, filter/sort by underfunded categories, and use quick-fund buttons to meet targets.

**Acceptance Scenarios**:

1. **Given** categories with targets (Groceries €400 needed, Emergency Fund €700 underfunded), **When** the user opens the budget month view, **Then** the top bar shows "Underfunded total €1,100" and categories are marked with their underfunded amounts
2. **Given** "Groceries" with €250 funded and €150 underfunded, **When** the user taps "Fund Underfunded" on Groceries and has €500 in "To Assign", **Then** the system assigns €150, Groceries shows "Funded", and "To Assign" decreases to €350
3. **Given** "Groceries" with €300 underfunded and only €100 in "To Assign", **When** the user taps "Fund Underfunded", **Then** the system assigns €100 and shows "Still underfunded €200"
4. **Given** multiple underfunded categories and €1,000 in "To Assign", **When** the user taps "Fund All Underfunded", **Then** the system allocates funds in priority order (Target by Date nearest first, then Monthly Needed, then Target Balance) until "To Assign" reaches €0 or all targets are met

---

### User Story 6 - Month Rollover with Target Persistence (Priority: P6)

Users need targets to behave consistently across month boundaries so they can trust the funding guidance.

**Why this priority**: This ensures the budgeting system remains predictable and trustworthy over time. Critical for user confidence but only testable after implementing basic targets.

**Independent Test**: User with targets set can navigate to the next month and verify that Monthly Needed resets underfunded amounts, Target Balance maintains the same target, and Target by Date adjusts monthly suggestions based on remaining months.

**Acceptance Scenarios**:

1. **Given** "Groceries" Monthly Needed €400 with €50 leftover from previous month, **When** the new month begins, **Then** funded_this_month resets to €0, available shows €50, and underfunded shows €400 (not €350)
2. **Given** "Emergency Fund" Target Balance €1,000 with €900 available, **When** a €100 expense is approved in the new month, **Then** available drops to €800 and underfunded increases to €200
3. **Given** "Insurance" Target by Date €600 by Oct 31 with 3 months remaining (Aug, Sep, Oct) and €300 available, **When** September begins, **Then** months_left becomes 2, suggested_monthly becomes €150 (ceiling of €300 ÷ 2), and underfunded adjusts accordingly
4. **Given** "Insurance" Target by Date €600 by Oct 31, **When** October begins (target month), **Then** months_left = 1 and suggested_monthly = €600 - available

---

### Edge Cases

- **Insufficient To Assign for funding**: When user attempts to fund underfunded categories but "To Assign" is less than underfunded amount, allow partial funding up to available "To Assign" and display "Still underfunded €X" message
- **Negative available (overspending)**: When approved transactions cause a category's available to go negative, display in warning state (red/alert styling) but allow funding actions to cover the overspend by increasing assignments
- **Target by Date in current month**: When target date is in the current month, set months_left = 1 (not 0) to avoid division by zero and ensure suggested_monthly = needed_now
- **Target by Date in the past**: Validation prevents setting target dates in the past during target creation/editing
- **Editing target mid-month**: When user modifies target amount or type, recompute underfunded immediately and update UI
- **Category deletion with target**: When user attempts to delete a category with an active target, require confirmation and either remove target automatically or transfer it to another category
- **Zero or negative target amounts**: Validation requires target amount > 0 during creation/editing
- **Concurrent target changes**: When multiple browser tabs/devices are open, ensure updates to targets and assignments are synchronized (optimistic locking or last-write-wins with refresh)
- **Rounding for Target by Date**: Always round suggested_monthly up to the nearest cent (ceiling function) to ensure target is met on time
- **Month navigation with pending inbox transactions**: When user navigates between months with unapproved transactions, ensure "To Assign" only reflects approved transactions for accuracy

## Requirements *(mandatory)*

### Functional Requirements

**User Authentication**

- **FR-AUTH-001**: System MUST provide a login page with email and password fields
- **FR-AUTH-002**: System MUST provide a registration page with email, password, and timezone fields
- **FR-AUTH-003**: System MUST redirect unauthenticated users to the login page when accessing protected routes
- **FR-AUTH-004**: System MUST display clear error messages for invalid login attempts
- **FR-AUTH-005**: System MUST redirect users to the dashboard after successful login
- **FR-AUTH-006**: System MUST provide a logout action that ends the user session
- **FR-AUTH-007**: System MUST automatically expire sessions after 30 minutes of inactivity
- **FR-AUTH-008**: System MUST validate email format and password strength during registration
- **FR-AUTH-009**: System MUST prevent duplicate email registration with clear error message

**Account Management**

- **FR-001**: System MUST support checking and savings bank account types
- **FR-002**: System MUST allow users to add accounts with initial balances
- **FR-003**: System MUST maintain accurate account balances based on approved transactions
- **FR-004**: System MUST calculate "To Assign" as the sum of all account balances minus assigned category funds

**Transaction Management**

- **FR-005**: System MUST import transactions from bank sync into a transaction inbox
- **FR-006**: System MUST require user approval before transactions affect budget calculations
- **FR-007**: System MUST allow users to categorize transactions during approval
- **FR-008**: Users MUST be able to create categorization rules (payee → category mappings)
- **FR-009**: System MUST auto-categorize transactions matching rules but still require approval
- **FR-010**: System MUST track transaction state (pending in inbox, approved, cleared for reconciliation)

**Transaction Categorization Extensibility** *(ML-ready interface)*

- **FR-043**: System MUST track categorization source for each transaction: MANUAL (user-assigned), RULE (matched by categorization rule), or ML_SUGGESTED (future: machine learning suggestion)
- **FR-044**: System MUST support an optional confidence score (0.0-1.0) for categorization suggestions, nullable for MANUAL and RULE sources
- **FR-045**: System MUST support batch approval of multiple transactions in the inbox with the same suggested category

**Transaction Search and Filtering**

- **FR-046**: System MUST provide transaction search by payee name (partial match, case-insensitive)
- **FR-047**: System MUST provide transaction search by memo content (partial match, case-insensitive)
- **FR-048**: System MUST provide transaction filtering by date range (start date, end date)
- **FR-049**: System MUST provide transaction filtering by amount range (minimum, maximum)
- **FR-050**: System MUST provide transaction filtering by category (including "uncategorized" option)
- **FR-051**: System MUST provide transaction filtering by account
- **FR-052**: System MUST provide transaction filtering by status (inbox, approved, cleared)
- **FR-053**: System MUST display uncategorized transaction count indicator in navigation (badge showing count of inbox transactions awaiting categorization)

**Category Management**

- **FR-011**: System MUST support category groups (e.g., "Monthly Bills", "Daily Living")
- **FR-012**: System MUST support individual categories within groups
- **FR-013**: System MUST track per-category per-month values: Available, Funded this month, Activity
- **FR-014**: System MUST allow users to assign funds from "To Assign" to categories
- **FR-015**: System MUST support negative available (overspending) with visual warning indicators

**Monthly Budget View**

- **FR-016**: System MUST display budget data in monthly views
- **FR-017**: System MUST allow navigation between past and future months
- **FR-018**: System MUST roll over leftover category Available amounts to the next month
- **FR-019**: System MUST reset "Funded this month" to €0 at month boundaries
- **FR-020**: System MUST display "To Assign" amount derived from account balances minus category assignments

**Reconciliation**

- **FR-021**: System MUST allow users to reconcile accounts against statement balances and dates
- **FR-022**: System MUST filter transactions by cleared/uncleared status during reconciliation
- **FR-023**: System MUST calculate discrepancy between statement balance and cleared balance
- **FR-024**: System MUST allow creation of adjustment transactions to resolve discrepancies
- **FR-025**: System MUST mark reconciliation as complete when cleared balance matches statement balance

**Spending Targets**

- **FR-026**: System MUST support three target types: Monthly Needed, Target Balance, Target by Date
- **FR-027**: System MUST validate target amounts > 0 and target dates not in the past
- **FR-028**: System MUST calculate underfunded amounts per target type:
  - Monthly Needed: `max(0, target_amount - funded_this_month)`
  - Target Balance: `max(0, target_amount - available_now)`
  - Target by Date: `max(0, ceiling((target_amount - available_now) / months_left) - funded_this_month)` where months_left includes current month
- **FR-029**: System MUST display target badge on categories with active targets
- **FR-030**: System MUST show "Underfunded €X", "Funded", or overfunded status per category
- **FR-031**: System MUST allow users to edit or remove targets with immediate recalculation

**Funding Guidance**

- **FR-032**: System MUST display total underfunded amount across all targeted categories
- **FR-033**: System MUST provide filtering/sorting by underfunded status
- **FR-034**: System MUST provide "Fund Underfunded" action per category
- **FR-035**: System MUST provide global "Fund All Underfunded" action
- **FR-036**: System MUST allocate funds in priority order: Target by Date (nearest first), Monthly Needed, Target Balance
- **FR-037**: System MUST record all funding assignments with timestamp in audit trail
- **FR-038**: System MUST handle partial funding when "To Assign" is insufficient

**Month Rollover Behavior**

- **FR-039**: System MUST reset funded_this_month to €0 for all categories at month boundaries
- **FR-040**: System MUST recalculate underfunded amounts for all targets when viewing different months
- **FR-041**: System MUST adjust Target by Date calculations based on months_left to target date
- **FR-042**: System MUST preserve target configurations across month boundaries

### Key Entities

- **Account**: Represents a bank checking or savings account; attributes include account name, type (checking/savings), current balance
- **Transaction**: Represents a financial transaction; attributes include date, payee, amount, account, category (nullable until approved), state (inbox/approved/cleared), memo, categorization_source (MANUAL/RULE/ML_SUGGESTED), confidence_score (0.0-1.0, nullable)
- **CategoryGroup**: Organizational container for categories; attributes include group name, display order
- **Category**: Budget category for tracking spending; attributes include category name, parent group, monthly values (available, funded_this_month, activity)
- **CategoryTarget**: Spending target configuration for a category; attributes include target type (Monthly Needed/Target Balance/Target by Date), target amount, target date (nullable), category reference
- **Assignment**: Record of funds assigned to a category; attributes include category, amount, month, timestamp (for audit trail)
- **CategorizationRule**: Auto-categorization rule; attributes include payee pattern, target category
- **Reconciliation**: Account reconciliation session; attributes include account, statement balance, statement date, status (in progress/completed), adjustment transaction (nullable)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-AUTH-001**: New users can complete registration and reach the dashboard in under 30 seconds
- **SC-AUTH-002**: Returning users can log in and reach the dashboard in under 10 seconds
- **SC-AUTH-003**: 95% of login attempts with valid credentials succeed on first try
- **SC-001**: Users can complete the full workflow from connecting a bank account to seeing imported transactions in under 2 minutes
- **SC-002**: Users can create a category, set a spending target, and fund it to target in under 60 seconds
- **SC-003**: Users can navigate from "new month" to "all targets fully funded" in under 60 seconds using "Fund All Underfunded"
- **SC-004**: System maintains budget balance integrity: sum of all category Available amounts + To Assign always equals total account balances (verified during reconciliation)
- **SC-005**: Underfunded calculations remain stable and predictable - no unexpected jumps when navigating between months or approving transactions
- **SC-006**: 90% of users successfully complete their first reconciliation without requiring support
- **SC-007**: Users understand target types and can set appropriate targets for 3+ categories within first session
- **SC-008**: Categorization rules reduce manual categorization effort by at least 40% after first month of use
- **SC-009**: Users can find specific transactions using search in under 5 seconds
- **SC-010**: Users can batch-approve 10+ similarly-categorized transactions in under 10 seconds
- **SC-011**: Uncategorized transaction count badge updates within 2 seconds of inbox changes

## Assumptions

1. **Bank sync mechanism**: Assumed integration with standard banking APIs (Open Banking, Plaid, or similar) for transaction import - implementation details deferred to technical planning
2. **Currency**: Defaulting to EUR (€) as shown in examples; multi-currency support is out of scope for MVP
3. **Timezone handling**: All dates/times use user's local timezone; month boundaries follow calendar months in user's timezone
4. **Single user**: MVP assumes single-user budgets; multi-user/shared budgets explicitly out of scope
5. **Transaction approval model**: All imported transactions require explicit user approval before affecting budget; fully automatic import without review is considered unsafe for MVP
6. **Target persistence**: Targets persist month-to-month until explicitly removed by user; no automatic expiration
7. **Funding priority**: Default priority order (Target by Date → Monthly Needed → Target Balance) is fixed in MVP; custom prioritization deferred to future iteration
8. **Reconciliation frequency**: Users expected to reconcile monthly aligned with statement cycles; system does not enforce reconciliation cadence
9. **Data retention**: All transaction history retained indefinitely; no automatic archival or deletion
10. **Performance baseline**: System expected to handle typical personal finance scale (1-5 accounts, 100-500 transactions/month, 20-50 categories) with response times under 2 seconds for all operations

## Out of Scope (Explicit Exclusions)

- Cash accounts and manual transaction entry flows (beyond adjustment transactions)
- Credit card-specific features (payment tracking, credit limit management, interest calculation)
- Advanced reporting, charts, and analytics beyond basic budget month view
- Shared budgets, multi-user access, or collaboration features
- Investment accounts, loans, mortgages, or complex debt tracking
- Automated savings/funding schedules
- Bill reminders and payment due dates
- Receipt attachments and document management
- Budget templates or pre-configured category structures
- Mobile apps (MVP can be web-only or specify platform)
- Data export to third-party tools (Mint, YNAB, etc.)
- Historical trend analysis or year-over-year comparisons
