"""
Categorization Rules API endpoints.

Handles CRUD operations for auto-categorization rules.
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.api.dependencies import CurrentUser
from mybudget.db.session import get_db
from mybudget.schemas.categorization_rule import (
    CategorizationRuleCreate,
    CategorizationRuleListResponse,
    CategorizationRuleMatch,
    CategorizationRuleResponse,
    CategorizationRuleTestRequest,
    CategorizationRuleTestResponse,
    CategorizationRuleUpdate,
    CategorizationRuleWithCategoryResponse,
)
from mybudget.services.categorization_rule_service import CategorizationRuleService

router = APIRouter()


@router.post("/", response_model=CategorizationRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: CategorizationRuleCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategorizationRuleResponse:
    """
    Create a new categorization rule.

    Rules are used to automatically categorize transactions based on payee pattern matching.
    """
    service = CategorizationRuleService(db)
    rule = await service.create_rule(current_user.id, data)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found or does not belong to user",
        )

    return CategorizationRuleResponse.model_validate(rule)


@router.get("/", response_model=CategorizationRuleListResponse)
async def list_rules(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategorizationRuleListResponse:
    """
    List all categorization rules for the current user.

    Returns rules with their associated category names.
    """
    service = CategorizationRuleService(db)
    rules_with_categories = await service.list_rules_with_category(current_user.id)

    rules = [
        CategorizationRuleWithCategoryResponse(
            id=rule.id,
            user_id=rule.user_id,
            payee_pattern=rule.payee_pattern,
            category_id=rule.category_id,
            category_name=category_name,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
        )
        for rule, category_name in rules_with_categories
    ]

    return CategorizationRuleListResponse(
        rules=rules,
        total=len(rules),
    )


@router.get("/{rule_id}", response_model=CategorizationRuleWithCategoryResponse)
async def get_rule(
    rule_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategorizationRuleWithCategoryResponse:
    """Get a specific categorization rule by ID."""
    service = CategorizationRuleService(db)
    result = await service.get_rule_with_category(current_user.id, rule_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categorization rule not found",
        )

    rule, category_name = result
    return CategorizationRuleWithCategoryResponse(
        id=rule.id,
        user_id=rule.user_id,
        payee_pattern=rule.payee_pattern,
        category_id=rule.category_id,
        category_name=category_name,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


@router.put("/{rule_id}", response_model=CategorizationRuleResponse)
async def update_rule(
    rule_id: UUID,
    data: CategorizationRuleUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategorizationRuleResponse:
    """
    Update a categorization rule.

    Can update the payee_pattern and/or category_id.
    """
    service = CategorizationRuleService(db)
    rule = await service.update_rule(current_user.id, rule_id, data)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categorization rule not found or category invalid",
        )

    return CategorizationRuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a categorization rule."""
    service = CategorizationRuleService(db)
    deleted = await service.delete_rule(current_user.id, rule_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categorization rule not found",
        )


@router.post("/test", response_model=CategorizationRuleTestResponse)
async def test_rule(
    data: CategorizationRuleTestRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategorizationRuleTestResponse:
    """
    Test which rule would match a given payee string.

    Useful for debugging and previewing rule behavior.
    """
    service = CategorizationRuleService(db)
    result = await service.find_matching_rule_with_category(current_user.id, data.payee)

    if result:
        rule, category_name = result
        return CategorizationRuleTestResponse(
            payee=data.payee,
            matched=True,
            rule=CategorizationRuleMatch(
                rule_id=rule.id,
                payee_pattern=rule.payee_pattern,
                category_id=rule.category_id,
                category_name=category_name,
            ),
        )

    return CategorizationRuleTestResponse(
        payee=data.payee,
        matched=False,
        rule=None,
    )
