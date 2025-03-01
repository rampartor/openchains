import pytest
from starlette.testclient import TestClient
from passlib.hash import bcrypt

from backend.app.main import User
from backend.tests.unit.helpers import get_unique_username


@pytest.mark.asyncio
async def test_register_endpoint_success(client: TestClient) -> None:
    """Test successful user registration."""
    # Unique username for this test to avoid conflicts
    test_username = get_unique_username("reg_user")
    test_password = "reg_password123"

    # Registration data
    user_data = {
        "username": test_username,
        "password": test_password,
        "role": "customer"  # Default role
    }

    # Attempt to register
    resp = client.post("/register", json=user_data)

    # Verify response
    assert resp.status_code == 200
    assert "message" in resp.json()
    assert resp.json()["message"] == "User created successfully"
    assert "user_id" in resp.json()

    # Verify user was created in database
    user = await User.get_or_none(username=test_username)
    assert user is not None
    assert user.username == test_username
    assert user.role == "customer"

    # Clean up
    await user.delete()


@pytest.mark.asyncio
async def test_register_endpoint_duplicate_username(client: TestClient) -> None:
    """Test registration with duplicate username."""
    # Create a test user first
    test_username = get_unique_username("existing_user")
    test_password = "password123"
    hashed_password = bcrypt.hash(test_password)

    # Create user in database
    user = await User.create(
        username=test_username,
        password=hashed_password,
        role="customer"
    )

    # Try to register with the same username
    user_data = {
        "username": test_username,
        "password": "different_password",
        "role": "customer"
    }

    # Attempt to register
    resp = client.post("/register", json=user_data)

    # Verify response - should be a conflict error
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Username already registered"

    # Clean up
    await user.delete()


@pytest.mark.asyncio
async def test_register_admin_user(client: TestClient) -> None:
    """Test registering a user with admin role."""
    # Unique username for this test
    test_username = get_unique_username("admin_reg")
    test_password = "admin_password123"

    # Registration data with admin role
    user_data = {
        "username": test_username,
        "password": test_password,
        "role": "admin"
    }

    # Attempt to register
    resp = client.post("/register", json=user_data)

    # Verify response
    assert resp.status_code == 200
    assert "message" in resp.json()
    assert resp.json()["message"] == "User created successfully"

    # Verify user was created in database with admin role
    user = await User.get_or_none(username=test_username)
    assert user is not None
    assert user.username == test_username
    assert user.role == "admin"

    # Clean up
    await user.delete()
