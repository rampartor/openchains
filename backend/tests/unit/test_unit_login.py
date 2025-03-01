# backend/tests/unit/test_unit_login.py
import pytest
from passlib.hash import bcrypt
from starlette.testclient import TestClient

from backend.app.main import User


def test_login_invalid_credentials(client: TestClient) -> None:
    # The login endpoint expects form data, not JSON
    resp = client.post("/login", data={"username": "foo", "password": "bar"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect username or password"


@pytest.mark.asyncio
async def test_login_successful(client: TestClient) -> None:
    # Create a test user with known credentials
    test_username = "testuser"
    test_password = "testpass123"
    hashed_password = bcrypt.hash(test_password)

    # Create user in database with role
    user = await User.create(
        username=test_username, password=hashed_password, role="customer"
    )

    # Attempt login with valid credentials using form data
    resp = client.post(
        "/login", data={"username": test_username, "password": test_password}
    )

    # Verify response - should return token info
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"

    # Clean up
    await user.delete()


@pytest.mark.asyncio
async def test_login_admin_user(client: TestClient) -> None:
    # Create an admin user with known credentials
    admin_username = "admin_test"
    admin_password = "admin123"
    hashed_password = bcrypt.hash(admin_password)

    # Create admin user in database
    admin = await User.create(
        username=admin_username, password=hashed_password, role="admin"
    )

    # Attempt login with valid credentials using form data
    resp = client.post(
        "/login", data={"username": admin_username, "password": admin_password}
    )

    # Verify response - should return token info
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"

    # Clean up
    await admin.delete()
