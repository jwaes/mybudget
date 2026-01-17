"""
Reconciliation API endpoints.

Handles account reconciliation workflow: start, mark cleared, adjust, complete.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.api.dependencies import CurrentUser
from mybudget.db.session import get_db
from mybudget.schemas.reconciliation import (
    ReconciliationCreate,
    ReconciliationMarkCleared,
    ReconciliationUnmarkCleared,
    ReconciliationCreateAdjustment,
    ReconciliationResponse,
    ReconciliationBalanceResponse,
    ReconciliationAdjustmentResponse,
)
from mybudget.schemas.transaction import TransactionResponse
from mybudget.services.reconciliation_service import ReconciliationService

router = APIRouter()


@router.post("/", response_model=ReconciliationResponse, status_code=status.HTTP_201_CREATED)
async def start_reconciliation(
    data: ReconciliationCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationResponse:
    """Start a new reconciliation session."""
    service = ReconciliationService(db)
    reconciliation = await service.start_reconciliation(current_user.id, data)

    if not reconciliation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    # Calculate balance info
    cleared_balance = await service.calculate_cleared_balance(reconciliation)
    discrepancy = reconciliation.statement_balance - cleared_balance

    return ReconciliationResponse(
        id=reconciliation.id,
        user_id=reconciliation.user_id,
        account_id=reconciliation.account_id,
        statement_balance=reconciliation.statement_balance,
        statement_date=reconciliation.statement_date,
        status=reconciliation.status,
        adjustment_transaction_id=reconciliation.adjustment_transaction_id,
        created_at=reconciliation.created_at,
        completed_at=reconciliation.completed_at,
        cleared_balance=cleared_balance,
        discrepancy=discrepancy,
    )


@router.get("/", response_model=list[ReconciliationResponse])
async def list_reconciliations(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    account_id: UUID | None = Query(None),
) -> list[ReconciliationResponse]:
    """List reconciliations with optional account filter."""
    service = ReconciliationService(db)
    reconciliations = await service.list_reconciliations(
        current_user.id,
        account_id=account_id,
    )

    result = []
    for recon in reconciliations:
        cleared_balance = await service.calculate_cleared_balance(recon)
        discrepancy = recon.statement_balance - cleared_balance
        result.append(ReconciliationResponse(
            id=recon.id,
            user_id=recon.user_id,
            account_id=recon.account_id,
            statement_balance=recon.statement_balance,
            statement_date=recon.statement_date,
            status=recon.status,
            adjustment_transaction_id=recon.adjustment_transaction_id,
            created_at=recon.created_at,
            completed_at=recon.completed_at,
            cleared_balance=cleared_balance,
            discrepancy=discrepancy,
        ))

    return result


@router.get("/{reconciliation_id}", response_model=ReconciliationResponse)
async def get_reconciliation(
    reconciliation_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationResponse:
    """Get reconciliation by ID."""
    service = ReconciliationService(db)
    reconciliation = await service.get_reconciliation(current_user.id, reconciliation_id)

    if not reconciliation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reconciliation not found",
        )

    cleared_balance = await service.calculate_cleared_balance(reconciliation)
    discrepancy = reconciliation.statement_balance - cleared_balance

    return ReconciliationResponse(
        id=reconciliation.id,
        user_id=reconciliation.user_id,
        account_id=reconciliation.account_id,
        statement_balance=reconciliation.statement_balance,
        statement_date=reconciliation.statement_date,
        status=reconciliation.status,
        adjustment_transaction_id=reconciliation.adjustment_transaction_id,
        created_at=reconciliation.created_at,
        completed_at=reconciliation.completed_at,
        cleared_balance=cleared_balance,
        discrepancy=discrepancy,
    )


@router.put("/{reconciliation_id}/mark-cleared", response_model=ReconciliationBalanceResponse)
async def mark_transactions_cleared(
    reconciliation_id: UUID,
    data: ReconciliationMarkCleared,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationBalanceResponse:
    """Mark transactions as cleared during reconciliation."""
    service = ReconciliationService(db)
    reconciliation = await service.mark_transactions_cleared(
        current_user.id, reconciliation_id, data
    )

    if not reconciliation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reconciliation or transaction not found",
        )

    cleared_balance = await service.calculate_cleared_balance(reconciliation)
    discrepancy = reconciliation.statement_balance - cleared_balance

    return ReconciliationBalanceResponse(
        cleared_balance=cleared_balance,
        discrepancy=discrepancy,
    )


@router.put("/{reconciliation_id}/unmark-cleared", response_model=ReconciliationBalanceResponse)
async def unmark_transactions_cleared(
    reconciliation_id: UUID,
    data: ReconciliationUnmarkCleared,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationBalanceResponse:
    """Unmark transactions as cleared."""
    service = ReconciliationService(db)
    reconciliation = await service.unmark_transactions_cleared(
        current_user.id, reconciliation_id, data
    )

    if not reconciliation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reconciliation or transaction not found",
        )

    cleared_balance = await service.calculate_cleared_balance(reconciliation)
    discrepancy = reconciliation.statement_balance - cleared_balance

    return ReconciliationBalanceResponse(
        cleared_balance=cleared_balance,
        discrepancy=discrepancy,
    )


@router.post("/{reconciliation_id}/create-adjustment", response_model=ReconciliationAdjustmentResponse, status_code=status.HTTP_201_CREATED)
async def create_adjustment(
    reconciliation_id: UUID,
    data: ReconciliationCreateAdjustment,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationAdjustmentResponse:
    """Create an adjustment transaction to balance the reconciliation."""
    service = ReconciliationService(db)
    reconciliation, adjustment = await service.create_adjustment(
        current_user.id, reconciliation_id, data
    )

    if not reconciliation or not adjustment:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reconciliation not found, category not found, or no discrepancy to adjust",
        )

    return ReconciliationAdjustmentResponse(
        adjustment_transaction=TransactionResponse.model_validate(adjustment).model_dump()
    )


@router.post("/{reconciliation_id}/complete", response_model=ReconciliationResponse)
async def complete_reconciliation(
    reconciliation_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReconciliationResponse:
    """Complete a reconciliation session."""
    service = ReconciliationService(db)
    reconciliation = await service.complete_reconciliation(
        current_user.id, reconciliation_id
    )

    if not reconciliation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reconciliation not found or has discrepancy",
        )

    cleared_balance = await service.calculate_cleared_balance(reconciliation)
    discrepancy = reconciliation.statement_balance - cleared_balance

    return ReconciliationResponse(
        id=reconciliation.id,
        user_id=reconciliation.user_id,
        account_id=reconciliation.account_id,
        statement_balance=reconciliation.statement_balance,
        statement_date=reconciliation.statement_date,
        status=reconciliation.status,
        adjustment_transaction_id=reconciliation.adjustment_transaction_id,
        created_at=reconciliation.created_at,
        completed_at=reconciliation.completed_at,
        cleared_balance=cleared_balance,
        discrepancy=discrepancy,
    )


@router.delete("/{reconciliation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_reconciliation(
    reconciliation_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Cancel an in-progress reconciliation."""
    service = ReconciliationService(db)
    canceled = await service.cancel_reconciliation(current_user.id, reconciliation_id)

    if not canceled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reconciliation not found or already completed",
        )
