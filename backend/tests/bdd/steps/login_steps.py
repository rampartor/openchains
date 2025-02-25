from behave import given, when, then
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@given('I have a user "{username}" with password "{password}"')
def step_impl(context, username, password):
    # In real usage, you'd create the user in the DB
    context.username = username
    context.password = password


@when('I post to "/login" with those credentials')
def step_impl(context):
    context.response = client.post("/login", json={
        "username": context.username,
        "password": context.password
    })


@then('I should receive a 200 status code')
def step_impl(context):
    assert context.response.status_code == 200


@then('the response should include "Hello, alice!"')
def step_impl(context):
    assert "Hello, alice!" in context.response.text
