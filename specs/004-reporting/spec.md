# Feature Specification: Reporting

**Feature Branch**: `004-reporting`
**Created**: 2026-01-18
**Status**: Draft
**Input**: Reporting - Financial reporting and analytics. Features: Category spending trends over time (weekly, monthly, quarterly views), budget health dashboard showing over/under budget visualization, net worth tracking across all accounts, CSV export of transactions and reports, date range selection for all reports.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Spending Trends by Category (Priority: P1)

A user wants to understand their spending patterns over time to identify where their money is going. They navigate to the reports section and view a visual breakdown of spending by category, with the ability to switch between weekly, monthly, and quarterly time periods.

**Why this priority**: Understanding spending patterns is the core value of financial reporting - it helps users make informed decisions about their budget and identify areas to cut back.

**Independent Test**: Can be fully tested by viewing the spending trends report and verifying category data matches actual transaction totals for the selected period.

**Acceptance Scenarios**:

1. **Given** a user has categorized transactions, **When** they view the spending trends report, **Then** they see a visual chart showing spending by category
2. **Given** the spending trends report is displayed, **When** the user selects "Monthly" view, **Then** the chart updates to show monthly aggregations
3. **Given** the spending trends report is displayed, **When** the user selects a specific category, **Then** they see detailed breakdown of that category's transactions
4. **Given** a user selects a custom date range, **When** they apply the filter, **Then** the chart updates to show only spending within that range

---

### User Story 2 - View Budget Health Dashboard (Priority: P1)

A user wants to see at a glance how their spending compares to their budget targets. They view a dashboard that shows which categories are on track, over budget, or under budget with clear visual indicators.

**Why this priority**: Budget health visualization is essential for the YNAB-style approach - users need to quickly see if they're staying within their planned spending.

**Independent Test**: Can be fully tested by viewing the budget health dashboard and verifying category status indicators match the relationship between spending and budget targets.

**Acceptance Scenarios**:

1. **Given** a user has budget targets set, **When** they view the budget health dashboard, **Then** they see all categories with visual indicators (green/yellow/red) showing budget status
2. **Given** a category is over budget, **When** viewing the dashboard, **Then** that category shows a red indicator with the overage amount
3. **Given** a category is under budget by more than 20%, **When** viewing the dashboard, **Then** that category shows a green indicator
4. **Given** a category is within 10% of its budget, **When** viewing the dashboard, **Then** that category shows a yellow "caution" indicator

---

### User Story 3 - Track Net Worth Over Time (Priority: P2)

A user wants to see their overall financial picture by tracking their net worth (total assets minus liabilities) over time. They view a chart showing net worth progression across months.

**Why this priority**: Net worth tracking provides the "big picture" view that complements detailed budget tracking.

**Independent Test**: Can be fully tested by viewing the net worth report and verifying the total matches the sum of all account balances.

**Acceptance Scenarios**:

1. **Given** a user has multiple accounts, **When** they view the net worth report, **Then** they see a line chart showing net worth over time
2. **Given** the user has checking and credit card accounts, **When** viewing net worth, **Then** checking adds to net worth and credit card balances subtract from it
3. **Given** the user selects a specific month, **When** clicking on the data point, **Then** they see a breakdown of assets and liabilities for that month
4. **Given** bank-connected accounts have synced, **When** viewing net worth, **Then** the balances from connected accounts are included in the calculation

---

### User Story 4 - Export Data to CSV (Priority: P2)

A user wants to export their financial data for use in external tools, tax preparation, or personal record-keeping. They can export transactions and report summaries to CSV format.

**Why this priority**: Data portability is important for user trust and enables integration with other financial tools.

**Independent Test**: Can be fully tested by exporting data and opening the CSV in a spreadsheet application to verify accuracy.

**Acceptance Scenarios**:

1. **Given** a user is viewing any report, **When** they click "Export to CSV", **Then** a CSV file downloads containing the report data
2. **Given** a user is on the transactions page, **When** they click "Export Transactions", **Then** they can select a date range and download matching transactions
3. **Given** a user exports transactions, **When** they open the CSV, **Then** it contains columns for date, payee, category, amount, account, and memo
4. **Given** a user exports with a date range filter, **When** the export completes, **Then** only transactions within that range are included

---

### User Story 5 - Filter Reports by Date Range (Priority: P2)

A user wants to analyze their finances for a specific time period. They can select custom date ranges for any report view.

**Why this priority**: Date filtering is foundational for all reporting - users need to zoom in on specific periods for analysis.

**Independent Test**: Can be fully tested by applying date filters and verifying only data within the range is displayed.

**Acceptance Scenarios**:

1. **Given** a user is viewing any report, **When** they click the date range selector, **Then** they see preset options (This Month, Last Month, This Quarter, This Year, Custom)
2. **Given** the user selects "Custom", **When** they enter start and end dates, **Then** the report updates to show only that period
3. **Given** a date range is applied, **When** switching between reports, **Then** the date range persists across report views
4. **Given** a user selects "Last Month", **When** the report updates, **Then** it shows data from the first to last day of the previous calendar month

---

### User Story 6 - View Income vs Expenses Summary (Priority: P3)

A user wants to see a simple summary of their total income versus expenses for a period to understand if they're spending more than they earn.

**Why this priority**: This is a fundamental financial health indicator that complements category-level spending analysis.

**Independent Test**: Can be fully tested by viewing the summary and verifying income and expense totals match transaction sums.

**Acceptance Scenarios**:

1. **Given** a user has income and expense transactions, **When** they view the income vs expenses summary, **Then** they see total income, total expenses, and the difference
2. **Given** expenses exceed income, **When** viewing the summary, **Then** the difference is shown in red as a negative number
3. **Given** income exceeds expenses, **When** viewing the summary, **Then** the difference is shown in green as savings
4. **Given** a date range is selected, **When** viewing the summary, **Then** only transactions within that range contribute to the totals

---

### Edge Cases

- What happens when a report is viewed with no data? Display an empty state message encouraging the user to add transactions.
- What happens when exporting a large dataset (10,000+ transactions)? Show a progress indicator and allow export to continue in the background.
- What happens when accounts have different currencies? Display a note about currency mixing and show amounts in their original currencies.
- What happens when viewing net worth before any accounts existed? Show a flat line at zero with a message about when tracking began.
- What happens when a category has a target in one month but not another? Show the target only for months where it was active.
- What happens when a transaction is uncategorized? Group uncategorized transactions in a separate "Uncategorized" category in reports.

---

## Requirements *(mandatory)*

### Functional Requirements

**Spending Trends**

- **FR-001**: System MUST display spending by category in a visual chart format
- **FR-002**: System MUST support viewing spending in weekly, monthly, and quarterly aggregations
- **FR-003**: System MUST allow drilling down into a category to see individual transactions
- **FR-004**: System MUST show comparison to previous period (e.g., this month vs last month)
- **FR-005**: System MUST display uncategorized spending as a separate category in reports

**Budget Health Dashboard**

- **FR-006**: System MUST display all budget categories with visual status indicators
- **FR-007**: System MUST use color coding: green for under budget, yellow for near limit, red for over budget
- **FR-008**: System MUST show the actual amount spent vs budgeted amount for each category
- **FR-009**: System MUST calculate percentage of budget used for each category
- **FR-010**: System MUST highlight categories that need attention (over budget or near limit)

**Net Worth Tracking**

- **FR-011**: System MUST calculate net worth as total assets minus total liabilities
- **FR-012**: System MUST track net worth changes over time with monthly data points
- **FR-013**: System MUST categorize accounts as assets (checking, savings) or liabilities (credit cards)
- **FR-014**: System MUST include bank-connected account balances in net worth calculation
- **FR-015**: System MUST show breakdown of assets and liabilities when viewing a specific time point

**Data Export**

- **FR-016**: System MUST export transaction data to CSV format
- **FR-017**: System MUST export report summaries to CSV format
- **FR-018**: System MUST include all relevant fields in transaction exports (date, payee, category, amount, account, memo)
- **FR-019**: System MUST allow filtering exports by date range
- **FR-020**: System MUST allow filtering exports by account or category
- **FR-021**: System MUST handle large exports (10,000+ rows) without timeout

**Date Range Selection**

- **FR-022**: System MUST provide preset date range options: This Month, Last Month, This Quarter, Last Quarter, This Year, Last Year
- **FR-023**: System MUST allow custom date range selection with start and end dates
- **FR-024**: System MUST apply date range filters to all report views
- **FR-025**: System MUST persist selected date range during a session
- **FR-026**: System MUST default to "This Month" when accessing reports

**Income vs Expenses**

- **FR-027**: System MUST calculate total income from transactions in income categories
- **FR-028**: System MUST calculate total expenses from transactions in expense categories
- **FR-029**: System MUST display the difference (savings or deficit)
- **FR-030**: System MUST show trends in income vs expenses over time

### Key Entities

- **ReportPeriod**: Represents a time period for report aggregation; attributes include start date, end date, period type (weekly/monthly/quarterly/yearly)
- **CategorySpending**: Represents aggregated spending for a category in a period; attributes include category, total amount, transaction count, percentage of total spending
- **BudgetStatus**: Represents a category's budget health; attributes include category, budgeted amount, actual spent, remaining, percentage used, status (on track/warning/over)
- **NetWorthSnapshot**: Represents net worth at a point in time; attributes include date, total assets, total liabilities, net worth, change from previous period

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view their spending trends within 3 seconds of navigation
- **SC-002**: 90% of users can identify their top spending category within 10 seconds of viewing reports
- **SC-003**: Budget health status is accurate to within real-time transaction data (refreshes within 1 minute of new transactions)
- **SC-004**: CSV exports of up to 1,000 transactions complete in under 5 seconds
- **SC-005**: Users can apply date range filters and see updated results in under 2 seconds
- **SC-006**: 80% of users access reports at least once per month after initial setup
- **SC-007**: Net worth calculations match manual verification with 100% accuracy

---

## Assumptions

- Users have categorized transactions to enable meaningful category reports
- Users have budget targets set for budget health dashboard to be useful
- Account types (checking, savings, credit card) correctly indicate asset vs liability
- Historical transaction data is available for trend analysis
- Report calculations use approved (non-inbox) transactions only
- Currency is consistent across accounts (single-currency budgeting assumed initially)
- Monthly snapshots are sufficient granularity for net worth tracking

---

## Dependencies

- Existing transaction system (from 001-spending-targets-mvp) for spending data
- Existing budget/target system (from 001-spending-targets-mvp) for budget health calculations
- Existing account system (from 001-spending-targets-mvp) for net worth tracking
- Bank connection sync (from 003-bank-feed-adapter) for real-time account balances
