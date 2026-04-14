from __future__ import annotations

from pathlib import Path
from typing import List

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from app.extensions import bcrypt, db, jwt, limiter
from config import Config
from config import configure_logging
from app.models import init_models
from app.utils.http import api_response, http_error_to_json
def _parse_rate_limits(value: str) -> List[str]:
    # Example: "200 per day;50 per hour"
    parts = [p.strip() for p in (value or "").split(";") if p.strip()]
    return parts


def create_app() -> Flask:
    configure_logging()
    app = Flask(__name__)
    app.config.from_object(Config)
    frontend_dist = Path(app.root_path).parent / "frontend" / "dist"

    # SQLAlchemy + JWT
    db.init_app(app)
    bcrypt.init_app(app)
    app.config["JWT_SECRET_KEY"] = Config.JWT_SECRET_KEY
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = Config.JWT_ACCESS_TOKEN_EXPIRES
    jwt.init_app(app)

    # Rate limiting
    app.config["RATELIMIT_STORAGE_URI"] = Config.RATELIMIT_STORAGE_URL
    limiter.default_limits = _parse_rate_limits(Config.RATE_LIMIT_DEFAULT)
    limiter.init_app(app)

    # Model reflection (maps existing tables)
    with app.app_context():
        try:
            init_models(db)
            app.logger.info("Reflected SQLAlchemy models from existing MySQL schema.")
        except Exception as e:
            app.logger.exception("Model reflection failed: %s", e)

    # Request logging
    @app.before_request
    def log_request():
        app.logger.info("%s %s", request.method, request.path)

    # Error handlers
    @app.errorhandler(HTTPException)
    def handle_http_exception(err: HTTPException):
        return http_error_to_json(err)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(err: Exception):
        app.logger.exception("Unhandled error: %s", err)
        return api_response(ok=False, message="Internal server error", status_code=500)

    # Register routes
    from app.routes.auth import bp as auth_bp
    from app.routes.users import bp as users_bp
    from app.routes.songs import bp as songs_bp
    from app.routes.playlists import bp as playlists_bp
    from app.routes.subscriptions import bp as subscriptions_bp
    from app.routes.transactions import bp as transactions_bp
    from app.routes.devices import bp as devices_bp
    from app.routes.recommendations import bp as recommendations_bp
    from app.routes.search import bp as search_bp
    from app.routes.notifications import bp as notifications_bp
    from app.routes.downloads import bp as downloads_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(songs_bp)
    app.register_blueprint(playlists_bp)
    app.register_blueprint(subscriptions_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(downloads_bp)

    @app.get("/")
    def frontend_index():
        if frontend_dist.exists():
            return send_from_directory(frontend_dist, "index.html")
        return jsonify(
            {
                "ok": True,
                "message": "Backend is running. Build the React frontend in /frontend to serve the web app.",
            }
        )

    @app.get("/<path:path>")
    def frontend_assets(path: str):
        candidate = frontend_dist / path
        if frontend_dist.exists() and candidate.exists() and candidate.is_file():
            return send_from_directory(frontend_dist, path)
        if frontend_dist.exists():
            return send_from_directory(frontend_dist, "index.html")
        return api_response(ok=False, message=f"Route /{path} not found", status_code=404)

    return app

