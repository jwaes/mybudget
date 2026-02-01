"""
Transaction sync service for synchronizing transactions from bank providers.

This service handles:
- Fetching transactions from bank provider APIs
- Deduplicating transactions (by external_id or fuzzy match)
- Creating INBOX transactions from provider data
- Managing sync job lifecycle and tracking
"""
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mybudget.adapters.base import BankProviderAdapter
from mybudget.adapters.types import ProviderTransaction
from mybudget.config import settings
from mybudget.models.bank_connection import (
    BankConnection,
    BankConnectionStatus,
    LinkedAccount,
    SyncJob,
    SyncJobStatus,
    SyncTriggerType,
)
from mybudget.models.transaction import Transaction, TransactionState


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # j+1 instead of j since previous_row and current_row are one character longer
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class TransactionSyncService:
    """Service for synchronizing transactions from bank providers."""

    def __init__(self, db: AsyncSession, adapter: BankProviderAdapter):
        """
        Initialize with database session and bank provider adapter.

        Args:
            db: Async database session
            adapter: Bank provider adapter (GoCardless, Mock, etc.)
        """
        self.db = db
        self.adapter = adapter

    async def trigger_manual_sync(
        self,
        user_id: UUID,
        connection_id: UUID,
        linked_account_id: UUID | None = None,
    ) -> SyncJob:
        """
        Trigger a manual sync for a bank connection.

        Creates a sync job and schedules it for execution.

        Args:
            user_id: User ID (for access control)
            connection_id: Bank connection ID
            linked_account_id: Optional specific account to sync (None = all accounts)

        Returns:
            Created SyncJob

        Raises:
            ValueError: If connection not found or not active
        """
        # Verify connection exists and belongs to user
        stmt = (
            select(BankConnection)
            .options(selectinload(BankConnection.linked_accounts))
            .where(
                BankConnection.id == connection_id,
                BankConnection.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        connection = result.scalar_one_or_none()

        if not connection:
            raise ValueError("Connection not found")

        if connection.status != BankConnectionStatus.ACTIVE:
            raise ValueError("Connection is not active")

        # Create sync job
        sync_job = SyncJob(
            connection_id=connection_id,
            linked_account_id=linked_account_id,
            status=SyncJobStatus.PENDING,
            trigger_type=SyncTriggerType.MANUAL,
        )
        self.db.add(sync_job)
        await self.db.commit()
        await self.db.refresh(sync_job)

        return sync_job

    async def sync_account(
        self,
        linked_account_id: UUID,
        sync_job: SyncJob,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> SyncJob:
        """
        Sync transactions for a specific linked account.

        Fetches transactions from the provider, deduplicates, and creates
        new INBOX transactions.

        Args:
            linked_account_id: Linked account to sync
            sync_job: SyncJob to track progress
            date_from: Start date for transactions (default: 90 days ago)
            date_to: End date for transactions (default: today)

        Returns:
            Updated SyncJob with results

        Raises:
            ValueError: If linked account not found or not properly configured
        """
        # Get linked account with connection
        stmt = (
            select(LinkedAccount)
            .options(selectinload(LinkedAccount.connection))
            .where(LinkedAccount.id == linked_account_id)
        )
        result = await self.db.execute(stmt)
        linked_account = result.scalar_one_or_none()

        if not linked_account:
            raise ValueError("Linked account not found")

        if not linked_account.account_id:
            raise ValueError("No internal account linked to this bank account")

        # Update sync job status to running
        sync_job.status = SyncJobStatus.RUNNING
        sync_job.started_at = datetime.now(UTC)
        await self.db.commit()

        try:
            # Set default date range
            if not date_from:
                date_from = date.today() - timedelta(days=90)
            if not date_to:
                date_to = date.today()

            # Fetch transactions from provider
            provider_transactions = await self.adapter.get_transactions(
                linked_account.provider_account_id,
                date_from=date_from,
                date_to=date_to,
            )

            sync_job.transactions_fetched = len(provider_transactions)

            # Get existing transactions for deduplication
            existing_transactions = await self._get_existing_transactions(
                linked_account.connection.user_id,
                linked_account.account_id,
                date_from,
                date_to,
            )

            # Process transactions
            import_batch_id = uuid4()
            imported_count = 0
            duplicate_count = 0

            for provider_tx in provider_transactions:
                if self._is_duplicate(provider_tx, existing_transactions):
                    duplicate_count += 1
                    continue

                # Create transaction
                transaction = self._create_transaction(
                    provider_tx,
                    linked_account.connection.user_id,
                    linked_account.account_id,
                    self.adapter.provider_name,
                    import_batch_id,
                )
                self.db.add(transaction)
                imported_count += 1

            # Update sync job
            sync_job.transactions_imported = imported_count
            sync_job.transactions_duplicates = duplicate_count
            sync_job.status = SyncJobStatus.COMPLETED
            sync_job.completed_at = datetime.now(UTC)

            # Update connection last_sync_at and schedule next sync
            linked_account.connection.last_sync_at = datetime.now(UTC)
            linked_account.connection.next_sync_at = datetime.now(UTC) + timedelta(
                hours=settings.BANK_SYNC_INTERVAL_HOURS
            )

            await self.db.commit()

        except Exception as e:
            # Handle errors
            sync_job.status = SyncJobStatus.FAILED
            sync_job.error_message = str(e)
            sync_job.completed_at = datetime.now(UTC)
            await self.db.commit()

        return sync_job

    async def _get_existing_transactions(
        self,
        user_id: UUID,
        account_id: UUID,
        date_from: date,
        date_to: date,
    ) -> list[Transaction]:
        """Get existing transactions for deduplication check."""
        # Expand date range slightly for fuzzy matching
        expanded_from = date_from - timedelta(days=2)
        expanded_to = date_to + timedelta(days=2)

        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.account_id == account_id,
            Transaction.date >= expanded_from,
            Transaction.date <= expanded_to,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    def _is_duplicate(
        self,
        provider_tx: ProviderTransaction,
        existing_transactions: list[Transaction],
    ) -> bool:
        """
        Check if a provider transaction is a duplicate.

        Uses two methods:
        1. External ID match (provider transaction ID)
        2. Fuzzy match: same date (+/- 1 day), same amount, similar payee

        Args:
            provider_tx: Transaction from provider
            existing_transactions: List of existing transactions

        Returns:
            True if duplicate found, False otherwise
        """
        for existing in existing_transactions:
            # Check external_id match first (most reliable)
            if existing.external_id and existing.external_id == provider_tx.id:
                return True

            # Fuzzy match: date, amount, payee
            date_match = abs((existing.date - provider_tx.date).days) <= 1
            amount_match = existing.amount == provider_tx.amount
            payee_match = self._payees_similar(
                existing.payee, provider_tx.payee
            )

            if date_match and amount_match and payee_match:
                return True

        return False

    def _payees_similar(self, payee1: str, payee2: str) -> bool:
        """
        Check if two payee names are similar using Levenshtein distance.

        Args:
            payee1: First payee name
            payee2: Second payee name

        Returns:
            True if payees are similar, False otherwise
        """
        # Normalize payees
        p1 = payee1.lower().strip()
        p2 = payee2.lower().strip()

        # Exact match
        if p1 == p2:
            return True

        # Calculate Levenshtein distance
        max_len = max(len(p1), len(p2))
        if max_len == 0:
            return True

        distance = _levenshtein_distance(p1, p2)
        # Allow up to 20% difference
        similarity_threshold = max_len * 0.2

        return distance <= similarity_threshold

    def _create_transaction(
        self,
        provider_tx: ProviderTransaction,
        user_id: UUID,
        account_id: UUID,
        import_source: str,
        import_batch_id: UUID,
    ) -> Transaction:
        """
        Create a Transaction from a provider transaction.

        Args:
            provider_tx: Transaction from provider
            user_id: User ID
            account_id: Internal account ID
            import_source: Source identifier (e.g., 'gocardless')
            import_batch_id: Batch ID for this sync

        Returns:
            New Transaction object (not yet persisted)
        """
        # Use payee property from ProviderTransaction which handles
        # creditor/debtor based on amount sign
        payee = provider_tx.payee

        return Transaction(
            user_id=user_id,
            account_id=account_id,
            date=provider_tx.date,
            payee=payee,
            amount=provider_tx.amount,
            memo=provider_tx.description if provider_tx.description != payee else None,
            state=TransactionState.INBOX,
            external_id=provider_tx.id,
            import_source=import_source,
            import_batch_id=import_batch_id,
        )

    async def get_sync_jobs(
        self,
        user_id: UUID,
        connection_id: UUID,
        status: SyncJobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SyncJob]:
        """
        Get sync jobs for a connection.

        Args:
            user_id: User ID (for access control)
            connection_id: Bank connection ID
            status: Optional status filter
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip

        Returns:
            List of SyncJob objects

        Raises:
            ValueError: If connection not found or not owned by user
        """
        # Verify connection ownership
        conn_stmt = select(BankConnection).where(
            BankConnection.id == connection_id,
            BankConnection.user_id == user_id,
        )
        conn_result = await self.db.execute(conn_stmt)
        connection = conn_result.scalar_one_or_none()

        if not connection:
            raise ValueError("Connection not found")

        # Build query for sync jobs
        stmt = (
            select(SyncJob)
            .where(SyncJob.connection_id == connection_id)
            .order_by(SyncJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        if status:
            stmt = stmt.where(SyncJob.status == status)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_sync_job(
        self,
        user_id: UUID,
        sync_job_id: UUID,
    ) -> SyncJob | None:
        """
        Get a specific sync job.

        Args:
            user_id: User ID (for access control)
            sync_job_id: Sync job ID

        Returns:
            SyncJob if found and owned by user, None otherwise
        """
        stmt = (
            select(SyncJob)
            .options(selectinload(SyncJob.connection))
            .where(SyncJob.id == sync_job_id)
        )
        result = await self.db.execute(stmt)
        sync_job = result.scalar_one_or_none()

        if not sync_job:
            return None

        # Verify ownership via connection
        if sync_job.connection.user_id != user_id:
            return None

        return sync_job

    async def run_sync_job(self, sync_job_id: UUID) -> SyncJob:
        """
        Execute a pending sync job.

        This method is typically called by a background worker.

        Args:
            sync_job_id: ID of the sync job to run

        Returns:
            Completed SyncJob

        Raises:
            ValueError: If sync job not found or not pending
        """
        stmt = (
            select(SyncJob)
            .options(
                selectinload(SyncJob.connection).selectinload(
                    BankConnection.linked_accounts
                )
            )
            .where(SyncJob.id == sync_job_id)
        )
        result = await self.db.execute(stmt)
        sync_job = result.scalar_one_or_none()

        if not sync_job:
            raise ValueError("Sync job not found")

        if sync_job.status != SyncJobStatus.PENDING:
            raise ValueError(f"Sync job is not pending (status: {sync_job.status})")

        # If specific account, sync just that one
        if sync_job.linked_account_id:
            return await self.sync_account(sync_job.linked_account_id, sync_job)

        # Otherwise sync all active linked accounts
        connection = sync_job.connection
        total_fetched = 0
        total_imported = 0
        total_duplicates = 0
        errors: list[str] = []

        sync_job.status = SyncJobStatus.RUNNING
        sync_job.started_at = datetime.now(UTC)
        await self.db.commit()

        for linked_account in connection.linked_accounts:
            if not linked_account.is_active or not linked_account.account_id:
                continue

            try:
                # Create a sub-job tracking object (or reuse main job for simple case)
                result_job = await self.sync_account(linked_account.id, sync_job)
                total_fetched += result_job.transactions_fetched
                total_imported += result_job.transactions_imported
                total_duplicates += result_job.transactions_duplicates

                if result_job.error_message:
                    errors.append(f"{linked_account.account_name}: {result_job.error_message}")
            except Exception as e:
                errors.append(f"{linked_account.account_name}: {str(e)}")

        # Update final totals
        sync_job.transactions_fetched = total_fetched
        sync_job.transactions_imported = total_imported
        sync_job.transactions_duplicates = total_duplicates
        sync_job.completed_at = datetime.now(UTC)

        if errors:
            sync_job.status = SyncJobStatus.FAILED
            sync_job.error_message = "; ".join(errors)
        else:
            sync_job.status = SyncJobStatus.COMPLETED
            # Schedule next automatic sync
            connection.next_sync_at = datetime.now(UTC) + timedelta(
                hours=settings.BANK_SYNC_INTERVAL_HOURS
            )

        await self.db.commit()
        return sync_job
