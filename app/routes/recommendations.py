from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.recommendations_controller import list_recommendations


bp = Blueprint("recommendations", __name__, url_prefix="")


@bp.get("/recommendations")
@jwt_required()
def recommendations_route():
    return list_recommendations(request)

