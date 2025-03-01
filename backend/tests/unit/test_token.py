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

    # OAuth2 form data format for token endpoint
    form_data = {"username": test_username, "password": test_password}

    # Attempt login with valid credentials
    resp = client.post("/token", data=form_data)

    # Verify response
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"

    # Clean up
    await user.delete()


@pytest.mark.asyncio
async def test_token_endpoint_invalid_credentials(client: TestClient) -> None:
    """Test the /token endpoint with invalid credentials."""
    # OAuth2 form data format for token endpoint with invalid credentials
    form_data = {"username": "nonexistent_user", "password": "wrong_password"}

    # Attempt login with invalid credentials
    resp = client.post("/token", data=form_data)

    # Verify response
    assert resp.status_code == 401
    assert resp.json()["detail"] == "Incorrect username or password"
