"""
Contract tests for Bank Connections API endpoints.
"""
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME, create_session_token
from mybudget.models.bank_connection import (
    BankConnection,
    BankConnectionStatus,
    LinkedAccount,
    LinkedAccountType,
)
from mybudget.models.user import User
from mybudget.schemas.bank_connection import ConnectionHealthStatus


@pytest.mark.contract
class TestInitiateConnectionAPI:
    """Contract tests for POST /api/connections/initiate."""

    @pytest.mark.asyncio
    async def test_initiate_connection_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test initiating a bank connection successfully."""
        user = User(
            email="initiate_conn@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/connections/initiate",
            json={
                "institution_id": "SANDBOXFINANCE_SFIN0000",
                "redirect_url": "https://app.example.com/callback",
            },
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "reference_id" in data
        assert "mock-bank.example.com" in data["authorization_url"]

    @pytest.mark.asyncio
    async def test_initiate_connection_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test initiating connection without authentication fails."""
        response = await client.post(
            "/api/connections/initiate",
            json={
                "institution_id": "SANDBOXFINANCE_SFIN0000",
                "redirect_url": "https://app.example.com/callback",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_initiate_connection_invalid_institution(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test initiating connection with invalid institution fails."""
        user = User(
            email="initiate_invalid@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/connections/initiate",
            json={
                "institution_id": "NONEXISTENT_BANK",
                "redirect_url": "https://app.example.com/callback",
            },
            cookies=cookies,
        )

        assert response.status_code == 400
        assert "Institution not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_initiate_connection_missing_fields(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test initiating connection with missing required fields."""
        user = User(
            email="initiate_missing@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            "/api/connections/initiate",
            json={},
            cookies=cookies,
        )

        assert response.status_code == 422


@pytest.mark.contract
class TestListConnectionsAPI:
    """Contract tests for GET /api/connections."""

    @pytest.mark.asyncio
    async def test_list_connections_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing connections when user has none."""
        user = User(
            email="list_empty@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/connections/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert data["connections"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_connections_with_data(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing connections with existing connection."""
        user = User(
            email="list_data@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-123",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
            access_valid_until=datetime.now(UTC) + timedelta(days=90),
        )
        db_session.add(connection)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/connections/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert len(data["connections"]) == 1
        assert data["total"] == 1
        assert data["connections"][0]["institution_name"] == "Sandbox Finance"
        assert data["connections"][0]["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_list_connections_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test listing connections without authentication fails."""
        response = await client.get("/api/connections/")

        assert response.status_code == 401


@pytest.mark.contract
class TestGetConnectionAPI:
    """Contract tests for GET /api/connections/{id}."""

    @pytest.mark.asyncio
    async def test_get_connection_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting a connection with linked accounts."""
        user = User(
            email="get_conn@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-456",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
            access_valid_until=datetime.now(UTC) + timedelta(days=90),
        )
        db_session.add(connection)
        await db_session.flush()

        linked_account = LinkedAccount(
            connection_id=connection.id,
            provider_account_id="ACC-001",
            account_name="Main Checking",
            account_number_masked="****1234",
            account_type=LinkedAccountType.CHECKING,
            currency="EUR",
            balance=Decimal("1000.00"),
            is_active=True,
        )
        db_session.add(linked_account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/connections/{connection.id}", cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(connection.id)
        assert data["institution_name"] == "Sandbox Finance"
        assert len(data["linked_accounts"]) == 1
        assert data["linked_accounts"][0]["account_name"] == "Main Checking"
        # Balance precision depends on model configuration - check it's close
        assert Decimal(data["linked_accounts"][0]["balance"]) == Decimal("1000.00")

    @pytest.mark.asyncio
    async def test_get_connection_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting non-existent connection returns 404."""
        user = User(
            email="get_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(f"/api/connections/{uuid4()}", cookies=cookies)

        assert response.status_code == 404
        assert response.json()["detail"] == "Connection not found"

    @pytest.mark.asyncio
    async def test_get_connection_other_user(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test getting another user's connection returns 404."""
        user1 = User(
            email="get_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user1)

        user2 = User(
            email="get_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user2)
        await db_session.flush()

        connection = BankConnection(
            user_id=user1.id,
            provider="mock",
            provider_connection_id="REQ-789",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        # User2 tries to access user1's connection
        token = create_session_token(user2.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/connections/{connection.id}", cookies=cookies
        )

        # Should return 404 to avoid leaking connection existence
        assert response.status_code == 404


@pytest.mark.contract
class TestDisconnectAPI:
    """Contract tests for DELETE /api/connections/{id}."""

    @pytest.mark.asyncio
    async def test_disconnect_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test disconnecting a connection successfully."""
        user = User(
            email="disconnect@example.com",
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
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        linked_account = LinkedAccount(
            connection_id=connection.id,
            provider_account_id="ACC-DISC",
            account_name="Disconnect Account",
            currency="EUR",
            is_active=True,
        )
        db_session.add(linked_account)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(
            f"/api/connections/{connection.id}", cookies=cookies
        )

        assert response.status_code == 204

        # Verify connection is disconnected
        await db_session.refresh(connection)
        assert connection.status == BankConnectionStatus.DISCONNECTED

        # Verify linked account is deactivated
        await db_session.refresh(linked_account)
        assert linked_account.is_active is False

    @pytest.mark.asyncio
    async def test_disconnect_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test disconnecting non-existent connection returns 404."""
        user = User(
            email="disc_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.delete(
            f"/api/connections/{uuid4()}", cookies=cookies
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_disconnect_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test disconnecting without authentication fails."""
        response = await client.delete(f"/api/connections/{uuid4()}")

        assert response.status_code == 401


@pytest.mark.contract
class TestInstitutionsAPI:
    """Contract tests for GET /api/institutions."""

    @pytest.mark.asyncio
    async def test_list_institutions_all(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test listing all available institutions."""
        user = User(
            email="inst_all@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/institutions/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert "institutions" in data
        assert "total" in data
        # MockBankAdapter has 3 default institutions
        assert len(data["institutions"]) == 3
        assert data["total"] == 3

        # Check institution structure
        inst = data["institutions"][0]
        assert "id" in inst
        assert "name" in inst
        assert "countries" in inst

    @pytest.mark.asyncio
    async def test_list_institutions_by_country(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering institutions by country."""
        user = User(
            email="inst_country@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        # Filter for France - only Euro Bank supports FR
        response = await client.get(
            "/api/institutions/", params={"country": "FR"}, cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["institutions"]) == 1
        assert data["institutions"][0]["id"] == "EUROBANK_EURO0002"

    @pytest.mark.asyncio
    async def test_list_institutions_unsupported_country(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test filtering by unsupported country returns empty list."""
        user = User(
            email="inst_unsupported@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/institutions/", params={"country": "XX"}, cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["institutions"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_institutions_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test listing institutions without authentication fails."""
        response = await client.get("/api/institutions/")

        assert response.status_code == 401


@pytest.mark.contract
class TestOAuthCallbackAPI:
    """Contract tests for GET /api/connections/callback."""

    @pytest.mark.asyncio
    async def test_callback_no_pending_connection(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test callback with no pending connection returns error."""
        user = User(
            email="callback_nopending@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/connections/callback",
            params={"ref": "invalid-ref"},
            cookies=cookies,
        )

        assert response.status_code == 400
        assert "No pending connection" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_callback_unauthenticated(
        self, client: AsyncClient
    ) -> None:
        """Test callback without authentication fails."""
        response = await client.get(
            "/api/connections/callback",
            params={"ref": "some-ref"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_callback_missing_ref(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test callback without ref parameter fails."""
        user = User(
            email="callback_noref@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            "/api/connections/callback",
            cookies=cookies,
        )

        assert response.status_code == 422


@pytest.mark.contract
class TestConnectionIsolation:
    """Contract tests for user isolation in bank connections."""

    @pytest.mark.asyncio
    async def test_list_only_shows_own_connections(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that list only shows user's own connections."""
        user1 = User(
            email="iso_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="iso_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.flush()

        # Create connection for user1
        conn1 = BankConnection(
            user_id=user1.id,
            provider="mock",
            provider_connection_id="REQ-U1",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="User1 Bank",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(conn1)

        # Create connection for user2
        conn2 = BankConnection(
            user_id=user2.id,
            provider="mock",
            provider_connection_id="REQ-U2",
            institution_id="TESTBANK_TEST0001",
            institution_name="User2 Bank",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(conn2)
        await db_session.flush()

        # User1 lists connections
        token1 = create_session_token(user1.id)
        cookies1 = {SESSION_COOKIE_NAME: token1}

        response = await client.get("/api/connections/", cookies=cookies1)

        assert response.status_code == 200
        data = response.json()
        assert len(data["connections"]) == 1
        assert data["connections"][0]["institution_name"] == "User1 Bank"

        # User2 lists connections
        token2 = create_session_token(user2.id)
        cookies2 = {SESSION_COOKIE_NAME: token2}

        response = await client.get("/api/connections/", cookies=cookies2)

        assert response.status_code == 200
        data = response.json()
        assert len(data["connections"]) == 1
        assert data["connections"][0]["institution_name"] == "User2 Bank"

    @pytest.mark.asyncio
    async def test_cannot_disconnect_other_user_connection(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that user cannot disconnect another user's connection."""
        user1 = User(
            email="iso_disc_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="iso_disc_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.flush()

        # Create connection for user1
        conn = BankConnection(
            user_id=user1.id,
            provider="mock",
            provider_connection_id="REQ-ISO",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="User1 Bank",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(conn)
        await db_session.flush()

        # User2 tries to disconnect user1's connection
        token2 = create_session_token(user2.id)
        cookies2 = {SESSION_COOKIE_NAME: token2}

        response = await client.delete(
            f"/api/connections/{conn.id}", cookies=cookies2
        )

        # Should return 404 to avoid leaking connection existence
        assert response.status_code == 404

        # Verify connection is still active
        await db_session.refresh(conn)
        assert conn.status == BankConnectionStatus.ACTIVE


@pytest.mark.contract
class TestConnectionHealthStatusAPI:
    """Contract tests for connection health status in responses."""

    @pytest.mark.asyncio
    async def test_list_connections_includes_health_status(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that list connections includes health_status field."""
        user = User(
            email="health_list@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Create an active connection with valid token
        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-HEALTH-1",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
            access_valid_until=datetime.now(UTC) + timedelta(days=90),
            last_sync_at=datetime.now(UTC) - timedelta(hours=1),
        )
        db_session.add(connection)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get("/api/connections/", cookies=cookies)

        assert response.status_code == 200
        data = response.json()
        assert len(data["connections"]) == 1
        assert "health_status" in data["connections"][0]
        assert data["connections"][0]["health_status"] == ConnectionHealthStatus.HEALTHY.value

    @pytest.mark.asyncio
    async def test_get_connection_includes_health_status(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test that get connection includes health_status field."""
        user = User(
            email="health_get@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-HEALTH-2",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
            access_valid_until=datetime.now(UTC) + timedelta(days=90),
        )
        db_session.add(connection)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/connections/{connection.id}", cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert "health_status" in data
        assert data["health_status"] == ConnectionHealthStatus.HEALTHY.value

    @pytest.mark.asyncio
    async def test_health_status_warning_for_expiring_token(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test warning health status when token is expiring soon."""
        user = User(
            email="health_warning@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Token expires in 5 days (within 7-day warning threshold)
        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-HEALTH-3",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
            access_valid_until=datetime.now(UTC) + timedelta(days=5),
        )
        db_session.add(connection)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/connections/{connection.id}", cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["health_status"] == ConnectionHealthStatus.WARNING.value

    @pytest.mark.asyncio
    async def test_health_status_error_for_expired_token(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test error health status when token is expired."""
        user = User(
            email="health_error@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Token expired yesterday
        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-HEALTH-4",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
            access_valid_until=datetime.now(UTC) - timedelta(days=1),
        )
        db_session.add(connection)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.get(
            f"/api/connections/{connection.id}", cookies=cookies
        )

        assert response.status_code == 200
        data = response.json()
        assert data["health_status"] == ConnectionHealthStatus.ERROR.value


@pytest.mark.contract
class TestReauthAPI:
    """Contract tests for POST /api/connections/{id}/reauth."""

    @pytest.mark.asyncio
    async def test_reauth_initiate_success(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test initiating re-authentication successfully."""
        user = User(
            email="reauth_success@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        # Create active connection with expiring token
        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-REAUTH-1",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
            access_valid_until=datetime.now(UTC) + timedelta(days=3),
        )
        db_session.add(connection)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{connection.id}/reauth",
            json={"redirect_url": "https://app.example.com/callback"},
            cookies=cookies,
        )

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "reference_id" in data
        assert "mock-bank.example.com" in data["authorization_url"]

        # Verify connection status was updated
        await db_session.refresh(connection)
        assert connection.status == BankConnectionStatus.PENDING_REAUTH

    @pytest.mark.asyncio
    async def test_reauth_connection_not_found(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test reauth for non-existent connection returns 400."""
        user = User(
            email="reauth_notfound@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{uuid4()}/reauth",
            json={"redirect_url": "https://app.example.com/callback"},
            cookies=cookies,
        )

        assert response.status_code == 400
        assert "Connection not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_reauth_disconnected_connection(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test reauth for disconnected connection fails."""
        user = User(
            email="reauth_disconnected@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-REAUTH-2",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.DISCONNECTED,
        )
        db_session.add(connection)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{connection.id}/reauth",
            json={"redirect_url": "https://app.example.com/callback"},
            cookies=cookies,
        )

        assert response.status_code == 400
        assert "Cannot re-authenticate a disconnected connection" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_reauth_other_user_connection(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test reauth for another user's connection returns 400."""
        user1 = User(
            email="reauth_user1@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        user2 = User(
            email="reauth_user2@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user1)
        db_session.add(user2)
        await db_session.flush()

        connection = BankConnection(
            user_id=user1.id,
            provider="mock",
            provider_connection_id="REQ-REAUTH-3",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        # User2 tries to reauth user1's connection
        token = create_session_token(user2.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{connection.id}/reauth",
            json={"redirect_url": "https://app.example.com/callback"},
            cookies=cookies,
        )

        # Should return 400 "Connection not found"
        assert response.status_code == 400
        assert "Connection not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_reauth_unauthenticated(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test reauth without authentication fails."""
        response = await client.post(
            f"/api/connections/{uuid4()}/reauth",
            json={"redirect_url": "https://app.example.com/callback"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_reauth_missing_redirect_url(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Test reauth without redirect_url fails validation."""
        user = User(
            email="reauth_noredirect@example.com",
            password_hash=hash_password("password123"),
            timezone="UTC",
        )
        db_session.add(user)
        await db_session.flush()

        connection = BankConnection(
            user_id=user.id,
            provider="mock",
            provider_connection_id="REQ-REAUTH-4",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.ACTIVE,
        )
        db_session.add(connection)
        await db_session.flush()

        token = create_session_token(user.id)
        cookies = {SESSION_COOKIE_NAME: token}

        response = await client.post(
            f"/api/connections/{connection.id}/reauth",
            json={},
            cookies=cookies,
        )

        assert response.status_code == 422
