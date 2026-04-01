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


def record_transaction(req: Request):
    Transactions = get_model("transactions")
    user_id = current_user_id()
    payload = req.get_json(silent=True) or {}

    user_fk_cols = find_foreign_key_columns_referencing(Transactions, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="transactions must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    # Plan foreign key is optional depending on schema.
    subscription_fk_cols = find_foreign_key_columns_referencing(Transactions, "subscription_plans")
    subscription_fk = subscription_fk_cols[0] if subscription_fk_cols else None
    plan_id = payload.get("subscription_id") or payload.get("plan_id") or payload.get("id")

    amount_col = find_column(Transactions, ["amount", "total_amount"], required=False)
    amount = payload.get("amount")

    payment_method_col = find_column(Transactions, ["payment_method", "method"], required=False)
    payment_method = payload.get("payment_method") or payload.get("method")

    status_col = find_column(Transactions, ["status", "transaction_status"], required=False)
    status = payload.get("status") or "completed"

    # Minimal required fields for a payment record.
    if amount_col is not None and amount is None:
        return api_response(ok=False, message="`amount` is required", status_code=400)
    if amount_col is not None:
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return api_response(ok=False, message="Invalid `amount` (must be INT)", status_code=400)
    if payment_method_col is not None and not payment_method:
        return api_response(ok=False, message="`payment_method` is required", status_code=400)
    if plan_id is not None:
        try:
            plan_id = int(plan_id)
        except (TypeError, ValueError):
            return api_response(ok=False, message="Invalid `subscription_id` / `plan_id`", status_code=400)

    data: Dict[str, Any] = {user_fk.name: user_id}
    if subscription_fk is not None and plan_id is not None:
        data[subscription_fk.name] = plan_id
    if amount_col is not None:
        data[amount_col.name] = amount
    if payment_method_col is not None and payment_method is not None:
        data[payment_method_col.name] = payment_method
    if status_col is not None and status is not None:
        data[status_col.name] = status

    try:
        tx = Transactions(**data)
        db.session.add(tx)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Transaction failed: {e}", status_code=500)

    return api_response(ok=True, data=row_to_dict(tx), message="Transaction recorded")


def list_transactions(req: Request):
    Transactions = get_model("transactions")
    user_id = current_user_id()
    page, per_page = parse_pagination(req)

    user_fk_cols = find_foreign_key_columns_referencing(Transactions, "users")
    if not user_fk_cols:
        return api_response(ok=False, message="transactions must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    # Schema has no created_at; order by transaction_id.
    order_col = find_column(Transactions, ["transaction_id", "id"], required=False) or primary_key_column(Transactions)

    total = Transactions.query.filter(user_fk == user_id).count()
    items = (
        Transactions.query.filter(user_fk == user_id)
        .order_by(order_col.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return api_response(
        ok=True,
        data={"items": [row_to_dict(i) for i in items], "pagination": make_pagination_meta(page, per_page, total)},
    )

