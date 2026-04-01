from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from flask_limiter.util import get_remote_address

from app.controllers.auth_controller import login, register
from app.extensions import limiter


bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.post("/register")
@limiter.limit("10 per minute")
def register_route():
    return register(request)


@bp.post("/login")
@limiter.limit("20 per minute")
def login_route():
    return login(request)

