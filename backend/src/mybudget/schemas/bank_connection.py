"""
Bank connection Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from mybudget.models.bank_connection import (
    BankConnectionStatus,
    LinkedAccountType,
)


class ConnectionHealthStatus(str, Enum):
    """Health status of a bank connection."""

    HEALTHY = "healthy"  # Active, valid token, recent sync
    WARNING = "warning"  # Token expiring within 7 days or sync stale
    ERROR = "error"  # Token expired, sync failed, or disconnected


class BankConnectionCreate(BaseModel):
    """Schema for initiating a new bank connection."""

    provider: str = Field(
        default="gocardless",
        description="Bank provider (currently only 'gocardless' supported)",
    )
    institution_id: str = Field(..., description="Institution ID from provider")
    redirect_url: str = Field(..., description="URL to redirect after OAuth")


class BankConnectionResponse(BaseModel):
    """Schema for bank connection response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    provider: str
    institution_id: str
    institution_name: str
    status: BankConnectionStatus
    status_detail: str | None = None
    last_sync_at: datetime | None = None
    next_sync_at: datetime | None = None
    access_valid_until: datetime | None = None
    created_at: datetime
    updated_at: datetime
    health_status: ConnectionHealthStatus | None = None


class BankConnectionWithAccountsResponse(BaseModel):
    """Schema for bank connection with linked accounts."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    provider: str
    institution_id: str
    institution_name: str
    status: BankConnectionStatus
    status_detail: str | None = None
    last_sync_at: datetime | None = None
    next_sync_at: datetime | None = None
    access_valid_until: datetime | None = None
    created_at: datetime
    updated_at: datetime
    linked_accounts: list["LinkedAccountResponse"]
    health_status: ConnectionHealthStatus | None = None


class BankConnectionListResponse(BaseModel):
    """Schema for list of bank connections response."""

    connections: list[BankConnectionResponse]
    total: int


class LinkedAccountResponse(BaseModel):
    """Schema for linked account response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    connection_id: UUID
    account_id: UUID | None = None
    provider_account_id: str
    account_name: str | None = None
    account_number_masked: str | None = None
    account_type: LinkedAccountType | None = None
    currency: str
    balance: Decimal | None = None
    balance_updated_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LinkedAccountLink(BaseModel):
    """Schema for linking a provider account to an internal account."""

    account_id: UUID = Field(..., description="Internal account ID to link to")


class InstitutionResponse(BaseModel):
    """Schema for bank institution from provider."""

    id: str = Field(..., description="Provider's institution ID")
    name: str = Field(..., description="Institution name")
    bic: str | None = Field(None, description="Bank Identifier Code (SWIFT)")
    logo_url: str | None = Field(None, description="URL to institution logo")
    countries: list[str] = Field(default_factory=list, description="Supported countries")


class InstitutionListResponse(BaseModel):
    """Schema for list of institutions response."""

    institutions: list[InstitutionResponse]
    total: int


class OAuthCallbackRequest(BaseModel):
    """Schema for OAuth callback from bank provider."""

    ref: str = Field(..., description="Reference ID from OAuth flow")


class OAuthInitResponse(BaseModel):
    """Schema for OAuth initialization response."""

    authorization_url: str = Field(..., description="URL to redirect user for bank auth")
    reference_id: str = Field(..., description="Reference to track this connection request")


class ReauthRequest(BaseModel):
    """Schema for re-authentication request."""

    redirect_url: str = Field(..., description="URL to redirect after OAuth")


# Forward reference resolution
BankConnectionWithAccountsResponse.model_rebuild()
