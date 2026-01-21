# Feature Specification: Bank Feed Adapter

**Feature Branch**: `003-bank-feed-adapter`
**Created**: 2026-01-18
**Updated**: 2026-01-21
**Status**: In Progress
**Input**: Bank Feed Adapter - Provider-agnostic bank connection interface. Supported providers: GoCardless Bank Account Data (Nordigen) and EnableBanking for AIS. Features: OAuth flow for bank connections, automatic transaction sync with configurable frequency, connection health monitoring and re-authentication prompts, support for checking/savings/credit card accounts, transaction deduplication logic, CSV import as fallback method. Provider selection is configurable per deployment or per connection.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Connect Bank Account via OAuth (Priority: P1)

A user wants to connect their bank account to automatically import transactions. They initiate the connection flow, select their bank from a list, authenticate via their bank's secure login (OAuth), and authorize read-only access to transaction data.

**Why this priority**: This is the core value proposition - automating transaction import eliminates manual data entry and ensures accurate, up-to-date financial data.

**Independent Test**: Can be fully tested by completing the bank connection flow and verifying the connection appears in the user's account list with a "Connected" status.

**Acceptance Scenarios**:

1. **Given** a user is on the accounts page, **When** they click "Connect Bank", **Then** they see a searchable list of supported banks
2. **Given** a user has selected their bank, **When** they complete the bank's OAuth authentication, **Then** they are redirected back to the app with a success message
3. **Given** a successful OAuth flow, **When** the connection is established, **Then** the connected bank account appears in the account list with current balance
4. **Given** a user cancels the OAuth flow, **When** they return to the app, **Then** they see a message explaining the connection was not completed and can retry

---

### User Story 2 - Automatic Transaction Sync (Priority: P1)

Connected bank accounts automatically sync new transactions at regular intervals without user intervention. Users see their latest transactions appear in the transaction inbox for categorization.

**Why this priority**: Automatic sync is the primary benefit of bank connections - without it, users would need to manually trigger imports.

**Independent Test**: Can be fully tested by waiting for the configured sync interval and verifying new transactions from the bank appear in the inbox.

**Acceptance Scenarios**:

1. **Given** a connected bank account with new transactions, **When** the scheduled sync runs, **Then** new transactions appear in the transaction inbox
2. **Given** a transaction already exists in the system, **When** a sync imports the same transaction again, **Then** the duplicate is detected and not created
3. **Given** a successful sync, **When** viewing the account, **Then** the "Last Synced" timestamp is updated

---

### User Story 3 - View Connection Status and Health (Priority: P2)

Users can view the status of their bank connections including last sync time, connection health, and any issues requiring attention (expired credentials, bank errors).

**Why this priority**: Users need visibility into whether their data is current and whether action is needed.

**Independent Test**: Can be fully tested by viewing the connections dashboard and verifying status indicators match the actual connection state.

**Acceptance Scenarios**:

1. **Given** a healthy bank connection, **When** viewing the accounts page, **Then** the connection shows a green "Connected" status with last sync time
2. **Given** a connection with expired credentials, **When** viewing the accounts page, **Then** the connection shows an orange "Needs Attention" status with a re-authenticate prompt
3. **Given** a connection with a bank-side error, **When** viewing the accounts page, **Then** the connection shows a red "Error" status with an explanation

---

### User Story 4 - Handle Expired Connections (Priority: P2)

When bank credentials expire or authorization is revoked, users are notified and can easily re-authenticate to restore the connection.

**Why this priority**: Connections expire due to bank security policies (typically 90 days for PSD2). Users must be able to restore access easily.

**Independent Test**: Can be fully tested by simulating an expired connection and completing the re-authentication flow.

**Acceptance Scenarios**:

1. **Given** a connection has expired, **When** the user views the accounts page, **Then** they see a clear notification with a "Reconnect" button
2. **Given** the user clicks "Reconnect", **When** they complete the OAuth flow, **Then** the connection is restored and syncing resumes
3. **Given** multiple connections have expired, **When** viewing the accounts page, **Then** each expired connection is clearly marked and can be individually reconnected

---

### User Story 5 - Manually Trigger Sync (Priority: P3)

Users can manually trigger a sync for any connected account when they want immediate updates rather than waiting for the next scheduled sync.

**Why this priority**: Provides user control and is useful when users know new transactions have occurred.

**Independent Test**: Can be fully tested by clicking the manual sync button and verifying new transactions appear.

**Acceptance Scenarios**:

1. **Given** a connected bank account, **When** the user clicks "Sync Now", **Then** a sync is triggered and a loading indicator appears
2. **Given** a sync is in progress, **When** it completes successfully, **Then** the user sees a success message and updated transaction count
3. **Given** a sync fails due to a temporary error, **When** it completes, **Then** the user sees an error message with option to retry

---

### User Story 6 - CSV Import Fallback (Priority: P3)

Users whose banks are not supported or who prefer not to use bank connections can import transactions via CSV file upload.

**Why this priority**: Ensures all users can use the app regardless of bank support, and provides a fallback if bank connections fail.

**Independent Test**: Can be fully tested by uploading a CSV file and verifying transactions are imported correctly.

**Acceptance Scenarios**:

1. **Given** a user is on the transactions page, **When** they click "Import CSV", **Then** they see a file upload dialog
2. **Given** a valid CSV file is uploaded, **When** the import runs, **Then** transactions are created in the inbox with a preview shown first
3. **Given** the CSV has formatting errors, **When** the import runs, **Then** the user sees specific error messages indicating which rows failed
4. **Given** the CSV contains duplicate transactions, **When** the import runs, **Then** duplicates are detected and the user is asked whether to skip or import them

---

### User Story 7 - Disconnect Bank Account (Priority: P3)

Users can disconnect a bank account, which stops automatic syncing and revokes authorization.

**Why this priority**: Users need control to remove connections they no longer want.

**Independent Test**: Can be fully tested by disconnecting an account and verifying syncing stops and the connection is removed.

**Acceptance Scenarios**:

1. **Given** a connected bank account, **When** the user clicks "Disconnect", **Then** they see a confirmation dialog explaining what will happen
2. **Given** the user confirms disconnection, **When** the action completes, **Then** the connection is removed and no further syncs occur
3. **Given** a disconnected account, **When** viewing transactions, **Then** previously synced transactions remain in the system

---

### Edge Cases

- What happens when a bank connection times out during OAuth? The user is shown a timeout error with option to retry.
- What happens when a bank returns malformed transaction data? The sync logs the error for that transaction and continues with valid ones.
- What happens when network connectivity is lost during sync? The sync fails gracefully and retries at next scheduled interval.
- What happens when the user connects the same bank account twice? The system detects the duplicate and prevents it, showing an informative message.
- What happens when a bank merges or renames? Existing connections continue to work; new connections use updated bank details.
- What happens when transaction amounts differ due to currency conversion? Transactions are stored in the original currency with the bank-provided amount.

---

## Requirements *(mandatory)*

### Functional Requirements

**Bank Connection Management**

- **FR-001**: System MUST allow users to initiate a bank connection by selecting from a list of supported banks
- **FR-002**: System MUST support OAuth-based bank authentication that redirects users to their bank's secure login
- **FR-003**: System MUST request only read-only access to account and transaction data (no write permissions)
- **FR-004**: System MUST store connection credentials securely and never expose raw tokens to the frontend
- **FR-005**: System MUST support multiple bank connections per user
- **FR-006**: System MUST support checking, savings, and credit card account types
- **FR-007**: System MUST allow users to disconnect a bank account at any time
- **FR-008**: System MUST revoke provider-side authorization when a user disconnects

**Automatic Transaction Sync**

- **FR-009**: System MUST automatically sync transactions from connected accounts at configurable intervals (default: every 6 hours)
- **FR-010**: System MUST sync all new transactions since the last successful sync
- **FR-011**: System MUST import transaction date, amount, payee/merchant name, and reference/memo
- **FR-012**: System MUST place all synced transactions in the transaction inbox for categorization
- **FR-013**: System MUST update account balances during sync

**Transaction Deduplication**

- **FR-014**: System MUST detect and prevent duplicate transaction imports using bank-provided transaction IDs
- **FR-015**: System MUST use fuzzy matching (date, amount, payee) for deduplication when bank transaction IDs are not available
- **FR-016**: System MUST mark potential duplicates for user review rather than silently discarding them

**Connection Health and Monitoring**

- **FR-017**: System MUST track connection status: Active, Needs Attention, Error, Disconnected
- **FR-018**: System MUST display last successful sync timestamp for each connection
- **FR-019**: System MUST detect expired credentials and prompt users to re-authenticate
- **FR-020**: System MUST notify users (in-app) when a connection requires attention
- **FR-021**: System MUST provide clear error messages when sync fails, distinguishing between user-fixable and system issues

**Manual Operations**

- **FR-022**: System MUST allow users to manually trigger a sync for any connected account
- **FR-023**: System MUST prevent multiple simultaneous syncs for the same account
- **FR-024**: System MUST show sync progress indicator during manual sync operations

**CSV Import Fallback**

- **FR-025**: System MUST accept CSV file uploads for transaction import
- **FR-026**: System MUST support common CSV formats (comma, semicolon, tab delimiters; various date formats)
- **FR-027**: System MUST validate CSV structure and provide specific error messages for invalid files
- **FR-028**: System MUST show a preview of transactions before committing the import
- **FR-029**: System MUST detect potential duplicates in CSV imports against existing transactions
- **FR-030**: System MUST allow users to select which columns map to which transaction fields

**Provider Abstraction**

- **FR-031**: System MUST use a provider-agnostic adapter interface for bank connections
- **FR-032**: System MUST support adding new bank connection providers without changes to core transaction logic
- **FR-033**: System MUST maintain consistent transaction data format regardless of provider
- **FR-034**: System MUST support GoCardless Bank Account Data (Nordigen) as a provider
- **FR-035**: System MUST support EnableBanking as an alternative provider
- **FR-036**: System MUST allow provider selection via configuration (environment variable or per-connection setting)
- **FR-037**: System MUST store which provider was used for each bank connection to ensure proper API calls
- **FR-038**: System MUST handle provider-specific authentication methods (API key/secret for GoCardless, JWT with RS256 for EnableBanking)

### Key Entities

- **BankConnection**: Represents a link between a user account and an external bank; attributes include status (Active/Needs Attention/Error/Disconnected), bank name, last sync timestamp, connection health, and provider reference
- **LinkedAccount**: Represents a specific account within a bank connection; attributes include account number (masked), account type (checking/savings/credit), current balance, currency
- **SyncJob**: Represents a transaction sync operation; attributes include status (pending/running/completed/failed), start time, end time, transactions imported count, error details if failed
- **ImportedTransaction**: Represents a transaction fetched from a bank before being added to inbox; attributes include bank transaction ID, date, amount, payee, memo/reference, source (bank sync or CSV import)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete bank connection setup in under 3 minutes (excluding bank-side authentication time)
- **SC-002**: 95% of automatic syncs complete successfully without user intervention
- **SC-003**: New transactions appear in the inbox within 15 minutes of being posted at the bank (during sync interval)
- **SC-004**: Duplicate transactions are detected with 99% accuracy using bank transaction IDs
- **SC-005**: Users can identify and resolve connection issues within 1 minute of viewing the accounts page
- **SC-006**: CSV import of 100 transactions completes in under 30 seconds
- **SC-007**: 90% of users with supported banks choose bank connection over CSV import

---

## Assumptions

- Users have valid accounts at supported banks
- Banks provide consistent transaction identifiers for deduplication
- OAuth tokens expire after approximately 90 days per PSD2 regulations (for European banks)
- Users have reliable internet connectivity for sync operations
- Sync frequency of every 6 hours is acceptable for most users (configurable for edge cases)
- Transaction data from banks includes at minimum: date, amount, and some form of payee/description
- CSV import field mapping can be saved per user for repeat imports from the same source
- GoCardless and EnableBanking provide overlapping but not identical bank coverage; having both maximizes supported banks
- EnableBanking uses JWT authentication with RS256 algorithm requiring a private key file
- Provider selection is typically deployment-wide, but per-connection override may be needed for specific banks
- Both providers return similar data structures that can be normalized to a common format

---

## Dependencies

- Existing account management system (from 001-spending-targets-mvp) for linking bank accounts to user accounts
- Existing transaction inbox system (from 001-spending-targets-mvp) for receiving imported transactions
- External bank connection provider API access and credentials:
  - GoCardless Bank Account Data: Secret ID and Secret Key
  - EnableBanking: Application ID and RS256 private key file
- Background job scheduler for automatic sync operations
- PyJWT library for EnableBanking JWT token generation
