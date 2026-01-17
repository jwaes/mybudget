"""
Contract tests for reconciliation API endpoints.

Tests the API contract for account reconciliation workflow.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.account import Account, AccountType
from mybudget.models.category import Category, CategoryGroup
from mybudget.models.transaction import Transaction, TransactionState
from mybudget.models.user import User

pytestmark = pytest.mark.asyncio


@pytest.mark.contract
class TestReconciliationAPI:
    """Tests for reconciliation API endpoints."""

    async def _create_user_and_auth(
        self, db_session: AsyncSession, email_suffix: str = ""
    ) -> tuple[User, dict]:
        """Create a user and return user + auth cookies."""
        user = User(
            email=f"recon_test{email_suffix}@example.com",
            password_hash=hash_password("TestPassword123!"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}
        return user, cookies

    async def _create_account(
        self, db_session: AsyncSession, user: User, balance: Decimal = Decimal("1000.00")
    ) -> Account:
        """Create an account for a user."""
        account = Account(
            user_id=user.id,
            name="Test Checking",
            account_type=AccountType.CHECKING,
            initial_balance=balance,
            balance=Decimal("0.00"),
        )
        db_session.add(account)
        await db_session.flush()
        return account

    async def _create_category(
        self, db_session: AsyncSession, user: User
    ) -> Category:
        """Create a category for a user."""
        group = CategoryGroup(
            user_id=user.id,
            name="Test Group",
            display_order=0,
        )
        db_session.add(group)
        await db_session.flush()

        category = Category(
            user_id=user.id,
            group_id=group.id,
            name="Test Category",
        )
        db_session.add(category)
        await db_session.flush()
        return category

    async def _create_approved_transaction(
        self, db_session: AsyncSession, user: User, account: Account, category: Category, amount: Decimal
    ) -> Transaction:
        """Create an approved transaction."""
        tx = Transaction(
            user_id=user.id,
            account_id=account.id,
            category_id=category.id,
            date=date.today(),
            payee="Test Payee",
            amount=amount,
            state=TransactionState.APPROVED,
        )
        db_session.add(tx)
        # Update account balance
        account.balance += amount
        await db_session.flush()
        return tx

    # T109: POST /reconciliations - Start reconciliation

    async def test_start_reconciliation_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test starting a new reconciliation session."""
        user, cookies = await self._create_user_and_auth(db_session, "_start")
        account = await self._create_account(db_session, user)

        response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "1000.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["account_id"] == str(account.id)
        assert data["statement_balance"] == "1000.0000"
        assert data["status"] == "IN_PROGRESS"
        assert "cleared_balance" in data
        assert "discrepancy" in data

    async def test_start_reconciliation_invalid_account(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test starting reconciliation with non-existent account."""
        user, cookies = await self._create_user_and_auth(db_session, "_invalid_acct")

        fake_id = str(uuid.uuid4())
        response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": fake_id,
                "statement_balance": "1000.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )

        assert response.status_code == 404

    async def test_start_reconciliation_future_date_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that future statement dates are rejected."""
        user, cookies = await self._create_user_and_auth(db_session, "_future")
        account = await self._create_account(db_session, user)

        future_date = date.today() + timedelta(days=30)
        response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "1000.00",
                "statement_date": future_date.isoformat(),
            },
            cookies=cookies,
        )

        assert response.status_code == 422

    async def test_get_reconciliation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test getting reconciliation details."""
        user, cookies = await self._create_user_and_auth(db_session, "_get")
        account = await self._create_account(db_session, user)

        # Start a reconciliation
        create_response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "1000.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )
        assert create_response.status_code == 201
        recon_id = create_response.json()["id"]

        # Get the reconciliation
        response = await client.get(
            f"/api/reconciliations/{recon_id}",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == recon_id
        assert data["status"] == "IN_PROGRESS"

    # T110: PUT /reconciliations/{id}/mark-cleared - Mark transactions as cleared

    async def test_mark_transactions_cleared(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test marking transactions as cleared during reconciliation."""
        user, cookies = await self._create_user_and_auth(db_session, "_mark")
        account = await self._create_account(db_session, user)
        category = await self._create_category(db_session, user)
        tx = await self._create_approved_transaction(
            db_session, user, account, category, Decimal("-100.00")
        )

        # Start reconciliation
        recon_response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "900.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )
        assert recon_response.status_code == 201
        recon_id = recon_response.json()["id"]

        # Mark transaction as cleared
        response = await client.put(
            f"/api/reconciliations/{recon_id}/mark-cleared",
            json={"transaction_ids": [str(tx.id)]},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert "cleared_balance" in data
        assert "discrepancy" in data

    async def test_mark_cleared_invalid_transaction(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test marking non-existent transaction as cleared."""
        user, cookies = await self._create_user_and_auth(db_session, "_invalid_tx")
        account = await self._create_account(db_session, user)

        # Start reconciliation
        recon_response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "1000.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )
        assert recon_response.status_code == 201
        recon_id = recon_response.json()["id"]

        fake_tx_id = str(uuid.uuid4())
        response = await client.put(
            f"/api/reconciliations/{recon_id}/mark-cleared",
            json={"transaction_ids": [fake_tx_id]},
            cookies=cookies,
        )

        assert response.status_code == 404

    async def test_unmark_cleared_transaction(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test unmarking a cleared transaction."""
        user, cookies = await self._create_user_and_auth(db_session, "_unmark")
        account = await self._create_account(db_session, user)
        category = await self._create_category(db_session, user)
        tx = await self._create_approved_transaction(
            db_session, user, account, category, Decimal("-50.00")
        )

        # Start reconciliation
        recon_response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "950.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )
        assert recon_response.status_code == 201
        recon_id = recon_response.json()["id"]

        # Mark as cleared
        await client.put(
            f"/api/reconciliations/{recon_id}/mark-cleared",
            json={"transaction_ids": [str(tx.id)]},
            cookies=cookies,
        )

        # Unmark
        response = await client.put(
            f"/api/reconciliations/{recon_id}/unmark-cleared",
            json={"transaction_ids": [str(tx.id)]},
            cookies=cookies,
        )

        assert response.status_code == 200

    # T111: POST /reconciliations/{id}/create-adjustment - Create adjustment transaction

    async def test_create_adjustment_for_discrepancy(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test creating adjustment transaction for discrepancy."""
        user, cookies = await self._create_user_and_auth(db_session, "_adjust")
        account = await self._create_account(db_session, user)
        category = await self._create_category(db_session, user)
        tx = await self._create_approved_transaction(
            db_session, user, account, category, Decimal("-100.00")
        )

        # Start reconciliation with a discrepancy (statement says 890, but cleared should be 900)
        recon_response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "890.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )
        assert recon_response.status_code == 201
        recon_id = recon_response.json()["id"]

        # Mark transaction as cleared
        await client.put(
            f"/api/reconciliations/{recon_id}/mark-cleared",
            json={"transaction_ids": [str(tx.id)]},
            cookies=cookies,
        )

        # Create adjustment to fix the discrepancy
        response = await client.post(
            f"/api/reconciliations/{recon_id}/create-adjustment",
            json={"category_id": str(category.id)},
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert "adjustment_transaction" in data

    async def test_create_adjustment_no_discrepancy_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that adjustment is rejected when no discrepancy exists."""
        user, cookies = await self._create_user_and_auth(db_session, "_no_discr")
        account = await self._create_account(db_session, user)
        category = await self._create_category(db_session, user)

        # Start reconciliation with matching balance
        recon_response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "1000.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )
        assert recon_response.status_code == 201
        recon_id = recon_response.json()["id"]

        # Try to create adjustment when discrepancy is 0
        response = await client.post(
            f"/api/reconciliations/{recon_id}/create-adjustment",
            json={"category_id": str(category.id)},
            cookies=cookies,
        )

        assert response.status_code == 400

    # Complete reconciliation

    async def test_complete_reconciliation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test completing a reconciliation when balanced."""
        user, cookies = await self._create_user_and_auth(db_session, "_complete")
        account = await self._create_account(db_session, user)

        # Start reconciliation matching starting balance
        recon_response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "1000.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )
        assert recon_response.status_code == 201
        recon_id = recon_response.json()["id"]

        # Complete it
        response = await client.post(
            f"/api/reconciliations/{recon_id}/complete",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["completed_at"] is not None

    async def test_complete_reconciliation_with_discrepancy_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test that completing reconciliation with discrepancy is rejected."""
        user, cookies = await self._create_user_and_auth(db_session, "_discr")
        account = await self._create_account(db_session, user)
        category = await self._create_category(db_session, user)
        await self._create_approved_transaction(
            db_session, user, account, category, Decimal("-100.00")
        )

        # Start reconciliation with mismatched balance
        recon_response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "500.00",  # Wrong balance
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )
        assert recon_response.status_code == 201
        recon_id = recon_response.json()["id"]

        # Try to complete - should fail
        response = await client.post(
            f"/api/reconciliations/{recon_id}/complete",
            cookies=cookies,
        )

        assert response.status_code == 400

    async def test_list_reconciliations_for_account(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test listing reconciliations for an account."""
        user, cookies = await self._create_user_and_auth(db_session, "_list")
        account = await self._create_account(db_session, user)

        # Create a reconciliation
        await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "1000.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )

        # List reconciliations for account
        response = await client.get(
            "/api/reconciliations/",
            params={"account_id": str(account.id)},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert all(r["account_id"] == str(account.id) for r in data)

    async def test_cancel_reconciliation(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Test canceling an in-progress reconciliation."""
        user, cookies = await self._create_user_and_auth(db_session, "_cancel")
        account = await self._create_account(db_session, user)

        # Start reconciliation
        recon_response = await client.post(
            "/api/reconciliations/",
            json={
                "account_id": str(account.id),
                "statement_balance": "1000.00",
                "statement_date": date.today().isoformat(),
            },
            cookies=cookies,
        )
        assert recon_response.status_code == 201
        recon_id = recon_response.json()["id"]

        # Cancel it
        response = await client.delete(
            f"/api/reconciliations/{recon_id}",
            cookies=cookies,
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = await client.get(
            f"/api/reconciliations/{recon_id}",
            cookies=cookies,
        )
        assert get_response.status_code == 404
