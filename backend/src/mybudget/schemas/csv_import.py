"""
CSV import Pydantic schemas for API request/response validation.
"""
from datetime import date as date_type
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CSVColumnMapping(BaseModel):
    """Schema for mapping CSV columns to transaction fields."""

    date_column: str = Field(..., description="Column name for transaction date")
    payee_column: str = Field(..., description="Column name for payee/description")
    amount_column: str = Field(..., description="Column name for amount")
    memo_column: str | None = Field(None, description="Column name for memo (optional)")
    date_format: str = Field(
        default="%Y-%m-%d",
        description="Date format string (e.g., '%Y-%m-%d', '%d/%m/%Y')",
    )
    decimal_separator: str = Field(
        default=".",
        description="Decimal separator ('.' or ',')",
    )
    amount_sign: str = Field(
        default="standard",
        description="How amounts are signed: 'standard' (negative=expense), 'inverted', or 'separate_columns'",
    )
    debit_column: str | None = Field(
        None,
        description="Debit column (for 'separate_columns' amount_sign)",
    )
    credit_column: str | None = Field(
        None,
        description="Credit column (for 'separate_columns' amount_sign)",
    )


class CSVPreviewRequest(BaseModel):
    """Schema for CSV preview request."""

    account_id: UUID = Field(..., description="Target account for import")
    mapping: CSVColumnMapping = Field(..., description="Column mapping configuration")
    skip_header: bool = Field(default=True, description="Skip first row as header")
    preview_rows: int = Field(default=5, ge=1, le=20, description="Number of rows to preview")


class CSVTransactionPreview(BaseModel):
    """Schema for a previewed transaction from CSV."""

    row_number: int
    date: date_type
    payee: str
    amount: Decimal
    memo: str | None = None
    is_duplicate: bool = Field(default=False, description="Whether transaction appears to be a duplicate")
    error: str | None = Field(None, description="Parsing error for this row if any")


class CSVPreviewResponse(BaseModel):
    """Schema for CSV preview response."""

    total_rows: int
    valid_rows: int
    error_rows: int
    duplicate_rows: int
    transactions: list[CSVTransactionPreview]
    sample_errors: list[str] = Field(
        default_factory=list,
        description="Sample of parsing errors encountered",
    )


class CSVImportRequest(BaseModel):
    """Schema for CSV import request."""

    account_id: UUID = Field(..., description="Target account for import")
    mapping: CSVColumnMapping = Field(..., description="Column mapping configuration")
    skip_header: bool = Field(default=True, description="Skip first row as header")
    skip_duplicates: bool = Field(default=True, description="Skip duplicate transactions")


class CSVImportResponse(BaseModel):
    """Schema for CSV import response."""

    total_rows: int
    imported_count: int
    skipped_count: int
    error_count: int
    duplicate_count: int
    errors: list[str] = Field(
        default_factory=list,
        description="List of errors encountered (max 10)",
    )
