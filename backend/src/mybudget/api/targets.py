"""
Targets API endpoints.

Handles category spending targets CRUD and underfunded calculation.
"""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.api.dependencies import CurrentUser
from mybudget.db.session import get_db
from mybudget.lib.date_utils import get_month_first_day
from mybudget.schemas.target import (
    CategoryTargetCreate,
    CategoryTargetUpdate,
    CategoryTargetResponse,
    UnderfundedResponse,
)
from mybudget.services.target_service import TargetService

router = APIRouter()


@router.post("/", response_model=CategoryTargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(
    data: CategoryTargetCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryTargetResponse:
    """Create a new category spending target."""
    service = TargetService(db)

    try:
        target = await service.create_target(current_user.id, data)
    except ValueError as e:
        if "already has a target" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category already has a target",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    # Get category name for response
    category_name = await service.get_category_name(current_user.id, target.category_id)

    response = CategoryTargetResponse.model_validate(target)
    response.category_name = category_name
    return response


@router.get("/", response_model=list[CategoryTargetResponse])
async def list_targets(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CategoryTargetResponse]:
    """List all targets for the current user."""
    service = TargetService(db)
    targets = await service.list_targets(current_user.id)

    result = []
    for target in targets:
        category_name = await service.get_category_name(current_user.id, target.category_id)
        response = CategoryTargetResponse.model_validate(target)
        response.category_name = category_name
        result.append(response)

    return result


@router.get("/{target_id}", response_model=CategoryTargetResponse)
async def get_target(
    target_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryTargetResponse:
    """Get a target by ID."""
    service = TargetService(db)
    target = await service.get_target(current_user.id, target_id)

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    category_name = await service.get_category_name(current_user.id, target.category_id)

    response = CategoryTargetResponse.model_validate(target)
    response.category_name = category_name
    return response


@router.put("/{target_id}", response_model=CategoryTargetResponse)
async def update_target(
    target_id: UUID,
    data: CategoryTargetUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryTargetResponse:
    """Update an existing target."""
    service = TargetService(db)

    try:
        target = await service.update_target(current_user.id, target_id, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    category_name = await service.get_category_name(current_user.id, target.category_id)

    response = CategoryTargetResponse.model_validate(target)
    response.category_name = category_name
    return response


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a target."""
    service = TargetService(db)
    deleted = await service.delete_target(current_user.id, target_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )


@router.get("/{target_id}/underfunded", response_model=UnderfundedResponse)
async def calculate_underfunded(
    target_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    month: date | None = Query(None, description="Month for calculation (YYYY-MM-DD)"),
) -> UnderfundedResponse:
    """
    Calculate underfunded amount for a target.

    Per FR-028 formulas:
    - Monthly Needed: max(0, target_amount - funded_this_month)
    - Target Balance: max(0, target_amount - available_now)
    - Target by Date: max(0, suggested_monthly - funded_this_month)
    """
    service = TargetService(db)

    # Default to current month if not specified
    calc_month = month if month else date.today()

    result = await service.calculate_underfunded(
        current_user.id, target_id, calc_month
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found",
        )

    return UnderfundedResponse(**result)
