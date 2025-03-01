#!/usr/bin/env python
import asyncio
import sys
import os
from getpass import getpass
import argparse

# Add the project root to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import User, get_password_hash
from tortoise import Tortoise


async def create_admin_user(username, password=None, interactive=False):
    """
    Create an admin user in the database.

    Args:
        username: The username for the admin
        password: The password for the admin (will prompt if not provided and interactive=True)
        interactive: Whether to prompt for confirmation and password input
    """
    # Connect to the database
    # Get the DB URL from environment variable or use a default
    db_url = os.environ.get("DATABASE_URL", "postgres://postgres:postgres@localhost:5432/openchains")

    await Tortoise.init(
        db_url=db_url,
        modules={"models": ["backend.app.main"]}
    )

    # Create schemas if they don't exist
    await Tortoise.generate_schemas(safe=True)

    # Check if admin already exists
    existing_user = await User.get_or_none(username=username)

    if existing_user:
        if interactive:
            print(f"User '{username}' already exists.")
            update = input(f"Do you want to update the password for '{username}'? (y/N): ").lower()
            if update != 'y':
                print("Operation canceled.")
                return False
        else:
            print(f"User '{username}' already exists. Use --force to update the password.")
            return False

    # Get the password if not provided
    if password is None:
        if interactive:
            while True:
                password = getpass("Enter password: ")
                if not password:
                    print("Password cannot be empty.")
                    continue

                password_confirm = getpass("Confirm password: ")
                if password != password_confirm:
                    print("Passwords do not match. Please try again.")
                else:
                    break
        else:
            print("Error: Password must be provided in non-interactive mode.")
            return False

    # Hash the password
    hashed_password = get_password_hash(password)

    # Create or update the user
    if existing_user:
        existing_user.password = hashed_password
        await existing_user.save()
        print(f"Password updated for admin user '{username}'.")
    else:
        await User.create(
            username=username,
            password=hashed_password,
            role="admin"
        )
        print(f"Created admin user '{username}'.")

    return True


async def main():
    parser = argparse.ArgumentParser(description="Create an admin user for OpenChains")
    parser.add_argument("username", help="Admin username")
    parser.add_argument("--password", help="Admin password (omit for interactive prompt)")
    parser.add_argument("--force", action="store_true", help="Force update if user exists")

    args = parser.parse_args()

    interactive = not args.password or not args.force

    success = await create_admin_user(args.username, args.password, interactive)

    # Cleanup
    await Tortoise.close_connections()

    sys.exit(0 if success else 1)


# Wrapper function for Poetry to use as console script
def main_wrapper():
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
