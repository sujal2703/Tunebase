from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from flask import Request

from app.controllers.common import current_user_id, get_model, parse_pagination
from app.extensions import db
from app.utils.http import api_response
from app.utils.pagination import make_pagination_meta
from app.utils.serialization import row_to_dict
from app.utils.schema_introspection import find_column, find_foreign_key_columns_referencing, primary_key_column


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def download_song(req: Request):
    Downloads = get_model("downloads")
    user_id = current_user_id()
    payload = req.get_json(silent=True) or {}
    song_id = payload.get("song_id") or payload.get("id")
    if not song_id:
        return api_response(ok=False, message="`song_id` is required", status_code=400)

    songs = get_model("songs")
    song_pk = primary_key_column(songs)
    if not songs.query.filter(song_pk == song_id).first():
        return api_response(ok=False, message="Song not found", status_code=404)

    user_fk_cols = find_foreign_key_columns_referencing(Downloads, "users")
    song_fk_cols = find_foreign_key_columns_referencing(Downloads, "songs")
    if not user_fk_cols or not song_fk_cols:
        return api_response(ok=False, message="downloads table must reference users and songs", status_code=500)
    user_fk = user_fk_cols[0]
    song_fk = song_fk_cols[0]

    downloaded_at_col = find_column(Downloads, ["downloaded_at", "created_at", "inserted_at", "created"], required=False)

    data: Dict[str, Any] = {user_fk.name: user_id, song_fk.name: song_id}
    if downloaded_at_col is not None:
        data[downloaded_at_col.name] = _now_utc()

    try:
        entry = Downloads(**data)
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Download record failed: {e}", status_code=500)

    return api_response(ok=True, data=row_to_dict(entry), message="Download recorded")


def list_downloads(req: Request):
    Downloads = get_model("downloads")
    user_id = current_user_id()
    page, per_page = parse_pagination(req)

    user_fk_cols = find_foreign_key_columns_referencing(Downloads, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="downloads must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    order_col = find_column(Downloads, ["downloaded_at", "created_at", "inserted_at", "created"], required=False) or primary_key_column(Downloads)

    total = Downloads.query.filter(user_fk == user_id).count()
    items = (
        Downloads.query.filter(user_fk == user_id)
        .order_by(order_col.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return api_response(
        ok=True,
        data={"items": [row_to_dict(i) for i in items], "pagination": make_pagination_meta(page, per_page, total)},
    )

