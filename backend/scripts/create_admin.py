# backend/scripts/create_admin.py
import argparse
import asyncio
import os
import socket
import sys
from pathlib import Path
from typing import NoReturn

from passlib.context import CryptContext
from tortoise import Tortoise

# Add the parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Generate a hashed password"""
    return pwd_context.hash(password)


def is_running_in_docker() -> bool:
    """Check if we're running inside a Docker container"""
    try:
        with open("/proc/1/cgroup", "rt") as f:
            return "docker" in f.read()
    except FileNotFoundError:
        return False


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


async def create_admin(username: str, password: str) -> None:
    """
    Create an admin user with the given username and password.

    Args:
        username: The admin username
        password: The admin password
    """
    # Get the appropriate database URL
    db_url = get_db_url()
    print(f"Connecting to database: {db_url}")

    try:
        # Initialize Tortoise
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["backend.app.main"]},
        )

        # Import User model after initializing Tortoise
        from backend.app.main import User

        # Check if user already exists
        existing_user = await User.get_or_none(username=username)
        if existing_user:
            print(f"User {username} already exists.")
            if existing_user.role != "admin":
                # Update role to admin
                existing_user.role = "admin"
                await existing_user.save()
                print(f"Updated {username} role to admin.")
            else:
                print(f"User {username} is already an admin.")
            return

        # Hash the password
        hashed_password = get_password_hash(password)

        # Create the admin user
        user = await User.create(
            username=username, password=hashed_password, role="admin", is_active=True
        )
        print(f"Admin user {username} created successfully with ID {user.id}.")

    except Exception as e:
        print(f"Error creating admin user: {e}")
        raise
    finally:
        # Close connections
        await Tortoise.close_connections()


async def main() -> None:
    """Main function to parse arguments and create admin user"""
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument(
        "username",
        type=str,
        nargs="?",
        default="admin",
        help="Admin username (default: admin)",
    )
    parser.add_argument(
        "--password",
        "-p",
        type=str,
        default="adminpassword",
        help="Admin password (default: adminpassword)",
    )
    args = parser.parse_args()

    await create_admin(args.username, args.password)


def main_wrapper() -> NoReturn:
    asyncio.run(main())
    sys.exit(0)


if __name__ == "__main__":
    """Entry point for the script"""
    main_wrapper()
