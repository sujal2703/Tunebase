from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from flask import Request

from app.controllers.common import current_user_id, get_model, parse_pagination
from app.extensions import db
from app.utils.http import api_response
from app.utils.pagination import make_pagination_meta
from app.utils.serialization import row_to_dict
from app.utils.schema_introspection import find_column, find_foreign_key_columns_referencing, primary_key_column


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def register_device(req: Request):
    Devices = get_model("devices")
    user_id = current_user_id()
    payload = req.get_json(silent=True) or {}

    user_fk_cols = find_foreign_key_columns_referencing(Devices, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="devices table must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    # Schema uses `devices.device_name` as the identifier.
    identifier_col = find_column(Devices, ["device_name"], required=True)

    device_identifier = payload.get("device_identifier") or payload.get("device_name") or payload.get("identifier")
    if not device_identifier:
        return api_response(ok=False, message="`device_identifier` (or `device_name`) is required", status_code=400)

    created_at_col = find_column(Devices, ["created_at", "inserted_at", "created"], required=False)

    existing = Devices.query.filter(user_fk == user_id, identifier_col == device_identifier).first()
    if existing:
        return api_response(ok=True, data=row_to_dict(existing), message="Device already registered")

    data: Dict[str, Any] = {user_fk.name: user_id, identifier_col.name: device_identifier}
    if created_at_col is not None:
        data[created_at_col.name] = _now_utc()

    try:
        device = Devices(**data)
        db.session.add(device)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Register device failed: {e}", status_code=500)

    return api_response(ok=True, data=row_to_dict(device), message="Device registered")


def list_sessions(req: Request):
    Sessions = get_model("sessions")
    user_id = current_user_id()
    page, per_page = parse_pagination(req)

    # Schema: sessions references `devices`, not `users`. Filter sessions by joining devices->users.
    Devices = get_model("devices")

    sessions_device_fk_cols = find_foreign_key_columns_referencing(Sessions, "devices")
    if not sessions_device_fk_cols:
        return api_response(ok=False, message="sessions table must reference devices", status_code=500)
    sessions_device_fk = sessions_device_fk_cols[0]  # sessions.<device_id>

    devices_user_fk_cols = find_foreign_key_columns_referencing(Devices, "users")
    if not devices_user_fk_cols:
        return api_response(ok=False, message="devices table must reference users", status_code=500)
    devices_user_fk = devices_user_fk_cols[0]  # devices.user_id

    devices_pk = find_column(Devices, ["device_id", "id"], required=False)
    if devices_pk is None:
        # Fallback: primary key
        devices_pk = primary_key_column(Devices)

    order_col = find_column(Sessions, ["login_time", "created_at", "inserted_at", "created"], required=False) or primary_key_column(Sessions)

    base_q = (
        Sessions.query.join(
            Devices,
            getattr(Sessions, sessions_device_fk.name) == getattr(Devices, devices_pk.name),
        ).filter(getattr(Devices, devices_user_fk.name) == user_id)
    )
    total = base_q.count()
    items = (
        base_q.order_by(order_col.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return api_response(
        ok=True,
        data={"items": [row_to_dict(i) for i in items], "pagination": make_pagination_meta(page, per_page, total)},
    )

