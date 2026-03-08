from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from app.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email et mot de passe requis"}), 400

    user = User.query.filter_by(email=data["email"], actif=True).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Identifiants invalides"}), 401

    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "user_id": user.id,
            "garage_id": user.garage_id,
            "role": user.role,
            "email": user.email,
        },
    )

    return jsonify({
        "access_token": token,
        "user": user.to_dict(),
        "garage": user.garage.to_dict(),
    })
