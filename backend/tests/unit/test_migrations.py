"""
Test database migrations to ensure they create the correct schema.
"""
import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.unit
@pytest.mark.asyncio
async def test_users_table_created(db_session: AsyncSession) -> None:
    """Test that the users table was created with correct schema."""
    # Get table information
    result = await db_session.execute(
        text(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
            """
        )
    )
    columns = {row[0]: (row[1], row[2]) for row in result.fetchall()}

    # Verify required columns exist with correct types
    assert "id" in columns
    assert columns["id"][0] == "uuid"
    assert columns["id"][1] == "NO"  # NOT NULL

    assert "email" in columns
    assert "character varying" in columns["email"][0]
    assert columns["email"][1] == "NO"

    assert "password_hash" in columns
    assert "character varying" in columns["password_hash"][0]
    assert columns["password_hash"][1] == "NO"

    assert "timezone" in columns
    assert "character varying" in columns["timezone"][0]
    assert columns["timezone"][1] == "NO"

    assert "created_at" in columns
    assert "timestamp with time zone" in columns["created_at"][0]
    assert columns["created_at"][1] == "NO"

    assert "updated_at" in columns
    assert "timestamp with time zone" in columns["updated_at"][0]
    assert columns["updated_at"][1] == "NO"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_users_table_indexes(db_session: AsyncSession) -> None:
    """Test that the users table has correct indexes."""
    result = await db_session.execute(
        text(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'users'
            ORDER BY indexname
            """
        )
    )
    indexes = {row[0]: row[1] for row in result.fetchall()}

    # Primary key index
    assert "pk_users" in indexes

    # Email index for fast lookups
    assert "ix_users_email" in indexes or "ix_email" in indexes


@pytest.mark.unit
@pytest.mark.asyncio
async def test_users_table_constraints(db_session: AsyncSession) -> None:
    """Test that the users table has correct constraints."""
    result = await db_session.execute(
        text(
            """
            SELECT conname, contype
            FROM pg_constraint
            WHERE conrelid = 'users'::regclass
            ORDER BY conname
            """
        )
    )
    constraints = {row[0]: row[1] for row in result.fetchall()}

    # Primary key constraint
    assert any("pk" in name for name in constraints.keys())

    # Unique constraint on email
    assert any("email" in name.lower() for name in constraints.keys())
