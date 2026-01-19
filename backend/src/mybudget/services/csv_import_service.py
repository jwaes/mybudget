"""
CSV import service for parsing and importing transactions from CSV files.
"""
from datetime import date as date_type
from datetime import datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO, StringIO
from typing import Any
from uuid import UUID

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.transaction import Transaction, TransactionState
from mybudget.schemas.csv_import import (
    CSVColumnMapping,
    CSVImportResponse,
    CSVPreviewResponse,
    CSVTransactionPreview,
)


class CSVImportService:
    """Service for CSV import operations."""

    def __init__(self, db: AsyncSession | None = None):
        """Initialize with optional database session."""
        self.db = db

    def parse_csv(
        self,
        file_content: bytes,
        mapping: CSVColumnMapping,
        delimiter: str = ",",
    ) -> list[dict[str, Any]]:
        """
        Parse CSV content using the provided column mapping.

        Args:
            file_content: Raw CSV file content as bytes
            mapping: Column mapping configuration
            delimiter: CSV delimiter (default: comma)

        Returns:
            List of parsed row dictionaries with keys: date, payee, amount, memo, error

        Raises:
            ValueError: If required columns are not found
        """
        # Try to detect encoding, default to utf-8
        try:
            content_str = file_content.decode("utf-8")
        except UnicodeDecodeError:
            content_str = file_content.decode("latin-1")

        # Read CSV with pandas
        try:
            df = pd.read_csv(
                StringIO(content_str),
                delimiter=delimiter,
                dtype=str,  # Read all as strings to handle manually
                keep_default_na=False,  # Don't convert empty strings to NaN
            )
        except pd.errors.EmptyDataError:
            return []

        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # Validate required columns exist
        required_columns = [mapping.date_column, mapping.payee_column]
        if mapping.amount_sign != "separate_columns":
            required_columns.append(mapping.amount_column)
        else:
            if mapping.debit_column:
                required_columns.append(mapping.debit_column)
            if mapping.credit_column:
                required_columns.append(mapping.credit_column)

        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in CSV. Available columns: {list(df.columns)}")

        # Optional memo column
        if mapping.memo_column and mapping.memo_column not in df.columns:
            raise ValueError(f"Column '{mapping.memo_column}' not found in CSV. Available columns: {list(df.columns)}")

        rows: list[dict[str, Any]] = []

        for idx, row in df.iterrows():
            parsed_row: dict[str, Any] = {
                "date": None,
                "payee": None,
                "amount": None,
                "memo": None,
                "error": None,
                "row_number": int(idx) + 2,  # +2 for header row and 0-based index
            }

            try:
                # Parse date
                date_str = str(row[mapping.date_column]).strip()
                parsed_row["date"] = datetime.strptime(date_str, mapping.date_format).date()

                # Parse payee
                parsed_row["payee"] = str(row[mapping.payee_column]).strip()

                # Parse amount based on sign mode
                parsed_row["amount"] = self._parse_amount(row, mapping)

                # Parse optional memo
                if mapping.memo_column:
                    memo_val = str(row[mapping.memo_column]).strip()
                    parsed_row["memo"] = memo_val if memo_val else None

            except Exception as e:
                parsed_row["error"] = str(e)

            rows.append(parsed_row)

        return rows

    def _parse_amount(
        self,
        row: pd.Series,
        mapping: CSVColumnMapping,
    ) -> Decimal:
        """
        Parse amount from CSV row based on mapping configuration.

        Args:
            row: Pandas Series representing CSV row
            mapping: Column mapping configuration

        Returns:
            Decimal amount (negative for expenses, positive for income)
        """
        if mapping.amount_sign == "separate_columns":
            # Handle separate debit/credit columns
            debit_str = str(row.get(mapping.debit_column, "")).strip() if mapping.debit_column else ""
            credit_str = str(row.get(mapping.credit_column, "")).strip() if mapping.credit_column else ""

            debit = self._parse_decimal(debit_str, mapping.decimal_separator)
            credit = self._parse_decimal(credit_str, mapping.decimal_separator)

            # Debit is negative (money out), credit is positive (money in)
            if debit and debit > 0:
                return -debit
            if credit and credit > 0:
                return credit
            return Decimal("0")

        # Single amount column
        amount_str = str(row[mapping.amount_column]).strip()
        amount = self._parse_decimal(amount_str, mapping.decimal_separator)

        if amount is None:
            raise ValueError(f"Invalid amount: {amount_str}")

        # Apply sign mode
        if mapping.amount_sign == "inverted":
            return -amount

        return amount  # standard mode

    def _parse_decimal(
        self,
        value: str,
        decimal_separator: str = ".",
    ) -> Decimal | None:
        """
        Parse a string value as Decimal.

        Args:
            value: String value to parse
            decimal_separator: Decimal separator ('.' or ',')

        Returns:
            Decimal value or None if empty/invalid
        """
        if not value:
            return None

        # Remove currency symbols and whitespace
        cleaned = value.strip()
        for char in ["$", "€", "£", "\xa0", " "]:
            cleaned = cleaned.replace(char, "")

        if not cleaned:
            return None

        # Handle decimal separator
        if decimal_separator == ",":
            # European format: 1.234,56 -> 1234.56
            cleaned = cleaned.replace(".", "").replace(",", ".")

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    async def preview_import(
        self,
        file_content: bytes,
        account_id: UUID,
        mapping: CSVColumnMapping,
        limit: int = 5,
        delimiter: str = ",",
    ) -> CSVPreviewResponse:
        """
        Preview CSV import without committing.

        Args:
            file_content: Raw CSV file content
            account_id: Target account ID
            mapping: Column mapping configuration
            limit: Number of rows to preview
            delimiter: CSV delimiter

        Returns:
            CSVPreviewResponse with preview data
        """
        rows = self.parse_csv(file_content, mapping, delimiter)

        # Count statistics
        total_rows = len(rows)
        valid_rows = sum(1 for r in rows if r["error"] is None)
        error_rows = total_rows - valid_rows

        # Detect duplicates for valid rows
        valid_parsed = [r for r in rows if r["error"] is None]
        duplicates = await self.detect_duplicates(valid_parsed, account_id) if self.db else [False] * len(valid_parsed)

        # Mark duplicates in rows
        dup_idx = 0
        for row in rows:
            if row["error"] is None:
                row["is_duplicate"] = duplicates[dup_idx]
                dup_idx += 1
            else:
                row["is_duplicate"] = False

        duplicate_count = sum(1 for d in duplicates if d)

        # Collect sample errors
        sample_errors = [
            f"Row {r['row_number']}: {r['error']}"
            for r in rows
            if r["error"] is not None
        ][:5]

        # Build preview transactions (limited)
        preview_txs = []
        for row in rows[:limit]:
            if row["error"] is None:
                preview_txs.append(
                    CSVTransactionPreview(
                        row_number=row["row_number"],
                        date=row["date"],
                        payee=row["payee"],
                        amount=row["amount"],
                        memo=row.get("memo"),
                        is_duplicate=row.get("is_duplicate", False),
                    )
                )
            else:
                # Include error rows in preview
                preview_txs.append(
                    CSVTransactionPreview(
                        row_number=row["row_number"],
                        date=date_type(1900, 1, 1),  # Placeholder date for error rows
                        payee=row.get("payee") or "Error",
                        amount=Decimal("0"),
                        error=row["error"],
                    )
                )

        return CSVPreviewResponse(
            total_rows=total_rows,
            valid_rows=valid_rows,
            error_rows=error_rows,
            duplicate_rows=duplicate_count,
            transactions=preview_txs,
            sample_errors=sample_errors,
        )

    async def detect_duplicates(
        self,
        transactions: list[dict[str, Any]],
        account_id: UUID,
    ) -> list[bool]:
        """
        Check for duplicate transactions in the database.

        Duplicates are detected based on matching: date, amount, and payee (case-insensitive)
        within the same account.

        Args:
            transactions: List of parsed transaction dictionaries
            account_id: Account ID to check against

        Returns:
            List of booleans indicating if each transaction is a duplicate
        """
        if not self.db or not transactions:
            return [False] * len(transactions)

        duplicates: list[bool] = []

        for tx in transactions:
            if tx.get("error") is not None:
                duplicates.append(False)
                continue

            # Query for existing transaction with same date, amount, and payee
            stmt = select(Transaction).where(
                Transaction.account_id == account_id,
                Transaction.date == tx["date"],
                Transaction.amount == tx["amount"],
                func.lower(Transaction.payee) == func.lower(tx["payee"]),
            )

            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()

            duplicates.append(existing is not None)

        return duplicates

    async def execute_import(
        self,
        file_content: bytes,
        account_id: UUID,
        mapping: CSVColumnMapping,
        user_id: UUID,
        skip_duplicates: bool = True,
        delimiter: str = ",",
    ) -> CSVImportResponse:
        """
        Execute CSV import and create transactions.

        Args:
            file_content: Raw CSV file content
            account_id: Target account ID
            mapping: Column mapping configuration
            user_id: User ID for created transactions
            skip_duplicates: Whether to skip duplicate transactions
            delimiter: CSV delimiter

        Returns:
            CSVImportResponse with import results
        """
        if not self.db:
            raise ValueError("Database session required for import")

        rows = self.parse_csv(file_content, mapping, delimiter)

        # Count statistics
        total_rows = len(rows)
        imported_count = 0
        skipped_count = 0
        error_count = 0
        duplicate_count = 0
        errors: list[str] = []

        # Get valid rows
        valid_rows = [r for r in rows if r["error"] is None]
        error_rows = [r for r in rows if r["error"] is not None]

        # Count errors
        error_count = len(error_rows)
        for err_row in error_rows[:10]:
            errors.append(f"Row {err_row['row_number']}: {err_row['error']}")

        # Detect duplicates
        duplicates = await self.detect_duplicates(valid_rows, account_id)

        # Import valid, non-duplicate rows
        for idx, row in enumerate(valid_rows):
            is_duplicate = duplicates[idx]

            if is_duplicate:
                duplicate_count += 1
                if skip_duplicates:
                    skipped_count += 1
                    continue

            # Create transaction
            transaction = Transaction(
                user_id=user_id,
                account_id=account_id,
                date=row["date"],
                payee=row["payee"],
                amount=row["amount"],
                memo=row.get("memo"),
                state=TransactionState.INBOX,
            )
            self.db.add(transaction)
            imported_count += 1

        await self.db.commit()

        return CSVImportResponse(
            total_rows=total_rows,
            imported_count=imported_count,
            skipped_count=skipped_count,
            error_count=error_count,
            duplicate_count=duplicate_count,
            errors=errors,
        )
