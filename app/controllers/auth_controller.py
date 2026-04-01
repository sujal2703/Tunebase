from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from flask import Request
from flask_jwt_extended import create_access_token

from app.controllers.common import get_model
from app.extensions import bcrypt, db
from app.utils.http import api_response
from app.utils.schema_introspection import find_column, find_foreign_key_columns_referencing, primary_key_column


def _now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def register(req: Request):
    """
    POST /auth/register
    Body: { "username": "...", "email": "...", "password": "..." }
    """
    Users = get_model("users")
    Authentication = get_model("authentication")
    Plans = get_model("subscription_plans")
    UserSubscriptions = get_model("user_subscriptions")
    payload = req.get_json(silent=True) or {}

    # Schema uses `name`, but callers may send `username`.
    name = payload.get("name") or payload.get("username")
    email = payload.get("email")
    password = payload.get("password")
    if not password:
        return api_response(ok=False, message="Password is required", status_code=400)
    if not email:
        return api_response(ok=False, message="`email` is required", status_code=400)

    pk_col = find_column(Users, ["id", "user_id"], required=True)
    email_col = find_column(Users, ["email", "email_address", "user_email"], required=False)
    name_col = find_column(Users, ["name", "full_name"], required=False)
    users_password_col = find_column(
        Users,
        ["password", "password_hash", "hashed_password", "pass_hash", "passworddigest"],
        required=False,
    )
    created_at_col = find_column(Users, ["created_at", "signup_date", "created"], required=False)
    updated_at_col = find_column(Users, ["updated_at"], required=False)

    auth_user_fk_cols = find_foreign_key_columns_referencing(Authentication, "users")
    if not auth_user_fk_cols:
        return api_response(ok=False, message="authentication table must reference users", status_code=500)
    auth_user_fk = auth_user_fk_cols[0]
    auth_password_col = find_column(
        Authentication,
        ["password_hash", "password", "hashed_password", "pass_hash", "passworddigest"],
        required=True,
    )
    auth_status_col = find_column(Authentication, ["account_status", "status"], required=False)
    auth_failed_attempts_col = find_column(Authentication, ["failed_attempts"], required=False)
    plan_name_col = find_column(Plans, ["plan_name", "name", "title"], required=False)
    free_plan = Plans.query.filter(plan_name_col == "Free").first() if plan_name_col is not None else None

    # Ensure we have a way to uniquely identify the account
    if email_col is None:
        return api_response(
            ok=False,
            message="User table must have an `email` column.",
            status_code=400,
        )
    if name_col is not None and not name:
        return api_response(ok=False, message="`name` is required", status_code=400)

    # Uniqueness checks (best-effort)
    try:
        existing_q = None
        if email_col is not None and email:
            existing_q = Users.query.filter(email_col == email).first()
        # Email is UNIQUE, so this is sufficient for uniqueness checks.
        if existing_q:
            return api_response(ok=False, message="User already exists", status_code=409)
    except Exception as e:
        return api_response(ok=False, message=f"User lookup failed: {e}", status_code=400)

    pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    data: Dict[str, Any] = {}
    if name_col is not None and name:
        data[name_col.name] = name
    if email_col is not None and email:
        data[email_col.name] = email
    if users_password_col is not None:
        data[users_password_col.name] = pw_hash
    if created_at_col is not None:
        data[created_at_col.name] = _now_utc()
    if updated_at_col is not None:
        data[updated_at_col.name] = _now_utc()

    try:
        user = Users(**data)
        db.session.add(user)
        db.session.flush()

        auth_data: Dict[str, Any] = {
            auth_user_fk.name: getattr(user, pk_col.name),
            auth_password_col.name: pw_hash,
        }
        if auth_status_col is not None:
            auth_data[auth_status_col.name] = "active"
        if auth_failed_attempts_col is not None:
            auth_data[auth_failed_attempts_col.name] = 0

        db.session.add(Authentication(**auth_data))

        if free_plan is not None:
            sub_user_fk_cols = find_foreign_key_columns_referencing(UserSubscriptions, "users")
            sub_plan_fk_cols = find_foreign_key_columns_referencing(UserSubscriptions, "subscription_plans")
            if sub_user_fk_cols and sub_plan_fk_cols:
                sub_start_col = find_column(UserSubscriptions, ["start_date", "started_at"], required=False)
                sub_end_col = find_column(UserSubscriptions, ["end_date", "ends_at"], required=False)
                sub_status_col = find_column(UserSubscriptions, ["status", "subscription_status"], required=False)
                free_sub_data: Dict[str, Any] = {
                    sub_user_fk_cols[0].name: getattr(user, pk_col.name),
                    sub_plan_fk_cols[0].name: getattr(free_plan, primary_key_column(Plans).name),
                }
                if sub_start_col is not None:
                    free_sub_data[sub_start_col.name] = _now_utc().date()
                if sub_end_col is not None:
                    free_sub_data[sub_end_col.name] = _now_utc().date() + timedelta(days=30)
                if sub_status_col is not None:
                    free_sub_data[sub_status_col.name] = "free"
                db.session.add(UserSubscriptions(**free_sub_data))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return api_response(ok=False, message=f"Registration failed: {e}", status_code=500)

    token = create_access_token(identity=str(getattr(user, pk_col.name)))
    return api_response(ok=True, data={"access_token": token, "user_id": getattr(user, pk_col.name)})


def _ensure_device_for_user(user_id: int, device_identifier: str, device_name: Optional[str], platform: Optional[str]):
    Devices = get_model("devices")
    devices_user_fk_cols = find_foreign_key_columns_referencing(Devices, "users")
    if not devices_user_fk_cols:
        raise RuntimeError("Devices table must have a foreign key referencing users.")
    devices_user_fk = devices_user_fk_cols[0]

    # Schema uses `device_name` as the identifier.
    identifier_col = find_column(Devices, ["device_name"], required=True)
    last_active_col = find_column(Devices, ["last_active", "created_at", "inserted_at", "created"], required=False)
    device_type_col = find_column(Devices, ["device_type", "platform"], required=False)

    existing = Devices.query.filter(
        devices_user_fk == user_id,
        identifier_col == device_identifier,
    ).first()
    if existing:
        return existing

    data: Dict[str, Any] = {
        devices_user_fk.name: user_id,
        identifier_col.name: device_identifier,
    }
    # `device_name` is already stored as the identifier. Extra fields are ignored if they don't exist.
    if last_active_col is not None:
        data[last_active_col.name] = _now_utc()
    if device_type_col is not None and platform:
        data[device_type_col.name] = platform

    device = Devices(**data)
    db.session.add(device)
    db.session.commit()
    return device


def _create_session(user_id: int, device_id: int):
    Sessions = get_model("sessions")

    device_fk_cols = find_foreign_key_columns_referencing(Sessions, "devices")
    if not device_fk_cols:
        raise RuntimeError("Sessions table must have a foreign key referencing devices.")
    device_fk = device_fk_cols[0]

    login_time_col = find_column(
        Sessions,
        ["login_time", "started_at", "created_at", "created", "session_start", "inserted_at"],
        required=False,
    )
    if login_time_col is None:
        raise RuntimeError("Sessions table must have a `login_time` column.")

    user_fk_cols = find_foreign_key_columns_referencing(Sessions, "users")
    data: Dict[str, Any] = {device_fk.name: device_id, login_time_col.name: _now_utc()}
    if user_fk_cols:
        data[user_fk_cols[0].name] = user_id

    status_col = find_column(Sessions, ["status"], required=False)
    if status_col is not None:
        data[status_col.name] = "active"

    session = Sessions(**data)
    db.session.add(session)
    db.session.commit()
    return session


def login(req: Request):
    """
    POST /auth/login
    Body: { "email": "...", "username": "...", "password": "...", "device_identifier": "...", ... }
    """
    Users = get_model("users")
    Authentication = get_model("authentication")
    payload = req.get_json(silent=True) or {}

    password = payload.get("password")
    if not password:
        return api_response(ok=False, message="Password is required", status_code=400)

    pk_col = find_column(Users, ["id", "user_id"], required=True)
    email_col = find_column(Users, ["email", "email_address", "user_email"], required=False)
    name_col = find_column(Users, ["name", "full_name"], required=False)
    users_password_col = find_column(
        Users,
        ["password", "password_hash", "hashed_password", "pass_hash", "passworddigest"],
        required=False,
    )

    # Decide which identifier to use
    user = None
    identifier_value = None
    identifier_type = None
    if email_col is not None and payload.get("email"):
        identifier_value = payload.get("email")
        identifier_type = "email"
        user = Users.query.filter(email_col == identifier_value).first()
    elif name_col is not None and (payload.get("name") or payload.get("username")):
        identifier_value = payload.get("name") or payload.get("username")
        identifier_type = "name"
        user = Users.query.filter(name_col == identifier_value).first()
    else:
        return api_response(ok=False, message="Provide `email` or `name`", status_code=400)

    if not user:
        return api_response(ok=False, message="Invalid credentials", status_code=401)

    auth_user_fk_cols = find_foreign_key_columns_referencing(Authentication, "users")
    if not auth_user_fk_cols:
        return api_response(ok=False, message="authentication table must reference users", status_code=500)

    auth_user_fk = auth_user_fk_cols[0]
    password_col = find_column(
        Authentication,
        ["password_hash", "password", "hashed_password", "pass_hash", "passworddigest"],
        required=True,
    )
    auth_record = Authentication.query.filter(auth_user_fk == getattr(user, pk_col.name)).first()
    if not auth_record:
        return api_response(ok=False, message="Invalid credentials", status_code=401)

    stored_password = getattr(auth_record, password_col.name)
    if stored_password is None and users_password_col is not None:
        stored_password = getattr(user, users_password_col.name)
    if stored_password is None:
        return api_response(ok=False, message="Invalid credentials", status_code=401)

    # If your DB already contains plaintext passwords (your initial seed), allow a
    # one-time compatibility fallback; newly registered users are bcrypt-hashed.
    is_bcrypt_hash = isinstance(stored_password, str) and stored_password.startswith("$2")
    if is_bcrypt_hash:
        try:
            if not bcrypt.check_password_hash(stored_password, password):
                return api_response(ok=False, message="Invalid credentials", status_code=401)
        except Exception:
            return api_response(ok=False, message="Invalid credentials", status_code=401)
    else:
        if str(stored_password) != str(password):
            return api_response(ok=False, message="Invalid credentials", status_code=401)

    last_login_col = find_column(Authentication, ["last_login"], required=False)
    if last_login_col is not None:
        setattr(auth_record, last_login_col.name, _now_utc())
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    user_id = int(getattr(user, pk_col.name))

    # Device + session tracking: schema uses `devices.device_name`.
    device_identifier = payload.get("device_identifier") or payload.get("device_name") or payload.get("identifier")
    device_name = payload.get("device_name")
    platform = payload.get("platform")

    try:
        device_id = None
        if not device_identifier:
            return api_response(ok=False, message="`device_identifier` (device name) is required", status_code=400)

        device = _ensure_device_for_user(
            user_id=user_id,
            device_identifier=device_identifier,
            device_name=device_name,
            platform=platform,
        )
        device_pk_col = primary_key_column(get_model("devices"))
        device_id = int(getattr(device, device_pk_col.name))
        _create_session(user_id=user_id, device_id=device_id)
    except Exception as e:
        # Auth succeeded; don't fail login solely due to session/device tracking.
        from flask import current_app

        current_app.logger.warning("Session/device tracking failed: %s", e)

    access_token = create_access_token(identity=str(user_id))
    return api_response(
        ok=True,
        data={"access_token": access_token, "user_id": user_id, "identifier_type": identifier_type},
    )

