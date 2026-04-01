from __future__ import annotations

from app.extensions import db


class Users(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255))
    date_of_birth = db.Column(db.Date)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)


class Authentication(db.Model):
    __tablename__ = "authentication"

    auth_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    failed_attempts = db.Column(db.Integer, default=0)
    account_status = db.Column(db.String(50), default="active")
    last_login = db.Column(db.DateTime)


class Artists(db.Model):
    __tablename__ = "artists"

    artist_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    artist_name = db.Column(db.String(150))
    bio = db.Column(db.Text)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)


class Albums(db.Model):
    __tablename__ = "albums"

    album_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    album_name = db.Column(db.String(150))
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.artist_id"), nullable=False)
    release_date = db.Column(db.Date)
    is_deleted = db.Column(db.Boolean, default=False)


class Genres(db.Model):
    __tablename__ = "genres"

    genre_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    genre_name = db.Column(db.String(100))


class Songs(db.Model):
    __tablename__ = "songs"

    song_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(150))
    duration = db.Column(db.Integer)
    total_plays = db.Column(db.Integer)
    total_likes = db.Column(db.Integer)

    artist_id = db.Column(db.Integer, db.ForeignKey("artists.artist_id"), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey("albums.album_id"), nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey("genres.genre_id"), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)


class Playlists(db.Model):
    __tablename__ = "playlists"

    playlist_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    playlist_name = db.Column(db.String(150))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)


class PlaylistSongs(db.Model):
    __tablename__ = "playlist_songs"

    playlist_id = db.Column(db.Integer, db.ForeignKey("playlists.playlist_id"), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id"), primary_key=True)
    added_at = db.Column(db.DateTime)


class Follows(db.Model):
    __tablename__ = "follows"

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.artist_id"), primary_key=True)


class PlayHistory(db.Model):
    __tablename__ = "play_history"

    play_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id"), nullable=False)
    played_at = db.Column(db.DateTime, nullable=False)


class Likes(db.Model):
    __tablename__ = "likes"

    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id"), primary_key=True)
    liked_at = db.Column(db.DateTime)


class Devices(db.Model):
    __tablename__ = "devices"

    device_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    device_name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.String(50))
    last_active = db.Column(db.DateTime)


class Sessions(db.Model):
    __tablename__ = "sessions"

    session_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.device_id"), nullable=False)
    login_time = db.Column(db.DateTime, nullable=False)
    logout_time = db.Column(db.DateTime)
    status = db.Column(db.String(50))


class SubscriptionPlans(db.Model):
    __tablename__ = "subscription_plans"

    plan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    duration_days = db.Column(db.Integer)


class UserSubscriptions(db.Model):
    __tablename__ = "user_subscriptions"

    subscription_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("subscription_plans.plan_id"), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(50))


class Transactions(db.Model):
    __tablename__ = "transactions"

    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey("user_subscriptions.subscription_id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    transaction_date = db.Column(db.DateTime)
    status = db.Column(db.String(50))


class Notifications(db.Model):
    __tablename__ = "notifications"

    notification_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    message = db.Column(db.Text)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime)


class Downloads(db.Model):
    __tablename__ = "downloads"

    download_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id"), nullable=False)
    downloaded_at = db.Column(db.DateTime)


class SearchHistory(db.Model):
    __tablename__ = "search_history"

    search_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    search_query = db.Column(db.String(255))
    searched_at = db.Column(db.DateTime)


class UserInterest(db.Model):
    __tablename__ = "user_interest"

    # This table is modeled as a composite PK (user_id + genre_id).
    # If your real DB uses an auto-increment PK instead, tell me and I’ll adjust.
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey("genres.genre_id"), primary_key=True)
    interest_score = db.Column(db.Numeric(5, 2))


class Recommendations(db.Model):
    __tablename__ = "recommendations"

    recommendation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    song_id = db.Column(db.Integer, db.ForeignKey("songs.song_id"), nullable=False)
    score = db.Column(db.Numeric(5, 2))
    generated_at = db.Column(db.DateTime)

