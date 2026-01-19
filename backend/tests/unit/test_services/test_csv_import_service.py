"""
Unit tests for CSV import service.
"""
from datetime import date
from decimal import Decimal
from io import BytesIO
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.models.account import Account, AccountType
from mybudget.models.transaction import Transaction, TransactionState
from mybudget.models.user import User
from mybudget.lib.auth import hash_password
from mybudget.schemas.csv_import import CSVColumnMapping
from mybudget.services.csv_import_service import CSVImportService


@pytest.mark.unit
class TestParseCSV:
    """Tests for parse_csv method."""

    def test_parse_csv_standard_format(self) -> None:
        """Test parsing CSV with standard format (comma separated, negative amounts)."""
        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
2024-01-16,Salary,3500.00
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Description",
            amount_column="Amount",
            date_format="%Y-%m-%d",
            decimal_separator=".",
            amount_sign="standard",
        )

        service = CSVImportService()
        rows = service.parse_csv(csv_content, mapping)

        assert len(rows) == 2
        assert rows[0]["date"] == date(2024, 1, 15)
        assert rows[0]["payee"] == "Grocery Store"
        assert rows[0]["amount"] == Decimal("-85.50")

        assert rows[1]["date"] == date(2024, 1, 16)
        assert rows[1]["payee"] == "Salary"
        assert rows[1]["amount"] == Decimal("3500.00")

    def test_parse_csv_european_format(self) -> None:
        """Test parsing CSV with European format (semicolon separated, comma decimals)."""
        csv_content = b"""Date;Payee;Debit;Credit
15/01/2024;Grocery Store;85,50;
16/01/2024;Salary;;3500,00
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Debit",  # Not used with separate_columns
            date_format="%d/%m/%Y",
            decimal_separator=",",
            amount_sign="separate_columns",
            debit_column="Debit",
            credit_column="Credit",
        )

        service = CSVImportService()
        rows = service.parse_csv(csv_content, mapping, delimiter=";")

        assert len(rows) == 2
        assert rows[0]["date"] == date(2024, 1, 15)
        assert rows[0]["payee"] == "Grocery Store"
        assert rows[0]["amount"] == Decimal("-85.50")  # Debit is negative

        assert rows[1]["date"] == date(2024, 1, 16)
        assert rows[1]["payee"] == "Salary"
        assert rows[1]["amount"] == Decimal("3500.00")  # Credit is positive

    def test_parse_csv_with_memo(self) -> None:
        """Test parsing CSV with optional memo column."""
        csv_content = b"""Date,Description,Amount,Notes
2024-01-15,Grocery Store,-85.50,Weekly shopping
2024-01-16,Gas Station,-45.00,
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Description",
            amount_column="Amount",
            memo_column="Notes",
        )

        service = CSVImportService()
        rows = service.parse_csv(csv_content, mapping)

        assert len(rows) == 2
        assert rows[0]["memo"] == "Weekly shopping"
        assert rows[1]["memo"] is None or rows[1]["memo"] == ""

    def test_parse_csv_inverted_sign(self) -> None:
        """Test parsing CSV with inverted sign (positive=expense)."""
        csv_content = b"""Date,Payee,Amount
2024-01-15,Grocery Store,85.50
2024-01-16,Salary,-3500.00
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
            amount_sign="inverted",
        )

        service = CSVImportService()
        rows = service.parse_csv(csv_content, mapping)

        assert rows[0]["amount"] == Decimal("-85.50")  # Inverted: positive becomes negative
        assert rows[1]["amount"] == Decimal("3500.00")  # Inverted: negative becomes positive

    def test_parse_csv_us_date_format(self) -> None:
        """Test parsing CSV with US date format (mm/dd/yyyy)."""
        csv_content = b"""Date,Payee,Amount
01/15/2024,Grocery Store,-85.50
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
            date_format="%m/%d/%Y",
        )

        service = CSVImportService()
        rows = service.parse_csv(csv_content, mapping)

        assert rows[0]["date"] == date(2024, 1, 15)

    def test_parse_csv_with_errors(self) -> None:
        """Test parsing CSV with some invalid rows."""
        csv_content = b"""Date,Payee,Amount
2024-01-15,Grocery Store,-85.50
invalid-date,Bad Row,100.00
2024-01-17,Gas Station,-45.00
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
        )

        service = CSVImportService()
        rows = service.parse_csv(csv_content, mapping)

        # Should have 3 rows, with one having an error
        assert len(rows) == 3
        assert rows[0]["error"] is None
        assert rows[1]["error"] is not None  # Invalid date
        assert rows[2]["error"] is None

    def test_parse_csv_empty_file(self) -> None:
        """Test parsing empty CSV file."""
        csv_content = b"""Date,Payee,Amount
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
        )

        service = CSVImportService()
        rows = service.parse_csv(csv_content, mapping)

        assert len(rows) == 0

    def test_parse_csv_missing_column(self) -> None:
        """Test parsing CSV with missing required column."""
        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",  # Column doesn't exist
            amount_column="Amount",
        )

        service = CSVImportService()
        with pytest.raises(ValueError, match="Column 'Payee' not found"):
            service.parse_csv(csv_content, mapping)

    def test_parse_csv_strips_whitespace(self) -> None:
        """Test that CSV parsing strips whitespace from values."""
        csv_content = b"""Date,Payee,Amount
2024-01-15,  Grocery Store  ,-85.50
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
        )

        service = CSVImportService()
        rows = service.parse_csv(csv_content, mapping)

        assert rows[0]["payee"] == "Grocery Store"


@pytest.mark.unit
class TestPreviewImport:
    """Tests for preview_import method."""

    @pytest.mark.asyncio
    async def test_preview_import_returns_limited_rows(
        self, db_session: AsyncSession
    ) -> None:
        """Test that preview returns limited number of rows."""
        user = User(
            email="preview_test@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        csv_content = b"""Date,Payee,Amount
2024-01-15,Store 1,-10.00
2024-01-16,Store 2,-20.00
2024-01-17,Store 3,-30.00
2024-01-18,Store 4,-40.00
2024-01-19,Store 5,-50.00
2024-01-20,Store 6,-60.00
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
        )

        service = CSVImportService(db_session)
        preview = await service.preview_import(csv_content, account.id, mapping, limit=3)

        assert preview.total_rows == 6
        assert len(preview.transactions) == 3
        assert preview.transactions[0].payee == "Store 1"
        assert preview.transactions[2].payee == "Store 3"

    @pytest.mark.asyncio
    async def test_preview_import_counts_errors(
        self, db_session: AsyncSession
    ) -> None:
        """Test that preview counts error rows."""
        user = User(
            email="preview_errors@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        csv_content = b"""Date,Payee,Amount
2024-01-15,Store 1,-10.00
invalid-date,Bad Row,100.00
2024-01-17,Store 3,-30.00
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
        )

        service = CSVImportService(db_session)
        preview = await service.preview_import(csv_content, account.id, mapping, limit=10)

        assert preview.total_rows == 3
        assert preview.valid_rows == 2
        assert preview.error_rows == 1
        assert len(preview.sample_errors) > 0


@pytest.mark.unit
class TestDetectDuplicates:
    """Tests for detect_duplicates method."""

    @pytest.mark.asyncio
    async def test_detect_duplicates_finds_matches(
        self, db_session: AsyncSession
    ) -> None:
        """Test that duplicates are detected based on date, amount, payee."""
        user = User(
            email="dup_detect@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        # Create existing transaction
        existing_tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2024, 1, 15),
            payee="Grocery Store",
            amount=Decimal("-85.50"),
            state=TransactionState.INBOX,
        )
        db_session.add(existing_tx)
        await db_session.flush()

        # Try to detect duplicates
        parsed_rows = [
            {
                "date": date(2024, 1, 15),
                "payee": "Grocery Store",
                "amount": Decimal("-85.50"),
                "memo": None,
                "error": None,
            },
            {
                "date": date(2024, 1, 16),
                "payee": "Different Store",
                "amount": Decimal("-50.00"),
                "memo": None,
                "error": None,
            },
        ]

        service = CSVImportService(db_session)
        duplicates = await service.detect_duplicates(parsed_rows, account.id)

        assert len(duplicates) == 2
        assert duplicates[0] is True  # First row is duplicate
        assert duplicates[1] is False  # Second row is not duplicate

    @pytest.mark.asyncio
    async def test_detect_duplicates_case_insensitive(
        self, db_session: AsyncSession
    ) -> None:
        """Test that payee matching is case-insensitive."""
        user = User(
            email="dup_case@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        existing_tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2024, 1, 15),
            payee="GROCERY STORE",
            amount=Decimal("-85.50"),
            state=TransactionState.INBOX,
        )
        db_session.add(existing_tx)
        await db_session.flush()

        parsed_rows = [
            {
                "date": date(2024, 1, 15),
                "payee": "grocery store",  # Lowercase
                "amount": Decimal("-85.50"),
                "memo": None,
                "error": None,
            },
        ]

        service = CSVImportService(db_session)
        duplicates = await service.detect_duplicates(parsed_rows, account.id)

        assert duplicates[0] is True  # Should still detect as duplicate


@pytest.mark.unit
class TestExecuteImport:
    """Tests for execute_import method."""

    @pytest.mark.asyncio
    async def test_execute_import_creates_transactions(
        self, db_session: AsyncSession
    ) -> None:
        """Test that execute_import creates transactions in INBOX state."""
        user = User(
            email="exec_import@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        csv_content = b"""Date,Payee,Amount
2024-01-15,Grocery Store,-85.50
2024-01-16,Salary,3500.00
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
        )

        service = CSVImportService(db_session)
        result = await service.execute_import(
            csv_content, account.id, mapping, user.id, skip_duplicates=True
        )

        assert result.total_rows == 2
        assert result.imported_count == 2
        assert result.skipped_count == 0
        assert result.error_count == 0

    @pytest.mark.asyncio
    async def test_execute_import_skips_duplicates(
        self, db_session: AsyncSession
    ) -> None:
        """Test that execute_import skips duplicates when configured."""
        user = User(
            email="exec_skip@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        # Create existing transaction
        existing_tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2024, 1, 15),
            payee="Grocery Store",
            amount=Decimal("-85.50"),
            state=TransactionState.INBOX,
        )
        db_session.add(existing_tx)
        await db_session.flush()

        csv_content = b"""Date,Payee,Amount
2024-01-15,Grocery Store,-85.50
2024-01-16,New Store,-50.00
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
        )

        service = CSVImportService(db_session)
        result = await service.execute_import(
            csv_content, account.id, mapping, user.id, skip_duplicates=True
        )

        assert result.total_rows == 2
        assert result.imported_count == 1  # Only non-duplicate
        assert result.duplicate_count == 1
        assert result.skipped_count == 1  # Skipped due to duplicate

    @pytest.mark.asyncio
    async def test_execute_import_imports_duplicates_when_disabled(
        self, db_session: AsyncSession
    ) -> None:
        """Test that execute_import imports duplicates when skip_duplicates=False."""
        user = User(
            email="exec_allow_dup@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        # Create existing transaction
        existing_tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2024, 1, 15),
            payee="Grocery Store",
            amount=Decimal("-85.50"),
            state=TransactionState.INBOX,
        )
        db_session.add(existing_tx)
        await db_session.flush()

        csv_content = b"""Date,Payee,Amount
2024-01-15,Grocery Store,-85.50
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
        )

        service = CSVImportService(db_session)
        result = await service.execute_import(
            csv_content, account.id, mapping, user.id, skip_duplicates=False
        )

        assert result.total_rows == 1
        assert result.imported_count == 1  # Imported even though duplicate
        assert result.duplicate_count == 1  # Still counted as duplicate

    @pytest.mark.asyncio
    async def test_execute_import_skips_error_rows(
        self, db_session: AsyncSession
    ) -> None:
        """Test that execute_import skips rows with parsing errors."""
        user = User(
            email="exec_errors@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        csv_content = b"""Date,Payee,Amount
2024-01-15,Grocery Store,-85.50
invalid-date,Bad Row,100.00
2024-01-17,Gas Station,-45.00
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
        )

        service = CSVImportService(db_session)
        result = await service.execute_import(
            csv_content, account.id, mapping, user.id, skip_duplicates=True
        )

        assert result.total_rows == 3
        assert result.imported_count == 2
        assert result.error_count == 1
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_execute_import_with_memo(
        self, db_session: AsyncSession
    ) -> None:
        """Test that execute_import includes memo field."""
        user = User(
            email="exec_memo@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        csv_content = b"""Date,Payee,Amount,Notes
2024-01-15,Grocery Store,-85.50,Weekly shopping
"""
        mapping = CSVColumnMapping(
            date_column="Date",
            payee_column="Payee",
            amount_column="Amount",
            memo_column="Notes",
        )

        service = CSVImportService(db_session)
        result = await service.execute_import(
            csv_content, account.id, mapping, user.id, skip_duplicates=True
        )

        assert result.imported_count == 1

        # Verify the transaction was created with memo
        from sqlalchemy import select
        stmt = select(Transaction).where(
            Transaction.account_id == account.id,
            Transaction.payee == "Grocery Store",
        )
        db_result = await db_session.execute(stmt)
        tx = db_result.scalar_one()
        assert tx.memo == "Weekly shopping"
        assert tx.state == TransactionState.INBOX
