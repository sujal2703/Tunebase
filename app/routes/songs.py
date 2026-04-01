from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.songs_controller import get_song, list_songs, like_song, play_song


bp = Blueprint("songs", __name__, url_prefix="")


@bp.get("/songs")
@jwt_required()
def songs_list_route():
    return list_songs(request)


@bp.get("/songs/<song_id>")
@jwt_required()
def songs_get_route(song_id: str):
    return get_song(request, song_id)


@bp.post("/songs/<song_id>/like")
@jwt_required()
def songs_like_route(song_id: str):
    return like_song(request, song_id)


@bp.post("/songs/<song_id>/play")
@jwt_required()
def songs_play_route(song_id: str):
    return play_song(request, song_id)

