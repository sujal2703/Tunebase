import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


def _is_placeholder_database_url(value: str) -> bool:
    if not value:
        return True
    return any(token in value for token in ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"])


def _get_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    # Flask
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"

    # DB
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")
    if _is_placeholder_database_url(SQLALCHEMY_DATABASE_URI):
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        name = os.getenv("DB_NAME", "")
        user = os.getenv("DB_USER", "")
        password = os.getenv("DB_PASSWORD", "")
        if name and user:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=_get_int("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", 60)
    )

    # Bcrypt
    BCRYPT_LOG_ROUNDS = _get_int("BCRYPT_LOG_ROUNDS", 12)

    # Rate limiting
    RATE_LIMIT_DEFAULT = os.getenv("RATE_LIMIT_DEFAULT", "200 per day;50 per hour")

    # Add configuration for Flask-Limiter storage backend
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", "memory://")

