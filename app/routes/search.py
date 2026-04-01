from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.search_controller import (
    clear_search_history,
    delete_search_history_item,
    search,
    search_history,
)


bp = Blueprint("search", __name__, url_prefix="")


@bp.post("/search")
@jwt_required()
def search_route():
    return search(request)


@bp.get("/search/history")
@jwt_required()
def search_history_route():
    return search_history(request)


@bp.delete("/search/history")
@jwt_required()
def clear_search_history_route():
    return clear_search_history(request)


@bp.delete("/search/history/<int:search_id>")
@jwt_required()
def delete_search_history_item_route(search_id: int):
    return delete_search_history_item(search_id)

