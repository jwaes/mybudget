"""
Contract tests for authentication API endpoints.

Tests the API contracts defined in the OpenAPI specification.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.models.user import User


@pytest.mark.contract
@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient) -> None:
    """Test POST /api/register returns 201 with valid data."""
    response = await client.post(
        "/api/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "timezone": "Europe/Brussels",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["timezone"] == "Europe/Brussels"
    assert "id" in data
    assert "password" not in data  # Password should not be returned


@pytest.mark.contract
@pytest.mark.asyncio
async def test_register_user_duplicate_email(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test POST /api/register returns 409 for duplicate email."""
    # Create existing user
    existing_user = User(
        email="existing@example.com",
        password_hash=hash_password("password"),
        timezone="UTC",
    )
    db_session.add(existing_user)
    await db_session.flush()

    # Try to register with same email
    response = await client.post(
        "/api/register",
        json={
            "email": "existing@example.com",
            "password": "AnotherPassword123!",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 409
    data = response.json()
    assert "already registered" in data["detail"].lower()


@pytest.mark.contract
@pytest.mark.asyncio
async def test_register_user_invalid_email(client: AsyncClient) -> None:
    """Test POST /api/register returns 422 for invalid email."""
    response = await client.post(
        "/api/register",
        json={
            "email": "not-an-email",
            "password": "SecurePassword123!",
            "timezone": "UTC",
        },
    )

    assert response.status_code == 422


@pytest.mark.contract
@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test POST /api/login returns 200 with valid credentials."""
    # Create user
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("CorrectPassword"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    # Login
    response = await client.post(
        "/api/login",
        json={
            "email": "testuser@example.com",
            "password": "CorrectPassword",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Login successful"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_login_invalid_password(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test POST /api/login returns 401 for invalid password."""
    # Create user
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("CorrectPassword"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    # Try login with wrong password
    response = await client.post(
        "/api/login",
        json={
            "email": "testuser@example.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401
    data = response.json()
    assert "invalid" in data["detail"].lower()


@pytest.mark.contract
@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    """Test POST /api/login returns 401 for nonexistent user."""
    response = await client.post(
        "/api/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword",
        },
    )

    assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
async def test_logout(client: AsyncClient) -> None:
    """Test POST /api/logout returns 200."""
    response = await client.post("/api/logout")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient) -> None:
    """Test GET /api/me returns 401 without authentication."""
    response = await client.get("/api/me")

    # Should return 401 when not authenticated
    assert response.status_code == 401


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_current_user_success(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test GET /api/me returns 200 with valid session."""
    # Create user
    user = User(
        email="sessionuser@example.com",
        password_hash=hash_password("TestPassword123!"),
        timezone="Europe/Brussels",
    )
    db_session.add(user)
    await db_session.flush()

    # Login to get session cookie
    login_response = await client.post(
        "/api/login",
        json={
            "email": "sessionuser@example.com",
            "password": "TestPassword123!",
        },
    )
    assert login_response.status_code == 200

    # Access /me with the session cookie
    response = await client.get("/api/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "sessionuser@example.com"
    assert data["timezone"] == "Europe/Brussels"
    assert "id" in data
    assert "password" not in data
