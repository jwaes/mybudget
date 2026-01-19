# Tasks: Bank Feed Adapter

**Input**: Design documents from `/specs/003-bank-feed-adapter/`
**Prerequisites**: plan.md, spec.md
**Last Updated**: 2026-01-19

**Tests**: Per constitution's TDD principle, ALL tasks include tests. Red-Green-Refactor is mandatory.

**Organization**: Tasks are grouped by phase to enable incremental delivery.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US7)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/mybudget/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`
- **Database migrations**: `backend/migrations/versions/`

---

## Phase 1: Foundation (Data Models & Provider Interface)

**Purpose**: Create database schema and provider abstraction layer

### Models & Migrations

- [x] T001 Create BankConnection model in backend/src/mybudget/models/bank_connection.py (id, user_id, provider, provider_connection_id, institution_id, institution_name, status, status_detail, last_sync_at, next_sync_at, access_valid_until, timestamps)
- [x] T002 [P] Create LinkedAccount model in backend/src/mybudget/models/bank_connection.py (consolidated with BankConnection)
- [x] T003 [P] Create SyncJob model in backend/src/mybudget/models/bank_connection.py (consolidated with BankConnection)
- [ ] T004 [P] Create CSVImportMapping model in backend/src/mybudget/models/csv_import_mapping.py (id, user_id, name, delimiter, date_column, date_format, amount_column, payee_column, memo_column)
- [ ] T005 Add external_id, import_source, import_batch_id columns to Transaction model
- [x] T006 Generate Alembic migration for bank feed tables
- [x] T007 Create Pydantic schemas in backend/src/mybudget/schemas/bank_connection.py
- [x] T008 [P] Create Pydantic schemas in backend/src/mybudget/schemas/sync_job.py
- [x] T009 [P] Create Pydantic schemas in backend/src/mybudget/schemas/csv_import.py
- [x] T010 Test: Write unit tests for models in backend/tests/unit/test_models/test_bank_connection.py

### Provider Adapter Interface

- [x] T011 Create BankProviderAdapter abstract base class in backend/src/mybudget/adapters/base.py (get_institutions, create_requisition, get_accounts, get_transactions, refresh_access, revoke_access)
- [x] T012 Create provider response dataclasses in backend/src/mybudget/adapters/types.py (Institution, ProviderAccount, ProviderTransaction)
- [x] T013 Create MockBankAdapter for testing in backend/src/mybudget/adapters/mock_adapter.py
- [x] T014 Test: Write unit tests for mock adapter in backend/tests/unit/test_adapters/test_mock_adapter.py (29 tests)

**Checkpoint**: Data models and provider interface ready

---

## Phase 2: GoCardless Integration (US1 - Bank Connection)

**Purpose**: Implement GoCardless/Nordigen adapter and OAuth flow

### GoCardless Adapter

- [x] T015 Install httpx and cryptography dependencies
- [x] T016 Create GoCardlessAdapter in backend/src/mybudget/adapters/gocardless_adapter.py
- [x] T017 Implement get_institutions() method (search banks by country/name)
- [x] T018 Implement create_requisition() method (initiate OAuth flow)
- [x] T019 Implement get_accounts() method (fetch linked accounts)
- [x] T020 Implement get_transactions() method (fetch transactions for account)
- [x] T021 Implement refresh_access() method (handle token refresh)
- [x] T022 Implement revoke_access() method (disconnect and revoke)
- [x] T023 Add configuration for GoCardless credentials in backend/src/mybudget/config.py
- [x] T024 Test: Write unit tests with mocked HTTP in backend/tests/unit/test_adapters/test_gocardless_adapter.py (28 tests)

### Token Encryption

- [x] T025 Create token encryption utility in backend/src/mybudget/lib/encryption.py (encrypt_token, decrypt_token using Fernet)
- [x] T026 Test: Write unit tests for encryption in backend/tests/unit/test_lib/test_encryption.py (18 tests)

**Checkpoint**: GoCardless adapter ready for OAuth flow

---

## Phase 3: Connection Management Service & API (US1)

**Purpose**: Implement connection lifecycle management

### Service Layer

- [ ] T027 Create BankConnectionService in backend/src/mybudget/services/bank_connection_service.py
- [ ] T028 [US1] Implement initiate_connection() - creates requisition and returns redirect URL
- [ ] T029 [US1] Implement complete_oauth() - handles callback and activates connection
- [ ] T030 [US1] Implement list_connections() - returns user's bank connections
- [ ] T031 [US1] Implement get_connection() - returns connection with linked accounts
- [ ] T032 [US7] Implement disconnect() - revokes access and marks disconnected
- [ ] T033 Implement get_institutions() - searches available banks
- [ ] T034 Test: Write unit tests in backend/tests/unit/test_services/test_bank_connection_service.py

### API Endpoints

- [ ] T035 Create bank connections router in backend/src/mybudget/api/bank_connections.py
- [ ] T036 [US1] POST /api/v1/connections/initiate endpoint
- [ ] T037 [US1] GET /api/v1/connections/callback endpoint (OAuth callback)
- [ ] T038 [US1] GET /api/v1/connections endpoint (list connections)
- [ ] T039 [US1] GET /api/v1/connections/{id} endpoint (get connection details)
- [ ] T040 [US7] DELETE /api/v1/connections/{id} endpoint (disconnect)
- [ ] T041 GET /api/v1/institutions endpoint (search banks)
- [ ] T042 Register router in backend/src/mybudget/main.py
- [ ] T043 Test: Write contract tests in backend/tests/contract/test_bank_connections_api.py

**Checkpoint**: Bank connection OAuth flow functional

---

## Phase 4: Transaction Sync Service (US2, US5)

**Purpose**: Implement transaction syncing and deduplication

### Sync Service

- [ ] T044 Create TransactionSyncService in backend/src/mybudget/services/transaction_sync_service.py
- [ ] T045 [US2] Implement sync_account() - fetches and imports transactions for one linked account
- [ ] T046 [US2] Implement _deduplicate_transactions() - detects duplicates by external_id or fuzzy match
- [ ] T047 [US2] Implement _create_transactions() - creates inbox transactions from provider data
- [ ] T048 [US2] Implement _update_sync_job() - tracks sync progress
- [ ] T049 [US5] Implement trigger_manual_sync() - starts sync job for connection
- [ ] T050 Implement get_sync_jobs() - returns sync history for connection
- [ ] T051 Test: Write unit tests in backend/tests/unit/test_services/test_transaction_sync_service.py

### Sync API Endpoints

- [ ] T052 [US5] POST /api/v1/connections/{id}/sync endpoint (trigger manual sync)
- [ ] T053 GET /api/v1/sync-jobs endpoint (list sync jobs)
- [ ] T054 GET /api/v1/sync-jobs/{id} endpoint (get sync job details)
- [ ] T055 Test: Write contract tests in backend/tests/contract/test_sync_api.py

**Checkpoint**: Manual transaction sync working

---

## Phase 5: Automatic Sync & Scheduling (US2)

**Purpose**: Implement scheduled background sync

### Scheduler Integration

- [ ] T056 Install APScheduler dependency
- [ ] T057 Create scheduler module in backend/src/mybudget/scheduler/__init__.py
- [ ] T058 Create sync scheduler in backend/src/mybudget/scheduler/sync_scheduler.py
- [ ] T059 [US2] Implement schedule_sync_job() - schedules next sync for connection
- [ ] T060 [US2] Implement run_scheduled_syncs() - executes due sync jobs
- [ ] T061 [US2] Implement handle_sync_failure() - retry logic with backoff
- [ ] T062 Integrate scheduler startup in backend/src/mybudget/main.py
- [ ] T063 Add BANK_SYNC_INTERVAL_HOURS configuration
- [ ] T064 Test: Write unit tests in backend/tests/unit/test_scheduler/test_sync_scheduler.py

**Checkpoint**: Automatic transaction sync operational

---

## Phase 6: Connection Health & Re-auth (US3, US4)

**Purpose**: Implement connection monitoring and re-authentication

### Health Monitoring

- [ ] T065 [US3] Implement check_connection_health() in BankConnectionService
- [ ] T066 [US4] Implement detect_expiring_tokens() - finds connections needing re-auth
- [ ] T067 [US4] Implement initiate_reauth() - starts re-authentication flow
- [ ] T068 [US3] Add connection_health field to BankConnection response
- [ ] T069 Test: Write unit tests for health monitoring

### Status API

- [ ] T070 [US3] Add health_status to GET /api/v1/connections response
- [ ] T071 [US4] POST /api/v1/connections/{id}/reauth endpoint
- [ ] T072 Test: Write contract tests for re-auth flow

**Checkpoint**: Connection health monitoring complete

---

## Phase 7: CSV Import (US6)

**Purpose**: Implement CSV file import as fallback

### CSV Parser

- [x] T073 Install pandas dependency
- [x] T074 Create CSVImportService in backend/src/mybudget/services/csv_import_service.py
- [x] T075 [US6] Implement parse_csv() - reads file with multiple date/decimal format support
- [x] T076 [US6] Implement preview_import() - returns preview with duplicate detection
- [x] T077 [US6] Implement execute_import() - creates INBOX transactions from CSV
- [x] T078 [US6] Implement detect_duplicates() - checks date+amount+payee against existing
- [ ] T079 [US6] Implement save_mapping() - stores column mapping template (deferred)
- [x] T080 Test: Write unit tests in backend/tests/unit/test_services/test_csv_import_service.py (18 tests)

### CSV API Endpoints

- [x] T081 Create CSV import router in backend/src/mybudget/api/csv_import.py
- [x] T082 [US6] POST /api/import/csv/preview endpoint
- [x] T083 [US6] POST /api/import/csv endpoint
- [ ] T084 [US6] GET /api/import/mappings endpoint (deferred with T079)
- [ ] T085 [US6] POST /api/import/mappings endpoint (deferred with T079)
- [x] T086 Register router in main.py
- [x] T087 Test: Write contract tests in backend/tests/contract/test_csv_import_api.py (29 tests)

**Checkpoint**: CSV import functional

---

## Phase 8: Frontend - Connection UI (US1, US3, US4)

**Purpose**: Build bank connection management UI

### Bank Connection Components

- [ ] T088 Create bankConnectionService in frontend/src/services/bankConnectionService.ts
- [ ] T089 Create types in frontend/src/types/bankConnection.ts
- [ ] T090 [US1] Create BankSearchDialog component in frontend/src/components/BankSearchDialog.tsx
- [ ] T091 [US1] Create BankConnectionCallback page for OAuth redirect in frontend/src/pages/BankCallback.tsx
- [ ] T092 [US3] Create ConnectionStatusBadge component in frontend/src/components/ConnectionStatusBadge.tsx
- [ ] T093 [US3] Update AccountList to show connection status and sync info
- [ ] T094 [US4] Create ReconnectPrompt component in frontend/src/components/ReconnectPrompt.tsx
- [ ] T095 [US7] Add disconnect confirmation dialog
- [ ] T096 Add route for callback page in frontend/src/App.tsx
- [ ] T097 Test: Write component tests in frontend/tests/components/

**Checkpoint**: Bank connection UI complete

---

## Phase 9: Frontend - Sync & Import UI (US5, US6)

**Purpose**: Build sync controls and CSV import UI

### Sync Controls

- [ ] T098 [US5] Add "Sync Now" button to AccountList
- [ ] T099 [US5] Create SyncStatusIndicator component
- [ ] T100 [US5] Show sync progress and results

### CSV Import

- [ ] T101 Create csvImportService in frontend/src/services/csvImportService.ts
- [ ] T102 [US6] Create CSVImportDialog component in frontend/src/components/CSVImportDialog.tsx
- [ ] T103 [US6] Create ColumnMappingForm component in frontend/src/components/ColumnMappingForm.tsx
- [ ] T104 [US6] Create ImportPreviewTable component in frontend/src/components/ImportPreviewTable.tsx
- [ ] T105 [US6] Add "Import CSV" button to Transactions page
- [ ] T106 Test: Write component tests for CSV import

**Checkpoint**: Sync and import UI complete

---

## Phase 10: Polish & Integration

**Purpose**: Final cleanup and end-to-end testing

- [ ] T107 Run all backend tests and ensure >80% coverage
- [ ] T108 Run all frontend tests
- [ ] T109 Test complete OAuth flow with GoCardless sandbox
- [ ] T110 Test automatic sync scheduling
- [ ] T111 Test CSV import with various file formats
- [ ] T112 Add error handling for network failures
- [ ] T113 Add loading states to all async operations
- [ ] T114 Update DEPLOYMENT.md with GoCardless configuration
- [ ] T115 Final code review and cleanup

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies - start here
- **Phase 2**: Depends on Phase 1 (models and adapter interface)
- **Phase 3**: Depends on Phase 2 (GoCardless adapter)
- **Phase 4**: Depends on Phase 3 (connection service)
- **Phase 5**: Depends on Phase 4 (sync service)
- **Phase 6**: Depends on Phase 3 (connection service)
- **Phase 7**: Depends on Phase 1 (models only) - can run parallel to 4-6
- **Phase 8**: Depends on Phases 3, 6 (backend APIs)
- **Phase 9**: Depends on Phases 4, 5, 7 (backend APIs)
- **Phase 10**: Depends on all phases

### Parallel Opportunities

- T002-T004 can run in parallel (different models)
- T007-T009 can run in parallel (different schemas)
- Phase 7 (CSV) can run parallel to Phases 4-6 after Phase 1

---

## Environment Setup

Required environment variables:

```bash
GOCARDLESS_SECRET_ID=your_secret_id
GOCARDLESS_SECRET_KEY=your_secret_key
GOCARDLESS_BASE_URL=https://bankaccountdata.gocardless.com/api/v2
BANK_SYNC_INTERVAL_HOURS=6
BANK_TOKEN_ENCRYPTION_KEY=your_fernet_key
```

Generate Fernet key:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```
