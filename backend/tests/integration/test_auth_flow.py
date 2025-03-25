# backend/tests/integration/test_auth_flow.py
import time
from typing import AsyncGenerator, Dict

import httpx
import pytest

# Constants for testing
BASE_BACKEND_URL = "http://localhost:8000"
BASE_FRONTEND_URL = "http://localhost:5173"
TEST_USERNAME = "integration_test_user"
TEST_PASSWORD = "integration_test_password"


@pytest.fixture
async def test_user() -> AsyncGenerator[Dict[str, str], None]:
    """Create a test user and clean up after tests"""
    # Register a test user
    async with httpx.AsyncClient() as client:
        register_response = await client.post(
            f"{BASE_BACKEND_URL}/register",
            json={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD,
                "role": "customer",
            },
            timeout=10.0,
        )

        # If user already exists, that's okay
        if register_response.status_code == 400 and "already registered" in register_response.text:
            pass
        else:
            assert register_response.status_code == 200, f"Failed to create test user: {register_response.text}"

    # Return user info
    yield {"username": TEST_USERNAME, "password": TEST_PASSWORD}

    # We could add cleanup code here if needed


@pytest.mark.asyncio
async def test_authentication_flow(test_user: Dict[str, str]) -> None:
    """Test the complete authentication flow from frontend to backend"""
    async with httpx.AsyncClient() as client:
        # Step 1: Get authentication token
        token_response = await client.post(
            f"{BASE_BACKEND_URL}/token",
            json={"username": test_user["username"], "password": test_user["password"]},
            timeout=10.0,
        )

        assert token_response.status_code == 200, f"Authentication failed: {token_response.text}"
        token_data = token_response.json()
        assert "access_token" in token_data, "Token not found in response"
        assert token_data["token_type"] == "bearer", "Incorrect token type"

        # Step 2: Check frontend is accessible
        frontend_response = await client.get(BASE_FRONTEND_URL, timeout=10.0)
        assert frontend_response.status_code == 200, "Frontend is not accessible"

        # Step 3: Verify token can be used for protected endpoints
        # If you have a protected endpoint, you can test it here
        # Example:
        # protected_response = await client.get(
        #     f"{BASE_BACKEND_URL}/protected",
        #     headers={"Authorization": f"Bearer {token_data['access_token']}"},
        #     timeout=10.0
        # )
        # assert protected_response.status_code == 200


@pytest.mark.asyncio
async def test_invalid_login() -> None:
    """Test login with invalid credentials"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_BACKEND_URL}/token",
            json={"username": "invalid_user", "password": "invalid_password"},
            timeout=10.0,
        )

        assert response.status_code == 401, "Expected 401 Unauthorized for invalid login"
        error_data = response.json()
        assert "detail" in error_data, "Error detail not found in response"
        assert error_data["detail"] == "Incorrect username or password", "Unexpected error message"


@pytest.mark.asyncio
async def test_api_response_time() -> None:
    """Test that API responses are reasonably fast"""
    async with httpx.AsyncClient() as client:
        start_time = time.time()
        response = await client.post(
            f"{BASE_BACKEND_URL}/token",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD},
            timeout=10.0,
        )
        end_time = time.time()

        response_time = end_time - start_time
        assert response_time < 2.0, f"API response too slow: {response_time:.2f} seconds"

        # Check if timing header is present
        assert "X-Process-Time" in response.headers, "Timing header not found"
