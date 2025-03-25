import asyncio
from typing import Any

from behave.model import Scenario
from tortoise import Tortoise


def before_all(context: Any) -> None:
    # Set up the event loop for async operations
    if hasattr(asyncio, "new_event_loop"):
        context.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(context.loop)
    else:
        context.loop = asyncio.get_event_loop()

    # Initialize Tortoise with in-memory SQLite for testing
    context.loop.run_until_complete(Tortoise.init(db_url="sqlite://:memory:", modules={"models": ["backend.app.main"]}))
    # Generate schemas
    context.loop.run_until_complete(Tortoise.generate_schemas())


def before_scenario(context: Any, scenario: Scenario) -> None:
    # Setup for each scenario if needed
    pass


def after_scenario(context: Any, scenario: Scenario) -> None:
    # Clean up after each scenario if needed
    pass


def after_all(context: Any) -> None:
    # Close Tortoise connections
    context.loop.run_until_complete(Tortoise.close_connections())
    # Close the event loop
    context.loop.close()
