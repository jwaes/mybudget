"""
Unit tests for TransactionSyncService.

Tests transaction sync operations: sync_account, deduplication, sync job management.
"""
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from mybudget.adapters.mock_adapter import MockBankAdapter
from mybudget.adapters.types import ProviderTransaction, ProviderTransactionStatus
from mybudget.models.bank_connection import (
    BankConnection,
    BankConnectionStatus,
    LinkedAccount,
    LinkedAccountType,
    SyncJob,
    SyncJobStatus,
    SyncTriggerType,
)
from mybudget.models.transaction import Transaction, TransactionState
from mybudget.services.transaction_sync_service import TransactionSyncService


class TestTransactionSyncServiceInit:
    """Tests for TransactionSyncService initialization."""

    def test_init_with_db_and_adapter(self) -> None:
        """Test service can be initialized with db and adapter."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)
        assert service.db == mock_db
        assert service.adapter == mock_adapter


class TestTriggerManualSync:
    """Tests for trigger_manual_sync method."""

    @pytest.mark.asyncio
    async def test_trigger_manual_sync_success(self) -> None:
        """Test triggering a manual sync successfully."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()
        linked_account_id = uuid4()

        # Create mock connection
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.provider = "mock"
        mock_connection.provider_connection_id = "REQ-123"
        mock_connection.status = BankConnectionStatus.ACTIVE

        # Create mock linked account
        mock_linked_account = MagicMock(spec=LinkedAccount)
        mock_linked_account.id = linked_account_id
        mock_linked_account.connection_id = connection_id
        mock_linked_account.provider_account_id = "ACC-001"
        mock_linked_account.account_id = uuid4()  # Has linked internal account
        mock_linked_account.is_active = True
        mock_connection.linked_accounts = [mock_linked_account]

        # Mock the query to return the connection
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.trigger_manual_sync(user_id, connection_id)

        assert result is not None
        assert result.connection_id == connection_id
        assert result.trigger_type == SyncTriggerType.MANUAL
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_manual_sync_connection_not_found(self) -> None:
        """Test trigger sync fails for non-existent connection."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Connection not found"):
            await service.trigger_manual_sync(user_id, connection_id)

    @pytest.mark.asyncio
    async def test_trigger_manual_sync_connection_not_active(self) -> None:
        """Test trigger sync fails for disconnected connection."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.status = BankConnectionStatus.DISCONNECTED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Connection is not active"):
            await service.trigger_manual_sync(user_id, connection_id)


class TestSyncAccount:
    """Tests for sync_account method."""

    @pytest.mark.asyncio
    async def test_sync_account_creates_transactions(self) -> None:
        """Test sync_account fetches and creates transactions."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()

        # Set up mock transactions to return
        provider_transactions = [
            ProviderTransaction(
                id="TX-001",
                date=date.today(),
                amount=Decimal("-50.00"),
                currency="EUR",
                description="Coffee Shop",
                status=ProviderTransactionStatus.BOOKED,
                creditor_name="Coffee Shop",
            ),
            ProviderTransaction(
                id="TX-002",
                date=date.today(),
                amount=Decimal("1500.00"),
                currency="EUR",
                description="Salary",
                status=ProviderTransactionStatus.BOOKED,
                debtor_name="Employer Inc",
            ),
        ]
        mock_adapter.set_transactions(provider_transactions)

        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()
        linked_account_id = uuid4()
        internal_account_id = uuid4()
        sync_job_id = uuid4()

        # Create mock linked account
        mock_linked_account = MagicMock(spec=LinkedAccount)
        mock_linked_account.id = linked_account_id
        mock_linked_account.connection_id = connection_id
        mock_linked_account.provider_account_id = "ACC-001"
        mock_linked_account.account_id = internal_account_id
        mock_linked_account.is_active = True

        # Create mock connection
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.provider = "mock"
        mock_connection.provider_connection_id = "REQ-123"
        mock_connection.status = BankConnectionStatus.ACTIVE

        mock_linked_account.connection = mock_connection

        # Create mock sync job
        mock_sync_job = MagicMock(spec=SyncJob)
        mock_sync_job.id = sync_job_id
        mock_sync_job.connection_id = connection_id
        mock_sync_job.linked_account_id = linked_account_id
        mock_sync_job.status = SyncJobStatus.PENDING
        mock_sync_job.transactions_fetched = 0
        mock_sync_job.transactions_imported = 0
        mock_sync_job.transactions_duplicates = 0

        # Mock query for linked account
        mock_la_result = MagicMock()
        mock_la_result.scalar_one_or_none.return_value = mock_linked_account

        # Mock query for existing transactions (none exist)
        mock_tx_result = MagicMock()
        mock_tx_scalars = MagicMock()
        mock_tx_scalars.all.return_value = []
        mock_tx_result.scalars.return_value = mock_tx_scalars

        mock_db.execute.side_effect = [mock_la_result, mock_tx_result]
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.sync_account(linked_account_id, mock_sync_job)

        # Should have fetched 2 transactions and imported both
        assert result.transactions_fetched == 2
        assert result.transactions_imported == 2
        assert result.transactions_duplicates == 0
        assert result.status == SyncJobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_sync_account_skips_duplicates(self) -> None:
        """Test sync_account detects and skips duplicate transactions."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()

        # Set up mock transactions to return
        provider_transactions = [
            ProviderTransaction(
                id="TX-001",
                date=date.today(),
                amount=Decimal("-50.00"),
                currency="EUR",
                description="Coffee Shop",
                status=ProviderTransactionStatus.BOOKED,
                creditor_name="Coffee Shop",
            ),
        ]
        mock_adapter.set_transactions(provider_transactions)

        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()
        linked_account_id = uuid4()
        internal_account_id = uuid4()
        sync_job_id = uuid4()

        # Create mock linked account
        mock_linked_account = MagicMock(spec=LinkedAccount)
        mock_linked_account.id = linked_account_id
        mock_linked_account.connection_id = connection_id
        mock_linked_account.provider_account_id = "ACC-001"
        mock_linked_account.account_id = internal_account_id
        mock_linked_account.is_active = True

        # Create mock connection
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.provider = "mock"
        mock_connection.provider_connection_id = "REQ-123"
        mock_connection.status = BankConnectionStatus.ACTIVE

        mock_linked_account.connection = mock_connection

        # Create mock sync job
        mock_sync_job = MagicMock(spec=SyncJob)
        mock_sync_job.id = sync_job_id
        mock_sync_job.connection_id = connection_id
        mock_sync_job.linked_account_id = linked_account_id
        mock_sync_job.status = SyncJobStatus.PENDING
        mock_sync_job.transactions_fetched = 0
        mock_sync_job.transactions_imported = 0
        mock_sync_job.transactions_duplicates = 0

        # Mock query for linked account
        mock_la_result = MagicMock()
        mock_la_result.scalar_one_or_none.return_value = mock_linked_account

        # Mock existing transaction (duplicate)
        existing_tx = MagicMock(spec=Transaction)
        existing_tx.id = uuid4()
        existing_tx.external_id = "TX-001"  # Same as provider transaction
        existing_tx.date = date.today()
        existing_tx.amount = Decimal("-50.00")
        existing_tx.payee = "Coffee Shop"

        mock_tx_result = MagicMock()
        mock_tx_scalars = MagicMock()
        mock_tx_scalars.all.return_value = [existing_tx]
        mock_tx_result.scalars.return_value = mock_tx_scalars

        mock_db.execute.side_effect = [mock_la_result, mock_tx_result]
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        result = await service.sync_account(linked_account_id, mock_sync_job)

        # Should have fetched 1 but imported 0 due to duplicate
        assert result.transactions_fetched == 1
        assert result.transactions_imported == 0
        assert result.transactions_duplicates == 1
        assert result.status == SyncJobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_sync_account_linked_account_not_found(self) -> None:
        """Test sync_account fails for non-existent linked account."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        linked_account_id = uuid4()
        mock_sync_job = MagicMock(spec=SyncJob)
        mock_sync_job.id = uuid4()
        mock_sync_job.status = SyncJobStatus.PENDING

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Linked account not found"):
            await service.sync_account(linked_account_id, mock_sync_job)

    @pytest.mark.asyncio
    async def test_sync_account_no_internal_account_linked(self) -> None:
        """Test sync_account fails if no internal account is linked."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        linked_account_id = uuid4()
        connection_id = uuid4()

        mock_linked_account = MagicMock(spec=LinkedAccount)
        mock_linked_account.id = linked_account_id
        mock_linked_account.connection_id = connection_id
        mock_linked_account.account_id = None  # No internal account linked
        mock_linked_account.is_active = True

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = uuid4()
        mock_linked_account.connection = mock_connection

        mock_sync_job = MagicMock(spec=SyncJob)
        mock_sync_job.id = uuid4()
        mock_sync_job.status = SyncJobStatus.PENDING

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_linked_account
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="No internal account linked"):
            await service.sync_account(linked_account_id, mock_sync_job)

    @pytest.mark.asyncio
    async def test_sync_account_handles_provider_error(self) -> None:
        """Test sync_account handles provider API errors gracefully."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter(fail_on_transactions=True)
        service = TransactionSyncService(mock_db, mock_adapter)

        linked_account_id = uuid4()
        connection_id = uuid4()
        internal_account_id = uuid4()

        mock_linked_account = MagicMock(spec=LinkedAccount)
        mock_linked_account.id = linked_account_id
        mock_linked_account.connection_id = connection_id
        mock_linked_account.provider_account_id = "ACC-001"
        mock_linked_account.account_id = internal_account_id
        mock_linked_account.is_active = True

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = uuid4()
        mock_connection.provider = "mock"
        mock_connection.provider_connection_id = "REQ-123"
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_linked_account.connection = mock_connection

        mock_sync_job = MagicMock(spec=SyncJob)
        mock_sync_job.id = uuid4()
        mock_sync_job.status = SyncJobStatus.PENDING
        mock_sync_job.error_message = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_linked_account
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        result = await service.sync_account(linked_account_id, mock_sync_job)

        assert result.status == SyncJobStatus.FAILED
        assert result.error_message is not None
        assert "Mock transaction fetch failure" in result.error_message


class TestDeduplicateTransactions:
    """Tests for _deduplicate_transactions method."""

    def test_deduplicate_by_external_id(self) -> None:
        """Test deduplication by external_id match."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        existing_tx = MagicMock(spec=Transaction)
        existing_tx.external_id = "TX-001"
        existing_tx.date = date.today()
        existing_tx.amount = Decimal("-50.00")
        existing_tx.payee = "Coffee Shop"

        provider_tx = ProviderTransaction(
            id="TX-001",
            date=date.today(),
            amount=Decimal("-50.00"),
            currency="EUR",
            description="Coffee Shop",
            status=ProviderTransactionStatus.BOOKED,
        )

        is_duplicate = service._is_duplicate(provider_tx, [existing_tx])
        assert is_duplicate is True

    def test_deduplicate_by_fuzzy_match_same_day(self) -> None:
        """Test deduplication by fuzzy match (same date, amount, similar payee)."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        existing_tx = MagicMock(spec=Transaction)
        existing_tx.external_id = None  # No external ID
        existing_tx.date = date.today()
        existing_tx.amount = Decimal("-50.00")
        existing_tx.payee = "Coffee Shop"

        provider_tx = ProviderTransaction(
            id="TX-NEW",
            date=date.today(),
            amount=Decimal("-50.00"),
            currency="EUR",
            description="Coffee Shop",  # Same payee
            status=ProviderTransactionStatus.BOOKED,
        )

        is_duplicate = service._is_duplicate(provider_tx, [existing_tx])
        assert is_duplicate is True

    def test_deduplicate_by_fuzzy_match_adjacent_day(self) -> None:
        """Test deduplication allows +/- 1 day tolerance."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        existing_tx = MagicMock(spec=Transaction)
        existing_tx.external_id = None
        existing_tx.date = date.today() - timedelta(days=1)  # Yesterday
        existing_tx.amount = Decimal("-50.00")
        existing_tx.payee = "Coffee Shop"

        provider_tx = ProviderTransaction(
            id="TX-NEW",
            date=date.today(),  # Today
            amount=Decimal("-50.00"),
            currency="EUR",
            description="Coffee Shop",
            status=ProviderTransactionStatus.BOOKED,
        )

        is_duplicate = service._is_duplicate(provider_tx, [existing_tx])
        assert is_duplicate is True

    def test_no_duplicate_different_amount(self) -> None:
        """Test that different amounts are not duplicates."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        existing_tx = MagicMock(spec=Transaction)
        existing_tx.external_id = None
        existing_tx.date = date.today()
        existing_tx.amount = Decimal("-50.00")
        existing_tx.payee = "Coffee Shop"

        provider_tx = ProviderTransaction(
            id="TX-NEW",
            date=date.today(),
            amount=Decimal("-75.00"),  # Different amount
            currency="EUR",
            description="Coffee Shop",
            status=ProviderTransactionStatus.BOOKED,
        )

        is_duplicate = service._is_duplicate(provider_tx, [existing_tx])
        assert is_duplicate is False

    def test_no_duplicate_different_payee(self) -> None:
        """Test that different payees with same amount/date are not duplicates."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        existing_tx = MagicMock(spec=Transaction)
        existing_tx.external_id = None
        existing_tx.date = date.today()
        existing_tx.amount = Decimal("-50.00")
        existing_tx.payee = "Coffee Shop"

        provider_tx = ProviderTransaction(
            id="TX-NEW",
            date=date.today(),
            amount=Decimal("-50.00"),
            currency="EUR",
            description="Restaurant",  # Different payee
            status=ProviderTransactionStatus.BOOKED,
        )

        is_duplicate = service._is_duplicate(provider_tx, [existing_tx])
        assert is_duplicate is False

    def test_no_duplicate_far_apart_dates(self) -> None:
        """Test that transactions more than 1 day apart are not duplicates."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        existing_tx = MagicMock(spec=Transaction)
        existing_tx.external_id = None
        existing_tx.date = date.today() - timedelta(days=5)  # 5 days ago
        existing_tx.amount = Decimal("-50.00")
        existing_tx.payee = "Coffee Shop"

        provider_tx = ProviderTransaction(
            id="TX-NEW",
            date=date.today(),
            amount=Decimal("-50.00"),
            currency="EUR",
            description="Coffee Shop",
            status=ProviderTransactionStatus.BOOKED,
        )

        is_duplicate = service._is_duplicate(provider_tx, [existing_tx])
        assert is_duplicate is False


class TestGetSyncJobs:
    """Tests for get_sync_jobs method."""

    @pytest.mark.asyncio
    async def test_get_sync_jobs_returns_jobs(self) -> None:
        """Test getting sync jobs for a connection."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        # Create mock connection
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id

        # Create mock sync jobs
        mock_job1 = MagicMock(spec=SyncJob)
        mock_job1.id = uuid4()
        mock_job1.connection_id = connection_id
        mock_job1.status = SyncJobStatus.COMPLETED
        mock_job1.trigger_type = SyncTriggerType.MANUAL
        mock_job1.created_at = datetime.now(UTC)

        mock_job2 = MagicMock(spec=SyncJob)
        mock_job2.id = uuid4()
        mock_job2.connection_id = connection_id
        mock_job2.status = SyncJobStatus.PENDING
        mock_job2.trigger_type = SyncTriggerType.SCHEDULED
        mock_job2.created_at = datetime.now(UTC) - timedelta(hours=1)

        # Mock connection query
        mock_conn_result = MagicMock()
        mock_conn_result.scalar_one_or_none.return_value = mock_connection

        # Mock jobs query
        mock_jobs_result = MagicMock()
        mock_jobs_scalars = MagicMock()
        mock_jobs_scalars.all.return_value = [mock_job1, mock_job2]
        mock_jobs_result.scalars.return_value = mock_jobs_scalars

        mock_db.execute.side_effect = [mock_conn_result, mock_jobs_result]

        result = await service.get_sync_jobs(user_id, connection_id)

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_sync_jobs_connection_not_found(self) -> None:
        """Test get_sync_jobs fails for non-existent connection."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Connection not found"):
            await service.get_sync_jobs(user_id, connection_id)

    @pytest.mark.asyncio
    async def test_get_sync_jobs_with_status_filter(self) -> None:
        """Test getting sync jobs filtered by status."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id

        mock_job = MagicMock(spec=SyncJob)
        mock_job.id = uuid4()
        mock_job.connection_id = connection_id
        mock_job.status = SyncJobStatus.COMPLETED

        mock_conn_result = MagicMock()
        mock_conn_result.scalar_one_or_none.return_value = mock_connection

        mock_jobs_result = MagicMock()
        mock_jobs_scalars = MagicMock()
        mock_jobs_scalars.all.return_value = [mock_job]
        mock_jobs_result.scalars.return_value = mock_jobs_scalars

        mock_db.execute.side_effect = [mock_conn_result, mock_jobs_result]

        result = await service.get_sync_jobs(
            user_id, connection_id, status=SyncJobStatus.COMPLETED
        )

        assert len(result) == 1
        assert result[0].status == SyncJobStatus.COMPLETED


class TestGetSyncJob:
    """Tests for get_sync_job method."""

    @pytest.mark.asyncio
    async def test_get_sync_job_success(self) -> None:
        """Test getting a specific sync job."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        sync_job_id = uuid4()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id

        mock_job = MagicMock(spec=SyncJob)
        mock_job.id = sync_job_id
        mock_job.connection_id = connection_id
        mock_job.status = SyncJobStatus.COMPLETED
        mock_job.connection = mock_connection

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result

        result = await service.get_sync_job(user_id, sync_job_id)

        assert result is not None
        assert result.id == sync_job_id

    @pytest.mark.asyncio
    async def test_get_sync_job_not_found(self) -> None:
        """Test getting a non-existent sync job returns None."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        sync_job_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await service.get_sync_job(user_id, sync_job_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_get_sync_job_wrong_user(self) -> None:
        """Test getting another user's sync job returns None."""
        mock_db = AsyncMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        other_user_id = uuid4()
        sync_job_id = uuid4()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = other_user_id  # Different user

        mock_job = MagicMock(spec=SyncJob)
        mock_job.id = sync_job_id
        mock_job.connection_id = connection_id
        mock_job.connection = mock_connection

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_db.execute.return_value = mock_result

        result = await service.get_sync_job(user_id, sync_job_id)

        # Returns None for wrong user to prevent leaking info
        assert result is None


class TestCreateTransactionFromProvider:
    """Tests for _create_transaction method."""

    def test_create_transaction_expense(self) -> None:
        """Test creating a transaction from provider expense."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        account_id = uuid4()
        import_batch_id = uuid4()

        provider_tx = ProviderTransaction(
            id="TX-001",
            date=date.today(),
            amount=Decimal("-50.00"),
            currency="EUR",
            description="Coffee Shop",
            status=ProviderTransactionStatus.BOOKED,
            creditor_name="Coffee Shop",
        )

        transaction = service._create_transaction(
            provider_tx, user_id, account_id, "mock", import_batch_id
        )

        assert transaction.user_id == user_id
        assert transaction.account_id == account_id
        assert transaction.date == date.today()
        assert transaction.amount == Decimal("-50.00")
        assert transaction.payee == "Coffee Shop"
        assert transaction.state == TransactionState.INBOX
        assert transaction.external_id == "TX-001"
        assert transaction.import_source == "mock"
        assert transaction.import_batch_id == import_batch_id

    def test_create_transaction_income(self) -> None:
        """Test creating a transaction from provider income."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        user_id = uuid4()
        account_id = uuid4()
        import_batch_id = uuid4()

        provider_tx = ProviderTransaction(
            id="TX-002",
            date=date.today(),
            amount=Decimal("1500.00"),
            currency="EUR",
            description="Salary",
            status=ProviderTransactionStatus.BOOKED,
            debtor_name="Employer Inc",
        )

        transaction = service._create_transaction(
            provider_tx, user_id, account_id, "gocardless", import_batch_id
        )

        assert transaction.amount == Decimal("1500.00")
        assert transaction.payee == "Employer Inc"  # Uses debtor_name for income
        assert transaction.external_id == "TX-002"
        assert transaction.import_source == "gocardless"


class TestPayeeSimilarity:
    """Tests for payee similarity calculation (fuzzy matching)."""

    def test_similar_payees(self) -> None:
        """Test that similar payees are detected."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        # Same string
        assert service._payees_similar("Coffee Shop", "Coffee Shop") is True

        # Case insensitive
        assert service._payees_similar("COFFEE SHOP", "coffee shop") is True

        # Minor typo/variation
        assert service._payees_similar("Coffe Shop", "Coffee Shop") is True

    def test_dissimilar_payees(self) -> None:
        """Test that dissimilar payees are not matched."""
        mock_db = MagicMock()
        mock_adapter = MockBankAdapter()
        service = TransactionSyncService(mock_db, mock_adapter)

        assert service._payees_similar("Coffee Shop", "Restaurant") is False
        assert service._payees_similar("Amazon", "Netflix") is False
