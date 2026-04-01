from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.downloads_controller import download_song, list_downloads


bp = Blueprint("downloads", __name__, url_prefix="")


@bp.post("/downloads")
@jwt_required()
def downloads_post():
    return download_song(request)


@bp.get("/downloads")
@jwt_required()
def downloads_get():
    return list_downloads(request)

