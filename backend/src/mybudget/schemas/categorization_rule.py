"""
CategorizationRule Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class CategorizationRuleCreate(BaseModel):
    """Schema for creating a new categorization rule."""

    payee_pattern: str = Field(..., min_length=1, max_length=255, description="Payee pattern to match")
    category_id: UUID = Field(..., description="Category to assign when pattern matches")


class CategorizationRuleUpdate(BaseModel):
    """Schema for updating a categorization rule."""

    payee_pattern: str | None = Field(None, min_length=1, max_length=255, description="Payee pattern to match")
    category_id: UUID | None = Field(None, description="Category to assign when pattern matches")


class CategorizationRuleResponse(BaseModel):
    """Schema for categorization rule response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    payee_pattern: str
    category_id: UUID
    created_at: datetime
    updated_at: datetime


class CategorizationRuleWithCategoryResponse(BaseModel):
    """Schema for categorization rule with category name."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    payee_pattern: str
    category_id: UUID
    category_name: str
    created_at: datetime
    updated_at: datetime


class CategorizationRuleListResponse(BaseModel):
    """Schema for list of categorization rules response."""

    rules: list[CategorizationRuleWithCategoryResponse]
    total: int


class CategorizationRuleMatch(BaseModel):
    """Schema for a matched rule result."""

    rule_id: UUID
    payee_pattern: str
    category_id: UUID
    category_name: str
