from typing import Any

from behave import given, then, when
from fastapi.testclient import TestClient
from passlib.context import CryptContext

from backend.app.main import User, app

# Create a test client
client = TestClient(app)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@given('I have a user "{username}" with password "{password}"')
def step_impl_user(context: Any, username: str, password: str) -> None:
    # Create user with hashed password
    hashed_password = pwd_context.hash(password)

    async def create_user() -> Any:
        # First delete any existing users with this username
        await User.filter(username=username).delete()
        # Create the user
        return await User.create(
            username=username, password=hashed_password, role="customer"
        )

    # Run the async function in the event loop
    context.user = context.loop.run_until_complete(create_user())
    context.username = username
    context.password = password


@when('I post to "{endpoint}" with those credentials')
def step_impl_login(context: Any, endpoint: str) -> None:
    # Make the login request with JSON format
    context.response = client.post(
        endpoint, json={"username": context.username, "password": context.password}
    )


@then("I should receive a 200 status code")
def step_impl_status(context: Any) -> None:
    assert (
        context.response.status_code == 200
    ), f"Expected 200, got {context.response.status_code}: {context.response.text}"


@then("the response should include an access token")
def step_impl_token(context: Any) -> None:
    response_json = context.response.json()
    assert (
        "access_token" in response_json
    ), f"Expected access_token in response, but got: {response_json}"
    assert response_json["token_type"] == "bearer", "Expected token_type to be 'bearer'"
