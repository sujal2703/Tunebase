from __future__ import annotations

from flask import Request

from app.controllers.common import current_user_id, get_model, parse_pagination
from app.utils.http import api_response
from app.utils.pagination import make_pagination_meta
from app.utils.serialization import row_to_dict
from app.utils.schema_introspection import find_foreign_key_columns_referencing, find_column, primary_key_column


def list_notifications(req: Request):
    Notifications = get_model("notifications")
    user_id = current_user_id()
    page, per_page = parse_pagination(req)

    user_fk_cols = find_foreign_key_columns_referencing(Notifications, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="notifications must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    order_col = find_column(Notifications, ["created_at", "inserted_at", "created", "login_time"], required=False)
    if order_col is None:
        order_col = primary_key_column(Notifications)

    total = Notifications.query.filter(user_fk == user_id).count()
    items = (
        Notifications.query.filter(user_fk == user_id)
        .order_by(order_col.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return api_response(
        ok=True,
        data={"items": [row_to_dict(i) for i in items], "pagination": make_pagination_meta(page, per_page, total)},
    )

