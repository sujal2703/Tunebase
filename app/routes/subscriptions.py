from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.subscriptions_controller import list_plans, subscribe_to_plan, subscription_status


bp = Blueprint("subscriptions", __name__, url_prefix="")


@bp.get("/plans")
@jwt_required()
def plans_route():
    # Viewing plans typically doesn't need auth, but protected matches requirement.
    return list_plans(request)


@bp.post("/subscriptions")
@jwt_required()
def subscribe_route():
    return subscribe_to_plan(request)


@bp.get("/subscriptions/status")
@jwt_required()
def status_route():
    return subscription_status(request)

