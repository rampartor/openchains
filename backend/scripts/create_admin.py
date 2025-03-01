# backend/scripts/create_admin.py
import argparse
import asyncio
import os

from passlib.context import CryptContext
from tortoise import Tortoise

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def create_admin(username: str, password: str) -> None:
    """
    Create an admin user with the given username and password.

    Args:
        username: The admin username
        password: The admin password
    """
    # Get the database URL from environment or use default
    db_url = os.environ.get(
        "DATABASE_URL", "postgres://postgres:postgres@postgres:5432/openchains"
    )

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

    # Close connections
    await Tortoise.close_connections()


async def main() -> None:
    """Main function to parse arguments and create admin user"""
    parser = argparse.ArgumentParser(description="Create an admin user")
    parser.add_argument(
        "--username", type=str, default="admin", help="Admin username (default: admin)"
    )
    parser.add_argument(
        "--password",
        type=str,
        default="adminpassword",
        help="Admin password (default: adminpassword)",
    )
    args = parser.parse_args()

    await create_admin(args.username, args.password)


if __name__ == "__main__":
    """Entry point for the script"""
    asyncio.run(main())
