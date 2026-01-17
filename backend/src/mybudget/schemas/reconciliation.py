"""
Reconciliation Pydantic schemas for API request/response validation.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from mybudget.models.reconciliation import ReconciliationStatus


class ReconciliationCreate(BaseModel):
    """Schema for starting a new reconciliation."""

    account_id: UUID = Field(..., description="Account ID to reconcile")
    statement_balance: Decimal = Field(
        ..., description="Balance from bank statement"
    )
    statement_date: date = Field(..., description="Date of bank statement")

    @field_validator("statement_date")
    @classmethod
    def statement_date_not_in_future(cls, v: date) -> date:
        """Validate that statement date is not in the future."""
        from datetime import date as date_today

        if v > date_today.today():
            raise ValueError("Statement date cannot be in the future")
        return v


class ReconciliationMarkCleared(BaseModel):
    """Schema for marking transactions as cleared."""

    transaction_ids: list[UUID] = Field(
        ..., min_length=1, description="Transaction IDs to mark as cleared"
    )


class ReconciliationUnmarkCleared(BaseModel):
    """Schema for unmarking transactions as cleared."""

    transaction_ids: list[UUID] = Field(
        ..., min_length=1, description="Transaction IDs to unmark"
    )


class ReconciliationCreateAdjustment(BaseModel):
    """Schema for creating adjustment transaction."""

    category_id: UUID = Field(
        ..., description="Category ID for the adjustment transaction"
    )


class ReconciliationResponse(BaseModel):
    """Schema for reconciliation response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    account_id: UUID
    statement_balance: Decimal
    statement_date: date
    status: ReconciliationStatus
    adjustment_transaction_id: UUID | None
    created_at: datetime
    completed_at: datetime | None
    cleared_balance: Decimal = Field(
        ..., description="Sum of starting balance + cleared transactions"
    )
    discrepancy: Decimal = Field(
        ..., description="Difference between statement and cleared balance"
    )


class ReconciliationBalanceResponse(BaseModel):
    """Schema for reconciliation balance update response."""

    cleared_balance: Decimal
    discrepancy: Decimal


class ReconciliationAdjustmentResponse(BaseModel):
    """Schema for reconciliation adjustment response."""

    adjustment_transaction: dict  # TransactionResponse embedded


class ReconciliationListResponse(BaseModel):
    """Schema for list of reconciliations response."""

    reconciliations: list[ReconciliationResponse]


class TransactionClearedResponse(BaseModel):
    """Schema for transaction with cleared status."""

    id: UUID
    payee: str
    amount: Decimal
    date: date
    cleared: bool
