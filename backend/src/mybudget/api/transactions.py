"""
Transactions API endpoints.

Handles transaction CRUD operations, CSV import, and approval workflow.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.api.dependencies import CurrentUser
from mybudget.db.session import get_db
from mybudget.models.transaction import TransactionState
from mybudget.schemas.transaction import (
    TransactionApprove,
    TransactionBulkApprove,
    TransactionBulkResult,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from mybudget.services.transaction_service import TransactionService

router = APIRouter()


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    data: TransactionCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionResponse:
    """Create a new transaction."""
    service = TransactionService(db)
    transaction = await service.create_transaction(current_user.id, data)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account or category not found",
        )

    return TransactionResponse.model_validate(transaction)


@router.get("/", response_model=TransactionListResponse)
async def list_transactions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    account_id: UUID | None = None,
    state: TransactionState | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> TransactionListResponse:
    """List transactions with optional filters."""
    service = TransactionService(db)
    transactions, total = await service.list_transactions(
        current_user.id,
        account_id=account_id,
        state=state,
        limit=limit,
        offset=offset,
    )

    return TransactionListResponse(
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
    )


@router.get("/inbox", response_model=TransactionListResponse)
async def list_inbox_transactions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    account_id: UUID | None = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> TransactionListResponse:
    """List inbox (unapproved) transactions."""
    service = TransactionService(db)
    transactions, total = await service.list_transactions(
        current_user.id,
        account_id=account_id,
        state=TransactionState.INBOX,
        limit=limit,
        offset=offset,
    )

    return TransactionListResponse(
        transactions=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionResponse:
    """Get transaction by ID."""
    service = TransactionService(db)
    transaction = await service.get_transaction(current_user.id, transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return TransactionResponse.model_validate(transaction)


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionResponse:
    """Update a transaction."""
    service = TransactionService(db)
    try:
        transaction = await service.update_transaction(current_user.id, transaction_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction or category not found",
        )

    return TransactionResponse.model_validate(transaction)


@router.post("/{transaction_id}/approve", response_model=TransactionResponse)
async def approve_transaction(
    transaction_id: UUID,
    data: TransactionApprove,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionResponse:
    """Approve a transaction with a category."""
    service = TransactionService(db)
    transaction = await service.approve_transaction(current_user.id, transaction_id, data)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction or category not found",
        )

    return TransactionResponse.model_validate(transaction)


@router.post("/{transaction_id}/unapprove", response_model=TransactionResponse)
async def unapprove_transaction(
    transaction_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionResponse:
    """Unapprove a transaction (move back to inbox)."""
    service = TransactionService(db)
    transaction = await service.unapprove_transaction(current_user.id, transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return TransactionResponse.model_validate(transaction)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a transaction."""
    service = TransactionService(db)
    deleted = await service.delete_transaction(current_user.id, transaction_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )


@router.post("/batch-approve", response_model=TransactionBulkResult)
async def batch_approve_transactions(
    data: TransactionBulkApprove,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionBulkResult:
    """
    Batch approve multiple transactions with the same category (FR-045).

    Approves multiple transactions at once, all with the same category.
    Returns count of successes and failures.
    """
    service = TransactionService(db)
    result = await service.batch_approve_transactions(
        current_user.id,
        data.transaction_ids,
        data.category_id,
    )
    return result
