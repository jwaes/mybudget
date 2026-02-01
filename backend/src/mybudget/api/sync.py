"""
Sync API endpoints for transaction synchronization.

Handles manual sync triggering and sync job management.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.adapters import MockBankAdapter
from mybudget.adapters.base import BankProviderAdapter
from mybudget.api.dependencies import CurrentUser
from mybudget.db.session import get_db
from mybudget.models.bank_connection import SyncJobStatus
from mybudget.schemas.sync_job import (
    SyncJobCreate,
    SyncJobListResponse,
    SyncJobResponse,
)
from mybudget.services.transaction_sync_service import TransactionSyncService

router = APIRouter()


def get_bank_adapter() -> BankProviderAdapter:
    """
    Get the bank provider adapter based on configuration.

    For now, uses MockBankAdapter in development. In production,
    this would return GoCardlessAdapter configured with credentials.
    """
    # TODO: Add configuration to switch adapters based on environment
    # For MVP testing, always use mock adapter
    return MockBankAdapter()


@router.post(
    "/connections/{connection_id}/sync",
    response_model=SyncJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_sync(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
    data: SyncJobCreate | None = None,
) -> SyncJobResponse:
    """
    Trigger a manual sync for a bank connection.

    Creates a sync job that will fetch new transactions from the bank.
    The sync is executed asynchronously.

    Args:
        connection_id: Bank connection ID to sync
        data: Optional sync configuration (specific linked account)

    Returns:
        SyncJobResponse with the created job details

    Raises:
        400: If connection is not active
        404: If connection not found
    """
    service = TransactionSyncService(db, adapter)

    try:
        linked_account_id = data.linked_account_id if data else None
        sync_job = await service.trigger_manual_sync(
            user_id=current_user.id,
            connection_id=connection_id,
            linked_account_id=linked_account_id,
        )

        # Execute the sync immediately for manual triggers
        sync_job = await service.run_sync_job(sync_job.id)

        return SyncJobResponse.model_validate(sync_job)

    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg,
            ) from None
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        ) from None


@router.get("/sync-jobs", response_model=SyncJobListResponse)
async def list_sync_jobs(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
    connection_id: Annotated[
        UUID, Query(description="Filter by connection ID")
    ],
    job_status: Annotated[
        SyncJobStatus | None,
        Query(alias="status", description="Filter by job status"),
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SyncJobListResponse:
    """
    List sync jobs for a connection.

    Returns paginated sync job history with optional status filtering.

    Args:
        connection_id: Bank connection ID (required)
        status: Optional status filter (PENDING, RUNNING, COMPLETED, FAILED)
        limit: Maximum number of jobs to return (1-100, default 50)
        offset: Number of jobs to skip for pagination

    Returns:
        SyncJobListResponse with jobs and total count

    Raises:
        404: If connection not found
    """
    service = TransactionSyncService(db, adapter)

    try:
        jobs = await service.get_sync_jobs(
            user_id=current_user.id,
            connection_id=connection_id,
            status=job_status,
            limit=limit,
            offset=offset,
        )

        return SyncJobListResponse(
            jobs=[SyncJobResponse.model_validate(job) for job in jobs],
            total=len(jobs),  # For proper pagination, this should query count separately
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None


@router.get("/sync-jobs/{sync_job_id}", response_model=SyncJobResponse)
async def get_sync_job(
    sync_job_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
) -> SyncJobResponse:
    """
    Get details of a specific sync job.

    Args:
        sync_job_id: Sync job ID

    Returns:
        SyncJobResponse with job details

    Raises:
        404: If sync job not found or belongs to another user
    """
    service = TransactionSyncService(db, adapter)

    sync_job = await service.get_sync_job(
        user_id=current_user.id,
        sync_job_id=sync_job_id,
    )

    if not sync_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sync job not found",
        )

    return SyncJobResponse.model_validate(sync_job)
