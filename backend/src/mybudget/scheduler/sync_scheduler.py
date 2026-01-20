"""
Sync scheduler for automatic bank transaction synchronization.

This module provides scheduled sync functionality:
- Schedules next sync for connections after each sync completes
- Runs background job to check for due syncs every 5 minutes
- Handles sync failures with exponential backoff retry logic
"""

import contextlib
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mybudget.adapters import GoCardlessAdapter
from mybudget.adapters.base import BankProviderAdapter
from mybudget.config import settings
from mybudget.db.session import AsyncSessionLocal
from mybudget.models.bank_connection import (
    BankConnection,
    BankConnectionStatus,
    SyncJob,
    SyncJobStatus,
    SyncTriggerType,
)
from mybudget.scheduler import scheduler
from mybudget.services.transaction_sync_service import TransactionSyncService

if TYPE_CHECKING:
    pass

logger = structlog.get_logger(__name__)

# Retry delays in seconds: 5 minutes, 15 minutes, 1 hour
RETRY_DELAYS = [5 * 60, 15 * 60, 60 * 60]


class SyncScheduler:
    """
    Scheduler for automatic bank sync operations.

    Manages the scheduling of sync jobs and handles retry logic
    for failed syncs with exponential backoff.
    """

    def __init__(
        self,
        sync_interval_hours: int | None = None,
        check_interval_minutes: int | None = None,
        max_retries: int | None = None,
    ):
        """
        Initialize the sync scheduler.

        Args:
            sync_interval_hours: Hours between syncs (default from config)
            check_interval_minutes: Minutes between due sync checks (default from config)
            max_retries: Maximum retry attempts for failed syncs (default from config)
        """
        self.sync_interval_hours = sync_interval_hours or settings.BANK_SYNC_INTERVAL_HOURS
        self.check_interval_minutes = (
            check_interval_minutes or settings.BANK_SYNC_CHECK_INTERVAL_MINUTES
        )
        self.max_retries = max_retries or settings.BANK_SYNC_MAX_RETRIES

    def _get_adapter_for_provider(self, provider: str) -> BankProviderAdapter | None:
        """
        Get the appropriate adapter for a provider.

        Args:
            provider: Provider name (e.g., 'gocardless')

        Returns:
            BankProviderAdapter instance or None if not configured
        """
        if provider == "gocardless":
            try:
                return GoCardlessAdapter()
            except Exception as e:
                logger.warning(
                    "Failed to create GoCardless adapter",
                    error=str(e),
                )
                return None
        return None

    async def schedule_sync_job(
        self,
        db: AsyncSession,
        connection_id: UUID,
    ) -> datetime:
        """
        Schedule the next sync for a connection.

        Updates the connection's next_sync_at field based on the
        configured sync interval.

        Args:
            db: Database session
            connection_id: Connection to schedule sync for

        Returns:
            Scheduled datetime for next sync

        Raises:
            ValueError: If connection not found
        """
        stmt = select(BankConnection).where(BankConnection.id == connection_id)
        result = await db.execute(stmt)
        connection = result.scalar_one_or_none()

        if not connection:
            raise ValueError(f"Connection not found: {connection_id}")

        # Calculate next sync time
        base_time = connection.last_sync_at or datetime.now(UTC)
        next_sync_at = base_time + timedelta(hours=self.sync_interval_hours)

        # Ensure next sync is in the future
        now = datetime.now(UTC)
        if next_sync_at <= now:
            next_sync_at = now + timedelta(hours=self.sync_interval_hours)

        connection.next_sync_at = next_sync_at
        await db.commit()

        logger.info(
            "Scheduled next sync",
            connection_id=str(connection_id),
            next_sync_at=next_sync_at.isoformat(),
        )

        return next_sync_at

    async def run_scheduled_syncs(self) -> dict[str, int]:
        """
        Run all due sync jobs.

        Checks for connections where next_sync_at <= now and creates
        PENDING sync jobs, then executes them.

        This method is called periodically by the scheduler.

        Returns:
            Dict with counts of syncs_triggered, syncs_completed, syncs_failed
        """
        stats = {"syncs_triggered": 0, "syncs_completed": 0, "syncs_failed": 0}

        async with AsyncSessionLocal() as db:
            # Find connections due for sync
            now = datetime.now(UTC)
            stmt = (
                select(BankConnection)
                .options(selectinload(BankConnection.linked_accounts))
                .where(
                    BankConnection.status == BankConnectionStatus.ACTIVE,
                    BankConnection.next_sync_at.isnot(None),
                    BankConnection.next_sync_at <= now,
                )
            )
            result = await db.execute(stmt)
            due_connections = list(result.scalars().all())

            logger.info(
                "Checking for due syncs",
                due_connections_count=len(due_connections),
            )

            for connection in due_connections:
                try:
                    # Create sync job
                    sync_job = SyncJob(
                        connection_id=connection.id,
                        status=SyncJobStatus.PENDING,
                        trigger_type=SyncTriggerType.SCHEDULED,
                    )
                    db.add(sync_job)
                    await db.commit()
                    await db.refresh(sync_job)

                    stats["syncs_triggered"] += 1

                    # Get adapter for provider
                    adapter = self._get_adapter_for_provider(connection.provider)
                    if not adapter:
                        logger.warning(
                            "No adapter available for provider",
                            provider=connection.provider,
                            connection_id=str(connection.id),
                        )
                        sync_job.status = SyncJobStatus.FAILED
                        sync_job.error_message = f"No adapter for provider: {connection.provider}"
                        await db.commit()
                        stats["syncs_failed"] += 1
                        continue

                    # Execute sync
                    sync_service = TransactionSyncService(db, adapter)
                    result_job = await sync_service.run_sync_job(sync_job.id)

                    if result_job.status == SyncJobStatus.COMPLETED:
                        stats["syncs_completed"] += 1
                        # Schedule next sync
                        await self.schedule_sync_job(db, connection.id)
                    else:
                        stats["syncs_failed"] += 1
                        # Handle failure with retry logic
                        await self.handle_sync_failure(db, sync_job, connection)

                except Exception as e:
                    logger.exception(
                        "Error processing scheduled sync",
                        connection_id=str(connection.id),
                        error=str(e),
                    )
                    stats["syncs_failed"] += 1

        logger.info(
            "Scheduled sync run complete",
            **stats,
        )
        return stats

    async def handle_sync_failure(
        self,
        db: AsyncSession,
        sync_job: SyncJob,
        connection: BankConnection,
    ) -> None:
        """
        Handle a failed sync job with retry logic.

        Implements exponential backoff with delays:
        - Retry 1: 5 minutes
        - Retry 2: 15 minutes
        - Retry 3: 1 hour

        After max retries, marks connection as NEEDS_ATTENTION.

        Args:
            db: Database session
            sync_job: Failed sync job
            connection: Associated bank connection
        """
        # Count failed sync jobs for this connection
        stmt = (
            select(SyncJob)
            .where(
                SyncJob.connection_id == connection.id,
                SyncJob.status == SyncJobStatus.FAILED,
            )
            .order_by(SyncJob.created_at.desc())
            .limit(self.max_retries + 1)
        )
        result = await db.execute(stmt)
        recent_failures = list(result.scalars().all())

        # Count consecutive failures (stop counting if we find a success)
        consecutive_failures = 0
        for job in recent_failures:
            if job.status == SyncJobStatus.FAILED:
                consecutive_failures += 1
            else:
                break

        logger.info(
            "Handling sync failure",
            connection_id=str(connection.id),
            sync_job_id=str(sync_job.id),
            consecutive_failures=consecutive_failures,
            max_retries=self.max_retries,
        )

        if consecutive_failures >= self.max_retries:
            # Mark connection as needing attention
            connection.status = BankConnectionStatus.NEEDS_ATTENTION
            connection.status_detail = (
                f"Sync failed {consecutive_failures} times. Last error: {sync_job.error_message}"
            )
            connection.next_sync_at = None  # Stop scheduling until fixed
            await db.commit()

            logger.warning(
                "Connection marked as NEEDS_ATTENTION after max retries",
                connection_id=str(connection.id),
                consecutive_failures=consecutive_failures,
            )
        else:
            # Schedule retry with exponential backoff
            retry_index = min(consecutive_failures - 1, len(RETRY_DELAYS) - 1)
            retry_delay = RETRY_DELAYS[retry_index]

            next_sync_at = datetime.now(UTC) + timedelta(seconds=retry_delay)
            connection.next_sync_at = next_sync_at
            await db.commit()

            logger.info(
                "Scheduled retry sync",
                connection_id=str(connection.id),
                retry_number=consecutive_failures,
                retry_delay_seconds=retry_delay,
                next_sync_at=next_sync_at.isoformat(),
            )

    def register_jobs(self) -> None:
        """
        Register scheduled jobs with the APScheduler instance.

        Adds the run_scheduled_syncs job to run at the configured interval.
        """
        # Remove existing job if present (for restarts)
        with contextlib.suppress(Exception):
            scheduler.remove_job("run_scheduled_syncs")

        # Add the scheduled sync job
        scheduler.add_job(
            self.run_scheduled_syncs,
            trigger=IntervalTrigger(minutes=self.check_interval_minutes),
            id="run_scheduled_syncs",
            name="Run scheduled bank syncs",
            replace_existing=True,
        )

        logger.info(
            "Registered scheduled sync job",
            check_interval_minutes=self.check_interval_minutes,
            sync_interval_hours=self.sync_interval_hours,
        )


# Global scheduler instance
sync_scheduler = SyncScheduler()


def get_sync_scheduler() -> SyncScheduler:
    """Get the global sync scheduler instance."""
    return sync_scheduler


__all__ = ["SyncScheduler", "sync_scheduler", "get_sync_scheduler", "RETRY_DELAYS"]
