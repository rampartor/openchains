# backend/tests/unit/test_token.py
import pytest
from passlib.hash import bcrypt
from starlette.testclient import TestClient

from backend.app.main import User
from backend.tests.unit.helpers import get_unique_username


@pytest.mark.asyncio
async def test_token_endpoint_valid_credentials(client: TestClient) -> None:
    """Test the /token endpoint with valid credentials."""
    # Create a test user with known credentials
    test_username = get_unique_username("token_user")
    test_password = "token_test_pass123"
    hashed_password = bcrypt.hash(test_password)

    # Create user in database
    user = await User.create(
        username=test_username, password=hashed_password, role="customer"
    )

    # Send JSON request to token endpoint
    response = client.post(
        "/token", json={"username": test_username, "password": test_password}
    )

    # Verify response
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

    # Clean up
    await user.delete()


@pytest.mark.asyncio
async def test_token_endpoint_invalid_credentials(client: TestClient) -> None:
    """Test the /token endpoint with invalid credentials."""
    # Send JSON request with invalid credentials
    response = client.post(
        "/token", json={"username": "nonexistent_user", "password": "wrong_password"}
    )

    # Verify response
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
