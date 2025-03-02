# backend/scripts/migrate.py
import asyncio
import os
import sys
import socket
from pathlib import Path
from typing import NoReturn, List, Dict, Any, Optional

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

from tortoise import Tortoise, connections


class Migration:
    def __init__(self, name: str):
        self.name = name
        self.up_queries: List[str] = []
        self.down_queries: List[str] = []

    def add_column(self, table: str, column: str, type_def: str, default: Optional[str] = None) -> None:
        """Add a column to a table"""
        query = f"ALTER TABLE {table} ADD COLUMN {column} {type_def}"
        if default is not None:
            query += f" DEFAULT {default}"
        self.up_queries.append(query)
        self.down_queries.append(f"ALTER TABLE {table} DROP COLUMN {column}")

    def create_table(self, table: str, columns: Dict[str, str],
                     primary_key: Optional[str] = None) -> None:
        """Create a table with columns"""
        cols = [f"{name} {type_def}" for name, type_def in columns.items()]
        if primary_key:
            cols.append(f"PRIMARY KEY ({primary_key})")

        query = f"CREATE TABLE {table} ({', '.join(cols)})"
        self.up_queries.append(query)
        self.down_queries.append(f"DROP TABLE {table}")


async def run_migration(migration: Migration, direction: str = "up") -> None:
    """Run a migration in the specified direction"""
    # Connect to the database
    db_url = get_db_url()
    print(f"Connecting to database: {db_url}")

    try:
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["backend.app.main"]},
        )

        # Get a connection
        conn = connections.get_connection("default")

        # Create migrations table if it doesn't exist
        await ensure_migrations_table(conn)

        # Check if migration exists
        if direction == "up":
            if await migration_exists(conn, migration.name):
                print(f"Migration '{migration.name}' already applied, skipping.")
                return

            queries = migration.up_queries
            print(f"Applying migration '{migration.name}'...")
        else:
            if not await migration_exists(conn, migration.name):
                print(f"Migration '{migration.name}' not applied, can't roll back.")
                return

            queries = migration.down_queries
            print(f"Rolling back migration '{migration.name}'...")

        # Run the migration queries
        for query in queries:
            await conn.execute_query(query)

        # Update migrations table
        if direction == "up":
            await conn.execute_query(
                "INSERT INTO migrations (name, applied_at) VALUES ($1, NOW())",
                [migration.name]
            )
        else:
            await conn.execute_query(
                "DELETE FROM migrations WHERE name = $1",
                [migration.name]
            )

        print(f"Migration '{migration.name}' {direction} completed successfully.")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        # Close connections
        await Tortoise.close_connections()


async def ensure_migrations_table(conn) -> None:
    """Ensure migrations table exists"""
    await conn.execute_script("""
    CREATE TABLE IF NOT EXISTS migrations (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL UNIQUE,
        applied_at TIMESTAMP NOT NULL
    )
    """)


async def migration_exists(conn, name: str) -> bool:
    """Check if migration has been applied"""
    result = await conn.execute_query(
        "SELECT COUNT(*) FROM migrations WHERE name = $1",
        [name]
    )
    return result[1][0][0] > 0


def can_resolve_host(hostname: str) -> bool:
    """Check if a hostname can be resolved"""
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False


def get_db_url() -> str:
    """Get the appropriate database URL based on environment"""
    # First check environment variable
    if db_url := os.environ.get("DATABASE_URL"):
        return db_url

    # If "postgres" hostname can be resolved, use it (Docker environment)
    if can_resolve_host("postgres"):
        return "postgres://postgres:postgres@postgres:5432/openchains"

    # Otherwise, fallback to localhost (local development)
    return "postgres://postgres:postgres@localhost:5432/openchains"


def create_role_field_migration() -> Migration:
    """Create migration to add role field to User model"""
    migration = Migration("add_role_field_20250302")
    migration.add_column(
        table="users",
        column="role",
        type_def="VARCHAR(20) NOT NULL",
        default="'customer'"
    )
    return migration


async def main() -> None:
    """Run the migrations"""
    # Parse arguments
    import argparse
    parser = argparse.ArgumentParser(description="Database migrations")
    parser.add_argument("--down", action="store_true", help="Roll back migrations")
    args = parser.parse_args()

    # Run migrations
    direction = "down" if args.down else "up"
    await run_migration(create_role_field_migration(), direction)


def main_wrapper() -> NoReturn:
    """Wrapper for Poetry scripts"""
    asyncio.run(main())
    sys.exit(0)


if __name__ == "__main__":
    main_wrapper()
