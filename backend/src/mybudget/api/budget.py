"""
Budget API endpoints.

Handles budget month view and funding operations.
"""
import re
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.api.dependencies import get_current_user, get_db
from mybudget.models.user import User
from mybudget.services.budget_service import BudgetService

router = APIRouter()


def parse_month(month_str: str) -> date:
    """
    Parse a YYYY-MM formatted month string to a date (first day of month).

    Args:
        month_str: Month string in YYYY-MM format

    Returns:
        Date representing the first day of the month

    Raises:
        HTTPException: If format is invalid
    """
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


@router.get("/{month}")
async def get_budget_month_view(
    month: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get budget month view for the current user.

    Returns all category groups with their categories, each with
    funded_this_month, activity, and available amounts.

    Args:
        month: Month in YYYY-MM format
        current_user: Authenticated user
        db: Database session

    Returns:
        Budget month view with groups, categories, and budget info
    """
    month_date = parse_month(month)
    budget_service = BudgetService(db)
    return await budget_service.get_month_view(current_user.id, month_date)


@router.get("/{month}/underfunded-summary")
async def get_underfunded_summary(
    month: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get underfunded summary for a month.

    Returns total underfunded amount and per-category breakdown.

    Args:
        month: Month in YYYY-MM format
        current_user: Authenticated user
        db: Database session

    Returns:
        Dict with total_underfunded and categories list
    """
    from mybudget.services.funding_service import FundingService

    month_date = parse_month(month)
    funding_service = FundingService(db)
    summary = await funding_service.get_underfunded_summary(
        current_user.id, month_date
    )

    # Convert Decimals to strings for JSON serialization
    return {
        "total_underfunded": str(summary["total_underfunded"]),
        "categories_underfunded": len(summary["categories"]),
        "categories": [
            {
                "category_id": str(cat["category_id"]),
                "category_name": cat["category_name"],
                "underfunded": str(cat["underfunded"]),
            }
            for cat in summary["categories"]
        ],
    }


@router.post("/{month}/fund-underfunded/{category_id}")
async def fund_underfunded_category(
    month: str,
    category_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Fund an underfunded category.

    Funds up to the underfunded amount, limited by available To Assign.

    Args:
        month: Month in YYYY-MM format
        category_id: Category UUID
        current_user: Authenticated user
        db: Database session

    Returns:
        Funding result with funded_amount, requested_amount, is_partial
    """
    from uuid import UUID
    from mybudget.services.funding_service import FundingService

    month_date = parse_month(month)

    try:
        cat_uuid = UUID(category_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category_id: {category_id}",
        )

    funding_service = FundingService(db)
    result = await funding_service.fund_single_category(
        current_user.id, cat_uuid, month_date
    )

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category not found: {category_id}",
        )

    await db.commit()

    return {
        "category_id": category_id,
        "amount_funded": str(result.funded_amount),
        "amount_requested": str(result.requested_amount),
        "is_partial": result.is_partial,
    }


@router.post("/{month}/fund-all-underfunded")
async def fund_all_underfunded(
    month: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Fund all underfunded categories in priority order.

    Funds categories in order of their group's display_order.
    Stops when To Assign is exhausted.

    Args:
        month: Month in YYYY-MM format
        current_user: Authenticated user
        db: Database session

    Returns:
        Funding result with total_funded, total_underfunded,
        categories_funded, is_partial
    """
    from mybudget.services.funding_service import FundingService

    month_date = parse_month(month)
    funding_service = FundingService(db)
    result = await funding_service.fund_all_underfunded(
        current_user.id, month_date
    )

    await db.commit()

    return {
        "total_funded": str(result.total_funded),
        "total_underfunded": str(result.total_underfunded),
        "categories_funded": result.categories_funded,
        "funded_categories": result.funded_categories,
        "is_partial": result.is_partial,
    }
