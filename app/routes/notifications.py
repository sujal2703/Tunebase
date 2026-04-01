from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.notifications_controller import list_notifications


bp = Blueprint("notifications", __name__, url_prefix="")


@bp.get("/notifications")
@jwt_required()
def notifications_route():
    return list_notifications(request)

