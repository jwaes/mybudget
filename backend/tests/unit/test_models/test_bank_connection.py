"""
Unit tests for bank connection models.
"""
from datetime import datetime, timedelta, UTC
from decimal import Decimal
from uuid import uuid4

import pytest

from mybudget.models.bank_connection import (
    BankConnection,
    BankConnectionStatus,
    LinkedAccount,
    LinkedAccountType,
    SyncJob,
    SyncJobStatus,
    SyncTriggerType,
)


class TestBankConnectionModel:
    """Tests for BankConnection model."""

    def test_create_bank_connection(self) -> None:
        """Test creating a bank connection with required fields."""
        user_id = uuid4()
        connection = BankConnection(
            user_id=user_id,
            provider="gocardless",
            provider_connection_id="REQ-123",
            institution_id="SANDBOXFINANCE_SFIN0000",
            institution_name="Sandbox Finance",
            status=BankConnectionStatus.PENDING,  # Explicit for unit tests
        )

        assert connection.user_id == user_id
        assert connection.provider == "gocardless"
        assert connection.provider_connection_id == "REQ-123"
        assert connection.institution_id == "SANDBOXFINANCE_SFIN0000"
        assert connection.institution_name == "Sandbox Finance"
        assert connection.status == BankConnectionStatus.PENDING

    def test_bank_connection_status_transitions(self) -> None:
        """Test connection status values."""
        assert BankConnectionStatus.PENDING.value == "PENDING"
        assert BankConnectionStatus.ACTIVE.value == "ACTIVE"
        assert BankConnectionStatus.NEEDS_ATTENTION.value == "NEEDS_ATTENTION"
        assert BankConnectionStatus.ERROR.value == "ERROR"
        assert BankConnectionStatus.DISCONNECTED.value == "DISCONNECTED"

    def test_bank_connection_with_status_detail(self) -> None:
        """Test connection with error status detail."""
        connection = BankConnection(
            user_id=uuid4(),
            provider="gocardless",
            provider_connection_id="REQ-456",
            institution_id="BANK123",
            institution_name="Test Bank",
            status=BankConnectionStatus.ERROR,
            status_detail="Bank temporarily unavailable",
        )

        assert connection.status == BankConnectionStatus.ERROR
        assert connection.status_detail == "Bank temporarily unavailable"

    def test_bank_connection_with_sync_timestamps(self) -> None:
        """Test connection with sync timestamps."""
        now = datetime.now(UTC)
        next_sync = now + timedelta(hours=6)

        connection = BankConnection(
            user_id=uuid4(),
            provider="gocardless",
            provider_connection_id="REQ-789",
            institution_id="BANK456",
            institution_name="Another Bank",
            last_sync_at=now,
            next_sync_at=next_sync,
        )

        assert connection.last_sync_at == now
        assert connection.next_sync_at == next_sync

    def test_bank_connection_access_expiry(self) -> None:
        """Test connection with access token expiry."""
        expires = datetime.now(UTC) + timedelta(days=90)

        connection = BankConnection(
            user_id=uuid4(),
            provider="gocardless",
            provider_connection_id="REQ-101",
            institution_id="BANK789",
            institution_name="Euro Bank",
            access_valid_until=expires,
        )

        assert connection.access_valid_until == expires

    def test_is_access_expiring_soon(self) -> None:
        """Test checking if access is expiring soon."""
        # Access expires in 5 days
        soon_expiry = datetime.now(UTC) + timedelta(days=5)
        connection_soon = BankConnection(
            user_id=uuid4(),
            provider="gocardless",
            provider_connection_id="REQ-102",
            institution_id="BANK001",
            institution_name="Bank Soon",
            access_valid_until=soon_expiry,
            status=BankConnectionStatus.ACTIVE,
        )

        # Access expires in 30 days
        later_expiry = datetime.now(UTC) + timedelta(days=30)
        connection_later = BankConnection(
            user_id=uuid4(),
            provider="gocardless",
            provider_connection_id="REQ-103",
            institution_id="BANK002",
            institution_name="Bank Later",
            access_valid_until=later_expiry,
            status=BankConnectionStatus.ACTIVE,
        )

        assert connection_soon.is_access_expiring_soon(days=7) is True
        assert connection_later.is_access_expiring_soon(days=7) is False


class TestLinkedAccountModel:
    """Tests for LinkedAccount model."""

    def test_create_linked_account(self) -> None:
        """Test creating a linked account."""
        connection_id = uuid4()
        linked = LinkedAccount(
            connection_id=connection_id,
            provider_account_id="ACC-12345",
            account_name="Main Checking",
            account_number_masked="****1234",
            account_type=LinkedAccountType.CHECKING,
            currency="EUR",
            is_active=True,  # Explicit for unit tests
        )

        assert linked.connection_id == connection_id
        assert linked.provider_account_id == "ACC-12345"
        assert linked.account_name == "Main Checking"
        assert linked.account_number_masked == "****1234"
        assert linked.account_type == LinkedAccountType.CHECKING
        assert linked.currency == "EUR"
        assert linked.is_active is True

    def test_linked_account_types(self) -> None:
        """Test linked account type values."""
        assert LinkedAccountType.CHECKING.value == "CHECKING"
        assert LinkedAccountType.SAVINGS.value == "SAVINGS"
        assert LinkedAccountType.CREDIT.value == "CREDIT"

    def test_linked_account_with_balance(self) -> None:
        """Test linked account with balance."""
        now = datetime.now(UTC)
        linked = LinkedAccount(
            connection_id=uuid4(),
            provider_account_id="ACC-67890",
            account_type=LinkedAccountType.SAVINGS,
            balance=Decimal("5432.10"),
            balance_updated_at=now,
        )

        assert linked.balance == Decimal("5432.10")
        assert linked.balance_updated_at == now

    def test_linked_account_with_internal_account(self) -> None:
        """Test linked account linked to internal account."""
        account_id = uuid4()
        linked = LinkedAccount(
            connection_id=uuid4(),
            provider_account_id="ACC-11111",
            account_id=account_id,
            account_type=LinkedAccountType.CHECKING,
        )

        assert linked.account_id == account_id


class TestSyncJobModel:
    """Tests for SyncJob model."""

    def test_create_sync_job(self) -> None:
        """Test creating a sync job."""
        connection_id = uuid4()
        job = SyncJob(
            connection_id=connection_id,
            trigger_type=SyncTriggerType.MANUAL,
            status=SyncJobStatus.PENDING,  # Explicit for unit tests
            transactions_fetched=0,
            transactions_imported=0,
            transactions_duplicates=0,
        )

        assert job.connection_id == connection_id
        assert job.trigger_type == SyncTriggerType.MANUAL
        assert job.status == SyncJobStatus.PENDING
        assert job.transactions_fetched == 0
        assert job.transactions_imported == 0
        assert job.transactions_duplicates == 0

    def test_sync_job_status_values(self) -> None:
        """Test sync job status values."""
        assert SyncJobStatus.PENDING.value == "PENDING"
        assert SyncJobStatus.RUNNING.value == "RUNNING"
        assert SyncJobStatus.COMPLETED.value == "COMPLETED"
        assert SyncJobStatus.FAILED.value == "FAILED"

    def test_sync_trigger_types(self) -> None:
        """Test sync trigger type values."""
        assert SyncTriggerType.SCHEDULED.value == "SCHEDULED"
        assert SyncTriggerType.MANUAL.value == "MANUAL"
        assert SyncTriggerType.INITIAL.value == "INITIAL"

    def test_sync_job_for_linked_account(self) -> None:
        """Test sync job targeting specific linked account."""
        connection_id = uuid4()
        linked_account_id = uuid4()
        job = SyncJob(
            connection_id=connection_id,
            linked_account_id=linked_account_id,
            trigger_type=SyncTriggerType.SCHEDULED,
        )

        assert job.linked_account_id == linked_account_id

    def test_sync_job_completion(self) -> None:
        """Test completed sync job with stats."""
        now = datetime.now(UTC)
        job = SyncJob(
            connection_id=uuid4(),
            trigger_type=SyncTriggerType.MANUAL,
            status=SyncJobStatus.COMPLETED,
            started_at=now - timedelta(minutes=2),
            completed_at=now,
            transactions_fetched=50,
            transactions_imported=45,
            transactions_duplicates=5,
        )

        assert job.status == SyncJobStatus.COMPLETED
        assert job.transactions_fetched == 50
        assert job.transactions_imported == 45
        assert job.transactions_duplicates == 5

    def test_sync_job_failure(self) -> None:
        """Test failed sync job with error message."""
        job = SyncJob(
            connection_id=uuid4(),
            trigger_type=SyncTriggerType.SCHEDULED,
            status=SyncJobStatus.FAILED,
            error_message="Connection timeout after 30 seconds",
        )

        assert job.status == SyncJobStatus.FAILED
        assert job.error_message == "Connection timeout after 30 seconds"
