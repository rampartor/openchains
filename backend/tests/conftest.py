# backend/tests/conftest.py
import pytest
from starlette.testclient import TestClient
from fastapi import FastAPI
from backend.app.main import app
from backend.tests.config import setup_test_app


@pytest.fixture(scope="module")
def test_app():
    # Create a fresh app instance for testing
    app_for_testing = FastAPI()

    # Import your routes and models to the test app
    from backend.app.main import login, User
    app_for_testing.post("/login")(login)

    # Set up the test app with test configuration
    setup_test_app(app_for_testing)

    return app_for_testing


@pytest.fixture
def client(test_app):
    with TestClient(test_app) as client:
        yield client