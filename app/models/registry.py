from __future__ import annotations

from typing import Any, Dict

from app.extensions import db
from app.models.models import (
    Albums,
    Artists,
    Authentication,
    Downloads,
    Follows,
    Genres,
    Likes,
    Notifications,
    PlayHistory,
    Playlists,
    PlaylistSongs,
    Recommendations,
    SearchHistory,
    Sessions,
    Songs,
    SubscriptionPlans,
    UserInterest,
    UserSubscriptions,
    Users,
    Devices,
    Transactions,
)


TABLES = [
    "users",
    "authentication",
    "songs",
    "artists",
    "albums",
    "genres",
    "playlists",
    "playlist_songs",
    "follows",
    "play_history",
    "likes",
    "devices",
    "sessions",
    "subscription_plans",
    "user_subscriptions",
    "transactions",
    "notifications",
    "downloads",
    "search_history",
    "user_interest",
    "recommendations",
]


MODELS: Dict[str, Any] = {}


def init_models(_database: Any) -> None:
    """
    Initialize ORM models for the existing MySQL schema.

    This project does not recreate tables; it uses explicit models mapped to
    your existing table names.
    """
    global MODELS
    MODELS = {
        "users": Users,
        "authentication": Authentication,
        "songs": Songs,
        "artists": Artists,
        "albums": Albums,
        "genres": Genres,
        "playlists": Playlists,
        "playlist_songs": PlaylistSongs,
        "follows": Follows,
        "play_history": PlayHistory,
        "likes": Likes,
        "devices": Devices,
        "sessions": Sessions,
        "subscription_plans": SubscriptionPlans,
        "user_subscriptions": UserSubscriptions,
        "transactions": Transactions,
        "notifications": Notifications,
        "downloads": Downloads,
        "search_history": SearchHistory,
        "user_interest": UserInterest,
        "recommendations": Recommendations,
    }

