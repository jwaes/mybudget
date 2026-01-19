"""
Contract tests for Transactions API endpoints.
"""
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.account import Account, AccountType
from mybudget.models.category import Category, CategoryGroup
from mybudget.models.transaction import Transaction, TransactionState
from mybudget.models.categorization_rule import CategorizationRule
from mybudget.models.user import User


@pytest.mark.contract
class TestTransactionsAPI:
    """Contract tests for transactions API."""

    @pytest.mark.asyncio
    async def test_create_transaction(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a new transaction."""
        user = User(
            email="create_tx@example.com",
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

        response = await client.post(
            "/api/transactions/",
            json={
                "account_id": str(account.id),
                "date": "2026-01-15",
                "payee": "Grocery Store",
                "amount": "-50.00",
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["payee"] == "Grocery Store"
        assert data["amount"] == "-50.0000"
        assert data["state"] == "INBOX"
        assert data["account_id"] == str(account.id)

    @pytest.mark.asyncio
    async def test_create_transaction_invalid_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating transaction with non-existent account."""
        user = User(
            email="create_tx_invalid@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/transactions/",
            json={
                "account_id": str(uuid4()),
                "date": "2026-01-15",
                "payee": "Test",
                "amount": "-10.00",
            },
            cookies=cookies,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_list_transactions(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing transactions."""
        user = User(
            email="list_tx@example.com",
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

        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store 1",
            amount=Decimal("-25.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 16),
            payee="Store 2",
            amount=Decimal("-30.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/transactions/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["transactions"]) == 2

    @pytest.mark.asyncio
    async def test_list_inbox_transactions(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing inbox transactions."""
        user = User(
            email="list_inbox@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        tx_inbox = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Inbox TX",
            amount=Decimal("-25.00"),
            state=TransactionState.INBOX,
        )
        tx_approved = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date(2026, 1, 16),
            payee="Approved TX",
            amount=Decimal("-30.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add_all([tx_inbox, tx_approved])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/transactions/inbox", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["transactions"][0]["payee"] == "Inbox TX"

    @pytest.mark.asyncio
    async def test_get_transaction(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting a transaction by ID."""
        user = User(
            email="get_tx@example.com",
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

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test Payee",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/transactions/{tx.id}", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["payee"] == "Test Payee"

    @pytest.mark.asyncio
    async def test_approve_transaction(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test approving a transaction."""
        user = User(
            email="approve_tx@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Grocery Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/transactions/{tx.id}/approve",
            json={"category_id": str(category.id)},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "APPROVED"
        assert data["category_id"] == str(category.id)
        assert data["approved_at"] is not None

    @pytest.mark.asyncio
    async def test_unapprove_transaction(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test unapproving a transaction."""
        user = User(
            email="unapprove_tx@example.com",
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
            balance=Decimal("-50.00"),  # Already has approved transaction effect
        )
        db_session.add(account)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date(2026, 1, 15),
            payee="Grocery Store",
            amount=Decimal("-50.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/transactions/{tx.id}/unapprove",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "INBOX"
        assert data["approved_at"] is None

    @pytest.mark.asyncio
    async def test_update_transaction(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating a transaction."""
        user = User(
            email="update_tx@example.com",
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

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Old Payee",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/transactions/{tx.id}",
            json={"payee": "New Payee", "memo": "Updated memo"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["payee"] == "New Payee"
        assert data["memo"] == "Updated memo"

    @pytest.mark.asyncio
    async def test_delete_transaction(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test deleting a transaction."""
        user = User(
            email="delete_tx@example.com",
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

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Delete Me",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(f"/api/transactions/{tx.id}", cookies=cookies)

        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/transactions/{tx.id}", cookies=cookies)
        assert get_response.status_code == 404


@pytest.mark.contract
class TestCategorizationSource:
    """Contract tests for categorization source functionality (FR-043, FR-044, FR-045)."""

    @pytest.mark.asyncio
    async def test_approved_transaction_has_manual_source(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that approved transactions have categorization_source=MANUAL (T221)."""
        user = User(
            email="cat_source@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Grocery Store",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/transactions/{tx.id}/approve",
            json={"category_id": str(category.id)},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["categorization_source"] == "MANUAL"
        assert data["confidence_score"] is None  # Manual categorization has no confidence score

    @pytest.mark.asyncio
    async def test_transaction_response_includes_categorization_fields(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that transaction responses include categorization fields."""
        user = User(
            email="cat_fields@example.com",
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

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/transactions/{tx.id}", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        # Verify categorization fields are present in response
        assert "categorization_source" in data
        assert "confidence_score" in data

    @pytest.mark.asyncio
    async def test_inbox_transaction_has_no_categorization_source(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that inbox transactions have no categorization_source."""
        user = User(
            email="inbox_source@example.com",
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

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Test",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/transactions/{tx.id}", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["categorization_source"] is None
        assert data["confidence_score"] is None


@pytest.mark.contract
class TestBatchApprove:
    """Contract tests for batch approve functionality (FR-045)."""

    @pytest.mark.asyncio
    async def test_batch_approve_transactions(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test batch approving multiple transactions (T222)."""
        user = User(
            email="batch_approve@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        # Create 3 inbox transactions
        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store 1",
            amount=Decimal("-25.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 16),
            payee="Store 2",
            amount=Decimal("-30.00"),
            state=TransactionState.INBOX,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 17),
            payee="Store 3",
            amount=Decimal("-35.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/transactions/batch-approve",
            json={
                "transaction_ids": [str(tx1.id), str(tx2.id), str(tx3.id)],
                "category_id": str(category.id),
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 3
        assert data["failed_count"] == 0
        assert data["failed_ids"] == []

        # Verify transactions are now approved
        get_response = await client.get(f"/api/transactions/{tx1.id}", cookies=cookies)
        assert get_response.json()["state"] == "APPROVED"
        assert get_response.json()["category_id"] == str(category.id)
        assert get_response.json()["categorization_source"] == "MANUAL"

    @pytest.mark.asyncio
    async def test_batch_approve_invalid_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test batch approve with non-existent category fails all transactions."""
        user = User(
            email="batch_invalid_cat@example.com",
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

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store",
            amount=Decimal("-25.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/transactions/batch-approve",
            json={
                "transaction_ids": [str(tx.id)],
                "category_id": str(uuid4()),  # Non-existent category
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 0
        assert data["failed_count"] == 1
        assert str(tx.id) in [str(id) for id in data["failed_ids"]]

    @pytest.mark.asyncio
    async def test_batch_approve_already_approved(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test batch approve skips already approved transactions."""
        user = User(
            email="batch_already@example.com",
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
            balance=Decimal("-25.00"),  # Already has approved transaction effect
        )
        db_session.add(account)
        await db_session.flush()

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        # One inbox, one already approved
        tx_inbox = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Inbox TX",
            amount=Decimal("-30.00"),
            state=TransactionState.INBOX,
        )
        tx_approved = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date(2026, 1, 16),
            payee="Already Approved",
            amount=Decimal("-25.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add_all([tx_inbox, tx_approved])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/transactions/batch-approve",
            json={
                "transaction_ids": [str(tx_inbox.id), str(tx_approved.id)],
                "category_id": str(category.id),
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1  # Only inbox was approved
        assert data["failed_count"] == 1  # Already approved failed
        assert str(tx_approved.id) in [str(id) for id in data["failed_ids"]]

    @pytest.mark.asyncio
    async def test_batch_approve_mixed_results(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test batch approve with mixed valid/invalid transactions."""
        user = User(
            email="batch_mixed@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Valid TX",
            amount=Decimal("-25.00"),
            state=TransactionState.INBOX,
        )
        db_session.add(tx)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        non_existent_id = uuid4()

        response = await client.post(
            "/api/transactions/batch-approve",
            json={
                "transaction_ids": [str(tx.id), str(non_existent_id)],
                "category_id": str(category.id),
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["failed_count"] == 1
        assert str(non_existent_id) in [str(id) for id in data["failed_ids"]]

    @pytest.mark.asyncio
    async def test_batch_approve_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test batch approve without authentication fails."""
        response = await client.post(
            "/api/transactions/batch-approve",
            json={
                "transaction_ids": [str(uuid4())],
                "category_id": str(uuid4()),
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_batch_approve_empty_list_validation(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test batch approve with empty transaction list fails validation."""
        user = User(
            email="batch_empty@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/transactions/batch-approve",
            json={
                "transaction_ids": [],  # Empty list
                "category_id": str(uuid4()),
            },
            cookies=cookies,
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.contract
class TestTransactionSearchAPI:
    """Contract tests for transaction search and filter API (FR-046 to FR-052)."""

    @pytest.mark.asyncio
    async def test_search_by_payee_partial_match(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test searching transactions by payee (partial match, case-insensitive) (FR-046)."""
        user = User(
            email="search_payee@example.com",
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

        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Whole Foods Market",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 16),
            payee="WHOLE FOODS",
            amount=Decimal("-75.00"),
            state=TransactionState.INBOX,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 17),
            payee="Target",
            amount=Decimal("-30.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Search for "whole" - should match both Whole Foods transactions (case-insensitive)
        response = await client.get(
            "/api/transactions/",
            params={"payee_search": "whole"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        payees = [tx["payee"] for tx in data["transactions"]]
        assert "Whole Foods Market" in payees
        assert "WHOLE FOODS" in payees
        assert "Target" not in payees

    @pytest.mark.asyncio
    async def test_search_by_memo_partial_match(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test searching transactions by memo (partial match, case-insensitive) (FR-047)."""
        user = User(
            email="search_memo@example.com",
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

        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Store 1",
            memo="Birthday gift for mom",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 16),
            payee="Store 2",
            memo="BIRTHDAY party supplies",
            amount=Decimal("-75.00"),
            state=TransactionState.INBOX,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 17),
            payee="Store 3",
            memo="Weekly groceries",
            amount=Decimal("-30.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Search for "birthday" - should match both birthday-related transactions
        response = await client.get(
            "/api/transactions/",
            params={"memo_search": "birthday"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        memos = [tx["memo"] for tx in data["transactions"]]
        assert "Birthday gift for mom" in memos
        assert "BIRTHDAY party supplies" in memos
        assert "Weekly groceries" not in memos

    @pytest.mark.asyncio
    async def test_filter_by_date_range(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering transactions by date range (FR-048)."""
        user = User(
            email="filter_date@example.com",
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

        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 10),
            payee="Early TX",
            amount=Decimal("-10.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Mid TX",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 20),
            payee="Late TX",
            amount=Decimal("-30.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Filter for Jan 12-18 - should only get Mid TX
        response = await client.get(
            "/api/transactions/",
            params={"date_from": "2026-01-12", "date_to": "2026-01-18"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["transactions"][0]["payee"] == "Mid TX"

    @pytest.mark.asyncio
    async def test_filter_by_date_from_only(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering transactions by date_from only (FR-048)."""
        user = User(
            email="filter_date_from@example.com",
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

        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 10),
            payee="Early TX",
            amount=Decimal("-10.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Mid TX",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 20),
            payee="Late TX",
            amount=Decimal("-30.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Filter for transactions on or after Jan 15
        response = await client.get(
            "/api/transactions/",
            params={"date_from": "2026-01-15"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        payees = [tx["payee"] for tx in data["transactions"]]
        assert "Early TX" not in payees
        assert "Mid TX" in payees
        assert "Late TX" in payees

    @pytest.mark.asyncio
    async def test_filter_by_amount_range(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering transactions by amount range (FR-049)."""
        user = User(
            email="filter_amount@example.com",
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

        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Small TX",
            amount=Decimal("-10.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 16),
            payee="Medium TX",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 17),
            payee="Large TX",
            amount=Decimal("-100.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Filter for amounts between -75 and -25 (should get Medium TX)
        response = await client.get(
            "/api/transactions/",
            params={"amount_min": "-75.00", "amount_max": "-25.00"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["transactions"][0]["payee"] == "Medium TX"

    @pytest.mark.asyncio
    async def test_filter_by_category(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering transactions by category (FR-050)."""
        user = User(
            email="filter_category@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        groceries = Category(user_id=user.id, group_id=group.id, name="Groceries")
        dining = Category(user_id=user.id, group_id=group.id, name="Dining")
        db_session.add_all([groceries, dining])
        await db_session.flush()

        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=groceries.id,
            date=date(2026, 1, 15),
            payee="Grocery Store",
            amount=Decimal("-50.00"),
            state=TransactionState.APPROVED,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=dining.id,
            date=date(2026, 1, 16),
            payee="Restaurant",
            amount=Decimal("-30.00"),
            state=TransactionState.APPROVED,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 17),
            payee="Uncategorized TX",
            amount=Decimal("-20.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Filter for groceries category only
        response = await client.get(
            "/api/transactions/",
            params={"category_id": str(groceries.id)},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["transactions"][0]["payee"] == "Grocery Store"
        assert data["transactions"][0]["category_id"] == str(groceries.id)

    @pytest.mark.asyncio
    async def test_filter_uncategorized_only(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering for uncategorized transactions only (FR-050)."""
        user = User(
            email="filter_uncat@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date(2026, 1, 15),
            payee="Categorized TX",
            amount=Decimal("-50.00"),
            state=TransactionState.APPROVED,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 16),
            payee="Uncategorized TX 1",
            amount=Decimal("-30.00"),
            state=TransactionState.INBOX,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 17),
            payee="Uncategorized TX 2",
            amount=Decimal("-20.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Filter for uncategorized transactions only
        response = await client.get(
            "/api/transactions/",
            params={"uncategorized_only": "true"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        payees = [tx["payee"] for tx in data["transactions"]]
        assert "Uncategorized TX 1" in payees
        assert "Uncategorized TX 2" in payees
        assert "Categorized TX" not in payees
        # All returned transactions should have no category
        for tx in data["transactions"]:
            assert tx["category_id"] is None

    @pytest.mark.asyncio
    async def test_filter_by_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering transactions by account (FR-051)."""
        user = User(
            email="filter_account@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        checking = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        savings = Account(
            user_id=user.id,
            name="Savings",
            account_type=AccountType.SAVINGS,
            initial_balance=Decimal("5000.00"),
            balance=Decimal("0"),
        )
        db_session.add_all([checking, savings])
        await db_session.flush()

        tx1 = Transaction(
            user_id=user.id,
            account_id=checking.id,
            date=date(2026, 1, 15),
            payee="Checking TX 1",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=checking.id,
            date=date(2026, 1, 16),
            payee="Checking TX 2",
            amount=Decimal("-30.00"),
            state=TransactionState.INBOX,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=savings.id,
            date=date(2026, 1, 17),
            payee="Savings TX",
            amount=Decimal("-20.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Filter for checking account only
        response = await client.get(
            "/api/transactions/",
            params={"account_id": str(checking.id)},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        payees = [tx["payee"] for tx in data["transactions"]]
        assert "Checking TX 1" in payees
        assert "Checking TX 2" in payees
        assert "Savings TX" not in payees

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering transactions by status (FR-052)."""
        user = User(
            email="filter_status@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        category = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(category)
        await db_session.flush()

        tx_inbox = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Inbox TX",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx_approved = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date(2026, 1, 16),
            payee="Approved TX",
            amount=Decimal("-30.00"),
            state=TransactionState.APPROVED,
        )
        db_session.add_all([tx_inbox, tx_approved])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Filter for approved transactions only
        response = await client.get(
            "/api/transactions/",
            params={"state": "APPROVED"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["transactions"][0]["payee"] == "Approved TX"
        assert data["transactions"][0]["state"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_combined_search_and_filters(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test combining multiple search and filter parameters."""
        user = User(
            email="combined_search@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test Group", display_order=0)
        db_session.add(group)
        await db_session.flush()

        groceries = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(groceries)
        await db_session.flush()

        # Create varied transactions
        tx1 = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=groceries.id,
            date=date(2026, 1, 10),
            payee="Whole Foods",
            amount=Decimal("-100.00"),
            state=TransactionState.APPROVED,
        )
        tx2 = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=groceries.id,
            date=date(2026, 1, 15),
            payee="Whole Foods",
            amount=Decimal("-50.00"),
            state=TransactionState.APPROVED,
        )
        tx3 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 15),
            payee="Whole Foods",
            amount=Decimal("-25.00"),
            state=TransactionState.INBOX,
        )
        tx4 = Transaction(
            user_id=user.id,
            account_id=account.id,
            date=date(2026, 1, 20),
            payee="Target",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2, tx3, tx4])
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Combined: search for "whole", date range Jan 12-18, amount -75 to -25, groceries category
        response = await client.get(
            "/api/transactions/",
            params={
                "payee_search": "whole",
                "date_from": "2026-01-12",
                "date_to": "2026-01-18",
                "amount_min": "-75.00",
                "amount_max": "-25.00",
                "category_id": str(groceries.id),
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        # Only tx2 matches all criteria: "Whole Foods", Jan 15, -50.00, groceries category
        assert data["total"] == 1
        assert data["transactions"][0]["payee"] == "Whole Foods"
        assert Decimal(data["transactions"][0]["amount"]) == Decimal("-50.00")

    @pytest.mark.asyncio
    async def test_search_respects_user_isolation(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that search respects user isolation (can't see other users' transactions)."""
        user1 = User(
            email="user1_isolation@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="user2_isolation@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add_all([user1, user2])
        await db_session.flush()

        account1 = Account(
            user_id=user1.id,
            name="User1 Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        account2 = Account(
            user_id=user2.id,
            name="User2 Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add_all([account1, account2])
        await db_session.flush()

        # Both users have transactions with same payee
        tx1 = Transaction(
            user_id=user1.id,
            account_id=account1.id,
            date=date(2026, 1, 15),
            payee="Shared Payee Name",
            amount=Decimal("-50.00"),
            state=TransactionState.INBOX,
        )
        tx2 = Transaction(
            user_id=user2.id,
            account_id=account2.id,
            date=date(2026, 1, 15),
            payee="Shared Payee Name",
            amount=Decimal("-75.00"),
            state=TransactionState.INBOX,
        )
        db_session.add_all([tx1, tx2])
        await db_session.flush()

        # User1 searches for "Shared Payee"
        token1 = create_session_token(user1.id)
        cookies1 = {SESSION_COOKIE_NAME: token1}

        response = await client.get(
            "/api/transactions/",
            params={"payee_search": "Shared Payee"},
            cookies=cookies1,
        )

        assert response.status_code == 200
        data = response.json()
        # User1 should only see their own transaction
        assert data["total"] == 1
        assert Decimal(data["transactions"][0]["amount"]) == Decimal("-50.00")
        # Verify it's user1's transaction
        assert data["transactions"][0]["account_id"] == str(account1.id)

    @pytest.mark.asyncio
    async def test_search_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test that search requires authentication."""
        response = await client.get(
            "/api/transactions/",
            params={"payee_search": "test"},
        )

        assert response.status_code == 401


@pytest.mark.contract
class TestRuleBasedCategorization:
    """Contract tests for rule-based auto-categorization (T218)."""

    @pytest.mark.asyncio
    async def test_create_transaction_applies_matching_rule(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that creating a transaction without category applies matching rules (categorization_source=RULE)."""
        user = User(
            email="rule_apply@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        groceries = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(groceries)
        await db_session.flush()

        # Create a categorization rule that matches "whole foods"
        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="whole foods",
            category_id=groceries.id,
        )
        db_session.add(rule)
        await db_session.commit()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Create transaction without category - should auto-categorize via rule
        response = await client.post(
            "/api/transactions/",
            json={
                "account_id": str(account.id),
                "date": "2026-01-15",
                "payee": "WHOLE FOODS MARKET",  # Case-insensitive match
                "amount": "-75.00",
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] == str(groceries.id)
        assert data["categorization_source"] == "RULE"

    @pytest.mark.asyncio
    async def test_create_transaction_no_matching_rule(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that transaction without matching rule remains uncategorized."""
        user = User(
            email="rule_no_match@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        groceries = Category(user_id=user.id, group_id=group.id, name="Groceries")
        db_session.add(groceries)
        await db_session.flush()

        # Create a rule that won't match
        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="costco",
            category_id=groceries.id,
        )
        db_session.add(rule)
        await db_session.commit()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Create transaction that doesn't match any rule
        response = await client.post(
            "/api/transactions/",
            json={
                "account_id": str(account.id),
                "date": "2026-01-15",
                "payee": "Target",  # Doesn't match "costco" rule
                "amount": "-50.00",
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["category_id"] is None
        assert data["categorization_source"] is None

    @pytest.mark.asyncio
    async def test_create_transaction_explicit_category_not_overridden(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that explicit category is not overridden by matching rules."""
        user = User(
            email="rule_explicit@example.com",
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

        group = CategoryGroup(user_id=user.id, name="Test", display_order=0)
        db_session.add(group)
        await db_session.flush()

        groceries = Category(user_id=user.id, group_id=group.id, name="Groceries")
        dining = Category(user_id=user.id, group_id=group.id, name="Dining Out")
        db_session.add_all([groceries, dining])
        await db_session.flush()

        # Create a rule that would match
        rule = CategorizationRule(
            user_id=user.id,
            payee_pattern="whole foods",
            category_id=groceries.id,
        )
        db_session.add(rule)
        await db_session.commit()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Create transaction WITH explicit category - rule should NOT override
        response = await client.post(
            "/api/transactions/",
            json={
                "account_id": str(account.id),
                "date": "2026-01-15",
                "payee": "WHOLE FOODS MARKET",  # Would match rule
                "amount": "-75.00",
                "category_id": str(dining.id),  # Explicit category
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        # Should use explicit category, not rule category
        assert data["category_id"] == str(dining.id)
        # categorization_source is not set during create (only during approve)
        # The explicit category is used directly
