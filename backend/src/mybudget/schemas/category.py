"""
Category and CategoryGroup Pydantic schemas for API request/response validation.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class CategoryGroupCreate(BaseModel):
    """Schema for creating a new category group."""

    name: str = Field(..., min_length=1, max_length=100, description="Category group name")
    display_order: int = Field(default=0, ge=0, description="Display order for UI")


class CategoryGroupUpdate(BaseModel):
    """Schema for updating a category group."""

    name: str | None = Field(None, min_length=1, max_length=100, description="Category group name")
    display_order: int | None = Field(None, ge=0, description="Display order for UI")


class CategoryGroupResponse(BaseModel):
    """Schema for category group response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    display_order: int
    created_at: datetime
    updated_at: datetime


class CategoryCreate(BaseModel):
    """Schema for creating a new category."""

    group_id: UUID = Field(..., description="Parent category group ID")
    name: str = Field(..., min_length=1, max_length=100, description="Category name")


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    group_id: UUID | None = Field(None, description="Parent category group ID")
    name: str | None = Field(None, min_length=1, max_length=100, description="Category name")


class CategoryResponse(BaseModel):
    """Schema for category response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    group_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class CategoryWithGroupResponse(BaseModel):
    """Schema for category response with group info."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    group_id: UUID
    group_name: str
    name: str
    created_at: datetime
    updated_at: datetime


class CategoryGroupWithCategoriesResponse(BaseModel):
    """Schema for category group with its categories."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    display_order: int
    categories: list[CategoryResponse]
    created_at: datetime
    updated_at: datetime


class CategoryListResponse(BaseModel):
    """Schema for list of categories response."""

    groups: list[CategoryGroupWithCategoriesResponse]
    total_groups: int
    total_categories: int


class AssignmentCreate(BaseModel):
    """Schema for creating a fund assignment."""

    amount: Decimal = Field(..., description="Amount to assign (positive) or unassign (negative)")
    month: date = Field(..., description="Month to assign to (first day of month)")

    @field_validator("amount")
    @classmethod
    def amount_not_zero(cls, v: Decimal) -> Decimal:
        """Validate that amount is not zero."""
        if v == 0:
            raise ValueError("Amount cannot be zero")
        return v

    @field_validator("month")
    @classmethod
    def month_is_first_day(cls, v: date) -> date:
        """Validate that month is first day of month."""
        if v.day != 1:
            # Automatically adjust to first day
            return date(v.year, v.month, 1)
        return v


class AssignmentResponse(BaseModel):
    """Schema for assignment response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    category_id: UUID
    amount: Decimal
    month: date
    created_at: datetime


class CategoryBudgetResponse(BaseModel):
    """Schema for category budget info response."""

    id: UUID
    name: str
    funded_this_month: Decimal
    activity: Decimal
    available: Decimal
