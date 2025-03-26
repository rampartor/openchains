from typing import Generator

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient
from tortoise.contrib.fastapi import register_tortoise

from backend.app.main import login_for_access_token, register


@pytest.fixture(scope="module")
def test_app() -> FastAPI:
    # Create a fresh app instance for testing
    app_for_testing = FastAPI()

    # Import your routes and models to the test app
    app_for_testing.post("/token")(login_for_access_token)
    app_for_testing.post("/register")(register)

    # Set up the test app with test configuration
    register_tortoise(
        app_for_testing,
        db_url="sqlite://:memory:",
        modules={"models": ["backend.app.main"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )

    return app_for_testing


@pytest.fixture
def client(test_app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(test_app) as client:
        yield client
