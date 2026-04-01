from __future__ import annotations

from typing import Any, Dict, List, Optional

from flask import Request

from app.controllers.common import current_user_id, get_model, parse_pagination
from app.controllers.songs_controller import _serialize_song
from app.utils.http import api_response
from app.utils.pagination import make_pagination_meta
from app.utils.serialization import row_to_dict
from app.utils.schema_introspection import find_column, find_foreign_key_columns_referencing, primary_key_column
from app.extensions import db


def search(req: Request):
    Songs = get_model("songs")
    History = get_model("search_history")
    user_id = current_user_id()
    payload = req.get_json(silent=True) or {}
    query = payload.get("query")
    if not query or not isinstance(query, str):
        return api_response(ok=False, message="`query` must be a non-empty string", status_code=400)

    # Store search history (best-effort)
    try:
        user_fk_cols = find_foreign_key_columns_referencing(History, "users")
        user_fk = user_fk_cols[0] if user_fk_cols else find_column(History, ["user_id"], required=False)
        query_col = find_column(History, ["query", "search_query", "term", "q"], required=True)
        created_at_col = find_column(History, ["created_at", "inserted_at", "created"], required=False)
        data: Dict[str, Any] = {user_fk.name: user_id, query_col.name: query}
        if created_at_col is not None:
            from datetime import datetime, timezone

            data[created_at_col.name] = datetime.now(timezone.utc).replace(tzinfo=None)
        entry = History(**data)
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()

    page, per_page = parse_pagination(req)

    # Determine song title column.
    title_col = find_column(Songs, ["title", "song_name", "name"], required=True)

    q = f"%{query}%"
    total = Songs.query.filter(title_col.like(q)).count()
    order_col = find_column(Songs, ["created_at", "inserted_at", "id"], required=False)
    if order_col is None:
        order_col = primary_key_column(Songs)
    items = (
        Songs.query.filter(title_col.like(q))
        .order_by(order_col.desc())
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


def search_history(req: Request):
    History = get_model("search_history")
    user_id = current_user_id()
    page, per_page = parse_pagination(req)

    user_fk_cols = find_foreign_key_columns_referencing(History, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="search_history must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    # Schema doesn't store a separate timestamp; order by primary key.
    created_at_col = find_column(History, ["created_at", "inserted_at", "created"], required=False)
    order_col = created_at_col
    if order_col is None:
        order_col = primary_key_column(History)

    total = History.query.filter(user_fk == user_id).count()
    q = History.query.filter(user_fk == user_id).order_by(order_col.desc())
    items = q.offset((page - 1) * per_page).limit(per_page).all()

    return api_response(
        ok=True,
        data={"items": [row_to_dict(i) for i in items], "pagination": make_pagination_meta(page, per_page, total)},
    )


def clear_search_history(req: Request):
    History = get_model("search_history")
    user_id = current_user_id()

    user_fk_cols = find_foreign_key_columns_referencing(History, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="search_history must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    deleted = History.query.filter(user_fk == user_id).delete(synchronize_session=False)
    db.session.commit()

    return api_response(
        ok=True,
        message="Search history cleared.",
        data={"deleted": deleted},
    )


def delete_search_history_item(search_id: int):
    History = get_model("search_history")
    user_id = current_user_id()

    user_fk_cols = find_foreign_key_columns_referencing(History, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="search_history must reference users", status_code=500)
    user_fk = user_fk_cols[0]
    pk_col = primary_key_column(History)

    item = History.query.filter(pk_col == search_id, user_fk == user_id).first()
    if item is None:
        return api_response(ok=False, message="Search history item not found.", status_code=404)

    db.session.delete(item)
    db.session.commit()

    return api_response(
        ok=True,
        message="Search removed from history.",
        data={"deleted_id": search_id},
    )

