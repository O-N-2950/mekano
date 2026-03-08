from flask import Blueprint, jsonify, request, g
from app.extensions import db
from app.models.client import Client
from app.middleware.tenant import tenant_required
from app.utils.validation import validate_required, validate_email, parse_date

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")


@clients_bp.route("", methods=["GET"])
@tenant_required
def list_clients():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    search = request.args.get("search", "", type=str).strip()

    query = Client.query.filter_by(garage_id=g.garage_id, actif=True)

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Client.nom.ilike(like),
                Client.prenom.ilike(like),
                Client.email.ilike(like),
                Client.telephone.ilike(like),
                Client.entreprise.ilike(like),
            )
        )

    query = query.order_by(Client.nom, Client.prenom)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [c.to_dict() for c in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@clients_bp.route("", methods=["POST"])
@tenant_required
def create_client():
    data = request.get_json() or {}

    errors = validate_required(data, ["nom", "prenom"])
    if data.get("email") and not validate_email(data["email"]):
        errors["email"] = "Format email invalide"
    if errors:
        return jsonify({"errors": errors}), 422

    client = Client(
        garage_id=g.garage_id,
        prenom=data["prenom"].strip(),
        nom=data["nom"].strip(),
        entreprise=data.get("entreprise", "").strip() or None,
        adresse=data.get("adresse", "").strip() or None,
        npa=data.get("npa", "").strip() or None,
        localite=data.get("localite", "").strip() or None,
        telephone=data.get("telephone", "").strip() or None,
        email=data.get("email", "").strip() or None,
        date_naissance=parse_date(data.get("date_naissance")),
        notes=data.get("notes", "").strip() or None,
    )
    db.session.add(client)
    db.session.commit()
    return jsonify(client.to_dict()), 201


@clients_bp.route("/<int:client_id>", methods=["GET"])
@tenant_required
def get_client(client_id):
    client = Client.query.filter_by(id=client_id, garage_id=g.garage_id, actif=True).first()
    if not client:
        return jsonify({"error": "Client non trouve"}), 404
    return jsonify(client.to_dict())


@clients_bp.route("/<int:client_id>", methods=["PUT"])
@tenant_required
def update_client(client_id):
    client = Client.query.filter_by(id=client_id, garage_id=g.garage_id, actif=True).first()
    if not client:
        return jsonify({"error": "Client non trouve"}), 404

    data = request.get_json() or {}

    errors = validate_required(data, ["nom", "prenom"])
    if data.get("email") and not validate_email(data["email"]):
        errors["email"] = "Format email invalide"
    if errors:
        return jsonify({"errors": errors}), 422

    client.prenom = data["prenom"].strip()
    client.nom = data["nom"].strip()
    client.entreprise = data.get("entreprise", "").strip() or None
    client.adresse = data.get("adresse", "").strip() or None
    client.npa = data.get("npa", "").strip() or None
    client.localite = data.get("localite", "").strip() or None
    client.telephone = data.get("telephone", "").strip() or None
    client.email = data.get("email", "").strip() or None
    client.date_naissance = parse_date(data.get("date_naissance"))
    client.notes = data.get("notes", "").strip() or None

    db.session.commit()
    return jsonify(client.to_dict())


@clients_bp.route("/<int:client_id>", methods=["DELETE"])
@tenant_required
def delete_client(client_id):
    client = Client.query.filter_by(id=client_id, garage_id=g.garage_id, actif=True).first()
    if not client:
        return jsonify({"error": "Client non trouve"}), 404

    client.actif = False
    db.session.commit()
    return jsonify({"message": "Client supprime"})
