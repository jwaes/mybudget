"""
Contract tests for CSV Import API endpoints.
"""
from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.account import Account, AccountType
from mybudget.models.transaction import Transaction, TransactionState
from mybudget.models.user import User


@pytest.mark.contract
class TestCSVImportPreview:
    """Contract tests for CSV import preview endpoint."""

    @pytest.mark.asyncio
    async def test_preview_csv_standard_format(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test previewing CSV import with standard format."""
        user = User(
            email="preview_csv@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
2024-01-16,Salary,3500.00
2024-01-17,Gas Station,-45.00
"""

        response = await client.post(
            "/api/import/csv/preview",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
                "date_format": "%Y-%m-%d",
                "decimal_separator": ".",
                "amount_sign": "standard",
                "delimiter": ",",
                "preview_rows": "5",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 3
        assert data["valid_rows"] == 3
        assert data["error_rows"] == 0
        assert len(data["transactions"]) == 3

        # Verify first transaction
        assert data["transactions"][0]["payee"] == "Grocery Store"
        assert Decimal(data["transactions"][0]["amount"]) == Decimal("-85.50")
        assert data["transactions"][0]["date"] == "2024-01-15"

    @pytest.mark.asyncio
    async def test_preview_csv_detects_duplicates(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that preview detects duplicate transactions."""
        user = User(
            email="preview_dup@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
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

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
2024-01-16,New Store,-50.00
"""

        response = await client.post(
            "/api/import/csv/preview",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2
        assert data["duplicate_rows"] == 1
        assert data["transactions"][0]["is_duplicate"] is True
        assert data["transactions"][1]["is_duplicate"] is False

    @pytest.mark.asyncio
    async def test_preview_csv_european_format(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test previewing CSV with European format (semicolon, comma decimal)."""
        user = User(
            email="preview_eu@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date;Payee;Debit;Credit
15/01/2024;Grocery Store;85,50;
16/01/2024;Salary;;3500,00
"""

        response = await client.post(
            "/api/import/csv/preview",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Payee",
                "amount_column": "Debit",
                "date_format": "%d/%m/%Y",
                "decimal_separator": ",",
                "amount_sign": "separate_columns",
                "debit_column": "Debit",
                "credit_column": "Credit",
                "delimiter": ";",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2
        assert data["valid_rows"] == 2

        # Verify amounts (debit negative, credit positive)
        assert Decimal(data["transactions"][0]["amount"]) == Decimal("-85.50")
        assert Decimal(data["transactions"][1]["amount"]) == Decimal("3500.00")

    @pytest.mark.asyncio
    async def test_preview_csv_invalid_column(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test preview fails with invalid column name."""
        user = User(
            email="preview_invalid@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
"""

        response = await client.post(
            "/api/import/csv/preview",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Payee",  # Column doesn't exist
                "amount_column": "Amount",
            },
            cookies=cookies,
        )

        assert response.status_code == 400
        assert "Column 'Payee' not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_preview_csv_nonexistent_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test preview fails with non-existent account."""
        user = User(
            email="preview_no_acct@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
"""
        from uuid import uuid4

        response = await client.post(
            "/api/import/csv/preview",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(uuid4()),  # Non-existent account
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
            },
            cookies=cookies,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"

    @pytest.mark.asyncio
    async def test_preview_csv_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test preview requires authentication."""
        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
"""
        from uuid import uuid4

        response = await client.post(
            "/api/import/csv/preview",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(uuid4()),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
            },
        )

        assert response.status_code == 401


@pytest.mark.contract
class TestCSVImportExecute:
    """Contract tests for CSV import execution endpoint."""

    @pytest.mark.asyncio
    async def test_import_csv_creates_transactions(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test importing CSV creates transactions in INBOX state."""
        user = User(
            email="import_csv@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
2024-01-16,Salary,3500.00
"""

        response = await client.post(
            "/api/import/csv/",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2
        assert data["imported_count"] == 2
        assert data["error_count"] == 0

        # Verify transactions were created
        stmt = select(Transaction).where(Transaction.account_id == account.id)
        result = await db_session.execute(stmt)
        transactions = result.scalars().all()

        assert len(transactions) == 2
        assert all(tx.state == TransactionState.INBOX for tx in transactions)
        assert all(tx.user_id == user.id for tx in transactions)

    @pytest.mark.asyncio
    async def test_import_csv_skips_duplicates(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test import skips duplicates when configured."""
        user = User(
            email="import_skip_dup@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
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

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
2024-01-16,New Store,-50.00
"""

        response = await client.post(
            "/api/import/csv/",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
                "skip_duplicates": "true",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2
        assert data["imported_count"] == 1
        assert data["duplicate_count"] == 1
        assert data["skipped_count"] == 1

        # Verify only one new transaction was created
        stmt = select(Transaction).where(
            Transaction.account_id == account.id,
            Transaction.payee == "New Store",
        )
        result = await db_session.execute(stmt)
        new_tx = result.scalar_one_or_none()
        assert new_tx is not None

    @pytest.mark.asyncio
    async def test_import_csv_allows_duplicates(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test import allows duplicates when configured."""
        user = User(
            email="import_allow_dup@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
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

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
"""

        response = await client.post(
            "/api/import/csv/",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
                "skip_duplicates": "false",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 1  # Imported despite being duplicate
        assert data["duplicate_count"] == 1

    @pytest.mark.asyncio
    async def test_import_csv_with_memo(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test importing CSV with memo column."""
        user = User(
            email="import_memo@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount,Notes
2024-01-15,Grocery Store,-85.50,Weekly shopping
"""

        response = await client.post(
            "/api/import/csv/",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
                "memo_column": "Notes",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 1

        # Verify memo was imported
        stmt = select(Transaction).where(Transaction.account_id == account.id)
        result = await db_session.execute(stmt)
        tx = result.scalar_one()
        assert tx.memo == "Weekly shopping"

    @pytest.mark.asyncio
    async def test_import_csv_handles_errors(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test import handles rows with errors gracefully."""
        user = User(
            email="import_errors@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
invalid-date,Bad Row,100.00
2024-01-17,Gas Station,-45.00
"""

        response = await client.post(
            "/api/import/csv/",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 3
        assert data["imported_count"] == 2
        assert data["error_count"] == 1
        assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_import_csv_user_isolation(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that users can't import to other users' accounts."""
        user1 = User(
            email="import_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="import_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        # Account belongs to user2
        account = Account(
            user_id=user2.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        # User1 tries to import to user2's account
        token = create_session_token(user1.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
"""

        response = await client.post(
            "/api/import/csv/",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
            },
            cookies=cookies,
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"

    @pytest.mark.asyncio
    async def test_import_csv_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test import requires authentication."""
        csv_content = b"""Date,Description,Amount
2024-01-15,Grocery Store,-85.50
"""
        from uuid import uuid4

        response = await client.post(
            "/api/import/csv/",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(uuid4()),
                "date_column": "Date",
                "payee_column": "Description",
                "amount_column": "Amount",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_import_csv_inverted_sign(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test importing CSV with inverted amount sign."""
        user = User(
            email="import_inverted@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # In inverted mode: positive = expense, negative = income
        csv_content = b"""Date,Payee,Amount
2024-01-15,Grocery Store,85.50
2024-01-16,Salary,-3500.00
"""

        response = await client.post(
            "/api/import/csv/",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Payee",
                "amount_column": "Amount",
                "amount_sign": "inverted",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 2

        # Verify amounts were inverted
        stmt = select(Transaction).where(
            Transaction.account_id == account.id,
            Transaction.payee == "Grocery Store",
        )
        result = await db_session.execute(stmt)
        grocery_tx = result.scalar_one()
        assert grocery_tx.amount == Decimal("-85.50")  # Inverted from positive

        stmt = select(Transaction).where(
            Transaction.account_id == account.id,
            Transaction.payee == "Salary",
        )
        result = await db_session.execute(stmt)
        salary_tx = result.scalar_one()
        assert salary_tx.amount == Decimal("3500.00")  # Inverted from negative

    @pytest.mark.asyncio
    async def test_import_csv_us_date_format(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test importing CSV with US date format (mm/dd/yyyy)."""
        user = User(
            email="import_us_date@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        csv_content = b"""Date,Payee,Amount
01/15/2024,Grocery Store,-85.50
"""

        response = await client.post(
            "/api/import/csv/",
            files={"file": ("transactions.csv", BytesIO(csv_content), "text/csv")},
            data={
                "account_id": str(account.id),
                "date_column": "Date",
                "payee_column": "Payee",
                "amount_column": "Amount",
                "date_format": "%m/%d/%Y",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 1

        # Verify date was parsed correctly
        stmt = select(Transaction).where(Transaction.account_id == account.id)
        result = await db_session.execute(stmt)
        tx = result.scalar_one()
        assert tx.date == date(2024, 1, 15)
