"""
User model.

Represents a user account with authentication credentials.
"""
from datetime import UTC, datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from mybudget.db.base import Base


def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(UTC)


class User(Base):
    """
    User account model.

    Attributes:
        id: UUID primary key (inherited from Base)
        email: Unique email address
        password_hash: Argon2id hashed password
        timezone: User's timezone (e.g., 'Europe/Brussels')
        created_at: Account creation timestamp
        updated_at: Last modification timestamp
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, insert_default="UTC")
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
        """Readable representation without exposing password hash."""
        return f"User(id={self.id}, email={self.email!r}, timezone={self.timezone!r})"
