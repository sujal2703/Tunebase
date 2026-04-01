from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from flask import Request
from flask_jwt_extended import get_jwt_identity

from app.models.registry import MODELS
from app.utils.pagination import get_pagination_params
from app.utils.serialization import row_to_dict
from app.utils.schema_introspection import find_column, primary_key_column, get_table_name


def require_models_ready() -> None:
    # Reflection failures are allowed at boot; endpoints should return clear errors.
    if not MODELS:
        raise RuntimeError("Database models are not initialized. Check DATABASE_URL / DB connectivity.")


def current_user_id() -> int:
    identity = get_jwt_identity()
    if identity is None:
        raise RuntimeError("Missing JWT identity")
    try:
        return int(identity)
    except (TypeError, ValueError):
        raise RuntimeError("JWT identity is not a valid user id")


def get_model(table_name: str) -> Any:
    require_models_ready()
    if table_name not in MODELS:
        raise RuntimeError(f"Model for table '{table_name}' is not available.")
    return MODELS[table_name]


def as_dict_or_none(model_cls: Any, obj: Any) -> Optional[Dict[str, Any]]:
    if obj is None:
        return None
    # Prefer column-driven serialization.
    return row_to_dict(obj)


def parse_pagination(request: Request) -> Tuple[int, int]:
    return get_pagination_params(request)


def get_column_or_400(model_cls: Any, candidates: list[str], field_name: str) -> Any:
    """
    Find a column; if missing, raise a ValueError so the caller can return 400.
    """
    return find_column(model_cls, candidates, required=True)


def get_pk_value(obj: Any, pk_col: Any) -> Any:
    return getattr(obj, pk_col.name)


def pick_ordering_column(model_cls: Any) -> Any:
    # Prefer a "created_at" style column for stable ordering.
    for cand in ["created_at", "inserted_at", "created", "updated_at", "login_time", "downloaded_at", "played_at"]:
        col = find_column(model_cls, [cand], required=False)
        if col is not None:
            return col
    return primary_key_column(model_cls)

