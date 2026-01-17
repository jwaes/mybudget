"""
FastAPI dependencies for authentication and authorization.

Provides dependency injection for protected routes.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.db.session import get_db
from mybudget.models.user import User


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Get current authenticated user from session.

    This is a placeholder implementation. In T028/T029, this will be
    enhanced with proper session management.

    Args:
        db: Database session

    Returns:
        Current authenticated user

    Raises:
        401: Not authenticated

    Usage:
        @app.get("/protected")
        async def protected_route(
            current_user: Annotated[User, Depends(get_current_user)]
        ):
            return {"user_id": current_user.id}
    """
    # TODO: Implement proper session management
    # For now, raise not authenticated
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
