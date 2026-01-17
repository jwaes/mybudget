"""
FastAPI dependencies for authentication and authorization.

Provides dependency injection for protected routes.
"""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.db.session import get_db
from mybudget.lib.session import SESSION_COOKIE_NAME, validate_session_token
from mybudget.models.user import User


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> User:
    """
    Get current authenticated user from session cookie.

    Args:
        db: Database session
        session: Session cookie value

    Returns:
        Current authenticated user

    Raises:
        401: Not authenticated (missing or invalid session)

    Usage:
        @app.get("/protected")
        async def protected_route(
            current_user: Annotated[User, Depends(get_current_user)]
        ):
            return {"user_id": current_user.id}
    """
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # Validate session token and extract user ID
    user_id = validate_session_token(session)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    # Fetch user from database
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


async def get_optional_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    session: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> User | None:
    """
    Get current user if authenticated, None otherwise.

    Useful for routes that can work with or without authentication.

    Args:
        db: Database session
        session: Session cookie value

    Returns:
        Current user if authenticated, None otherwise
    """
    if not session:
        return None

    user_id = validate_session_token(session)
    if not user_id:
        return None

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


# Type aliases for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]
