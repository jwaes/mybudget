"""
Unit tests for BankConnectionService.

Tests bank connection operations: initiate, complete OAuth, list, get, disconnect,
and health monitoring/re-authentication.
"""
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from mybudget.adapters.mock_adapter import MockBankAdapter
from mybudget.adapters.types import ProviderAccountType
from mybudget.models.bank_connection import (
    BankConnection,
    BankConnectionStatus,
    LinkedAccount,
    LinkedAccountType,
    SyncJob,
    SyncTriggerType,
)
from mybudget.schemas.bank_connection import ConnectionHealthStatus
from mybudget.services.bank_connection_service import (
    BankConnectionService,
    _map_account_type,
)


class TestMapAccountType:
    """Tests for _map_account_type helper function."""

    def test_map_checking(self) -> None:
        """Test mapping CHECKING type."""
        result = _map_account_type(ProviderAccountType.CHECKING)
        assert result == LinkedAccountType.CHECKING

    def test_map_savings(self) -> None:
        """Test mapping SAVINGS type."""
        result = _map_account_type(ProviderAccountType.SAVINGS)
        assert result == LinkedAccountType.SAVINGS

    def test_map_credit(self) -> None:
        """Test mapping CREDIT type."""
        result = _map_account_type(ProviderAccountType.CREDIT)
        assert result == LinkedAccountType.CREDIT

    def test_map_other_returns_none(self) -> None:
        """Test mapping OTHER type returns None."""
        result = _map_account_type(ProviderAccountType.OTHER)
        assert result is None

    def test_map_loan_returns_none(self) -> None:
        """Test mapping LOAN type returns None."""
        result = _map_account_type(ProviderAccountType.LOAN)
        assert result is None


class TestBankConnectionServiceInit:
    """Tests for BankConnectionService initialization."""

    def test_init_with_db_and_adapter(self) -> None:
        """Test service can be initialized with db and adapter."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)
        assert service.db == mock_db
        assert service.adapter == mock_adapter


class TestInitiateConnection:
    """Tests for initiate_connection method."""

    @pytest.mark.asyncio
    async def test_initiate_connection_success(self) -> None:
        """Test initiating a connection successfully."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        institution_id = "SANDBOXFINANCE_SFIN0000"
        redirect_url = "https://app.example.com/callback"

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.initiate_connection(
            user_id, institution_id, redirect_url
        )

        # Verify response
        assert result.authorization_url is not None
        assert "mock-bank.example.com" in result.authorization_url
        assert result.reference_id is not None

        # Verify connection was added to DB
        mock_db.add.assert_called_once()
        added_connection = mock_db.add.call_args[0][0]
        assert isinstance(added_connection, BankConnection)
        assert added_connection.user_id == user_id
        assert added_connection.institution_id == institution_id
        assert added_connection.status == BankConnectionStatus.PENDING
        assert added_connection.provider == "mock"

        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_initiate_connection_institution_not_found(self) -> None:
        """Test initiate connection fails for unknown institution."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        institution_id = "NONEXISTENT_BANK"
        redirect_url = "https://app.example.com/callback"

        with pytest.raises(ValueError, match="Institution not found"):
            await service.initiate_connection(user_id, institution_id, redirect_url)

    @pytest.mark.asyncio
    async def test_initiate_connection_requisition_failure(self) -> None:
        """Test initiate connection handles requisition creation failure."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter(fail_on_requisition=True)
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        institution_id = "SANDBOXFINANCE_SFIN0000"
        redirect_url = "https://app.example.com/callback"

        with pytest.raises(RuntimeError, match="Mock requisition failure"):
            await service.initiate_connection(user_id, institution_id, redirect_url)


class TestCompleteOAuth:
    """Tests for complete_oauth method."""

    @pytest.mark.asyncio
    async def test_complete_oauth_success(self) -> None:
        """Test completing OAuth flow successfully."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        # Set up mock requisition in adapter
        requisition_id = "REQ-12345678"
        mock_adapter.add_requisition(
            requisition_id=requisition_id,
            institution_id="SANDBOXFINANCE_SFIN0000",
            status="LN",  # Linked
        )

        # Create mock pending connection
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.provider = "mock"
        mock_connection.provider_connection_id = requisition_id
        mock_connection.institution_id = "SANDBOXFINANCE_SFIN0000"
        mock_connection.institution_name = "Sandbox Finance"
        mock_connection.status = BankConnectionStatus.PENDING
        mock_connection.status_detail = None
        mock_connection.last_sync_at = None
        mock_connection.next_sync_at = None
        mock_connection.access_valid_until = None
        mock_connection.created_at = datetime.now(UTC)
        mock_connection.updated_at = datetime.now(UTC)
        mock_connection.linked_accounts = []

        # Mock the query to return our pending connection
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_connection]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        # Make refresh populate the missing fields on LinkedAccount objects
        async def populate_refresh(obj: object) -> None:
            if isinstance(obj, LinkedAccount):
                obj.id = uuid4()
                obj.created_at = datetime.now(UTC)
                obj.updated_at = datetime.now(UTC)

        mock_db.refresh = AsyncMock(side_effect=populate_refresh)

        result = await service.complete_oauth(user_id, "ref-123")

        # Verify connection was updated
        assert mock_connection.status == BankConnectionStatus.ACTIVE
        assert mock_connection.access_valid_until is not None

        # Verify linked accounts were added (2 default mock accounts)
        add_calls = mock_db.add.call_args_list
        linked_accounts_added = [
            call[0][0]
            for call in add_calls
            if isinstance(call[0][0], LinkedAccount)
        ]
        assert len(linked_accounts_added) == 2

        # Verify sync job was created
        sync_jobs_added = [
            call[0][0] for call in add_calls if isinstance(call[0][0], SyncJob)
        ]
        assert len(sync_jobs_added) == 1
        assert sync_jobs_added[0].trigger_type == SyncTriggerType.INITIAL

        mock_db.commit.assert_awaited_once()

        # Verify result has linked accounts
        assert len(result.linked_accounts) == 2

    @pytest.mark.asyncio
    async def test_complete_oauth_no_pending_connection(self) -> None:
        """Test complete OAuth when no pending connection exists."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()

        # Return empty list - no pending connections
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="No pending connection found"):
            await service.complete_oauth(user_id, "ref-123")


class TestListConnections:
    """Tests for list_connections method."""

    @pytest.mark.asyncio
    async def test_list_connections_with_connections(self) -> None:
        """Test listing connections when user has connections."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()

        # Create mock connections
        mock_connections = [
            MagicMock(spec=BankConnection),
            MagicMock(spec=BankConnection),
        ]
        for i, conn in enumerate(mock_connections):
            conn.id = uuid4()
            conn.user_id = user_id
            conn.provider = "mock"
            conn.provider_connection_id = f"REQ-{i}"
            conn.institution_id = "SANDBOXFINANCE_SFIN0000"
            conn.institution_name = "Sandbox Finance"
            conn.status = BankConnectionStatus.ACTIVE
            conn.status_detail = None
            conn.last_sync_at = None
            conn.next_sync_at = None
            conn.access_valid_until = datetime.now(UTC) + timedelta(days=90)
            conn.created_at = datetime.now(UTC)
            conn.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_connections
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_connections(user_id)

        assert len(result) == 2
        assert result[0].institution_name == "Sandbox Finance"
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_connections_empty(self) -> None:
        """Test listing connections when user has none."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_connections(user_id)

        assert result == []


class TestGetConnection:
    """Tests for get_connection method."""

    @pytest.mark.asyncio
    async def test_get_connection_found(self) -> None:
        """Test getting a connection that exists."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        # Create mock connection with linked accounts
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.provider = "mock"
        mock_connection.provider_connection_id = "REQ-123"
        mock_connection.institution_id = "SANDBOXFINANCE_SFIN0000"
        mock_connection.institution_name = "Sandbox Finance"
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.status_detail = None
        mock_connection.last_sync_at = datetime.now(UTC)
        mock_connection.next_sync_at = None
        mock_connection.access_valid_until = datetime.now(UTC) + timedelta(days=90)
        mock_connection.created_at = datetime.now(UTC)
        mock_connection.updated_at = datetime.now(UTC)

        # Mock linked account
        mock_linked_account = MagicMock(spec=LinkedAccount)
        mock_linked_account.id = uuid4()
        mock_linked_account.connection_id = connection_id
        mock_linked_account.account_id = None
        mock_linked_account.provider_account_id = "ACC-001"
        mock_linked_account.account_name = "Main Checking"
        mock_linked_account.account_number_masked = "****1234"
        mock_linked_account.account_type = LinkedAccountType.CHECKING
        mock_linked_account.currency = "EUR"
        mock_linked_account.balance = Decimal("1000.00")
        mock_linked_account.balance_updated_at = datetime.now(UTC)
        mock_linked_account.is_active = True
        mock_linked_account.created_at = datetime.now(UTC)
        mock_linked_account.updated_at = datetime.now(UTC)

        mock_connection.linked_accounts = [mock_linked_account]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result

        result = await service.get_connection(user_id, connection_id)

        assert result is not None
        assert result.id == connection_id
        assert result.institution_name == "Sandbox Finance"
        assert len(result.linked_accounts) == 1
        assert result.linked_accounts[0].account_name == "Main Checking"

    @pytest.mark.asyncio
    async def test_get_connection_not_found(self) -> None:
        """Test getting a connection that doesn't exist."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_connection(user_id, connection_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_connection_wrong_user(self) -> None:
        """Test getting a connection owned by another user returns None."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        other_user_id = uuid4()
        connection_id = uuid4()

        # Query should return None because of user_id filter
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_connection(other_user_id, connection_id)

        assert result is None


class TestDisconnect:
    """Tests for disconnect method."""

    @pytest.mark.asyncio
    async def test_disconnect_success(self) -> None:
        """Test disconnecting a connection successfully."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        # Add requisition to adapter so revoke works
        requisition_id = "REQ-123"
        mock_adapter.add_requisition(
            requisition_id=requisition_id,
            institution_id="SANDBOXFINANCE_SFIN0000",
        )

        # Create mock connection with linked accounts
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.provider_connection_id = requisition_id
        mock_connection.status = BankConnectionStatus.ACTIVE

        mock_linked_account = MagicMock(spec=LinkedAccount)
        mock_linked_account.is_active = True
        mock_connection.linked_accounts = [mock_linked_account]

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        result = await service.disconnect(user_id, connection_id)

        assert result is True
        assert mock_connection.status == BankConnectionStatus.DISCONNECTED
        assert mock_connection.status_detail == "Disconnected by user"
        assert mock_linked_account.is_active is False
        mock_db.commit.assert_awaited_once()

        # Verify requisition was revoked in adapter
        assert requisition_id not in mock_adapter._requisitions

    @pytest.mark.asyncio
    async def test_disconnect_not_found(self) -> None:
        """Test disconnecting a connection that doesn't exist."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.disconnect(user_id, connection_id)

        assert result is False


class TestGetInstitutions:
    """Tests for get_institutions method."""

    @pytest.mark.asyncio
    async def test_get_institutions_all(self) -> None:
        """Test getting all institutions."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        result = await service.get_institutions()

        # MockBankAdapter has 3 default institutions
        assert len(result) == 3
        assert result[0].id == "SANDBOXFINANCE_SFIN0000"
        assert result[0].name == "Sandbox Finance"
        assert "BE" in result[0].countries

    @pytest.mark.asyncio
    async def test_get_institutions_by_country(self) -> None:
        """Test getting institutions filtered by country."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        # Filter for Belgium only
        result = await service.get_institutions(country="BE")

        # All 3 mock institutions support BE
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_get_institutions_by_country_filtered(self) -> None:
        """Test getting institutions with country filtering reduces results."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        # Filter for France - only Euro Bank supports FR
        result = await service.get_institutions(country="FR")

        assert len(result) == 1
        assert result[0].id == "EUROBANK_EURO0002"

    @pytest.mark.asyncio
    async def test_get_institutions_empty_country(self) -> None:
        """Test getting institutions for unsupported country."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        result = await service.get_institutions(country="XX")

        assert len(result) == 0


class TestUserIsolation:
    """Tests ensuring connection operations respect user isolation."""

    @pytest.mark.asyncio
    async def test_list_connections_only_returns_user_connections(self) -> None:
        """Test that list_connections only returns connections for the user."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()

        # Mock returns only user's connections (query filtered by user_id)
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = uuid4()
        mock_connection.user_id = user_id
        mock_connection.provider = "mock"
        mock_connection.provider_connection_id = "REQ-1"
        mock_connection.institution_id = "SANDBOXFINANCE_SFIN0000"
        mock_connection.institution_name = "Sandbox Finance"
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.status_detail = None
        mock_connection.last_sync_at = None
        mock_connection.next_sync_at = None
        mock_connection.access_valid_until = datetime.now(UTC) + timedelta(days=90)
        mock_connection.created_at = datetime.now(UTC)
        mock_connection.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_connection]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_connections(user_id)

        assert len(result) == 1
        assert all(r.user_id == user_id for r in result)

    @pytest.mark.asyncio
    async def test_disconnect_enforces_user_ownership(self) -> None:
        """Test that disconnect only works for user's own connection."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        other_user_id = uuid4()
        connection_id = uuid4()

        # Query with wrong user returns None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.disconnect(other_user_id, connection_id)

        assert result is False


class TestComputeHealthStatus:
    """Tests for compute_health_status method."""

    def test_healthy_connection_with_valid_token(self) -> None:
        """Test healthy connection with valid token and recent sync."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.access_valid_until = datetime.now(UTC) + timedelta(days=30)
        mock_connection.last_sync_at = datetime.now(UTC) - timedelta(hours=1)

        result = service.compute_health_status(mock_connection)

        assert result == ConnectionHealthStatus.HEALTHY

    def test_error_when_status_not_active(self) -> None:
        """Test error status for non-active connections."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        for status in [
            BankConnectionStatus.PENDING,
            BankConnectionStatus.ERROR,
            BankConnectionStatus.DISCONNECTED,
            BankConnectionStatus.PENDING_REAUTH,
        ]:
            mock_connection = MagicMock(spec=BankConnection)
            mock_connection.status = status
            mock_connection.access_valid_until = datetime.now(UTC) + timedelta(days=30)
            mock_connection.last_sync_at = None

            result = service.compute_health_status(mock_connection)

            assert result == ConnectionHealthStatus.ERROR, f"Expected ERROR for status {status}"

    def test_error_when_token_expired(self) -> None:
        """Test error status when token is expired."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.access_valid_until = datetime.now(UTC) - timedelta(hours=1)
        mock_connection.last_sync_at = None

        result = service.compute_health_status(mock_connection)

        assert result == ConnectionHealthStatus.ERROR

    def test_warning_when_token_expiring_soon(self) -> None:
        """Test warning status when token is expiring within 7 days."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.access_valid_until = datetime.now(UTC) + timedelta(days=5)
        mock_connection.last_sync_at = datetime.now(UTC) - timedelta(hours=1)

        result = service.compute_health_status(mock_connection)

        assert result == ConnectionHealthStatus.WARNING

    def test_warning_when_sync_stale(self) -> None:
        """Test warning status when last sync is stale (>24h)."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.access_valid_until = datetime.now(UTC) + timedelta(days=30)
        mock_connection.last_sync_at = datetime.now(UTC) - timedelta(hours=30)

        result = service.compute_health_status(mock_connection)

        assert result == ConnectionHealthStatus.WARNING

    def test_healthy_when_no_last_sync(self) -> None:
        """Test healthy status when no sync has occurred yet."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.access_valid_until = datetime.now(UTC) + timedelta(days=30)
        mock_connection.last_sync_at = None

        result = service.compute_health_status(mock_connection)

        assert result == ConnectionHealthStatus.HEALTHY

    def test_healthy_when_no_access_valid_until(self) -> None:
        """Test healthy status when access_valid_until is not set."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.access_valid_until = None
        mock_connection.last_sync_at = datetime.now(UTC) - timedelta(hours=1)

        result = service.compute_health_status(mock_connection)

        assert result == ConnectionHealthStatus.HEALTHY

    def test_needs_attention_status_is_not_error(self) -> None:
        """Test that NEEDS_ATTENTION status doesn't result in ERROR health."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.status = BankConnectionStatus.NEEDS_ATTENTION
        mock_connection.access_valid_until = datetime.now(UTC) + timedelta(days=30)
        mock_connection.last_sync_at = datetime.now(UTC) - timedelta(hours=1)

        result = service.compute_health_status(mock_connection)

        assert result == ConnectionHealthStatus.HEALTHY


class TestCheckConnectionHealth:
    """Tests for check_connection_health method."""

    @pytest.mark.asyncio
    async def test_check_connection_health_found(self) -> None:
        """Test checking health of existing connection."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        connection_id = uuid4()
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.access_valid_until = datetime.now(UTC) + timedelta(days=30)
        mock_connection.last_sync_at = datetime.now(UTC) - timedelta(hours=1)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result

        result = await service.check_connection_health(connection_id)

        assert result == ConnectionHealthStatus.HEALTHY

    @pytest.mark.asyncio
    async def test_check_connection_health_not_found(self) -> None:
        """Test checking health of non-existent connection."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        connection_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.check_connection_health(connection_id)

        assert result is None


class TestDetectExpiringTokens:
    """Tests for detect_expiring_tokens method."""

    @pytest.mark.asyncio
    async def test_detect_expiring_tokens_finds_connections(self) -> None:
        """Test finding connections with expiring tokens."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()

        # Create mock connections
        mock_connections = [
            MagicMock(spec=BankConnection),
            MagicMock(spec=BankConnection),
        ]
        for i, conn in enumerate(mock_connections):
            conn.id = uuid4()
            conn.user_id = user_id
            conn.status = BankConnectionStatus.ACTIVE
            conn.access_valid_until = datetime.now(UTC) + timedelta(days=3 + i)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_connections
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.detect_expiring_tokens(days_ahead=7)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_detect_expiring_tokens_empty(self) -> None:
        """Test detect expiring tokens when no connections are expiring."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.detect_expiring_tokens(days_ahead=7)

        assert result == []


class TestInitiateReauth:
    """Tests for initiate_reauth method."""

    @pytest.mark.asyncio
    async def test_initiate_reauth_success(self) -> None:
        """Test initiating re-authentication successfully."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.institution_id = "SANDBOXFINANCE_SFIN0000"
        mock_connection.status = BankConnectionStatus.ACTIVE

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        result = await service.initiate_reauth(
            user_id=user_id,
            connection_id=connection_id,
            redirect_url="https://app.example.com/callback",
        )

        assert result.authorization_url is not None
        assert "mock-bank.example.com" in result.authorization_url
        assert result.reference_id is not None
        assert mock_connection.status == BankConnectionStatus.PENDING_REAUTH
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_initiate_reauth_connection_not_found(self) -> None:
        """Test initiate reauth fails for non-existent connection."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Connection not found"):
            await service.initiate_reauth(
                user_id=user_id,
                connection_id=connection_id,
                redirect_url="https://app.example.com/callback",
            )

    @pytest.mark.asyncio
    async def test_initiate_reauth_disconnected_connection(self) -> None:
        """Test initiate reauth fails for disconnected connection."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.status = BankConnectionStatus.DISCONNECTED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Cannot re-authenticate a disconnected connection"):
            await service.initiate_reauth(
                user_id=user_id,
                connection_id=connection_id,
                redirect_url="https://app.example.com/callback",
            )


class TestCompleteReauth:
    """Tests for complete_reauth method."""

    @pytest.mark.asyncio
    async def test_complete_reauth_success(self) -> None:
        """Test completing re-auth flow successfully."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        # Set up mock requisition in adapter
        requisition_id = "REQ-REAUTH-123"
        mock_adapter.add_requisition(
            requisition_id=requisition_id,
            institution_id="SANDBOXFINANCE_SFIN0000",
            status="LN",  # Linked
        )

        # Create mock pending reauth connection
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.provider = "mock"
        mock_connection.provider_connection_id = requisition_id
        mock_connection.institution_id = "SANDBOXFINANCE_SFIN0000"
        mock_connection.institution_name = "Sandbox Finance"
        mock_connection.status = BankConnectionStatus.PENDING_REAUTH
        mock_connection.status_detail = "Re-authentication in progress"
        mock_connection.last_sync_at = datetime.now(UTC) - timedelta(hours=1)
        mock_connection.next_sync_at = None
        mock_connection.access_valid_until = None
        mock_connection.created_at = datetime.now(UTC) - timedelta(days=30)
        mock_connection.updated_at = datetime.now(UTC)
        mock_connection.linked_accounts = []

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_connection]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.complete_reauth(user_id)

        assert mock_connection.status == BankConnectionStatus.ACTIVE
        assert mock_connection.status_detail is None
        assert mock_connection.access_valid_until is not None
        assert result.health_status == ConnectionHealthStatus.HEALTHY
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_complete_reauth_no_pending_connection(self) -> None:
        """Test complete reauth when no pending reauth connection exists."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = BankConnectionService(mock_db, mock_adapter)

        user_id = uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="No pending re-auth connection found"):
            await service.complete_reauth(user_id)
