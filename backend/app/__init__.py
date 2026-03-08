import os
import logging
from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, jwt, migrate, cors, limiter

logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Fix Railway's postgres:// → postgresql://
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("postgres://"):
        app.config["SQLALCHEMY_DATABASE_URI"] = uri.replace(
            "postgres://", "postgresql://", 1
        )

    # Verify JWT secret strength in production
    if os.getenv("FLASK_ENV") == "production":
        jwt_key = app.config.get("JWT_SECRET_KEY", "")
        if len(jwt_key) < 32:
            raise RuntimeError("JWT_SECRET_KEY must be at least 256 bits (32 chars) in production")

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    limiter.init_app(app)

    from app.routes import register_routes
    register_routes(app)

    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # Global error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Requête invalide", "details": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Ressource non trouvée"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Méthode non autorisée"}), 405

    @app.errorhandler(429)
    def ratelimit_exceeded(e):
        return jsonify({"error": "Trop de requêtes, veuillez patienter"}), 429

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Erreur interne: {e}", exc_info=True)
        return jsonify({"error": "Erreur interne du serveur"}), 500

    @app.route("/health")
    def health():
        return {"status": "ok", "app": "Mekano"}

    return app
