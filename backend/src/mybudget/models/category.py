"""
Category and CategoryGroup models.

Represents budget categories organized into groups.
"""
from datetime import datetime, timezone as dt_timezone
from uuid import UUID

from sqlalchemy import String, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mybudget.db.base import Base


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(dt_timezone.utc)


class CategoryGroup(Base):
    """
    Category group model.

    Organizational container for categories (e.g., "Monthly Bills", "Daily Living").

    Attributes:
        id: UUID primary key (inherited from Base)
        user_id: Reference to the owning user
        name: Group display name
        display_order: Order for UI display
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "category_groups"

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_category_groups_user_name"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        insert_default=0,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        insert_default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        insert_default=utc_now,
        onupdate=utc_now,
    )

    def __repr__(self) -> str:
        """Readable representation of CategoryGroup."""
        return f"CategoryGroup(id={self.id}, name={self.name!r}, order={self.display_order})"


class Category(Base):
    """
    Budget category model.

    Represents a budget category within a group (e.g., "Groceries" under "Daily Living").

    Attributes:
        id: UUID primary key (inherited from Base)
        user_id: Reference to the owning user
        group_id: Reference to the parent category group
        name: Category display name
        created_at: Creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "categories"

    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_categories_user_name"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    group_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("category_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        insert_default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        insert_default=utc_now,
        onupdate=utc_now,
    )

    def __repr__(self) -> str:
        """Readable representation of Category."""
        return f"Category(id={self.id}, name={self.name!r})"
