from flask import Blueprint

api = Blueprint("api", __name__, url_prefix="/api")


def register_routes(app):
    from app.routes.auth import auth_bp
    from app.routes.clients import clients_bp
    from app.routes.vehicules import vehicules_bp
    from app.routes.ordres import ordres_bp

    api.register_blueprint(auth_bp)
    api.register_blueprint(clients_bp)
    api.register_blueprint(vehicules_bp)
    api.register_blueprint(ordres_bp)
    app.register_blueprint(api)
