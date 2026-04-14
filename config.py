def configure_logging():
    pass
import logging
import os
from datetime import timedelta

from dotenv import load_dotenv


load_dotenv()


def configure_logging() -> None:
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


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
    if not SQLALCHEMY_DATABASE_URI:
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "3306")
        name = os.getenv("DB_NAME", "")
        user = os.getenv("DB_USER", "")
        password = os.getenv("DB_PASSWORD", "")
        if name and user:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"
    # Allow the app to start even if DB env vars are not configured yet.
    # In production, always set `DATABASE_URL` (or the DB_* components) to point to your MySQL instance.
    if not SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

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
    RATELIMIT_STORAGE_URL = os.getenv("RATELIMIT_STORAGE_URL", "memory://")


__all__ = ["Config", "configure_logging"]

