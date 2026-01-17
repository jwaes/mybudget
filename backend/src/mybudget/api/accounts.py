"""
Accounts API endpoints.

Handles account CRUD operations.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.api.dependencies import CurrentUser
from mybudget.db.session import get_db
from mybudget.schemas.account import (
    AccountCreate,
    AccountListResponse,
    AccountResponse,
    AccountUpdate,
)
from mybudget.services.account_service import AccountService

router = APIRouter()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    data: AccountCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountResponse:
    """Create a new bank account."""
    service = AccountService(db)
    account = await service.create_account(current_user.id, data)
    return AccountResponse.model_validate(account)


@router.get("/", response_model=AccountListResponse)
async def list_accounts(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountListResponse:
    """List all accounts for the current user."""
    service = AccountService(db)
    accounts = await service.list_accounts(current_user.id)
    return AccountListResponse(
        accounts=[AccountResponse.model_validate(a) for a in accounts],
        total=len(accounts),
    )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountResponse:
    """Get account by ID."""
    service = AccountService(db)
    account = await service.get_account(current_user.id, account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return AccountResponse.model_validate(account)


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: UUID,
    data: AccountUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AccountResponse:
    """Update an account."""
    service = AccountService(db)
    account = await service.update_account(current_user.id, account_id, data)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return AccountResponse.model_validate(account)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete an account."""
    service = AccountService(db)
    deleted = await service.delete_account(current_user.id, account_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
