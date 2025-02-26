from typing import Any

from behave import given, then, when
from fastapi.testclient import TestClient
from passlib.hash import bcrypt

from backend.app.main import User, app

# Create a test client
client = TestClient(app)


@given('I have a user "{username}" with password "{password}"')
def step_impl_user(context: Any, username: str, password: str) -> None:
    # Create user with hashed password
    hashed_password = bcrypt.hash(password)

    async def create_user() -> Any:
        # First delete any existing users with this username
        await User.filter(username=username).delete()
        # Create the user
        return await User.create(
            username=username, password_hash=hashed_password, role="customer"
        )

    # Run the async function in the event loop
    context.user = context.loop.run_until_complete(create_user())
    context.username = username
    context.password = password


@when('I post to "/login" with those credentials')
def step_impl_login(context: Any) -> None:
    # Make the login request
    context.response = client.post(
        "/login", json={"username": context.username, "password": context.password}
    )


@then("I should receive a 200 status code")
def step_impl_status(context: Any) -> None:
    assert (
        context.response.status_code == 200
    ), f"Expected 200, got {context.response.status_code}: {context.response.text}"


@then('the response should include "{text}"')
def step_impl_text(context: Any, text: str) -> None:
    assert (
        text in context.response.text
    ), f"Expected '{text}' in response, but got: {context.response.text}"
