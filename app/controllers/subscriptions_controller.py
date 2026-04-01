from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from flask import Request

from app.controllers.common import current_user_id, get_model, parse_pagination
from app.extensions import db
from app.utils.http import api_response
from app.utils.serialization import row_to_dict
from app.utils.pagination import make_pagination_meta
from app.utils.schema_introspection import find_column, find_foreign_key_columns_referencing, primary_key_column


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _free_plan_payload():
    Plans = get_model("subscription_plans")
    name_col = find_column(Plans, ["plan_name", "name", "title"], required=False)
    free_plan = None
    if name_col is not None:
        free_plan = Plans.query.filter(name_col == "Free").first()
    if free_plan is not None:
        payload = row_to_dict(free_plan)
        payload["status"] = "free"
        payload["active_plan"] = payload.get("plan_name") or "Free"
        return payload
    return {
        "plan_name": "Free",
        "description": "Ad-supported streaming on one device.",
        "price": 0,
        "duration_days": 30,
        "status": "free",
        "active_plan": "Free",
    }


def _plan_columns(Plans):
    return {
        "pk": primary_key_column(Plans),
        "name": find_column(Plans, ["plan_name", "name", "title"], required=False),
        "price": find_column(Plans, ["price", "amount", "cost"], required=False),
        "duration": find_column(Plans, ["duration_days", "duration", "validity_days"], required=False),
        "description": find_column(Plans, ["description", "details"], required=False),
    }


def _subscription_columns(UserSubs):
    return {
        "pk": primary_key_column(UserSubs),
        "user_fk_cols": find_foreign_key_columns_referencing(UserSubs, "users"),
        "plan_fk_cols": find_foreign_key_columns_referencing(UserSubs, "subscription_plans"),
        "status": find_column(UserSubs, ["status", "subscription_status"], required=False),
        "start": find_column(UserSubs, ["start_date", "started_at", "created_at", "inserted_at"], required=False),
        "end": find_column(UserSubs, ["end_date", "ends_at"], required=False),
    }


def _transaction_columns(Transactions):
    return {
        "user_fk_cols": find_foreign_key_columns_referencing(Transactions, "users"),
        "sub_fk_cols": find_foreign_key_columns_referencing(Transactions, "user_subscriptions"),
        "amount": find_column(Transactions, ["amount", "price", "total"], required=False),
        "method": find_column(Transactions, ["payment_method", "method"], required=False),
        "date": find_column(Transactions, ["transaction_date", "created_at", "paid_at"], required=False),
        "status": find_column(Transactions, ["status", "payment_status"], required=False),
    }


def _serialize_subscription_with_plan(subscription: Any, plan: Any) -> Dict[str, Any]:
    plan_payload = row_to_dict(plan) if plan is not None else {}
    subscription_payload = row_to_dict(subscription)
    return {
        **subscription_payload,
        "plan_name": plan_payload.get("plan_name") or plan_payload.get("name") or "Unknown Plan",
        "plan_description": plan_payload.get("description"),
        "plan_price": plan_payload.get("price"),
        "duration_days": plan_payload.get("duration_days"),
    }


def list_plans(req: Request):
    Plans = get_model("subscription_plans")
    page, per_page = parse_pagination(req)
    pk = primary_key_column(Plans)
    order_col = find_column(Plans, ["id", "created_at", "inserted_at", "price"], required=False)
    if order_col is None:
        order_col = pk

    total = Plans.query.count()
    items = Plans.query.order_by(order_col.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return api_response(
        ok=True,
        data={"items": [row_to_dict(i) for i in items], "pagination": make_pagination_meta(page, per_page, total)},
    )


def subscribe_to_plan(req: Request):
    Plans = get_model("subscription_plans")
    UserSubs = get_model("user_subscriptions")
    Transactions = get_model("transactions")
    user_id = current_user_id()
    payload = req.get_json(silent=True) or {}
    plan_id = payload.get("plan_id") or payload.get("id")
    if not plan_id:
        return api_response(ok=False, message="`plan_id` is required", status_code=400)

    try:
        plan_id_int = int(plan_id)
    except (TypeError, ValueError):
        return api_response(ok=False, message="Invalid `plan_id`", status_code=400)

    sub_cols = _subscription_columns(UserSubs)
    user_fk_cols = sub_cols["user_fk_cols"]
    plan_fk_cols = sub_cols["plan_fk_cols"]
    if not user_fk_cols:
        return api_response(ok=False, message="user_subscriptions must reference users", status_code=500)

    user_fk = user_fk_cols[0]

    plan_cols = _plan_columns(Plans)
    plan = Plans.query.filter(plan_cols["pk"] == plan_id_int).first()
    if plan is None:
        return api_response(ok=False, message="Selected plan not found", status_code=404)

    plan_col = plan_fk_cols[0] if plan_fk_cols else None
    if plan_col is None:
        plan_col = find_column(UserSubs, ["plan_id", "subscription_plan_id"], required=False)
    if plan_col is None:
        return api_response(ok=False, message="user_subscriptions must have plan_id column/FK", status_code=500)

    status_col = sub_cols["status"]
    start_col = sub_cols["start"]
    end_col = sub_cols["end"]
    payment_method = payload.get("payment_method") or "upi"
    today = _now_utc().date()
    duration_days = getattr(plan, plan_cols["duration"].name) if plan_cols["duration"] is not None else 30
    end_date = today + timedelta(days=max(int(duration_days or 30) - 1, 0))

    active_subscriptions = UserSubs.query.filter(user_fk == user_id)
    if status_col is not None:
        active_subscriptions = active_subscriptions.filter(status_col == "active")
    for existing_subscription in active_subscriptions.all():
        if status_col is not None:
            setattr(existing_subscription, status_col.name, "replaced")
        if end_col is not None:
            setattr(existing_subscription, end_col.name, today)

    status_value = "active"
    data: Dict[str, Any] = {user_fk.name: user_id, plan_col.name: plan_id_int}
    if status_col is not None:
        data[status_col.name] = status_value
    if start_col is not None:
        data[start_col.name] = today
    if end_col is not None and end_col.name not in data:
        data[end_col.name] = end_date

    try:
        sub = UserSubs(**data)
        db.session.add(sub)
        db.session.flush()

        transaction_cols = _transaction_columns(Transactions)
        transaction_user_fk_cols = transaction_cols["user_fk_cols"]
        transaction_sub_fk_cols = transaction_cols["sub_fk_cols"]
        if transaction_user_fk_cols and transaction_sub_fk_cols:
            transaction_data: Dict[str, Any] = {
                transaction_user_fk_cols[0].name: user_id,
                transaction_sub_fk_cols[0].name: getattr(sub, sub_cols["pk"].name),
            }
            if transaction_cols["amount"] is not None and plan_cols["price"] is not None:
                transaction_data[transaction_cols["amount"].name] = getattr(plan, plan_cols["price"].name)
            if transaction_cols["method"] is not None:
                transaction_data[transaction_cols["method"].name] = payment_method
            if transaction_cols["date"] is not None:
                transaction_data[transaction_cols["date"].name] = _now_utc()
            if transaction_cols["status"] is not None:
                transaction_data[transaction_cols["status"].name] = "completed"
            db.session.add(Transactions(**transaction_data))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Subscription failed: {e}", status_code=500)

    return api_response(
        ok=True,
        data=_serialize_subscription_with_plan(sub, plan),
        message=f"Subscribed to {getattr(plan, plan_cols['name'].name) if plan_cols['name'] is not None else 'plan'}",
    )


def subscription_status(req: Request):
    Plans = get_model("subscription_plans")
    UserSubs = get_model("user_subscriptions")
    user_id = current_user_id()
    sub_cols = _subscription_columns(UserSubs)
    pk = sub_cols["pk"]

    user_fk_cols = sub_cols["user_fk_cols"]
    if not user_fk_cols:
        return api_response(ok=False, message="user_subscriptions must reference users", status_code=500)
    user_fk = user_fk_cols[0]

    order_col = sub_cols["start"]
    if order_col is None:
        order_col = pk

    status_col = sub_cols["status"]
    end_col = sub_cols["end"]
    plan_col = sub_cols["plan_fk_cols"][0] if sub_cols["plan_fk_cols"] else find_column(UserSubs, ["plan_id"], required=False)

    latest = (
        UserSubs.query.filter(user_fk == user_id)
        .order_by(order_col.desc())
        .first()
    )
    if not latest:
        free_payload = _free_plan_payload()
        return api_response(
            ok=True,
            data={
                "subscribed": False,
                "status": "free",
                "active_plan": "Free",
                "subscription": free_payload,
            },
        )

    status_val = getattr(latest, status_col.name) if status_col is not None else None
    if end_col is not None and getattr(latest, end_col.name) is not None and getattr(latest, end_col.name) < _now_utc().date():
        status_val = "expired"

    plan = None
    if plan_col is not None:
        plan = Plans.query.filter(primary_key_column(Plans) == getattr(latest, plan_col.name)).first()

    subscription_payload = _serialize_subscription_with_plan(latest, plan)
    active_plan_name = subscription_payload.get("plan_name") or "Free"
    return api_response(
        ok=True,
        data={
            "subscribed": status_val == "active",
            "status": status_val,
            "active_plan": active_plan_name,
            "subscription": subscription_payload,
        },
    )

