from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Request

from app.controllers.common import current_user_id, get_model, parse_pagination, pick_ordering_column
from app.extensions import db
from app.utils.http import api_response
from app.utils.pagination import make_pagination_meta
from app.utils.serialization import row_to_dict
from app.utils.schema_introspection import find_column, find_foreign_key_columns_referencing, primary_key_column


AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg", ".m4a")
AUDIO_DIRECTORY = Path(__file__).resolve().parent.parent / "static" / "audio"


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _serialize_song(song: Any, *, user_id: int | None = None):
    Songs = get_model("songs")
    Artists = get_model("artists")
    Albums = get_model("albums")
    Genres = get_model("genres")
    Likes = get_model("likes")

    data = row_to_dict(song)

    artist_fk_col = find_column(Songs, ["artist_id"], required=False)
    album_fk_col = find_column(Songs, ["album_id"], required=False)
    genre_fk_col = find_column(Songs, ["genre_id"], required=False)

    if artist_fk_col is not None:
        artist = Artists.query.filter(primary_key_column(Artists) == getattr(song, artist_fk_col.name)).first()
        if artist:
            artist_name_col = find_column(Artists, ["artist_name", "name"], required=False)
            if artist_name_col is not None:
                data["artist_name"] = getattr(artist, artist_name_col.name)

    if album_fk_col is not None:
        album = Albums.query.filter(primary_key_column(Albums) == getattr(song, album_fk_col.name)).first()
        if album:
            album_name_col = find_column(Albums, ["album_name", "name", "title"], required=False)
            if album_name_col is not None:
                data["album_name"] = getattr(album, album_name_col.name)

    if genre_fk_col is not None:
        genre = Genres.query.filter(primary_key_column(Genres) == getattr(song, genre_fk_col.name)).first()
        if genre:
            genre_name_col = find_column(Genres, ["genre_name", "name"], required=False)
            if genre_name_col is not None:
                data["genre_name"] = getattr(genre, genre_name_col.name)

    if user_id is not None:
        like_user_fk_cols = find_foreign_key_columns_referencing(Likes, "users")
        like_song_fk_cols = find_foreign_key_columns_referencing(Likes, "songs")
        if like_user_fk_cols and like_song_fk_cols:
            existing_like = Likes.query.filter(
                like_user_fk_cols[0] == user_id,
                like_song_fk_cols[0] == getattr(song, primary_key_column(Songs).name),
            ).first()
            data["liked_by_user"] = existing_like is not None

    song_id = getattr(song, primary_key_column(Songs).name)
    for extension in AUDIO_EXTENSIONS:
        candidate = AUDIO_DIRECTORY / f"{song_id}{extension}"
        if candidate.exists():
            data["audio_url"] = f"/static/audio/{song_id}{extension}"
            data["has_real_audio"] = True
            break
    else:
        data["audio_url"] = None
        data["has_real_audio"] = False

    return data


def list_songs(req: Request):
    Songs = get_model("songs")
    user_id = current_user_id()
    page, per_page = parse_pagination(req)

    order_col = pick_ordering_column(Songs)
    pk_col = primary_key_column(Songs)

    total = Songs.query.count()
    items = (
        Songs.query.order_by(order_col.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return api_response(
        ok=True,
        data={
            "items": [_serialize_song(i, user_id=user_id) for i in items],
            "pagination": make_pagination_meta(page, per_page, total),
        },
    )


def get_song(req: Request, song_id: str):
    Songs = get_model("songs")
    pk_col = primary_key_column(Songs)
    try:
        song_id_int = int(song_id)
    except (TypeError, ValueError):
        return api_response(ok=False, message="Invalid song id", status_code=400)
    song = Songs.query.filter(pk_col == song_id_int).first()
    if not song:
        return api_response(ok=False, message="Song not found", status_code=404)
    return api_response(ok=True, data=_serialize_song(song, user_id=current_user_id()))


def like_song(req: Request, song_id: str):
    Like = get_model("likes")
    user_id = current_user_id()
    Songs = get_model("songs")

    try:
        song_pk_value = int(song_id)
    except (TypeError, ValueError):
        return api_response(ok=False, message="Invalid song id", status_code=400)

    song_pk = primary_key_column(Songs)
    # Verify song exists (best-effort)
    if not Songs.query.filter(song_pk == song_pk_value).first():
        return api_response(ok=False, message="Song not found", status_code=404)

    user_fk_cols = find_foreign_key_columns_referencing(Like, "users")
    song_fk_cols = find_foreign_key_columns_referencing(Like, "songs")
    if not user_fk_cols or not song_fk_cols:
        return api_response(ok=False, message="Likes table must reference users and songs", status_code=500)
    user_fk = user_fk_cols[0]
    song_fk = song_fk_cols[0]

    created_at_col = find_column(Like, ["liked_at", "created_at", "inserted_at", "created"], required=False)

    existing = Like.query.filter(user_fk == user_id, song_fk == song_pk_value).first()
    total_likes_col = find_column(Songs, ["total_likes"], required=False)
    song = Songs.query.filter(song_pk == song_pk_value).first()
    if existing:
        try:
            db.session.delete(existing)
            if total_likes_col is not None and song is not None:
                current_total = getattr(song, total_likes_col.name) or 0
                setattr(song, total_likes_col.name, max(current_total - 1, 0))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return api_response(ok=False, message=f"Unliking failed: {e}", status_code=500)
        return api_response(
            ok=True,
            message="Unliked",
            data={
                "song_id": song_pk_value,
                "liked": False,
                "total_likes": getattr(song, total_likes_col.name) if total_likes_col is not None and song is not None else None,
            },
        )

    data: Dict[str, Any] = {user_fk.name: user_id, song_fk.name: song_pk_value}
    if created_at_col is not None:
        data[created_at_col.name] = _now_utc()

    try:
        like = Like(**data)
        db.session.add(like)
        if total_likes_col is not None and song is not None:
            current_total = getattr(song, total_likes_col.name) or 0
            setattr(song, total_likes_col.name, current_total + 1)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Liking failed: {e}", status_code=500)

    return api_response(
        ok=True,
        message="Liked",
        data={
            "song_id": song_pk_value,
            "liked": True,
            "total_likes": getattr(song, total_likes_col.name) if total_likes_col is not None and song is not None else None,
        },
    )


def play_song(req: Request, song_id: str):
    PlayHistory = get_model("play_history")
    user_id = current_user_id()
    Songs = get_model("songs")
    song_pk = primary_key_column(Songs)

    try:
        song_pk_value = int(song_id)
    except (TypeError, ValueError):
        return api_response(ok=False, message="Invalid song id", status_code=400)

    if not Songs.query.filter(song_pk == song_pk_value).first():
        return api_response(ok=False, message="Song not found", status_code=404)

    user_fk_cols = find_foreign_key_columns_referencing(PlayHistory, "users")
    song_fk_cols = find_foreign_key_columns_referencing(PlayHistory, "songs")
    if not user_fk_cols or not song_fk_cols:
        return api_response(ok=False, message="play_history table must reference users and songs", status_code=500)
    user_fk = user_fk_cols[0]
    song_fk = song_fk_cols[0]
    total_plays_col = find_column(Songs, ["total_plays"], required=False)
    song = Songs.query.filter(song_pk == song_pk_value).first()

    played_at_col = find_column(
        PlayHistory,
        ["played_at", "play_time", "timestamp", "created_at", "inserted_at"],
        required=False,
    )

    data: Dict[str, Any] = {user_fk.name: user_id, song_fk.name: song_pk_value}
    if played_at_col is not None:
        data[played_at_col.name] = _now_utc()

    try:
        entry = PlayHistory(**data)
        db.session.add(entry)
        if total_plays_col is not None and song is not None:
            current_total = getattr(song, total_plays_col.name) or 0
            setattr(song, total_plays_col.name, current_total + 1)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Play tracking failed: {e}", status_code=500)

    return api_response(
        ok=True,
        message="Play recorded",
        data={
            "song_id": song_pk_value,
            "total_plays": getattr(song, total_plays_col.name) if total_plays_col is not None and song is not None else None,
            "song": _serialize_song(song, user_id=user_id) if song is not None else None,
        },
    )

