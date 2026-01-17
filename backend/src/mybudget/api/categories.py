"""
Categories API endpoints.

Handles category group and category CRUD operations, and fund assignments.
"""
import re
from datetime import date
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.api.dependencies import CurrentUser
from mybudget.db.session import get_db
from mybudget.schemas.category import (
    CategoryGroupCreate,
    CategoryGroupUpdate,
    CategoryGroupResponse,
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    CategoryGroupWithCategoriesResponse,
    AssignmentCreate,
    AssignmentResponse,
    CategoryBudgetResponse,
)
from mybudget.services.category_service import CategoryService
from mybudget.services.budget_service import BudgetService

router = APIRouter()


# Category Group endpoints

@router.post("/groups", response_model=CategoryGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_category_group(
    data: CategoryGroupCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryGroupResponse:
    """Create a new category group."""
    service = CategoryService(db)
    group = await service.create_category_group(current_user.id, data)
    return CategoryGroupResponse.model_validate(group)


@router.get("/groups", response_model=list[CategoryGroupResponse])
async def list_category_groups(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CategoryGroupResponse]:
    """List all category groups for the current user."""
    service = CategoryService(db)
    groups = await service.list_category_groups(current_user.id)
    return [CategoryGroupResponse.model_validate(g) for g in groups]


@router.get("/groups/{group_id}", response_model=CategoryGroupResponse)
async def get_category_group(
    group_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryGroupResponse:
    """Get category group by ID."""
    service = CategoryService(db)
    group = await service.get_category_group(current_user.id, group_id)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category group not found",
        )

    return CategoryGroupResponse.model_validate(group)


@router.put("/groups/{group_id}", response_model=CategoryGroupResponse)
async def update_category_group(
    group_id: UUID,
    data: CategoryGroupUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryGroupResponse:
    """Update a category group."""
    service = CategoryService(db)
    group = await service.update_category_group(current_user.id, group_id, data)

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category group not found",
        )

    return CategoryGroupResponse.model_validate(group)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category_group(
    group_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a category group (cascades to categories)."""
    service = CategoryService(db)
    deleted = await service.delete_category_group(current_user.id, group_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category group not found",
        )


# Category endpoints

@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    """Create a new category."""
    service = CategoryService(db)
    category = await service.create_category(current_user.id, data)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category group not found",
        )

    return CategoryResponse.model_validate(category)


@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    group_id: UUID | None = None,
) -> CategoryListResponse:
    """List all categories with their groups."""
    service = CategoryService(db)
    groups_with_cats = await service.list_groups_with_categories(current_user.id)

    response_groups = []
    total_categories = 0

    for group, categories in groups_with_cats:
        if group_id is not None and group.id != group_id:
            continue

        cat_responses = [CategoryResponse.model_validate(c) for c in categories]
        total_categories += len(cat_responses)

        response_groups.append(
            CategoryGroupWithCategoriesResponse(
                id=group.id,
                user_id=group.user_id,
                name=group.name,
                display_order=group.display_order,
                categories=cat_responses,
                created_at=group.created_at,
                updated_at=group.updated_at,
            )
        )

    return CategoryListResponse(
        groups=response_groups,
        total_groups=len(response_groups),
        total_categories=total_categories,
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    """Get category by ID."""
    service = CategoryService(db)
    category = await service.get_category(current_user.id, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return CategoryResponse.model_validate(category)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    data: CategoryUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    """Update a category."""
    service = CategoryService(db)
    category = await service.update_category(current_user.id, category_id, data)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return CategoryResponse.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a category."""
    service = CategoryService(db)
    deleted = await service.delete_category(current_user.id, category_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )


# Assignment and Budget endpoints


def parse_month_query(month_str: str) -> date:
    """Parse a YYYY-MM month query string to a date (first day of month)."""
    if not re.match(r"^\d{4}-\d{2}$", month_str):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid month format: {month_str}. Expected YYYY-MM.",
        )
    try:
        year, month = month_str.split("-")
        return date(int(year), int(month), 1)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid month: {month_str}. {str(e)}",
        )


@router.post("/{category_id}/assign", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
async def assign_funds_to_category(
    category_id: UUID,
    data: AssignmentCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AssignmentResponse:
    """
    Assign (or unassign) funds to a category for a specific month.

    Positive amounts assign funds, negative amounts unassign.
    """
    # Verify category exists and belongs to user
    cat_service = CategoryService(db)
    category = await cat_service.get_category(current_user.id, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    budget_service = BudgetService(db)
    assignment = await budget_service.assign_funds(
        user_id=current_user.id,
        category_id=category_id,
        amount=data.amount,
        month=data.month,
    )

    return AssignmentResponse.model_validate(assignment)


@router.get("/{category_id}/budget")
async def get_category_budget(
    category_id: UUID,
    month: str = Query(..., description="Month in YYYY-MM format"),
    current_user: CurrentUser = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get budget info for a category in a specific month.

    Returns funded_this_month, activity, and available amounts.
    """
    # Verify category exists and belongs to user
    cat_service = CategoryService(db)
    category = await cat_service.get_category(current_user.id, category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    month_date = parse_month_query(month)
    budget_service = BudgetService(db)
    budget_info = await budget_service.get_category_budget_info(category_id, month_date)

    return {
        "id": str(category.id),
        "name": category.name,
        "funded_this_month": str(budget_info["funded_this_month"]),
        "activity": str(budget_info["activity"]),
        "available": str(budget_info["available"]),
    }
