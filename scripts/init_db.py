from __future__ import annotations

from flask_bcrypt import generate_password_hash
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app import create_app
from app.extensions import db
from app.models.models import (
    Albums,
    Artists,
    Authentication,
    Genres,
    Notifications,
    Songs,
    SubscriptionPlans,
    UserInterest,
    Users,
)
from config import Config


def ensure_database_exists() -> None:
    database_uri = Config.SQLALCHEMY_DATABASE_URI
    if not database_uri:
        raise RuntimeError(
            "Database configuration is missing. Set DATABASE_URL or DB_HOST/DB_NAME/DB_USER/DB_PASSWORD in .env."
        )

    url = make_url(database_uri)
    database_name = url.database
    if not database_name:
        raise RuntimeError("Database name is missing from the configured database URI.")

    server_url = url.set(database="mysql")
    engine = create_engine(server_url)

    with engine.connect() as connection:
        connection.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database_name}`"))
        connection.commit()


def seed_reference_data() -> None:
    existing_demo_user = Users.query.filter_by(email="demo@example.com").first()
    if existing_demo_user:
        existing_auth = Authentication.query.filter_by(user_id=existing_demo_user.user_id).first()
        if not existing_auth:
            db.session.add(
                Authentication(
                    user_id=existing_demo_user.user_id,
                    password_hash=generate_password_hash("Password123!").decode("utf-8"),
                    failed_attempts=0,
                    account_status="active",
                )
            )
            db.session.commit()
        return

    artist_1 = Artists(artist_name="Arohi Lane")
    artist_2 = Artists(artist_name="Neon Harbour")
    db.session.add_all([artist_1, artist_2])
    db.session.flush()

    album_1 = Albums(album_name="City Echoes", artist_id=artist_1.artist_id)
    album_2 = Albums(album_name="Afterglow Miles", artist_id=artist_2.artist_id)
    db.session.add_all([album_1, album_2])
    db.session.flush()

    genre_1 = Genres(genre_name="Indie Pop")
    genre_2 = Genres(genre_name="Synthwave")
    db.session.add_all([genre_1, genre_2])
    db.session.flush()

    demo_user = Users(
        name="Demo User",
        email="demo@example.com",
    )
    db.session.add(demo_user)
    db.session.flush()
    db.session.add(
        Authentication(
            user_id=demo_user.user_id,
            password_hash=generate_password_hash("Password123!").decode("utf-8"),
            failed_attempts=0,
            account_status="active",
        )
    )

    songs = [
        Songs(
            title="Midnight Signals",
            duration=214,
            total_plays=1820,
            total_likes=420,
            artist_id=artist_1.artist_id,
            album_id=album_1.album_id,
            genre_id=genre_1.genre_id,
        ),
        Songs(
            title="Warm Static",
            duration=198,
            total_plays=1360,
            total_likes=318,
            artist_id=artist_1.artist_id,
            album_id=album_1.album_id,
            genre_id=genre_1.genre_id,
        ),
        Songs(
            title="Glass Highway",
            duration=241,
            total_plays=2215,
            total_likes=505,
            artist_id=artist_2.artist_id,
            album_id=album_2.album_id,
            genre_id=genre_2.genre_id,
        ),
        Songs(
            title="Night Circuit",
            duration=229,
            total_plays=1942,
            total_likes=462,
            artist_id=artist_2.artist_id,
            album_id=album_2.album_id,
            genre_id=genre_2.genre_id,
        ),
    ]
    db.session.add_all(songs)

    plans = [
        SubscriptionPlans(plan_name="Mini", price=99),
        SubscriptionPlans(plan_name="Premium", price=199),
        SubscriptionPlans(plan_name="Family", price=299),
    ]
    db.session.add_all(plans)

    interests = [
        UserInterest(user_id=demo_user.user_id, genre_id=genre_1.genre_id, interest_score=0.9),
        UserInterest(user_id=demo_user.user_id, genre_id=genre_2.genre_id, interest_score=0.8),
    ]
    db.session.add_all(interests)

    db.session.add(
        Notifications(
            user_id=demo_user.user_id,
            message="Welcome to PulseDB Music. Your demo library is ready.",
        )
    )

    db.session.commit()


def main() -> None:
    ensure_database_exists()
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_reference_data()
    print("Database initialized successfully.")
    print("Demo login: demo@example.com / Password123!")


if __name__ == "__main__":
    main()
