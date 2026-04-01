from __future__ import annotations

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.controllers.transactions_controller import list_transactions, record_transaction


bp = Blueprint("transactions", __name__, url_prefix="/transactions")


@bp.post("")
@jwt_required()
def record_transaction_route():
    return record_transaction(request)


@bp.get("")
@jwt_required()
def transactions_history_route():
    return list_transactions(request)

