from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise


def setup_test_app(app: FastAPI) -> None:
    # Set up CORS for testing
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Tortoise with in-memory SQLite for testing
    register_tortoise(
        app,
        db_url="sqlite://:memory:",
        modules={"models": ["backend.app.main"]},
        generate_schemas=True,
        add_exception_handlers=True,
    )
