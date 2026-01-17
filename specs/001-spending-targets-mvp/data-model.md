# Data Model: MyBudget MVP

**Date**: 2026-01-16
**Feature**: Spending Targets MVP
**Database**: PostgreSQL 15+
**ORM**: SQLAlchemy 2.0

## Overview

This document defines the database schema for MyBudget MVP. All entities are designed to support:
- Financial precision (DECIMAL types, no floating point)
- Data integrity (foreign keys, constraints)
- Timezone-aware dates (month boundaries)
- Audit trails (timestamps on all mutations)
- Single-user MVP (no multi-tenancy)

---

## Entity Relationship Diagram

```
┌──────────────┐
│    User      │ (MVP: single user, future multi-user)
└──────┬───────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
┌──────────────┐                      ┌─────────────────┐
│   Account    │                      │  CategoryGroup  │
└──────┬───────┘                      └────────┬────────┘
       │                                       │
       │                                       ▼
       │                              ┌────────────────┐
       │                              │   Category     │
       │                              └────────┬───────┘
       │                                       │
       │                                       ├───────────────┐
       │                                       │               │
       ▼                                       ▼               ▼
┌──────────────┐                      ┌──────────────┐ ┌─────────────┐
│ Transaction  │─────categorized────> │ Assignment   │ │CategoryTarget│
└──────┬───────┘     by rule          └──────────────┘ └─────────────┘
       │
       │
       └──────────────┐
                      │
                      ▼
              ┌───────────────────┐
              │ CategorizationRule│
              └───────────────────┘

┌──────────────┐
│Reconciliation│ (linked to Account)
└──────────────┘
```

---

## Entities

### 1. User

**Purpose**: Represent a MyBudget user (MVP: single user system, prepared for future multi-user)

**PostgreSQL Schema**:
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,  -- Argon2id hash
    full_name       VARCHAR(255),
    timezone        VARCHAR(50) NOT NULL DEFAULT 'UTC',  -- For month boundaries
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

**Python Type** (SQLAlchemy):
```python
from sqlalchemy import String, DateTime, UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Validation Rules** (from spec):
- Email: Valid email format, unique
- Password: Min 12 characters, hashed with Argon2id before storage
- Timezone: Valid IANA timezone string

**Relationships**:
- One user has many accounts
- One user has many category groups

---

### 2. Account

**Purpose**: Represent a bank checking or savings account (FR-001, FR-002, FR-003)

**PostgreSQL Schema**:
```sql
CREATE TYPE account_type AS ENUM ('CHECKING', 'SAVINGS');

CREATE TABLE accounts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,  -- e.g., "ING Checking", "KBC Savings"
    account_type    account_type NOT NULL,
    balance         DECIMAL(19, 4) NOT NULL DEFAULT 0,  -- Current balance
    initial_balance DECIMAL(19, 4) NOT NULL,  -- Starting balance (for auditing)
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_accounts_user_id ON accounts(user_id);
```

**Python Type**:
```python
from decimal import Decimal
from enum import Enum

class AccountType(str, Enum):
    CHECKING = "CHECKING"
    SAVINGS = "SAVINGS"

class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType), nullable=False)
    balance: Mapped[Decimal] = mapped_column(DECIMAL(19, 4), nullable=False, default=Decimal("0"))
    initial_balance: Mapped[Decimal] = mapped_column(DECIMAL(19, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Validation Rules**:
- Name: Required, max 100 chars
- Account type: Must be CHECKING or SAVINGS
- Initial balance: Cannot be changed after creation
- Balance: Updated automatically based on approved transactions

**Computed Properties**:
- `current_balance`: Same as `balance` (maintained by transaction approval workflow)

---

### 3. Transaction

**Purpose**: Represent a financial transaction (FR-005, FR-006, FR-007, FR-010)

**PostgreSQL Schema**:
```sql
CREATE TYPE transaction_state AS ENUM ('INBOX', 'APPROVED', 'CLEARED');

CREATE TABLE transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id      UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    category_id     UUID REFERENCES categories(id) ON DELETE SET NULL,  -- Nullable until approved
    date            DATE NOT NULL,  -- Transaction date (not import date)
    payee           VARCHAR(255) NOT NULL,
    amount          DECIMAL(19, 4) NOT NULL,  -- Positive = inflow, Negative = outflow
    memo            TEXT,
    state           transaction_state NOT NULL DEFAULT 'INBOX',
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    approved_at     TIMESTAMP WITH TIME ZONE,  -- When state changed to APPROVED
    cleared_at      TIMESTAMP WITH TIME ZONE   -- When marked cleared during reconciliation
);

CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_account_id ON transactions(account_id);
CREATE INDEX idx_transactions_category_id ON transactions(category_id);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_state ON transactions(state);
```

**Python Type**:
```python
from datetime import date

class TransactionState(str, Enum):
    INBOX = "INBOX"
    APPROVED = "APPROVED"
    CLEARED = "CLEARED"

class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payee: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(19, 4), nullable=False)
    memo: Mapped[str | None] = mapped_column(Text)
    state: Mapped[TransactionState] = mapped_column(Enum(TransactionState), nullable=False, default=TransactionState.INBOX, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
```

**Validation Rules**:
- Date: Required, cannot be in future
- Payee: Required
- Amount: Non-zero (positive = income, negative = expense)
- Category: Optional in INBOX state, required when APPROVED

**State Transitions**:
```
INBOX → APPROVED → CLEARED
  └──────┘        (can unapprove)
```

**Business Rules**:
- Only APPROVED transactions affect category budgets and account balances
- Only CLEARED transactions count in reconciliation
- Changing state from INBOX to APPROVED sets `approved_at` timestamp
- Changing state to CLEARED sets `cleared_at` timestamp

---

### 4. CategoryGroup

**Purpose**: Organizational container for categories (FR-011)

**PostgreSQL Schema**:
```sql
CREATE TABLE category_groups (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    display_order   INTEGER NOT NULL DEFAULT 0,  -- For UI ordering
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, name)  -- Group names unique per user
);

CREATE INDEX idx_category_groups_user_id ON category_groups(user_id);
CREATE INDEX idx_category_groups_display_order ON category_groups(display_order);
```

**Python Type**:
```python
class CategoryGroup(Base):
    __tablename__ = "category_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Validation Rules**:
- Name: Required, unique per user
- Display order: Non-negative integer

---

### 5. Category

**Purpose**: Budget category for tracking spending (FR-012, FR-013, FR-014, FR-015)

**PostgreSQL Schema**:
```sql
CREATE TABLE categories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    group_id        UUID NOT NULL REFERENCES category_groups(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(user_id, name)  -- Category names unique per user
);

CREATE INDEX idx_categories_user_id ON categories(user_id);
CREATE INDEX idx_categories_group_id ON categories(group_id);
```

**Python Type**:
```python
class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("category_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Methods for computed values (not stored)
    def get_available(self, month: date) -> Decimal:
        """Calculate available = rollover + funded_this_month - activity"""
        pass

    def get_funded_this_month(self, month: date) -> Decimal:
        """Sum of assignments for this month"""
        pass

    def get_activity(self, month: date) -> Decimal:
        """Sum of approved transaction amounts for this month"""
        pass
```

**Validation Rules**:
- Name: Required, unique per user
- Group: Must belong to valid category group

**Computed Values (NOT stored in DB)**:
Per FR-013, these are calculated on-demand for a given month:
- `available`: Money currently available (rollover + funded_this_month - activity)
- `funded_this_month`: Sum of assignments in current month
- `activity`: Sum of approved transaction amounts in current month

**Note**: These values are computed per month and NOT stored to maintain data integrity and simplify month rollover logic.

---

### 6. Assignment

**Purpose**: Record of funds assigned to categories (FR-037 - audit trail)

**PostgreSQL Schema**:
```sql
CREATE TABLE assignments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id     UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    amount          DECIMAL(19, 4) NOT NULL,  -- Can be positive (assign) or negative (unassign)
    month           DATE NOT NULL,  -- First day of month (e.g., 2026-01-01)
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assignments_user_id ON assignments(user_id);
CREATE INDEX idx_assignments_category_id ON assignments(category_id);
CREATE INDEX idx_assignments_month ON assignments(month);
CREATE INDEX idx_assignments_category_month ON assignments(category_id, month);  -- Common query
```

**Python Type**:
```python
class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(19, 4), nullable=False)
    month: Mapped[date] = mapped_column(Date, nullable=False, index=True)  # Always first day of month
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
```

**Validation Rules**:
- Amount: Non-zero (positive to assign, negative to unassign)
- Month: Must be first day of month (e.g., 2026-01-01, not 2026-01-15)

**Business Rules**:
- Assignments are append-only (never updated, always insert new record)
- Negative assignments represent "unassigning" funds back to "To Assign"
- `funded_this_month` = SUM(amount) WHERE month = current_month

---

### 7. CategoryTarget

**Purpose**: Spending target configuration for category (FR-026, FR-027, FR-028)

**PostgreSQL Schema**:
```sql
CREATE TYPE target_type AS ENUM ('MONTHLY_NEEDED', 'TARGET_BALANCE', 'TARGET_BY_DATE');

CREATE TABLE category_targets (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id     UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    target_type     target_type NOT NULL,
    amount          DECIMAL(19, 4) NOT NULL CHECK (amount > 0),
    target_date     DATE,  -- Required for TARGET_BY_DATE, null otherwise
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(category_id),  -- One target per category
    CHECK (
        (target_type = 'TARGET_BY_DATE' AND target_date IS NOT NULL) OR
        (target_type != 'TARGET_BY_DATE' AND target_date IS NULL)
    )
);

CREATE INDEX idx_category_targets_user_id ON category_targets(user_id);
CREATE INDEX idx_category_targets_category_id ON category_targets(category_id);
```

**Python Type**:
```python
class TargetType(str, Enum):
    MONTHLY_NEEDED = "MONTHLY_NEEDED"
    TARGET_BALANCE = "TARGET_BALANCE"
    TARGET_BY_DATE = "TARGET_BY_DATE"

class CategoryTarget(Base):
    __tablename__ = "category_targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    target_type: Mapped[TargetType] = mapped_column(Enum(TargetType), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(19, 4), nullable=False)
    target_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Underfunded calculation (FR-028)
    def calculate_underfunded(self, funded_this_month: Decimal, available_now: Decimal, current_month: date) -> Decimal:
        """Calculate underfunded amount based on target type"""
        if self.target_type == TargetType.MONTHLY_NEEDED:
            return max(Decimal("0"), self.amount - funded_this_month)

        elif self.target_type == TargetType.TARGET_BALANCE:
            return max(Decimal("0"), self.amount - available_now)

        elif self.target_type == TargetType.TARGET_BY_DATE:
            # Calculate months_left including current month
            months_left = self._calculate_months_left(current_month)
            if months_left <= 0:
                months_left = 1  # Edge case: target month is current month

            needed_now = max(Decimal("0"), self.amount - available_now)
            suggested_monthly = (needed_now / months_left).quantize(Decimal("0.01"), rounding="ROUND_CEILING")
            return max(Decimal("0"), suggested_monthly - funded_this_month)

        return Decimal("0")

    def _calculate_months_left(self, current_month: date) -> int:
        """Calculate months from current_month to target_date (inclusive)"""
        if not self.target_date:
            return 0

        # Calculate month difference
        months = (self.target_date.year - current_month.year) * 12 + (self.target_date.month - current_month.month) + 1
        return max(1, months)  # Always at least 1 month
```

**Validation Rules** (FR-027):
- Amount: Must be > 0
- Target date: Cannot be in the past (validated on create/update)
- Target type: Must be one of the three enum values
- Constraint: TARGET_BY_DATE requires target_date, others must have null target_date

**Underfunded Calculation Logic** (FR-028):
Per the spec formulas:
- **Monthly Needed**: `underfunded = max(0, target_amount - funded_this_month)`
- **Target Balance**: `underfunded = max(0, target_amount - available_now)`
- **Target by Date**:
  ```
  months_left = months from current to target (inclusive)
  needed_now = max(0, target_amount - available_now)
  suggested_monthly = ceiling(needed_now / months_left)
  underfunded = max(0, suggested_monthly - funded_this_month)
  ```

---

### 8. CategorizationRule

**Purpose**: Auto-categorization rule (FR-008, FR-009)

**PostgreSQL Schema**:
```sql
CREATE TABLE categorization_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    payee_pattern   VARCHAR(255) NOT NULL,  -- Exact match or simple wildcard
    category_id     UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    created_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_categorization_rules_user_id ON categorization_rules(user_id);
CREATE INDEX idx_categorization_rules_payee_pattern ON categorization_rules(payee_pattern);
```

**Python Type**:
```python
class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    payee_pattern: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def matches(self, payee: str) -> bool:
        """Check if payee matches this rule pattern"""
        # MVP: simple case-insensitive exact match
        # Future: support wildcards, regex
        return self.payee_pattern.lower() in payee.lower()
```

**Validation Rules**:
- Payee pattern: Required
- Category: Must be valid category

**Business Rules** (FR-009):
- Matching transactions are auto-categorized but still require user approval
- Multiple rules can match same payee (first match wins or manual selection)
- Rules are applied when transactions are imported/created

---

### 9. Reconciliation

**Purpose**: Account reconciliation session (FR-021, FR-025)

**PostgreSQL Schema**:
```sql
CREATE TYPE reconciliation_status AS ENUM ('IN_PROGRESS', 'COMPLETED');

CREATE TABLE reconciliations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    account_id          UUID NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    statement_balance   DECIMAL(19, 4) NOT NULL,
    statement_date      DATE NOT NULL,
    status              reconciliation_status NOT NULL DEFAULT 'IN_PROGRESS',
    adjustment_transaction_id UUID REFERENCES transactions(id) ON DELETE SET NULL,  -- If discrepancy adjustment needed
    created_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at        TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_reconciliations_user_id ON reconciliations(user_id);
CREATE INDEX idx_reconciliations_account_id ON reconciliations(account_id);
CREATE INDEX idx_reconciliations_status ON reconciliations(status);
```

**Python Type**:
```python
class ReconciliationStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    statement_balance: Mapped[Decimal] = mapped_column(DECIMAL(19, 4), nullable=False)
    statement_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[ReconciliationStatus] = mapped_column(Enum(ReconciliationStatus), nullable=False, default=ReconciliationStatus.IN_PROGRESS, index=True)
    adjustment_transaction_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    def calculate_cleared_balance(self) -> Decimal:
        """Sum of all CLEARED transactions for this account up to statement_date"""
        pass

    def calculate_discrepancy(self) -> Decimal:
        """statement_balance - cleared_balance"""
        pass
```

**Validation Rules**:
- Statement balance: Required
- Statement date: Cannot be in future
- Adjustment transaction: Optional, only if discrepancy exists

**Business Rules** (FR-023, FR-024, FR-025):
- Calculate cleared_balance = SUM(CLEARED transaction amounts) for account
- Calculate discrepancy = statement_balance - cleared_balance
- If discrepancy ≠ 0: create adjustment transaction (FR-024)
- Mark COMPLETED when discrepancy = 0

---

## Indexes Summary

**Critical Indexes** (for query performance):
- `users.email`: Unique constraint + login queries
- `accounts.user_id`: Filter accounts by user
- `transactions.user_id, account_id, category_id, date, state`: Common filters
- `assignments.category_id, month`: Calculating funded_this_month
- `category_targets.category_id`: One target per category constraint

**Composite Indexes**:
- `assignments(category_id, month)`: Most common query pattern for budget calculations
- None others needed for MVP (single-user workload is small)

---

## Data Migration Strategy

### Alembic Migrations
1. Initial schema: Create all tables with constraints
2. Version control: Each schema change = new migration
3. Review before apply: Manually review auto-generated migrations

### Seed Data (Optional)
For development/testing:
- Default user with hashed password
- Sample category groups ("Monthly Bills", "Daily Living", "Savings")
- Sample categories ("Groceries", "Rent", "Emergency Fund")
- No production seed data (user creates own budget structure)

---

## Constraints & Validations Summary

**Database Constraints**:
- Primary keys: UUID on all tables
- Foreign keys: All relationships enforced with CASCADE/SET NULL as appropriate
- Unique constraints: email, category names, group names (per user)
- Check constraints: target amount > 0, target_date logic
- NOT NULL: All required fields enforced at DB level

**Application-Level Validations** (Pydantic):
- Email format validation
- Password strength (min 12 chars)
- Payee required
- Transaction amount non-zero
- Target date not in past
- Month is first day of month for assignments

---

## Testing Considerations

Per constitution's TDD requirements:

**Unit Tests**:
- Model methods (e.g., `CategoryTarget.calculate_underfunded`)
- Validation rules
- Business logic (state transitions)

**Integration Tests**:
- Database constraints (uniqueness, foreign keys)
- Transaction rollbacks
- Cascade deletes

**Test Data Generation**:
- Use Faker for realistic names, emails
- Use decimal.Decimal for all monetary values
- Use timezone-aware datetimes

---

**Status**: Data model complete. Ready for API contract generation.
