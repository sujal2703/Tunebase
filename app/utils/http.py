from __future__ import annotations

from typing import Any, Dict, Optional

from flask import jsonify
from werkzeug.exceptions import HTTPException


def api_response(*, ok: bool, data: Any = None, message: Optional[str] = None, status_code: int = 200):
    payload: Dict[str, Any] = {"ok": ok}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def http_error_to_json(err: HTTPException):
    return api_response(ok=False, message=getattr(err, "description", str(err)), status_code=err.code or 500)

