# backend/app/db_config.py
TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.asyncpg",
            "credentials": {
                "host": "localhost",  # Use "postgres" in Docker
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
