"""
Unit tests for SyncScheduler.

Tests sync scheduling, execution, and failure handling with retry logic.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from mybudget.models.bank_connection import (
    BankConnection,
    BankConnectionStatus,
    LinkedAccount,
    SyncJob,
    SyncJobStatus,
)
from mybudget.scheduler.sync_scheduler import (
    RETRY_DELAYS,
    SyncScheduler,
    get_sync_scheduler,
    sync_scheduler,
)


class TestSyncSchedulerInit:
    """Tests for SyncScheduler initialization."""

    def test_init_with_defaults(self) -> None:
        """Test scheduler uses config defaults."""
        scheduler = SyncScheduler()
        # These values come from settings defaults
        assert scheduler.sync_interval_hours == 6
        assert scheduler.check_interval_minutes == 5
        assert scheduler.max_retries == 3

    def test_init_with_custom_values(self) -> None:
        """Test scheduler accepts custom values."""
        scheduler = SyncScheduler(
            sync_interval_hours=12,
            check_interval_minutes=10,
            max_retries=5,
        )
        assert scheduler.sync_interval_hours == 12
        assert scheduler.check_interval_minutes == 10
        assert scheduler.max_retries == 5


class TestGetSyncScheduler:
    """Tests for get_sync_scheduler function."""

    def test_returns_global_instance(self) -> None:
        """Test get_sync_scheduler returns the global instance."""
        assert get_sync_scheduler() is sync_scheduler

    def test_returns_same_instance(self) -> None:
        """Test get_sync_scheduler always returns the same instance."""
        instance1 = get_sync_scheduler()
        instance2 = get_sync_scheduler()
        assert instance1 is instance2


class TestGetAdapterForProvider:
    """Tests for _get_adapter_for_provider method."""

    def test_returns_none_for_unknown_provider(self) -> None:
        """Test returns None for unknown provider."""
        scheduler = SyncScheduler()
        adapter = scheduler._get_adapter_for_provider("unknown")
        assert adapter is None

    @patch("mybudget.scheduler.sync_scheduler.GoCardlessAdapter")
    def test_returns_gocardless_adapter(self, mock_adapter_class: MagicMock) -> None:
        """Test returns GoCardless adapter for 'gocardless' provider."""
        mock_adapter = MagicMock()
        mock_adapter_class.return_value = mock_adapter

        scheduler = SyncScheduler()
        adapter = scheduler._get_adapter_for_provider("gocardless")

        assert adapter is mock_adapter
        mock_adapter_class.assert_called_once()

    @patch("mybudget.scheduler.sync_scheduler.GoCardlessAdapter")
    def test_returns_none_when_adapter_fails(self, mock_adapter_class: MagicMock) -> None:
        """Test returns None when adapter initialization fails."""
        mock_adapter_class.side_effect = Exception("Failed to initialize")

        scheduler = SyncScheduler()
        adapter = scheduler._get_adapter_for_provider("gocardless")

        assert adapter is None


class TestScheduleSyncJob:
    """Tests for schedule_sync_job method."""

    @pytest.mark.asyncio
    async def test_schedules_next_sync_after_last_sync(self) -> None:
        """Test schedules next sync based on last_sync_at."""
        mock_db = AsyncMock()
        connection_id = uuid4()
        last_sync = datetime.now(UTC) - timedelta(hours=1)

        # Create mock connection
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.last_sync_at = last_sync
        mock_connection.next_sync_at = None

        # Mock query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        scheduler = SyncScheduler(sync_interval_hours=6)
        next_sync = await scheduler.schedule_sync_job(mock_db, connection_id)

        # Should be 6 hours after last sync
        expected_time = last_sync + timedelta(hours=6)
        assert abs((next_sync - expected_time).total_seconds()) < 1
        assert mock_connection.next_sync_at == next_sync

    @pytest.mark.asyncio
    async def test_schedules_future_sync_when_past_due(self) -> None:
        """Test schedules future sync when calculated time is in the past."""
        mock_db = AsyncMock()
        connection_id = uuid4()
        last_sync = datetime.now(UTC) - timedelta(hours=12)  # 12 hours ago

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.last_sync_at = last_sync
        mock_connection.next_sync_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        scheduler = SyncScheduler(sync_interval_hours=6)
        next_sync = await scheduler.schedule_sync_job(mock_db, connection_id)

        # Should be in the future (6 hours from now)
        now = datetime.now(UTC)
        assert next_sync > now

    @pytest.mark.asyncio
    async def test_schedules_from_now_when_no_last_sync(self) -> None:
        """Test schedules from now when no last_sync_at."""
        mock_db = AsyncMock()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.last_sync_at = None
        mock_connection.next_sync_at = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_connection
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        scheduler = SyncScheduler(sync_interval_hours=6)
        now_before = datetime.now(UTC)
        next_sync = await scheduler.schedule_sync_job(mock_db, connection_id)
        now_after = datetime.now(UTC)

        # Should be approximately 6 hours from now
        expected_min = now_before + timedelta(hours=6)
        expected_max = now_after + timedelta(hours=6)
        assert expected_min <= next_sync <= expected_max

    @pytest.mark.asyncio
    async def test_raises_for_nonexistent_connection(self) -> None:
        """Test raises ValueError for non-existent connection."""
        mock_db = AsyncMock()
        connection_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        scheduler = SyncScheduler()

        with pytest.raises(ValueError, match="Connection not found"):
            await scheduler.schedule_sync_job(mock_db, connection_id)


class TestRunScheduledSyncs:
    """Tests for run_scheduled_syncs method."""

    @pytest.mark.asyncio
    @patch("mybudget.scheduler.sync_scheduler.AsyncSessionLocal")
    async def test_processes_due_connections(self, mock_session_local: MagicMock) -> None:
        """Test processes connections with next_sync_at <= now."""
        connection_id = uuid4()
        user_id = uuid4()
        linked_account_id = uuid4()

        # Create mock connection due for sync
        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.user_id = user_id
        mock_connection.provider = "gocardless"
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.next_sync_at = datetime.now(UTC) - timedelta(minutes=5)
        mock_connection.linked_accounts = []

        # Create mock linked account
        mock_linked_account = MagicMock(spec=LinkedAccount)
        mock_linked_account.id = linked_account_id
        mock_linked_account.account_id = uuid4()
        mock_linked_account.is_active = True
        mock_connection.linked_accounts = [mock_linked_account]

        # Mock database session
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

        # Mock query for due connections
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_connection]
        mock_db.execute.return_value = mock_result

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock adapter
        with patch.object(
            SyncScheduler, "_get_adapter_for_provider", return_value=None
        ):
            scheduler = SyncScheduler()
            stats = await scheduler.run_scheduled_syncs()

        # Should have triggered 1 sync and failed (no adapter)
        assert stats["syncs_triggered"] == 1
        assert stats["syncs_failed"] == 1

    @pytest.mark.asyncio
    @patch("mybudget.scheduler.sync_scheduler.AsyncSessionLocal")
    async def test_returns_empty_stats_when_no_due_connections(
        self, mock_session_local: MagicMock
    ) -> None:
        """Test returns zero stats when no connections are due."""
        mock_db = AsyncMock()
        mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session_local.return_value.__aexit__ = AsyncMock(return_value=None)

        # No connections due
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        scheduler = SyncScheduler()
        stats = await scheduler.run_scheduled_syncs()

        assert stats["syncs_triggered"] == 0
        assert stats["syncs_completed"] == 0
        assert stats["syncs_failed"] == 0


class TestHandleSyncFailure:
    """Tests for handle_sync_failure method."""

    @pytest.mark.asyncio
    async def test_schedules_retry_after_first_failure(self) -> None:
        """Test schedules retry with first delay after first failure."""
        mock_db = AsyncMock()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.next_sync_at = None

        mock_sync_job = MagicMock(spec=SyncJob)
        mock_sync_job.id = uuid4()
        mock_sync_job.connection_id = connection_id
        mock_sync_job.status = SyncJobStatus.FAILED
        mock_sync_job.error_message = "Test error"

        # Mock query - only 1 recent failure
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sync_job]
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        scheduler = SyncScheduler(max_retries=3)
        await scheduler.handle_sync_failure(mock_db, mock_sync_job, mock_connection)

        # Should schedule retry with first delay (5 minutes)
        assert mock_connection.next_sync_at is not None
        expected_delay = timedelta(seconds=RETRY_DELAYS[0])
        now = datetime.now(UTC)
        assert (
            now + expected_delay - timedelta(seconds=5)
            <= mock_connection.next_sync_at
            <= now + expected_delay + timedelta(seconds=5)
        )
        # Connection should still be active
        assert mock_connection.status == BankConnectionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_schedules_retry_with_increasing_delays(self) -> None:
        """Test retry delays increase with consecutive failures."""
        mock_db = AsyncMock()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.next_sync_at = None

        # Create 2 recent failures
        mock_sync_job1 = MagicMock(spec=SyncJob)
        mock_sync_job1.status = SyncJobStatus.FAILED
        mock_sync_job2 = MagicMock(spec=SyncJob)
        mock_sync_job2.status = SyncJobStatus.FAILED
        mock_sync_job2.id = uuid4()
        mock_sync_job2.connection_id = connection_id
        mock_sync_job2.error_message = "Test error"

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_sync_job2, mock_sync_job1]
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        scheduler = SyncScheduler(max_retries=3)
        await scheduler.handle_sync_failure(mock_db, mock_sync_job2, mock_connection)

        # Should use second delay (15 minutes) for 2nd failure
        expected_delay = timedelta(seconds=RETRY_DELAYS[1])
        now = datetime.now(UTC)
        assert (
            now + expected_delay - timedelta(seconds=5)
            <= mock_connection.next_sync_at
            <= now + expected_delay + timedelta(seconds=5)
        )

    @pytest.mark.asyncio
    async def test_marks_needs_attention_after_max_retries(self) -> None:
        """Test marks connection as NEEDS_ATTENTION after max retries."""
        mock_db = AsyncMock()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.next_sync_at = datetime.now(UTC)
        mock_connection.status_detail = None

        # Create 3 recent failures (max retries)
        mock_sync_job = MagicMock(spec=SyncJob)
        mock_sync_job.id = uuid4()
        mock_sync_job.connection_id = connection_id
        mock_sync_job.status = SyncJobStatus.FAILED
        mock_sync_job.error_message = "API Error"

        failures = [
            MagicMock(spec=SyncJob, status=SyncJobStatus.FAILED),
            MagicMock(spec=SyncJob, status=SyncJobStatus.FAILED),
            MagicMock(spec=SyncJob, status=SyncJobStatus.FAILED),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = failures
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        scheduler = SyncScheduler(max_retries=3)
        await scheduler.handle_sync_failure(mock_db, mock_sync_job, mock_connection)

        # Should mark as NEEDS_ATTENTION
        assert mock_connection.status == BankConnectionStatus.NEEDS_ATTENTION
        assert mock_connection.next_sync_at is None
        assert "failed 3 times" in mock_connection.status_detail

    @pytest.mark.asyncio
    async def test_resets_retry_count_after_success(self) -> None:
        """Test consecutive failure count resets after a success."""
        mock_db = AsyncMock()
        connection_id = uuid4()

        mock_connection = MagicMock(spec=BankConnection)
        mock_connection.id = connection_id
        mock_connection.status = BankConnectionStatus.ACTIVE
        mock_connection.next_sync_at = None

        mock_sync_job = MagicMock(spec=SyncJob)
        mock_sync_job.id = uuid4()
        mock_sync_job.connection_id = connection_id
        mock_sync_job.status = SyncJobStatus.FAILED
        mock_sync_job.error_message = "Test error"

        # Recent jobs: 1 failure, 1 success, 1 failure (only 1 consecutive)
        failures_with_success = [
            MagicMock(spec=SyncJob, status=SyncJobStatus.FAILED),
            MagicMock(spec=SyncJob, status=SyncJobStatus.COMPLETED),
            MagicMock(spec=SyncJob, status=SyncJobStatus.FAILED),
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = failures_with_success
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()

        scheduler = SyncScheduler(max_retries=3)
        await scheduler.handle_sync_failure(mock_db, mock_sync_job, mock_connection)

        # Should still be active (only 1 consecutive failure)
        assert mock_connection.status == BankConnectionStatus.ACTIVE
        # Should have scheduled next sync
        assert mock_connection.next_sync_at is not None


class TestRegisterJobs:
    """Tests for register_jobs method."""

    @patch("mybudget.scheduler.sync_scheduler.scheduler")
    def test_registers_sync_job(self, mock_scheduler: MagicMock) -> None:
        """Test registers run_scheduled_syncs job."""
        sync_scheduler_instance = SyncScheduler(check_interval_minutes=10)
        sync_scheduler_instance.register_jobs()

        mock_scheduler.add_job.assert_called_once()
        call_args = mock_scheduler.add_job.call_args
        assert call_args.kwargs["id"] == "run_scheduled_syncs"
        assert call_args.kwargs["replace_existing"] is True

    @patch("mybudget.scheduler.sync_scheduler.scheduler")
    def test_removes_existing_job_before_register(self, mock_scheduler: MagicMock) -> None:
        """Test removes existing job before registering new one."""
        sync_scheduler_instance = SyncScheduler()
        sync_scheduler_instance.register_jobs()

        mock_scheduler.remove_job.assert_called_with("run_scheduled_syncs")

    @patch("mybudget.scheduler.sync_scheduler.scheduler")
    def test_handles_missing_job_gracefully(self, mock_scheduler: MagicMock) -> None:
        """Test handles missing job when removing."""
        mock_scheduler.remove_job.side_effect = Exception("Job not found")

        sync_scheduler_instance = SyncScheduler()
        # Should not raise
        sync_scheduler_instance.register_jobs()

        mock_scheduler.add_job.assert_called_once()


class TestRetryDelays:
    """Tests for retry delay constants."""

    def test_retry_delays_exist(self) -> None:
        """Test RETRY_DELAYS constant is defined."""
        assert RETRY_DELAYS is not None
        assert len(RETRY_DELAYS) == 3

    def test_retry_delays_are_increasing(self) -> None:
        """Test retry delays increase with each retry."""
        assert RETRY_DELAYS[0] < RETRY_DELAYS[1] < RETRY_DELAYS[2]

    def test_retry_delays_values(self) -> None:
        """Test retry delays have expected values."""
        assert RETRY_DELAYS[0] == 5 * 60  # 5 minutes
        assert RETRY_DELAYS[1] == 15 * 60  # 15 minutes
        assert RETRY_DELAYS[2] == 60 * 60  # 1 hour


class TestSchedulerModule:
    """Tests for scheduler module initialization."""

    def test_scheduler_instance_exists(self) -> None:
        """Test global scheduler instance exists."""
        from mybudget.scheduler import scheduler

        assert scheduler is not None

    def test_scheduler_is_asyncio_scheduler(self) -> None:
        """Test scheduler is AsyncIOScheduler."""
        from apscheduler.schedulers.asyncio import AsyncIOScheduler

        from mybudget.scheduler import scheduler

        assert isinstance(scheduler, AsyncIOScheduler)

    def test_scheduler_has_coalesce_enabled(self) -> None:
        """Test scheduler has coalesce option enabled."""
        from mybudget.scheduler import scheduler

        # Check job defaults
        assert scheduler._job_defaults["coalesce"] is True

    def test_scheduler_has_max_instances_one(self) -> None:
        """Test scheduler limits job instances to 1."""
        from mybudget.scheduler import scheduler

        assert scheduler._job_defaults["max_instances"] == 1
