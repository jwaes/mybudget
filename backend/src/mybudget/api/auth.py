"""
Authentication API endpoints.

Handles user login, logout, and current user retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.db.session import DBSession
from mybudget.lib.auth import hash_password, verify_password
from mybudget.models.user import User
from mybudget.schemas.user import UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: DBSession) -> User:
    """
    Register a new user.

    Args:
        user_data: User registration data
        db: Database session

    Returns:
        Created user (without password hash)

    Raises:
        409: Email already registered
    """
    # Check if email already exists
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        timezone=user_data.timezone,
    )

    db.add(new_user)
    await db.flush()

    return new_user


@router.post("/login")
async def login(
    credentials: UserLogin, response: Response, db: DBSession
) -> dict[str, str]:
    """
    Login user and create session.

    Args:
        credentials: Login credentials
        response: FastAPI response to set cookies
        db: Database session

    Returns:
        Success message

    Raises:
        401: Invalid credentials
    """
    # Find user by email
    stmt = select(User).where(User.email == credentials.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # TODO: Create session and set cookie
    # For now, just return success
    # In T028, we'll implement proper session management

    return {"message": "Login successful", "user_id": str(user.id)}


@router.post("/logout")
async def logout(response: Response) -> dict[str, str]:
    """
    Logout user and destroy session.

    Args:
        response: FastAPI response to clear cookies

    Returns:
        Success message
    """
    # TODO: Destroy session and clear cookie
    # For now, just return success

    return {"message": "Logout successful"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(db: DBSession) -> User:
    """
    Get current authenticated user.

    Args:
        db: Database session

    Returns:
        Current user

    Raises:
        401: Not authenticated
    """
    # TODO: Get user from session
    # For now, raise not implemented

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Session management not yet implemented",
    )
