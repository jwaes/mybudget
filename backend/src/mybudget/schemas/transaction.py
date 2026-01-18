"""
Transaction Pydantic schemas for API request/response validation.
"""
from datetime import date as date_type
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mybudget.models.transaction import CategorizationSource, TransactionState


class TransactionCreate(BaseModel):
    """Schema for creating a new transaction."""

    account_id: UUID = Field(..., description="Account ID")
    date: date_type = Field(..., description="Transaction date")
    payee: str = Field(..., min_length=1, max_length=255, description="Payee/merchant name")
    amount: Decimal = Field(..., description="Transaction amount (positive=income, negative=expense)")
    memo: str | None = Field(None, max_length=1000, description="Optional memo/notes")
    category_id: UUID | None = Field(None, description="Category ID (optional for INBOX)")

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: Decimal) -> Decimal:
        """Validate that amount is not zero."""
        if v == Decimal("0"):
            raise ValueError("Amount cannot be zero")
        return v


class TransactionUpdate(BaseModel):
    """Schema for updating a transaction."""

    date: date_type | None = Field(None, description="Transaction date")
    payee: str | None = Field(None, min_length=1, max_length=255, description="Payee/merchant name")
    amount: Decimal | None = Field(None, description="Transaction amount")
    memo: str | None = Field(None, max_length=1000, description="Optional memo/notes")
    category_id: UUID | None = Field(None, description="Category ID")

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: Decimal | None) -> Decimal | None:
        """Validate that amount is not zero if provided."""
        if v is not None and v == Decimal("0"):
            raise ValueError("Amount cannot be zero")
        return v


class TransactionApprove(BaseModel):
    """Schema for approving a transaction."""

    category_id: UUID | None = Field(
        None, description="Category ID (optional - if null, goes to Ready to Assign)"
    )


class TransactionResponse(BaseModel):
    """Schema for transaction response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    account_id: UUID
    category_id: UUID | None
    date: date_type
    payee: str
    amount: Decimal
    memo: str | None
    state: TransactionState
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    cleared_at: datetime | None
    categorization_source: CategorizationSource | None = None
    confidence_score: Decimal | None = None


class TransactionWithDetailsResponse(BaseModel):
    """Schema for transaction response with account and category names."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    account_id: UUID
    account_name: str
    category_id: UUID | None
    category_name: str | None
    date: date_type
    payee: str
    amount: Decimal
    memo: str | None
    state: TransactionState
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None
    cleared_at: datetime | None


class TransactionListResponse(BaseModel):
    """Schema for list of transactions response."""

    transactions: list[TransactionResponse]
    total: int


class TransactionBulkApprove(BaseModel):
    """Schema for bulk approving transactions."""

    transaction_ids: list[UUID] = Field(..., min_length=1, description="Transaction IDs to approve")
    category_id: UUID = Field(..., description="Category ID to assign")


class TransactionBulkResult(BaseModel):
    """Schema for bulk operation result."""

    success_count: int
    failed_count: int
    failed_ids: list[UUID]
