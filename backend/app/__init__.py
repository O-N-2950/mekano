from flask import Flask
from app.config import Config
from app.extensions import db, jwt, migrate, cors


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Fix Railway's postgres:// → postgresql://
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if uri.startswith("postgres://"):
        app.config["SQLALCHEMY_DATABASE_URI"] = uri.replace(
            "postgres://", "postgresql://", 1
        )

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    from app.routes import register_routes
    register_routes(app)

    @app.route("/health")
    def health():
        return {"status": "ok", "app": "GarageNEO"}

    return app
