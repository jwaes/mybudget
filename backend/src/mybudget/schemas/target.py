"""
Target Pydantic schemas for API request/response validation.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from mybudget.models.target import TargetType


class CategoryTargetCreate(BaseModel):
    """Schema for creating a new category target."""

    category_id: UUID = Field(..., description="UUID of the category")
    target_type: TargetType = Field(..., description="Type of target")
    amount: Decimal = Field(..., gt=0, description="Target amount (must be > 0)")
    target_date: date | None = Field(None, description="Required for TARGET_BY_DATE")

    @model_validator(mode="after")
    def validate_target_date(self) -> "CategoryTargetCreate":
        """Validate target_date is required for TARGET_BY_DATE."""
        if self.target_type == TargetType.TARGET_BY_DATE and self.target_date is None:
            raise ValueError("target_date is required for TARGET_BY_DATE")
        if self.target_type != TargetType.TARGET_BY_DATE and self.target_date is not None:
            raise ValueError("target_date should only be set for TARGET_BY_DATE")
        return self


class CategoryTargetUpdate(BaseModel):
    """Schema for updating a category target."""

    target_type: TargetType | None = Field(None, description="Type of target")
    amount: Decimal | None = Field(None, gt=0, description="Target amount (must be > 0)")
    target_date: date | None = Field(None, description="Required for TARGET_BY_DATE")


class CategoryTargetResponse(BaseModel):
    """Schema for category target response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    category_name: str | None = None  # Populated from join
    target_type: TargetType
    amount: Decimal
    target_date: date | None
    created_at: datetime
    updated_at: datetime

    @field_validator("amount", mode="before")
    @classmethod
    def format_amount(cls, v: Decimal) -> str:
        """Format amount as string with 2 decimal places."""
        if isinstance(v, Decimal):
            return str(v.quantize(Decimal("0.01")))
        return v


class UnderfundedResponse(BaseModel):
    """Schema for underfunded calculation response."""

    target_id: UUID
    category_id: UUID
    month: date
    target_type: TargetType
    target_amount: str
    funded_this_month: str
    available_now: str
    suggested_monthly: str | None = None  # Only for TARGET_BY_DATE
    months_left: int | None = None  # Only for TARGET_BY_DATE
    underfunded: str
    status: str  # UNDERFUNDED, FUNDED, OVERFUNDED
