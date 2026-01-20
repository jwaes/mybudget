"""
Bank Connections API endpoints.

Handles bank connection OAuth flow, listing, and management.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.adapters import MockBankAdapter
from mybudget.adapters.base import BankProviderAdapter
from mybudget.api.dependencies import CurrentUser
from mybudget.db.session import get_db
from mybudget.schemas.bank_connection import (
    BankConnectionCreate,
    BankConnectionListResponse,
    BankConnectionWithAccountsResponse,
    InstitutionListResponse,
    InstitutionResponse,
    OAuthInitResponse,
    ReauthRequest,
)
from mybudget.services.bank_connection_service import BankConnectionService

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


@router.post("/initiate", response_model=OAuthInitResponse)
async def initiate_connection(
    data: BankConnectionCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
) -> OAuthInitResponse:
    """
    Initiate a new bank connection via OAuth.

    Returns an authorization URL where the user should be redirected
    to complete bank authentication.
    """
    service = BankConnectionService(db, adapter)
    try:
        result = await service.initiate_connection(
            user_id=current_user.id,
            institution_id=data.institution_id,
            redirect_url=data.redirect_url,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bank provider error: {e}",
        ) from None


@router.get("/callback", response_model=BankConnectionWithAccountsResponse)
async def oauth_callback(
    ref: Annotated[str, Query(description="Reference ID from OAuth flow")],
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
) -> BankConnectionWithAccountsResponse:
    """
    Complete OAuth flow after user returns from bank.

    This endpoint is called after the user completes bank authentication.
    It activates the connection and fetches linked accounts.
    """
    service = BankConnectionService(db, adapter)
    try:
        result = await service.complete_oauth(
            user_id=current_user.id,
            reference_id=ref,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None


@router.get("/", response_model=BankConnectionListResponse)
async def list_connections(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
) -> BankConnectionListResponse:
    """
    List all bank connections for the current user.
    """
    service = BankConnectionService(db, adapter)
    connections = await service.list_connections(current_user.id)
    return BankConnectionListResponse(
        connections=connections,
        total=len(connections),
    )


@router.get("/{connection_id}", response_model=BankConnectionWithAccountsResponse)
async def get_connection(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
) -> BankConnectionWithAccountsResponse:
    """
    Get a bank connection with its linked accounts.
    """
    service = BankConnectionService(db, adapter)
    connection = await service.get_connection(current_user.id, connection_id)

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    return connection


@router.post("/{connection_id}/reauth", response_model=OAuthInitResponse)
async def initiate_reauth(
    connection_id: UUID,
    data: ReauthRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
) -> OAuthInitResponse:
    """
    Initiate re-authentication for an expiring or expired connection.

    Returns an authorization URL where the user should be redirected
    to complete bank re-authentication.
    """
    service = BankConnectionService(db, adapter)
    try:
        result = await service.initiate_reauth(
            user_id=current_user.id,
            connection_id=connection_id,
            redirect_url=data.redirect_url,
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Bank provider error: {e}",
        ) from None


@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(
    connection_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
) -> None:
    """
    Disconnect a bank connection and revoke access.

    This will:
    - Revoke access with the bank provider
    - Mark the connection as DISCONNECTED
    - Deactivate all linked accounts
    """
    service = BankConnectionService(db, adapter)
    disconnected = await service.disconnect(current_user.id, connection_id)

    if not disconnected:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )


# Institutions endpoint - separate from connections
institutions_router = APIRouter()


@institutions_router.get("/", response_model=InstitutionListResponse)
async def list_institutions(
    _current_user: CurrentUser,  # Auth required but not used
    adapter: Annotated[BankProviderAdapter, Depends(get_bank_adapter)],
    country: Annotated[str | None, Query(description="ISO 3166-1 alpha-2 country code")] = None,
) -> InstitutionListResponse:
    """
    List available banking institutions.

    Optionally filter by country code (e.g., 'BE', 'NL', 'DE').
    """
    institutions = await adapter.get_institutions(country=country)

    response_institutions = [
        InstitutionResponse(
            id=inst.id,
            name=inst.name,
            bic=inst.bic,
            logo_url=inst.logo_url,
            countries=list(inst.countries),
        )
        for inst in institutions
    ]

    return InstitutionListResponse(
        institutions=response_institutions,
        total=len(response_institutions),
    )
