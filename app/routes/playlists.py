from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from flask_limiter import Limiter

from app.controllers.playlists_controller import add_song_to_playlist, create_playlist, list_user_playlists


bp = Blueprint("playlists", __name__, url_prefix="/playlists")


@bp.post("")
@jwt_required()
def playlists_create_route():
    return create_playlist(request)


@bp.get("")
@jwt_required()
def playlists_list_route():
    return list_user_playlists(request)


@bp.post("/<playlist_id>/songs")
@jwt_required()
def playlists_add_song_route(playlist_id: str):
    return add_song_to_playlist(request, playlist_id)

