import uuid


def get_unique_username(prefix="test_user"):
    """Generate a unique username using UUID to avoid conflicts."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"
