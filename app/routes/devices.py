from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.devices_controller import list_sessions, register_device


bp = Blueprint("devices", __name__, url_prefix="")


@bp.post("/devices")
@jwt_required()
def register_device_route():
    return register_device(request)


@bp.get("/sessions")
@jwt_required()
def sessions_route():
    return list_sessions(request)

