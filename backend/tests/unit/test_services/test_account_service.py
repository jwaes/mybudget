"""
Unit tests for AccountService.

Tests account CRUD operations: create, get, list, update, delete, retry_sync.
"""
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from mybudget.models.account import Account, AccountType, SyncStatus
from mybudget.schemas.account import AccountCreate, AccountUpdate
from mybudget.services.account_service import AccountService


class TestAccountServiceInit:
    """Tests for AccountService initialization."""

    def test_init_with_db_session(self) -> None:
        """Test AccountService can be initialized with db session."""
        mock_db = MagicMock()
        service = AccountService(mock_db)
        assert service.db == mock_db


class TestCreateAccount:
    """Tests for create_account method."""

    @pytest.mark.asyncio
    async def test_create_account_success(self) -> None:
        """Test creating an account with valid data."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        data = AccountCreate(
            name="Test Checking",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("1000.00"),
        )

        # Mock the db operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.create_account(user_id, data)

        # Verify db.add was called with an Account
        mock_db.add.assert_called_once()
        added_account = mock_db.add.call_args[0][0]
        assert isinstance(added_account, Account)
        assert added_account.user_id == user_id
        assert added_account.name == "Test Checking"
        assert added_account.account_type == AccountType.CHECKING
        assert added_account.initial_balance == Decimal("1000.00")
        assert added_account.balance == Decimal("0")

        # Verify commit and refresh were called
        mock_db.commit.assert_awaited_once()
        mock_db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_account_savings_type(self) -> None:
        """Test creating a savings account."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        data = AccountCreate(
            name="Emergency Fund",
            account_type=AccountType.SAVINGS,
            initial_balance=Decimal("5000.00"),
        )

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        await service.create_account(user_id, data)

        added_account = mock_db.add.call_args[0][0]
        assert added_account.account_type == AccountType.SAVINGS
        assert added_account.initial_balance == Decimal("5000.00")

    @pytest.mark.asyncio
    async def test_create_account_zero_initial_balance(self) -> None:
        """Test creating an account with zero initial balance."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        data = AccountCreate(
            name="New Account",
            account_type=AccountType.CHECKING,
            initial_balance=Decimal("0.00"),
        )

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        await service.create_account(user_id, data)

        added_account = mock_db.add.call_args[0][0]
        assert added_account.initial_balance == Decimal("0.00")
        assert added_account.balance == Decimal("0")


class TestGetAccount:
    """Tests for get_account method."""

    @pytest.mark.asyncio
    async def test_get_account_found(self) -> None:
        """Test getting an account that exists and belongs to user."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        mock_account = Account(
            id=account_id,
            user_id=user_id,
            name="Test Account",
            account_type=AccountType.CHECKING,
            balance=Decimal("500.00"),
            initial_balance=Decimal("1000.00"),
        )

        # Mock the query execution
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        mock_db.execute.return_value = mock_result

        result = await service.get_account(user_id, account_id)

        assert result == mock_account
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_account_not_found(self) -> None:
        """Test getting an account that doesn't exist."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_account(user_id, account_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_account_wrong_user(self) -> None:
        """Test that getting an account with wrong user_id returns None."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        other_user_id = uuid4()
        account_id = uuid4()

        # Account exists but belongs to other user - query returns None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_account(other_user_id, account_id)

        assert result is None


class TestListAccounts:
    """Tests for list_accounts method."""

    @pytest.mark.asyncio
    async def test_list_accounts_with_accounts(self) -> None:
        """Test listing accounts for a user with multiple accounts."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()

        mock_accounts = [
            Account(
                id=uuid4(),
                user_id=user_id,
                name="Account A",
                account_type=AccountType.CHECKING,
                balance=Decimal("500.00"),
                initial_balance=Decimal("1000.00"),
            ),
            Account(
                id=uuid4(),
                user_id=user_id,
                name="Account B",
                account_type=AccountType.SAVINGS,
                balance=Decimal("2000.00"),
                initial_balance=Decimal("2000.00"),
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_accounts
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_accounts(user_id)

        assert len(result) == 2
        assert result == mock_accounts
        mock_db.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_list_accounts_empty(self) -> None:
        """Test listing accounts for a user with no accounts."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_accounts(user_id)

        assert result == []


class TestUpdateAccount:
    """Tests for update_account method."""

    @pytest.mark.asyncio
    async def test_update_account_name_success(self) -> None:
        """Test updating account name successfully."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        mock_account = Account(
            id=account_id,
            user_id=user_id,
            name="Old Name",
            account_type=AccountType.CHECKING,
            balance=Decimal("500.00"),
            initial_balance=Decimal("1000.00"),
        )

        data = AccountUpdate(name="New Name")

        # Mock get_account to return the account
        with patch.object(service, "get_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_account
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_account(user_id, account_id, data)

            assert result is not None
            assert result.name == "New Name"
            mock_get.assert_awaited_once_with(user_id, account_id)
            mock_db.commit.assert_awaited_once()
            mock_db.refresh.assert_awaited_once_with(mock_account)

    @pytest.mark.asyncio
    async def test_update_account_not_found(self) -> None:
        """Test updating an account that doesn't exist."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        data = AccountUpdate(name="New Name")

        with patch.object(service, "get_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await service.update_account(user_id, account_id, data)

            assert result is None
            mock_get.assert_awaited_once_with(user_id, account_id)

    @pytest.mark.asyncio
    async def test_update_account_no_changes(self) -> None:
        """Test updating account with None values (no changes)."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        mock_account = Account(
            id=account_id,
            user_id=user_id,
            name="Original Name",
            account_type=AccountType.CHECKING,
            balance=Decimal("500.00"),
            initial_balance=Decimal("1000.00"),
        )

        data = AccountUpdate(name=None)

        with patch.object(service, "get_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_account
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.update_account(user_id, account_id, data)

            assert result is not None
            assert result.name == "Original Name"  # Name unchanged


class TestDeleteAccount:
    """Tests for delete_account method."""

    @pytest.mark.asyncio
    async def test_delete_account_success(self) -> None:
        """Test deleting an account successfully."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        mock_account = Account(
            id=account_id,
            user_id=user_id,
            name="To Delete",
            account_type=AccountType.CHECKING,
            balance=Decimal("0.00"),
            initial_balance=Decimal("1000.00"),
        )

        with patch.object(service, "get_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_account
            mock_db.delete = AsyncMock()
            mock_db.commit = AsyncMock()

            result = await service.delete_account(user_id, account_id)

            assert result is True
            mock_get.assert_awaited_once_with(user_id, account_id)
            mock_db.delete.assert_awaited_once_with(mock_account)
            mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete_account_not_found(self) -> None:
        """Test deleting an account that doesn't exist."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        with patch.object(service, "get_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await service.delete_account(user_id, account_id)

            assert result is False
            mock_get.assert_awaited_once_with(user_id, account_id)


class TestUpdateBalance:
    """Tests for update_balance method."""

    @pytest.mark.asyncio
    async def test_update_balance_positive(self) -> None:
        """Test adding positive amount to balance."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        account_id = uuid4()

        mock_account = MagicMock()
        mock_account.balance = Decimal("100.00")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        await service.update_balance(account_id, Decimal("50.00"))

        assert mock_account.balance == Decimal("150.00")
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_balance_negative(self) -> None:
        """Test subtracting amount from balance."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        account_id = uuid4()

        mock_account = MagicMock()
        mock_account.balance = Decimal("100.00")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        await service.update_balance(account_id, Decimal("-30.00"))

        assert mock_account.balance == Decimal("70.00")
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_balance_account_not_found(self) -> None:
        """Test update_balance when account doesn't exist (no-op)."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        account_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Should not raise, just no-op
        await service.update_balance(account_id, Decimal("50.00"))

        # Commit should not be called since no account found
        mock_db.commit.assert_not_awaited()


class TestUpdateSyncStatus:
    """Tests for update_sync_status method."""

    @pytest.mark.asyncio
    async def test_update_sync_status_success(self) -> None:
        """Test updating sync status to SUCCESS."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        account_id = uuid4()

        mock_account = MagicMock()
        mock_account.sync_status = SyncStatus.PENDING
        mock_account.sync_error = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        await service.update_sync_status(account_id, SyncStatus.SUCCESS)

        assert mock_account.sync_status == SyncStatus.SUCCESS
        assert mock_account.sync_error is None
        assert mock_account.last_sync_at is not None
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_sync_status_failed_with_error(self) -> None:
        """Test updating sync status to FAILED with error message."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        account_id = uuid4()

        mock_account = MagicMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        await service.update_sync_status(
            account_id, SyncStatus.FAILED, error="Connection timeout"
        )

        assert mock_account.sync_status == SyncStatus.FAILED
        assert mock_account.sync_error == "Connection timeout"
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_sync_status_success_clears_error(self) -> None:
        """Test that setting status to SUCCESS clears any previous error."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        account_id = uuid4()

        mock_account = MagicMock()
        mock_account.sync_status = SyncStatus.FAILED
        mock_account.sync_error = "Previous error"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Even if error is passed, it should be cleared for non-FAILED status
        await service.update_sync_status(
            account_id, SyncStatus.SUCCESS, error="This should be ignored"
        )

        assert mock_account.sync_status == SyncStatus.SUCCESS
        assert mock_account.sync_error is None

    @pytest.mark.asyncio
    async def test_update_sync_status_account_not_found(self) -> None:
        """Test update_sync_status when account doesn't exist (no-op)."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        account_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        # Should not raise, just no-op
        await service.update_sync_status(account_id, SyncStatus.SUCCESS)

        mock_db.commit.assert_not_awaited()


class TestRetrySync:
    """Tests for retry_sync method."""

    @pytest.mark.asyncio
    async def test_retry_sync_success(self) -> None:
        """Test retry sync resets status to PENDING."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        mock_account = MagicMock()
        mock_account.sync_status = SyncStatus.FAILED
        mock_account.sync_error = "Previous error"

        with patch.object(service, "get_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_account
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.retry_sync(user_id, account_id)

            assert result is not None
            assert mock_account.sync_status == SyncStatus.PENDING
            assert mock_account.sync_error is None
            mock_get.assert_awaited_once_with(user_id, account_id)
            mock_db.commit.assert_awaited_once()
            mock_db.refresh.assert_awaited_once_with(mock_account)

    @pytest.mark.asyncio
    async def test_retry_sync_account_not_found(self) -> None:
        """Test retry sync returns None when account not found."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        with patch.object(service, "get_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            result = await service.retry_sync(user_id, account_id)

            assert result is None
            mock_get.assert_awaited_once_with(user_id, account_id)

    @pytest.mark.asyncio
    async def test_retry_sync_from_never_synced(self) -> None:
        """Test retry sync from NEVER_SYNCED status."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()
        account_id = uuid4()

        mock_account = MagicMock()
        mock_account.sync_status = SyncStatus.NEVER_SYNCED
        mock_account.sync_error = None

        with patch.object(service, "get_account", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_account
            mock_db.commit = AsyncMock()
            mock_db.refresh = AsyncMock()

            result = await service.retry_sync(user_id, account_id)

            assert result is not None
            assert mock_account.sync_status == SyncStatus.PENDING


class TestUserIsolation:
    """Tests ensuring account operations respect user isolation."""

    @pytest.mark.asyncio
    async def test_get_account_enforces_user_ownership(self) -> None:
        """Test that get_account only returns accounts owned by the user."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        owner_user_id = uuid4()
        other_user_id = uuid4()
        account_id = uuid4()

        # The account belongs to owner_user_id
        mock_account = Account(
            id=account_id,
            user_id=owner_user_id,
            name="Owner's Account",
            account_type=AccountType.CHECKING,
            balance=Decimal("500.00"),
            initial_balance=Decimal("1000.00"),
        )

        # When queried by owner, returns the account
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_account
        mock_db.execute.return_value = mock_result

        result = await service.get_account(owner_user_id, account_id)
        assert result == mock_account

        # When queried by other user, query returns None (filtered by WHERE clause)
        mock_result.scalar_one_or_none.return_value = None
        result = await service.get_account(other_user_id, account_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_accounts_only_returns_user_accounts(self) -> None:
        """Test that list_accounts only returns accounts for the specified user."""
        mock_db = AsyncMock()
        service = AccountService(mock_db)

        user_id = uuid4()

        # Only user's accounts should be returned
        user_accounts = [
            Account(
                id=uuid4(),
                user_id=user_id,
                name="User Account",
                account_type=AccountType.CHECKING,
                balance=Decimal("100.00"),
                initial_balance=Decimal("100.00"),
            ),
        ]

        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = user_accounts
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await service.list_accounts(user_id)

        assert len(result) == 1
        assert all(acc.user_id == user_id for acc in result)
