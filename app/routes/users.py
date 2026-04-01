from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.users_controller import get_profile, update_profile


bp = Blueprint("users", __name__, url_prefix="/users")


@bp.get("/me")
@jwt_required()
def me_get():
    return get_profile(request)


@bp.patch("/me")
@jwt_required()
def me_patch():
    return update_profile(request)

