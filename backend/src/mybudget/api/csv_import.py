"""
CSV Import API endpoints.

Handles CSV file upload, preview, and import for transactions.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.api.dependencies import CurrentUser
from mybudget.db.session import get_db
from mybudget.models.account import Account
from mybudget.schemas.csv_import import (
    CSVColumnMapping,
    CSVImportResponse,
    CSVPreviewResponse,
)
from mybudget.services.csv_import_service import CSVImportService

router = APIRouter()

# Maximum file size: 5MB
MAX_FILE_SIZE = 5 * 1024 * 1024


async def _verify_account_ownership(
    db: AsyncSession, user_id: UUID, account_id: UUID
) -> Account | None:
    """Verify that the account belongs to the user."""
    stmt = select(Account).where(
        Account.id == account_id,
        Account.user_id == user_id,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@router.post("/preview", response_model=CSVPreviewResponse)
async def preview_csv_import(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(..., description="CSV file to preview"),
    account_id: UUID = Form(..., description="Target account ID"),
    date_column: str = Form(..., description="Column name for transaction date"),
    payee_column: str = Form(..., description="Column name for payee/description"),
    amount_column: str = Form(..., description="Column name for amount"),
    memo_column: str | None = Form(None, description="Column name for memo (optional)"),
    date_format: str = Form("%Y-%m-%d", description="Date format string"),
    decimal_separator: str = Form(".", description="Decimal separator ('.' or ',')"),
    amount_sign: str = Form("standard", description="Amount sign mode"),
    debit_column: str | None = Form(None, description="Debit column (for separate_columns mode)"),
    credit_column: str | None = Form(None, description="Credit column (for separate_columns mode)"),
    delimiter: str = Form(",", description="CSV delimiter"),
    preview_rows: int = Form(5, ge=1, le=20, description="Number of rows to preview"),
) -> CSVPreviewResponse:
    """
    Preview CSV import without committing.

    Upload a CSV file and get a preview of how transactions will be imported.
    This validates the mapping and shows sample rows with duplicate detection.
    """
    # Validate file type
    if file.content_type and file.content_type not in [
        "text/csv",
        "application/csv",
        "text/plain",
        "application/vnd.ms-excel",
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Must be CSV.",
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB.",
        )

    # Verify account ownership
    account = await _verify_account_ownership(db, current_user.id, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Build mapping
    mapping = CSVColumnMapping(
        date_column=date_column,
        payee_column=payee_column,
        amount_column=amount_column,
        memo_column=memo_column,
        date_format=date_format,
        decimal_separator=decimal_separator,
        amount_sign=amount_sign,
        debit_column=debit_column,
        credit_column=credit_column,
    )

    # Execute preview
    service = CSVImportService(db)
    try:
        preview = await service.preview_import(
            content, account_id, mapping, limit=preview_rows, delimiter=delimiter
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return preview


@router.post("/", response_model=CSVImportResponse)
async def import_csv(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(..., description="CSV file to import"),
    account_id: UUID = Form(..., description="Target account ID"),
    date_column: str = Form(..., description="Column name for transaction date"),
    payee_column: str = Form(..., description="Column name for payee/description"),
    amount_column: str = Form(..., description="Column name for amount"),
    memo_column: str | None = Form(None, description="Column name for memo (optional)"),
    date_format: str = Form("%Y-%m-%d", description="Date format string"),
    decimal_separator: str = Form(".", description="Decimal separator ('.' or ',')"),
    amount_sign: str = Form("standard", description="Amount sign mode"),
    debit_column: str | None = Form(None, description="Debit column (for separate_columns mode)"),
    credit_column: str | None = Form(None, description="Credit column (for separate_columns mode)"),
    delimiter: str = Form(",", description="CSV delimiter"),
    skip_duplicates: bool = Form(True, description="Skip duplicate transactions"),
) -> CSVImportResponse:
    """
    Import transactions from a CSV file.

    Upload a CSV file and import transactions into the specified account.
    Transactions are created in INBOX state, pending approval.
    """
    # Validate file type
    if file.content_type and file.content_type not in [
        "text/csv",
        "application/csv",
        "text/plain",
        "application/vnd.ms-excel",
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Must be CSV.",
        )

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // 1024 // 1024}MB.",
        )

    # Verify account ownership
    account = await _verify_account_ownership(db, current_user.id, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Build mapping
    mapping = CSVColumnMapping(
        date_column=date_column,
        payee_column=payee_column,
        amount_column=amount_column,
        memo_column=memo_column,
        date_format=date_format,
        decimal_separator=decimal_separator,
        amount_sign=amount_sign,
        debit_column=debit_column,
        credit_column=credit_column,
    )

    # Execute import
    service = CSVImportService(db)
    try:
        result = await service.execute_import(
            content,
            account_id,
            mapping,
            current_user.id,
            skip_duplicates=skip_duplicates,
            delimiter=delimiter,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return result
