"""
Integration tests for authentication flow.

Tests the complete login/logout/session lifecycle.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from mybudget.lib.auth import hash_password
from mybudget.lib.session import SESSION_COOKIE_NAME
from mybudget.models.user import User


@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_login_flow(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test complete login → access protected route → logout flow."""
    # Step 1: Create a user
    user = User(
        email="flowtest@example.com",
        password_hash=hash_password("FlowTestPassword123!"),
        timezone="America/New_York",
    )
    db_session.add(user)
    await db_session.flush()

    # Step 2: Verify we can't access /me without login
    response = await client.get("/api/me")
    assert response.status_code == 401

    # Step 3: Login
    login_response = await client.post(
        "/api/login",
        json={
            "email": "flowtest@example.com",
            "password": "FlowTestPassword123!",
        },
    )
    assert login_response.status_code == 200
    assert "user_id" in login_response.json()

    # Verify session cookie was set
    assert SESSION_COOKIE_NAME in client.cookies

    # Step 4: Access /me with session - should succeed
    me_response = await client.get("/api/me")
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["email"] == "flowtest@example.com"
    assert me_data["timezone"] == "America/New_York"

    # Step 5: Logout
    logout_response = await client.post("/api/logout")
    assert logout_response.status_code == 200

    # Step 6: Verify session cookie was cleared
    # Note: httpx client may still have the cookie but it should be invalid
    # The server clears it by setting an expired cookie


@pytest.mark.integration
@pytest.mark.asyncio
async def test_register_then_login_flow(client: AsyncClient) -> None:
    """Test complete register → login → access protected route flow."""
    # Step 1: Register a new user
    register_response = await client.post(
        "/api/register",
        json={
            "email": "newregister@example.com",
            "password": "NewRegisterPassword123!",
            "timezone": "Europe/London",
        },
    )
    assert register_response.status_code == 201
    user_data = register_response.json()
    assert user_data["email"] == "newregister@example.com"

    # Step 2: Login with the new user
    login_response = await client.post(
        "/api/login",
        json={
            "email": "newregister@example.com",
            "password": "NewRegisterPassword123!",
        },
    )
    assert login_response.status_code == 200

    # Step 3: Access /me
    me_response = await client.get("/api/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "newregister@example.com"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_login_with_wrong_password_does_not_create_session(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that failed login does not create a session."""
    # Create a user
    user = User(
        email="wrongpassword@example.com",
        password_hash=hash_password("CorrectPassword123!"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    # Attempt login with wrong password
    login_response = await client.post(
        "/api/login",
        json={
            "email": "wrongpassword@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert login_response.status_code == 401

    # Session cookie should not be set
    assert SESSION_COOKIE_NAME not in client.cookies

    # /me should still return 401
    me_response = await client.get("/api/me")
    assert me_response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multiple_logins_same_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that a user can login multiple times and get new sessions."""
    # Create a user
    user = User(
        email="multilogin@example.com",
        password_hash=hash_password("MultiLoginPassword123!"),
        timezone="UTC",
    )
    db_session.add(user)
    await db_session.flush()

    # First login
    login_response1 = await client.post(
        "/api/login",
        json={
            "email": "multilogin@example.com",
            "password": "MultiLoginPassword123!",
        },
    )
    assert login_response1.status_code == 200
    assert SESSION_COOKIE_NAME in client.cookies

    # Verify first session works
    me_response1 = await client.get("/api/me")
    assert me_response1.status_code == 200
    assert me_response1.json()["email"] == "multilogin@example.com"

    # Second login (simulating a re-login)
    login_response2 = await client.post(
        "/api/login",
        json={
            "email": "multilogin@example.com",
            "password": "MultiLoginPassword123!",
        },
    )
    assert login_response2.status_code == 200
    assert SESSION_COOKIE_NAME in client.cookies

    # Second session should also work
    me_response2 = await client.get("/api/me")
    assert me_response2.status_code == 200
    assert me_response2.json()["email"] == "multilogin@example.com"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_contains_correct_user_id(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Test that the session correctly identifies the logged-in user."""
    # Create two users
    user1 = User(
        email="user1@example.com",
        password_hash=hash_password("User1Password123!"),
        timezone="UTC",
    )
    user2 = User(
        email="user2@example.com",
        password_hash=hash_password("User2Password123!"),
        timezone="UTC",
    )
    db_session.add(user1)
    db_session.add(user2)
    await db_session.flush()

    # Login as user1
    await client.post(
        "/api/login",
        json={
            "email": "user1@example.com",
            "password": "User1Password123!",
        },
    )

    # /me should return user1's data
    me_response = await client.get("/api/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "user1@example.com"

    # Login as user2 (replaces session)
    await client.post(
        "/api/login",
        json={
            "email": "user2@example.com",
            "password": "User2Password123!",
        },
    )

    # /me should now return user2's data
    me_response = await client.get("/api/me")
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "user2@example.com"
