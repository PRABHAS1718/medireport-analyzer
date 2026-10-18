"""Unit and integration tests for user registration, authentication, and JWT lifecycle."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient, test_db):
    """Test successful user registration returns HTTP 201 and never exposes password."""
    payload = {
        "email": "student@example.com",
        "password": "StrongPassword123!",
        "preferred_language": "en",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == "student@example.com"
    assert data["preferred_language"] == "en"
    assert data["status"] == "active"
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data

    # Verify password was hashed in MongoDB
    user_in_db = await test_db.users.find_one({"email": "student@example.com"})
    assert user_in_db is not None
    assert user_in_db["password_hash"] != "StrongPassword123!"
    assert user_in_db["password_hash"].startswith("$2b$") or user_in_db["password_hash"].startswith("$2a$")


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(client: AsyncClient):
    """Test that duplicate email registration returns HTTP 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "Password123!",
    }
    # First registration
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration with same email
    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_register_short_password_rejected(client: AsyncClient):
    """Test that password with fewer than 8 characters is rejected with HTTP 422."""
    payload = {
        "email": "short@example.com",
        "password": "short",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test login with valid credentials returns JWT bearer token."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "ValidPassword123!"}
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "ValidPassword123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    """Test login with incorrect password returns HTTP 401."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpass@example.com", "password": "RealPassword123!"}
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "WrongPassword456!"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient):
    """Test protected /auth/me returns profile when bearer token is supplied."""
    # Register & Login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "profile@example.com", "password": "MySecretPassword1!"}
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "profile@example.com", "password": "MySecretPassword1!"}
    )
    token = login_res.json()["access_token"]

    # Call /auth/me with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "profile@example.com"


@pytest.mark.asyncio
async def test_protected_route_without_token(client: AsyncClient):
    """Test protected route returns HTTP 401 when token is omitted."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "credentials were not provided" in response.json()["detail"]


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token(client: AsyncClient):
    """Test protected route returns HTTP 401 when invalid token is passed."""
    headers = {"Authorization": "Bearer invalid.fake.token"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401
