"""
Contract tests for Accounts API endpoints.
"""
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.account import Account, AccountType
from mybudget.models.user import User


@pytest.mark.contract
class TestAccountsAPI:
    """Contract tests for accounts API."""

    @pytest.mark.asyncio
    async def test_create_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test creating a new account."""
        # Create test user
        user = User(
            email="create_account@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/accounts/",
            json={
                "name": "My Savings",
                "account_type": "SAVINGS",
                "initial_balance": "5000.00",
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Savings"
        assert data["account_type"] == "SAVINGS"
        assert data["initial_balance"] == "5000.0000"
        assert data["balance"] == "0.0000"
        assert data["user_id"] == str(user.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_account_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test creating account without authentication fails."""
        response = await client.post(
            "/api/accounts/",
            json={
                "name": "Test Account",
                "account_type": "CHECKING",
                "initial_balance": "1000.00",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_accounts_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing accounts when user has none."""
        user = User(
            email="list_empty@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/accounts/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["accounts"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_accounts_with_data(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing accounts with existing account."""
        user = User(
            email="list_data@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Test Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/accounts/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert len(data["accounts"]) == 1
        assert data["total"] == 1
        assert data["accounts"][0]["name"] == "Test Checking"

    @pytest.mark.asyncio
    async def test_get_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting account by ID."""
        user = User(
            email="get_account@example.com",
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

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/accounts/{account.id}", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(account.id)
        assert data["name"] == "Test Account"
        assert data["account_type"] == "CHECKING"

    @pytest.mark.asyncio
    async def test_get_account_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting non-existent account returns 404."""
        user = User(
            email="get_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/accounts/{uuid4()}", cookies=cookies)

        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"

    @pytest.mark.asyncio
    async def test_update_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating an account."""
        user = User(
            email="update_account@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Original Name",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/accounts/{account.id}",
            json={"name": "Updated Account Name"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Account Name"
        assert data["account_type"] == "CHECKING"  # Unchanged

    @pytest.mark.asyncio
    async def test_update_account_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test updating non-existent account returns 404."""
        user = User(
            email="update_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.put(
            f"/api/accounts/{uuid4()}",
            json={"name": "New Name"},
            cookies=cookies,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test deleting an account."""
        user = User(
            email="delete_account@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Delete Me",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(f"/api/accounts/{account.id}", cookies=cookies)

        assert response.status_code == 204

        # Verify account is deleted
        get_response = await client.get(f"/api/accounts/{account.id}", cookies=cookies)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_account_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test deleting non-existent account returns 404."""
        user = User(
            email="delete_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(f"/api/accounts/{uuid4()}", cookies=cookies)

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_account_isolation_between_users(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that users cannot access other users' accounts."""
        # Create first user with account
        user1 = User(
            email="isolation_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user1)
        await db_session.flush()

        account = Account(
            user_id=user1.id,
            name="User1 Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        # Create second user
        user2 = User(
            email="isolation_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user2)
        await db_session.flush()

        token2 = create_session_token(user2.id)
        cookies2 = {SESSION_COOKIE_NAME: token2}

        # Try to access user1's account as user2
        response = await client.get(f"/api/accounts/{account.id}", cookies=cookies2)

        # Should return 404 (not 403) to avoid leaking account existence
        assert response.status_code == 404


@pytest.mark.contract
class TestAccountSyncStatus:
    """Contract tests for account sync status functionality (FR-010a, FR-010b)."""

    @pytest.mark.asyncio
    async def test_new_account_has_never_synced_status(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that new accounts start with NEVER_SYNCED status (T213)."""
        user = User(
            email="sync_status@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/accounts/",
            json={
                "name": "New Account",
                "account_type": "CHECKING",
                "initial_balance": "1000.00",
            },
            cookies=cookies,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["sync_status"] == "NEVER_SYNCED"
        assert data["last_sync_at"] is None
        assert data["sync_error"] is None

    @pytest.mark.asyncio
    async def test_account_response_includes_sync_fields(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that account responses include all sync-related fields."""
        user = User(
            email="sync_fields@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Sync Test Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/accounts/{account.id}", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        # Verify all sync fields are present
        assert "sync_status" in data
        assert "last_sync_at" in data
        assert "sync_error" in data

    @pytest.mark.asyncio
    async def test_retry_sync_resets_status_to_pending(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test retry-sync endpoint resets status to PENDING (T211, FR-010b)."""
        from mybudget.models.account import SyncStatus

        user = User(
            email="retry_sync@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Create account with FAILED sync status
        account = Account(
            user_id=user.id,
            name="Failed Sync Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
            sync_status=SyncStatus.FAILED,
            sync_error="Previous sync failed",
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/accounts/{account.id}/retry-sync",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["sync_status"] == "PENDING"
        assert data["sync_error"] is None

    @pytest.mark.asyncio
    async def test_retry_sync_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test retry-sync returns 404 for non-existent account."""
        user = User(
            email="retry_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/accounts/{uuid4()}/retry-sync",
            cookies=cookies,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_retry_sync_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test retry-sync without authentication fails."""
        response = await client.post(
            f"/api/accounts/{uuid4()}/retry-sync",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_retry_sync_other_user_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test retry-sync returns 404 for another user's account."""
        from mybudget.models.account import SyncStatus

        # Create user1 with account
        user1 = User(
            email="retry_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user1)
        await db_session.flush()

        account = Account(
            user_id=user1.id,
            name="User1 Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
            sync_status=SyncStatus.FAILED,
        )
        db_session.add(account)
        await db_session.flush()

        # Create user2
        user2 = User(
            email="retry_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user2)
        await db_session.flush()

        token2 = create_session_token(user2.id)
        cookies2 = {SESSION_COOKIE_NAME: token2}

        # User2 tries to retry sync on user1's account
        response = await client.post(
            f"/api/accounts/{account.id}/retry-sync",
            cookies=cookies2,
        )

        # Should return 404 (not 403) to avoid leaking account existence
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_accounts_includes_sync_status(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that account list includes sync status for all accounts."""
        user = User(
            email="list_sync@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="List Sync Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
            balance=Decimal("0"),
        )
        db_session.add(account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/accounts/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["sync_status"] == "NEVER_SYNCED"
