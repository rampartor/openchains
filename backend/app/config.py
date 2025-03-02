import socket
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise


def can_resolve_host(hostname: str) -> bool:
    """Check if a hostname can be resolved"""
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False


def get_db_host() -> str:
    """Determine the database host based on environment"""
    # If "postgres" hostname can be resolved, use it (Docker environment)
    if can_resolve_host("postgres"):
        return "postgres"

    # Otherwise, fallback to localhost (local development)
    return "localhost"


# Determine the database host
DB_HOST = get_db_host()

# Create Tortoise ORM config
TORTOISE_ORM: Dict[str, Any] = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": DB_HOST,
                "port": "5432",
                "user": "postgres",
                "password": "postgres",
                "database": "openchains",
            },
        }
    },
    "apps": {
        "models": {
            "models": ["backend.app.main", "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": False,
    "timezone": "UTC",
}


async def init_db() -> None:
    """Initialize the database with proper migrations"""
    try:
        # Show which database we're connecting to
        print(f"Connecting to database at: {DB_HOST}")

        # Initialize Tortoise ORM
        await Tortoise.init(
            connections={"default": TORTOISE_ORM["connections"]["default"]},
            apps=TORTOISE_ORM["apps"],
        )

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

    except Exception as e:
        print(f"Database initialization error: {e}")
        raise


def setup_app(app: FastAPI) -> None:
    """Configure the app for production"""
    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://frontend:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create connection string based on detected host
    db_url = f"postgres://postgres:postgres@{DB_HOST}:5432/openchains"

    # Register Tortoise with production settings
    register_tortoise(
        app,
        db_url=db_url,
        modules={"models": ["backend.app.main"]},
        generate_schemas=False,  # We handle this separately
        add_exception_handlers=True,
    )


# For test environments
def setup_test_app(app: FastAPI) -> None:
    """Set up app for testing with SQLite in-memory database"""
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
