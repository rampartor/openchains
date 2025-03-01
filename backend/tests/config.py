# backend/app/config.py
from typing import Any, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
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


# Production configuration
TORTOISE_ORM: Dict[str, Any] = {
    "connections": {"default": "postgres://postgres:postgres@postgres:5432/openchains"},
    "apps": {
        "models": {
            "models": ["backend.app.main"],
            "default_connection": "default",
        },
    },
}


async def init_db() -> None:
    # Type the connection string explicitly
    db_url: str = TORTOISE_ORM["connections"]["default"]
    # Type the models list explicitly
    models_list: List[str] = TORTOISE_ORM["apps"]["models"]["models"]

    await Tortoise.init(db_url=db_url, modules={"models": models_list})

    # Get a connection
    conn = Tortoise.get_connection("default")

    try:
        # Check if the role column already exists to avoid errors
        check_query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='users' AND column_name='role';
        """
        result = await conn.execute_query(check_query)

        if not result[1]:  # Column doesn't exist
            print("Adding 'role' column to users table...")

            # Add the column with a default value
            await conn.execute_script(
                """
            ALTER TABLE users
            ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'customer';
            """
            )

            print("Migration completed successfully.")

    except Exception as e:
        print(f"Migration check failed: {e}")
        # Continue with normal schema generation

    # This will create tables and add any other missing columns
    await Tortoise.generate_schemas(safe=True)


def setup_prod_app(app: FastAPI) -> None:
    """Configure the app for production"""
    # Set up CORS for production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://frontend:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Type the connection string and models list explicitly
    db_url: str = TORTOISE_ORM["connections"]["default"]
    models_list: List[str] = TORTOISE_ORM["apps"]["models"]["models"]

    # Register Tortoise with production settings
    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": models_list},
        generate_schemas=False,  # We handle this separately
        add_exception_handlers=True,
    )
