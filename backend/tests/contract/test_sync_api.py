"""
Contract tests for Sync API endpoints.

Tests transaction synchronization: trigger sync, list sync jobs, get sync job.
"""
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.account import Account, AccountType
from mybudget.models.bank_connection import (
    BankConnection,
    BankConnectionStatus,
    LinkedAccount,
    LinkedAccountType,
    SyncJob,
    SyncJobStatus,
    SyncTriggerType,
)
from mybudget.models.user import User


@pytest.mark.contract
class TestTriggerSyncAPI:
    """Contract tests for POST /api/connections/{id}/sync."""

    @pytest.mark.asyncio
    async def test_trigger_sync_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test triggering a manual sync successfully."""
        # Create user
        user = User(
            email="sync_trigger@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Create internal account
        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=1000,
            initial_balance=1000,
        )
        db_session.add(account)
        await db_session.flush()

        # Create bank connection
        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-SYNC",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
            access_valid_until=datetime.now(UTC) + timedelta(days=90),
        )
        db_session.add(connection)
        await db_session.flush()

        # Create linked account
        linked_account = LinkedAccount(
            connection_id=connection.id,
            provider_account_id="ACC-001",
            account_id=account.id,  # Link to internal account
            account_name="Main Checking",
            account_type=LinkedAccountType.CHECKING,
            currency="EUR",
            is_active=True,
        )
        db_session.add(linked_account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{connection.id}/sync",
            cookies=cookies,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["connection_id"] == str(connection.id)
        assert data["status"] == "PENDING"
        assert data["trigger_type"] == "MANUAL"

    @pytest.mark.asyncio
    async def test_trigger_sync_with_specific_account(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test triggering sync for a specific linked account."""
        user = User(
            email="sync_specific@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        account = Account(
            user_id=user.id,
            name="Checking",
            account_type=AccountType.CHECKING,
            balance=1000,
            initial_balance=1000,
        )
        db_session.add(account)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-SPEC",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        linked_account = LinkedAccount(
            connection_id=connection.id,
            provider_account_id="ACC-002",
            account_id=account.id,
            account_name="Savings",
            account_type=LinkedAccountType.SAVINGS,
            currency="EUR",
            is_active=True,
        )
        db_session.add(linked_account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{connection.id}/sync",
            json={"linked_account_id": str(linked_account.id)},
            cookies=cookies,
        )

        assert response.status_code == 202
        data = response.json()
        assert data["linked_account_id"] == str(linked_account.id)

    @pytest.mark.asyncio
    async def test_trigger_sync_connection_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test triggering sync for non-existent connection returns 404."""
        user = User(
            email="sync_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{uuid4()}/sync",
            cookies=cookies,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_trigger_sync_connection_not_active(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test triggering sync for disconnected connection returns 400."""
        user = User(
            email="sync_inactive@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-DISC",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.DISCONNECTED,  # Not active
        )
        db_session.add(connection)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{connection.id}/sync",
            cookies=cookies,
        )

        assert response.status_code == 400
        assert "not active" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_trigger_sync_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test triggering sync without authentication fails."""
        response = await client.post(f"/api/connections/{uuid4()}/sync")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_trigger_sync_other_user_connection(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test triggering sync on another user's connection returns 404."""
        user1 = User(
            email="sync_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="sync_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.flush()

        connection = BankConnection(
            user_id=user1.id,
            provider="mock",
            provider_connection_id="REQ-U1",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        # User2 tries to trigger sync on user1's connection
        token = create_session_token(user2.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{connection.id}/sync",
            cookies=cookies,
        )

        # Should return 404 to not leak connection existence
        assert response.status_code == 404


@pytest.mark.contract
class TestListSyncJobsAPI:
    """Contract tests for GET /api/sync-jobs."""

    @pytest.mark.asyncio
    async def test_list_sync_jobs_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing sync jobs for a connection."""
        user = User(
            email="list_jobs@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-LIST",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        # Create sync jobs
        job1 = SyncJob(
            connection_id=connection.id,
            status=SyncJobStatus.COMPLETED,
            trigger_type=SyncTriggerType.MANUAL,
            started_at=datetime.now(UTC) - timedelta(hours=2),
            completed_at=datetime.now(UTC) - timedelta(hours=1),
            transactions_fetched=10,
            transactions_imported=8,
            transactions_duplicates=2,
        )
        job2 = SyncJob(
            connection_id=connection.id,
            status=SyncJobStatus.PENDING,
            trigger_type=SyncTriggerType.SCHEDULED,
            transactions_fetched=0,
            transactions_imported=0,
            transactions_duplicates=0,
        )
        db_session.add(job1)
        db_session.add(job2)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/sync-jobs",
            params={"connection_id": str(connection.id)},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert len(data["jobs"]) == 2

    @pytest.mark.asyncio
    async def test_list_sync_jobs_with_status_filter(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering sync jobs by status."""
        user = User(
            email="list_filter@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-FILTER",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        job_completed = SyncJob(
            connection_id=connection.id,
            status=SyncJobStatus.COMPLETED,
            trigger_type=SyncTriggerType.MANUAL,
            transactions_fetched=5,
            transactions_imported=5,
            transactions_duplicates=0,
        )
        job_pending = SyncJob(
            connection_id=connection.id,
            status=SyncJobStatus.PENDING,
            trigger_type=SyncTriggerType.SCHEDULED,
            transactions_fetched=0,
            transactions_imported=0,
            transactions_duplicates=0,
        )
        db_session.add(job_completed)
        db_session.add(job_pending)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/sync-jobs",
            params={
                "connection_id": str(connection.id),
                "status": "COMPLETED",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["status"] == "COMPLETED"

    @pytest.mark.asyncio
    async def test_list_sync_jobs_missing_connection_id(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing sync jobs without connection_id returns 422."""
        user = User(
            email="list_missing@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/sync-jobs",
            cookies=cookies,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_list_sync_jobs_connection_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing sync jobs for non-existent connection returns 404."""
        user = User(
            email="list_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/sync-jobs",
            params={"connection_id": str(uuid4())},
            cookies=cookies,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_sync_jobs_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test listing sync jobs without authentication fails."""
        response = await client.get(
            "/api/sync-jobs",
            params={"connection_id": str(uuid4())},
        )

        assert response.status_code == 401


@pytest.mark.contract
class TestGetSyncJobAPI:
    """Contract tests for GET /api/sync-jobs/{id}."""

    @pytest.mark.asyncio
    async def test_get_sync_job_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting a specific sync job."""
        user = User(
            email="get_job@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-GET",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        sync_job = SyncJob(
            connection_id=connection.id,
            status=SyncJobStatus.COMPLETED,
            trigger_type=SyncTriggerType.MANUAL,
            started_at=datetime.now(UTC) - timedelta(minutes=10),
            completed_at=datetime.now(UTC) - timedelta(minutes=5),
            transactions_fetched=15,
            transactions_imported=12,
            transactions_duplicates=3,
        )
        db_session.add(sync_job)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/sync-jobs/{sync_job.id}",
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sync_job.id)
        assert data["connection_id"] == str(connection.id)
        assert data["status"] == "COMPLETED"
        assert data["transactions_fetched"] == 15
        assert data["transactions_imported"] == 12
        assert data["transactions_duplicates"] == 3

    @pytest.mark.asyncio
    async def test_get_sync_job_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting non-existent sync job returns 404."""
        user = User(
            email="get_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/sync-jobs/{uuid4()}",
            cookies=cookies,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_sync_job_other_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting another user's sync job returns 404."""
        user1 = User(
            email="get_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="get_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.flush()

        connection = BankConnection(
            user_id=user1.id,
            provider="mock",
            provider_connection_id="REQ-OWNER",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        sync_job = SyncJob(
            connection_id=connection.id,
            status=SyncJobStatus.COMPLETED,
            trigger_type=SyncTriggerType.MANUAL,
            transactions_fetched=5,
            transactions_imported=5,
            transactions_duplicates=0,
        )
        db_session.add(sync_job)
        await db_session.flush()

        # User2 tries to access user1's sync job
        token = create_session_token(user2.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/sync-jobs/{sync_job.id}",
            cookies=cookies,
        )

        # Should return 404 to not leak job existence
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_sync_job_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test getting sync job without authentication fails."""
        response = await client.get(f"/api/sync-jobs/{uuid4()}")

        assert response.status_code == 401


@pytest.mark.contract
class TestSyncJobPagination:
    """Contract tests for sync job pagination."""

    @pytest.mark.asyncio
    async def test_sync_jobs_pagination(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test pagination of sync jobs."""
        user = User(
            email="paginate@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-PAGE",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        # Create 5 sync jobs
        for i in range(5):
            job = SyncJob(
                connection_id=connection.id,
                status=SyncJobStatus.COMPLETED,
                trigger_type=SyncTriggerType.SCHEDULED,
                transactions_fetched=i,
                transactions_imported=i,
                transactions_duplicates=0,
            )
            db_session.add(job)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Get first page (2 items)
        response = await client.get(
            "/api/sync-jobs",
            params={
                "connection_id": str(connection.id),
                "limit": 2,
                "offset": 0,
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 2

        # Get second page
        response = await client.get(
            "/api/sync-jobs",
            params={
                "connection_id": str(connection.id),
                "limit": 2,
                "offset": 2,
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 2

        # Get third page (only 1 remaining)
        response = await client.get(
            "/api/sync-jobs",
            params={
                "connection_id": str(connection.id),
                "limit": 2,
                "offset": 4,
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
