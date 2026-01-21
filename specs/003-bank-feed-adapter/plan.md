# Implementation Plan: Bank Feed Adapter

**Feature Branch**: `003-bank-feed-adapter`
**Created**: 2026-01-19
**Status**: Planning

---

## Architecture Overview

### Provider Abstraction Pattern

The bank feed adapter uses a provider-agnostic design that allows swapping or adding bank connection providers without changing core business logic.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ BankConnect  │  │ ConnectionUI │  │ CSVImportDialog      │   │
│  │   Dialog     │  │   Status     │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend API                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ /connections │  │ /sync        │  │ /import              │   │
│  │   endpoints  │  │   endpoints  │  │   endpoints          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Service Layer                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              BankConnectionService                        │   │
│  │  - initiate_connection()  - disconnect()                  │   │
│  │  - complete_oauth()       - get_connection_status()       │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              TransactionSyncService                       │   │
│  │  - sync_account()         - schedule_sync()               │   │
│  │  - deduplicate()          - import_from_csv()             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Provider Adapter Interface                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              BankProviderAdapter (ABC)                    │   │
│  │  - get_institutions()     - create_requisition()          │   │
│  │  - get_accounts()         - get_transactions()            │   │
│  │  - refresh_access()       - revoke_access()               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                              │                                   │
│        ┌────────────┬────────────┬────────────┬────────────┐    │
│        ▼            ▼            ▼            ▼            │    │
│  ┌───────────┐┌───────────┐┌───────────┐┌───────────┐     │    │
│  │ GoCardless││  Enable   ││  Plaid    ││  Mock     │     │    │
│  │  Adapter  ││  Banking  ││  Adapter  ││  Adapter  │     │    │
│  │ (Nordigen)││  Adapter  ││ (future)  ││  (tests)  │     │    │
│  └───────────┘└───────────┘└───────────┘└───────────┘     │    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Technology Choices

### GoCardless Bank Account Data (Nordigen)

**Why GoCardless/Nordigen:**
- PSD2-compliant AIS (Account Information Services) for European banks
- Free tier available for testing (50 connections/month)
- Simple REST API with OAuth flow
- Covers 2,400+ banks across 31 European countries
- Good documentation and sandbox environment

**API Flow:**
1. Create end-user agreement (requisition)
2. User authenticates with their bank via redirect
3. Receive access tokens on callback
4. Fetch accounts and transactions using access tokens
5. Refresh tokens before expiry (90 days typical)

### EnableBanking

**Why EnableBanking:**
- Alternative PSD2-compliant AIS provider for European banks
- Different bank coverage than GoCardless (complementary)
- Simple REST API with JWT authentication
- Supports 2,000+ banks across Europe
- Good fallback when GoCardless doesn't support a specific bank

**Authentication:**
- JWT tokens with RS256 algorithm
- Application ID as `kid` in JWT header
- Private key file for signing (generated during registration)
- Tokens valid for up to 24 hours (86400 seconds)

**API Flow:**
1. `GET /aspsps` - List available banks by country
2. `POST /auth` - Create authorization, returns redirect URL
3. User authenticates with their bank via redirect
4. Callback returns authorization code
5. `POST /sessions` - Exchange code for session, returns accounts
6. `GET /accounts/{id}/transactions` - Fetch transactions

**Key Differences from GoCardless:**
| Aspect | GoCardless | EnableBanking |
|--------|-----------|---------------|
| Auth | API Key/Secret | JWT RS256 |
| Banks endpoint | `/institutions` | `/aspsps` |
| OAuth start | `/requisitions` | `/auth` |
| OAuth complete | Get requisition status | `POST /sessions` |
| Session concept | Requisition with accounts | Session with accounts |

### Background Job Scheduler

**Options considered:**
- APScheduler (in-process, lightweight)
- Celery (distributed, Redis/RabbitMQ required)
- ARQ (async Redis queue)

**Choice: APScheduler** for MVP
- No additional infrastructure needed
- Sufficient for single-instance deployment
- Can migrate to Celery if scaling requires

### CSV Parsing

**Library: pandas**
- Handles multiple delimiters automatically
- Good date parsing capabilities
- Memory efficient for streaming large files

---

## Data Model

### New Tables

```sql
-- Bank connection to external provider
CREATE TABLE bank_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'gocardless', 'plaid', etc.
    provider_connection_id VARCHAR(255) NOT NULL,  -- requisition_id for GoCardless
    institution_id VARCHAR(100) NOT NULL,
    institution_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING, ACTIVE, NEEDS_ATTENTION, ERROR, DISCONNECTED
    status_detail TEXT,  -- Error message or additional info
    last_sync_at TIMESTAMPTZ,
    next_sync_at TIMESTAMPTZ,
    access_valid_until TIMESTAMPTZ,  -- Token expiry
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, provider, provider_connection_id)
);

-- Accounts discovered within a bank connection
CREATE TABLE linked_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID NOT NULL REFERENCES bank_connections(id) ON DELETE CASCADE,
    account_id UUID REFERENCES accounts(id) ON DELETE SET NULL,  -- Link to internal account
    provider_account_id VARCHAR(255) NOT NULL,
    account_name VARCHAR(255),
    account_number_masked VARCHAR(50),  -- e.g., "****1234"
    account_type VARCHAR(20),  -- CHECKING, SAVINGS, CREDIT
    currency VARCHAR(3) DEFAULT 'EUR',
    balance DECIMAL(19,4),
    balance_updated_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(connection_id, provider_account_id)
);

-- Sync job tracking
CREATE TABLE sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    connection_id UUID NOT NULL REFERENCES bank_connections(id) ON DELETE CASCADE,
    linked_account_id UUID REFERENCES linked_accounts(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',  -- PENDING, RUNNING, COMPLETED, FAILED
    trigger_type VARCHAR(20) NOT NULL,  -- SCHEDULED, MANUAL, INITIAL
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    transactions_fetched INTEGER DEFAULT 0,
    transactions_imported INTEGER DEFAULT 0,
    transactions_duplicates INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- CSV import mapping templates (per user)
CREATE TABLE csv_import_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    delimiter VARCHAR(5) DEFAULT ',',
    date_column VARCHAR(100),
    date_format VARCHAR(50),
    amount_column VARCHAR(100),
    payee_column VARCHAR(100),
    memo_column VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(user_id, name)
);
```

### Modifications to Existing Tables

```sql
-- Add to transactions table
ALTER TABLE transactions ADD COLUMN external_id VARCHAR(255);  -- Bank transaction ID
ALTER TABLE transactions ADD COLUMN import_source VARCHAR(20);  -- MANUAL, BANK_SYNC, CSV_IMPORT
ALTER TABLE transactions ADD COLUMN import_batch_id UUID;  -- Links transactions from same import

-- Index for deduplication
CREATE INDEX idx_transactions_external_id ON transactions(user_id, external_id) WHERE external_id IS NOT NULL;
```

---

## API Contracts

### Bank Connections

```
POST   /api/v1/connections/initiate
       Request: { institution_id: string }
       Response: { redirect_url: string, connection_id: string }

GET    /api/v1/connections/callback
       Query: ref=<requisition_id>
       Response: Redirect to frontend with status

GET    /api/v1/connections
       Response: { connections: BankConnection[] }

GET    /api/v1/connections/{id}
       Response: BankConnection with linked_accounts

DELETE /api/v1/connections/{id}
       Response: 204 No Content

POST   /api/v1/connections/{id}/sync
       Response: { job_id: string }

GET    /api/v1/institutions
       Query: country=<ISO>, search=<name>
       Response: { institutions: Institution[] }
```

### Sync Jobs

```
GET    /api/v1/sync-jobs
       Query: connection_id=<uuid>
       Response: { jobs: SyncJob[] }

GET    /api/v1/sync-jobs/{id}
       Response: SyncJob
```

### CSV Import

```
POST   /api/v1/import/csv/preview
       Body: multipart/form-data with file
       Response: { rows: ParsedRow[], columns: string[], suggested_mapping: Mapping }

POST   /api/v1/import/csv
       Body: { account_id: string, mapping: Mapping, file_id: string }
       Response: { imported: number, duplicates: number, errors: Error[] }

GET    /api/v1/import/mappings
       Response: { mappings: CSVMapping[] }

POST   /api/v1/import/mappings
       Body: CSVMapping
       Response: CSVMapping
```

---

## Security Considerations

### Token Storage
- Provider access tokens stored encrypted at rest (using Fernet)
- Tokens never exposed to frontend
- Refresh tokens rotated on each use

### OAuth Flow
- State parameter to prevent CSRF
- Short-lived authorization codes
- Secure redirect URI validation

### Data Access
- Read-only bank access (AIS only, no PIS)
- User can only access their own connections
- Connection deletion revokes provider-side access

---

## Implementation Phases

### Phase 1: Foundation
- Data models and migrations
- Provider adapter interface
- GoCardless adapter implementation (sandbox)

### Phase 2: Connection Management
- OAuth flow implementation
- Connection status tracking
- Institution search

### Phase 3: Transaction Sync
- Manual sync endpoint
- Transaction deduplication
- Sync job tracking

### Phase 4: Automatic Sync
- APScheduler integration
- Scheduled sync jobs
- Error handling and retry logic

### Phase 5: Connection Health
- Token expiry detection
- Re-authentication flow
- Status notifications

### Phase 6: CSV Import
- File upload and parsing
- Column mapping UI
- Duplicate detection

### Phase 7: Frontend Integration
- Bank connection dialog
- Connection status display
- Sync controls
- CSV import dialog

### Phase 8-10: (Completed)
- Phase 8: Frontend Connection UI
- Phase 9: Frontend Sync & Import UI
- Phase 10: Polish & Integration

### Phase 11: EnableBanking Integration
- EnableBanking adapter implementing BankProviderAdapter
- JWT RS256 authentication with private key
- Institution listing via `/aspsps` endpoint
- OAuth flow via `/auth` and `/sessions` endpoints
- Transaction fetching via `/accounts/{id}/transactions`
- Provider selection configuration (env var or per-connection)
- Update DEPLOYMENT.md with EnableBanking configuration
- Unit tests with mocked HTTP responses

---

## Testing Strategy

### Unit Tests
- Provider adapter methods (with mocked responses)
- Deduplication logic
- CSV parsing and mapping

### Integration Tests
- OAuth flow (with mock provider)
- Full sync cycle
- Connection lifecycle

### Contract Tests
- All API endpoints
- Error responses
- Pagination

### E2E Tests (Playwright)
- Complete bank connection flow (sandbox)
- Manual sync trigger
- CSV import workflow

---

## Configuration

```python
# Environment variables - GoCardless
GOCARDLESS_SECRET_ID = "..."
GOCARDLESS_SECRET_KEY = "..."
GOCARDLESS_BASE_URL = "https://bankaccountdata.gocardless.com/api/v2"  # or sandbox

# Environment variables - EnableBanking
ENABLEBANKING_APP_ID = "..."  # Application ID (used as kid in JWT)
ENABLEBANKING_PRIVATE_KEY_PATH = "/path/to/private_key.pem"  # RS256 private key
ENABLEBANKING_BASE_URL = "https://api.enablebanking.com"

# Provider selection
BANK_PROVIDER = "gocardless"  # or "enablebanking" - default provider for new connections

# Common settings
BANK_SYNC_INTERVAL_HOURS = 6
BANK_TOKEN_ENCRYPTION_KEY = "..."  # Fernet key
```

---

## Rollout Plan

1. **Sandbox Testing**: Use GoCardless sandbox with test banks
2. **Beta**: Enable for select users with real bank connections
3. **GA**: Enable bank feed for all users
4. **CSV Import**: Available immediately as fallback

---

## Future Considerations

- **Additional Providers**: Plaid (US banks), TrueLayer (UK), Tink (Nordic)
- **Webhooks**: Real-time transaction notifications (when providers support)
- **Multi-currency**: Handle non-EUR transactions with conversion
- **Statement PDFs**: Import transactions from bank statement PDFs
- **Provider Auto-Selection**: Automatically choose best provider based on user's bank
- **Provider Failover**: Try alternative provider if primary fails for a bank
