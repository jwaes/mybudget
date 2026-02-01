"""
Account Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from mybudget.models.account import AccountType, SyncStatus
from mybudget.schemas.bank_connection import ConnectionHealthStatus


class AccountCreate(BaseModel):
    """Schema for creating a new account."""

    name: str = Field(..., min_length=1, max_length=100, description="Account name")
    account_type: AccountType = Field(..., description="Account type (CHECKING or SAVINGS)")
    initial_balance: Decimal = Field(..., description="Initial account balance")


class AccountUpdate(BaseModel):
    """Schema for updating an account."""

    name: str | None = Field(None, min_length=1, max_length=100, description="Account name")


class AccountResponse(BaseModel):
    """Schema for account response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    account_type: AccountType
    balance: Decimal
    initial_balance: Decimal
    created_at: datetime
    updated_at: datetime
    sync_status: SyncStatus
    last_sync_at: datetime | None = None
    sync_error: str | None = None
    # Bank connection fields (for linked accounts)
    bank_connection_id: UUID | None = None
    bank_connection_name: str | None = None
    bank_connection_health: ConnectionHealthStatus | None = None


class AccountListResponse(BaseModel):
    """Schema for list of accounts response."""

    accounts: list[AccountResponse]
    total: int
