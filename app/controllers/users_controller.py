from __future__ import annotations

from typing import Any, Dict

from flask import Request

from app.controllers.common import current_user_id, get_model
from app.extensions import db, bcrypt
from app.utils.http import api_response
from app.utils.serialization import row_to_dict
from app.utils.schema_introspection import find_column, find_foreign_key_columns_referencing


def get_profile(req: Request):
    Users = get_model("users")
    user_id = current_user_id()
    pk_col = find_column(Users, ["id", "user_id"], required=True)

    user = Users.query.filter(pk_col == user_id).first()
    if not user:
        return api_response(ok=False, message="User not found", status_code=404)
    data = row_to_dict(user)
    # Never expose password hash.
    data.pop("password", None)
    return api_response(ok=True, data=data)


def update_profile(req: Request):
    Users = get_model("users")
    Authentication = get_model("authentication")
    user_id = current_user_id()
    payload: Dict[str, Any] = req.get_json(silent=True) or {}

    pk_col = find_column(Users, ["id", "user_id"], required=True)
    password_col = find_column(
        Authentication,
        ["password_hash", "password", "hashed_password", "pass_hash", "passworddigest"],
        required=False,
    )
    user_password_col = find_column(
        Users,
        ["password", "password_hash", "hashed_password", "pass_hash", "passworddigest"],
        required=False,
    )

    user = Users.query.filter(pk_col == user_id).first()
    if not user:
        return api_response(ok=False, message="User not found", status_code=404)

    auth_user_fk_cols = find_foreign_key_columns_referencing(Authentication, "users")
    auth_record = None
    if auth_user_fk_cols and password_col is not None:
        auth_record = Authentication.query.filter(auth_user_fk_cols[0] == user_id).first()

    # Update only safe fields.
    allowed_cols = set()
    name_col = find_column(Users, ["name"], required=False)
    email_col = find_column(Users, ["email", "email_address", "user_email"], required=False)
    if name_col is not None:
        allowed_cols.add(name_col.name)
    if email_col is not None:
        allowed_cols.add(email_col.name)

    updated_at_col = find_column(Users, ["updated_at"], required=False)
    updated = False
    for key, value in payload.items():
        # Exact column match first; also accept common aliases.
        col = None
        if key in allowed_cols:
            col = user.__table__.columns[key]
        else:
            normalized = key.lower()
            if normalized in {"name", "full_name"} and name_col is not None:
                col = user.__table__.columns[name_col.name]
            elif normalized in {"email", "user_email", "email_address"} and email_col is not None:
                col = user.__table__.columns[email_col.name]
            elif normalized in {"password", "new_password"} and password_col is not None:
                col = password_col

        if col is None:
            continue
        if col.primary_key:
            continue

        if password_col is not None and col.name == password_col.name:
            if isinstance(value, str) and value and auth_record is not None:
                hashed_password = bcrypt.generate_password_hash(value).decode("utf-8")
                setattr(auth_record, col.name, hashed_password)
                if user_password_col is not None:
                    setattr(user, user_password_col.name, hashed_password)
                updated = True
            continue

        setattr(user, col.name, value)
        updated = True

    if updated and updated_at_col is not None:
        setattr(user, updated_at_col.name, db.func.now())

    if not updated:
        return api_response(ok=False, message="No updatable fields provided", status_code=400)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Update failed: {e}", status_code=500)

    data = row_to_dict(user)
    data.pop("password", None)
    return api_response(ok=True, data=data)

