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
