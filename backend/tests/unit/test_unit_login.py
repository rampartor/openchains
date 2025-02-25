# backend/tests/unit/test_unit_login.py
import pytest
from passlib.hash import bcrypt
from backend.app.main import User


# Your existing test
def test_login_invalid_credentials(client):
    resp = client.post("/login", json={"username": "foo", "password": "bar"})
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


# New test for successful login
@pytest.mark.asyncio
async def test_login_successful(client):
    # Create a test user with known credentials
    test_username = "testuser"
    test_password = "testpass123"
    hashed_password = bcrypt.hash(test_password)

    # Create user in database
    user = await User.create(
        username=test_username,
        password_hash=hashed_password,
        role="customer"
    )

    # Attempt login with valid credentials
    resp = client.post("/login", json={
        "username": test_username,
        "password": test_password
    })

    # Verify response
    assert resp.status_code == 200
    assert resp.json()["message"] == f"Hello, {test_username}!"

    # Clean up
    await user.delete()