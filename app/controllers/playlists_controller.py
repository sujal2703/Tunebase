from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Request

from app.controllers.common import current_user_id, get_model, parse_pagination, pick_ordering_column
from app.extensions import db
from app.utils.http import api_response
from app.utils.pagination import make_pagination_meta
from app.utils.serialization import row_to_dict
from app.utils.schema_introspection import find_column, find_foreign_key_columns_referencing, primary_key_column
from app.controllers.songs_controller import _serialize_song


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _playlist_payload(playlist: Any):
    PlaylistSongs = get_model("playlist_songs")
    Songs = get_model("songs")
    data = row_to_dict(playlist)
    data["name"] = data.get("playlist_name") or data.get("name") or data.get("title")
    data.pop("description", None)

    playlist_fk_cols = find_foreign_key_columns_referencing(PlaylistSongs, "playlists")
    song_fk_cols = find_foreign_key_columns_referencing(PlaylistSongs, "songs")
    if playlist_fk_cols and song_fk_cols:
        playlist_fk = playlist_fk_cols[0]
        song_fk = song_fk_cols[0]
        playlist_id = getattr(playlist, primary_key_column(type(playlist)).name)
        playlist_song_rows = PlaylistSongs.query.filter(playlist_fk == playlist_id).all()
        song_ids = [getattr(row, song_fk.name) for row in playlist_song_rows]
        data["song_count"] = len(song_ids)
        if song_ids:
            song_pk = primary_key_column(Songs)
            songs = Songs.query.filter(song_pk.in_(song_ids)).all()
            songs_by_id = {getattr(song, song_pk.name): song for song in songs}
            data["songs"] = [_serialize_song(songs_by_id[song_id]) for song_id in song_ids if song_id in songs_by_id]
        else:
            data["songs"] = []
    else:
        data["song_count"] = 0
        data["songs"] = []

    return data


def create_playlist(req: Request):
    Playlists = get_model("playlists")
    user_id = current_user_id()
    payload = req.get_json(silent=True) or {}

    name_col = find_column(Playlists, ["name", "playlist_name", "title"], required=True)
    desc_col = find_column(Playlists, ["description", "details", "notes"], required=False)

    user_fk_cols = find_foreign_key_columns_referencing(Playlists, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="playlists table must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    created_at_col = find_column(Playlists, ["created_at", "inserted_at", "created"], required=False)

    name = payload.get("name")
    if not name:
        return api_response(ok=False, message="`name` is required", status_code=400)

    data: Dict[str, Any] = {user_fk.name: user_id, name_col.name: name}
    if desc_col is not None and payload.get("description"):
        data[desc_col.name] = payload.get("description")
    if created_at_col is not None:
        data[created_at_col.name] = _now_utc()

    try:
        playlist = Playlists(**data)
        db.session.add(playlist)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Create playlist failed: {e}", status_code=500)

    return api_response(ok=True, data=_playlist_payload(playlist), message="Playlist created")


def add_song_to_playlist(req: Request, playlist_id: str):
    Playlists = get_model("playlists")
    Songs = get_model("songs")
    PlaylistSongs = get_model("playlist_songs")
    user_id = current_user_id()
    payload = req.get_json(silent=True) or {}
    song_id = payload.get("song_id") or payload.get("id")
    if not song_id:
        return api_response(ok=False, message="`song_id` is required", status_code=400)

    playlist_pk = primary_key_column(Playlists)
    song_pk = primary_key_column(Songs)

    try:
        playlist_id_int = int(playlist_id)
        song_id_int = int(song_id)
    except (TypeError, ValueError):
        return api_response(ok=False, message="Invalid `playlist_id` or `song_id`", status_code=400)

    playlist = Playlists.query.filter(playlist_pk == playlist_id_int).first()
    if not playlist:
        return api_response(ok=False, message="Playlist not found", status_code=404)

    # Ensure ownership (if possible)
    user_fk_cols = find_foreign_key_columns_referencing(Playlists, "users")
    if user_fk_cols:
        if getattr(playlist, user_fk_cols[0].name) != user_id:
            return api_response(ok=False, message="Forbidden", status_code=403)

    song = Songs.query.filter(song_pk == song_id_int).first()
    if not song:
        return api_response(ok=False, message="Song not found", status_code=404)

    playlist_fk_cols = find_foreign_key_columns_referencing(PlaylistSongs, "playlists")
    song_fk_cols = find_foreign_key_columns_referencing(PlaylistSongs, "songs")
    if not playlist_fk_cols or not song_fk_cols:
        return api_response(ok=False, message="playlist_songs must reference playlists and songs", status_code=500)

    playlist_fk = playlist_fk_cols[0]
    song_fk = song_fk_cols[0]
    added_at_col = find_column(PlaylistSongs, ["added_at", "created_at", "inserted_at"], required=False)

    existing = PlaylistSongs.query.filter(playlist_fk == playlist_id_int, song_fk == song_id_int).first()
    if existing:
        payload = row_to_dict(existing)
        payload["playlist_id"] = playlist_id_int
        payload["song_id"] = song_id_int
        return api_response(ok=True, message="Song already in playlist", data=payload)

    data: Dict[str, Any] = {
        playlist_fk.name: playlist_id_int,
        song_fk.name: song_id_int,
    }
    if added_at_col is not None:
        data[added_at_col.name] = _now_utc()

    try:
        item = PlaylistSongs(**data)
        db.session.add(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Add song failed: {e}", status_code=500)

    payload = row_to_dict(item)
    payload["playlist_id"] = playlist_id_int
    payload["song_id"] = song_id_int
    return api_response(ok=True, message="Song added to playlist", data=payload)


def remove_song_from_playlist(playlist_id: str, song_id: str):
    Playlists = get_model("playlists")
    PlaylistSongs = get_model("playlist_songs")
    user_id = current_user_id()

    playlist_pk = primary_key_column(Playlists)

    try:
        playlist_id_int = int(playlist_id)
        song_id_int = int(song_id)
    except (TypeError, ValueError):
        return api_response(ok=False, message="Invalid `playlist_id` or `song_id`", status_code=400)

    playlist = Playlists.query.filter(playlist_pk == playlist_id_int).first()
    if not playlist:
        return api_response(ok=False, message="Playlist not found", status_code=404)

    user_fk_cols = find_foreign_key_columns_referencing(Playlists, "users")
    if user_fk_cols and getattr(playlist, user_fk_cols[0].name) != user_id:
        return api_response(ok=False, message="Forbidden", status_code=403)

    playlist_fk_cols = find_foreign_key_columns_referencing(PlaylistSongs, "playlists")
    song_fk_cols = find_foreign_key_columns_referencing(PlaylistSongs, "songs")
    if not playlist_fk_cols or not song_fk_cols:
        return api_response(ok=False, message="playlist_songs must reference playlists and songs", status_code=500)

    playlist_song = PlaylistSongs.query.filter(
        playlist_fk_cols[0] == playlist_id_int,
        song_fk_cols[0] == song_id_int,
    ).first()
    if not playlist_song:
        return api_response(ok=False, message="Song is not in this playlist", status_code=404)

    try:
        db.session.delete(playlist_song)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Remove song failed: {e}", status_code=500)

    return api_response(
        ok=True,
        message="Song removed from playlist",
        data={"playlist_id": playlist_id_int, "song_id": song_id_int},
    )


def list_user_playlists(req: Request):
    Playlists = get_model("playlists")
    user_id = current_user_id()
    page, per_page = parse_pagination(req)

    playlist_pk = primary_key_column(Playlists)
    order_col = pick_ordering_column(Playlists)

    user_fk_cols = find_foreign_key_columns_referencing(Playlists, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="playlists table must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    total = Playlists.query.filter(user_fk == user_id).count()
    items = (
        Playlists.query.filter(user_fk == user_id)
        .order_by(order_col.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return api_response(
        ok=True,
        data={
            "items": [_playlist_payload(i) for i in items],
            "pagination": make_pagination_meta(page, per_page, total),
        },
    )

