"""
Sync job Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from mybudget.models.bank_connection import SyncJobStatus, SyncTriggerType


class SyncJobCreate(BaseModel):
    """Schema for triggering a manual sync."""

    linked_account_id: UUID | None = Field(
        None, description="Specific account to sync (null = all accounts)"
    )


class SyncJobResponse(BaseModel):
    """Schema for sync job response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    connection_id: UUID
    linked_account_id: UUID | None = None
    status: SyncJobStatus
    trigger_type: SyncTriggerType
    started_at: datetime | None = None
    completed_at: datetime | None = None
    transactions_fetched: int
    transactions_imported: int
    transactions_duplicates: int
    error_message: str | None = None
    created_at: datetime


class SyncJobListResponse(BaseModel):
    """Schema for list of sync jobs response."""

    jobs: list[SyncJobResponse]
    total: int


class SyncStatusResponse(BaseModel):
    """Schema for overall sync status of a connection."""

    connection_id: UUID
    status: SyncJobStatus
    last_sync_at: datetime | None = None
    next_sync_at: datetime | None = None
    last_job: SyncJobResponse | None = None
    pending_jobs: int = Field(default=0, description="Number of pending/running jobs")
