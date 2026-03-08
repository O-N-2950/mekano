import logging
from flask import Blueprint, jsonify, request, g
from app.extensions import db, limiter
from app.models.client import Client
from app.middleware.tenant import tenant_required
from app.utils.validation import validate_required, validate_email, parse_date

logger = logging.getLogger(__name__)

clients_bp = Blueprint("clients", __name__, url_prefix="/clients")

FIELD_MAX_LENGTHS = {
    "nom": 100, "prenom": 100, "entreprise": 200,
    "adresse": 300, "npa": 10, "localite": 100,
    "telephone": 30, "email": 254, "notes": 5000,
}


def validate_lengths(data):
    errors = {}
    for field, maxlen in FIELD_MAX_LENGTHS.items():
        val = data.get(field, "")
        if val and len(str(val)) > maxlen:
            errors[field] = f"Maximum {maxlen} caractères"
    return errors


@clients_bp.route("", methods=["GET"])
@tenant_required
@limiter.limit("60 per minute")
def list_clients():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 25, type=int), 100)
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
@limiter.limit("20 per minute")
def create_client():
    data = request.get_json() or {}

    errors = validate_required(data, ["nom", "prenom"])
    errors.update(validate_lengths(data))
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
    logger.info(f"Client créé: {client.id} par garage {g.garage_id}")
    return jsonify(client.to_dict()), 201


@clients_bp.route("/<int:client_id>", methods=["GET"])
@tenant_required
@limiter.limit("60 per minute")
def get_client(client_id):
    client = Client.query.filter_by(id=client_id, garage_id=g.garage_id, actif=True).first()
    if not client:
        return jsonify({"error": "Client non trouvé"}), 404
    return jsonify(client.to_dict())


@clients_bp.route("/<int:client_id>", methods=["PUT"])
@tenant_required
@limiter.limit("20 per minute")
def update_client(client_id):
    client = Client.query.filter_by(id=client_id, garage_id=g.garage_id, actif=True).first()
    if not client:
        return jsonify({"error": "Client non trouvé"}), 404

    data = request.get_json() or {}

    errors = validate_required(data, ["nom", "prenom"])
    errors.update(validate_lengths(data))
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
    logger.info(f"Client modifié: {client.id} par garage {g.garage_id}")
    return jsonify(client.to_dict())


@clients_bp.route("/<int:client_id>", methods=["DELETE"])
@tenant_required
def delete_client(client_id):
    client = Client.query.filter_by(id=client_id, garage_id=g.garage_id, actif=True).first()
    if not client:
        return jsonify({"error": "Client non trouvé"}), 404

    client.actif = False
    db.session.commit()
    logger.info(f"Client supprimé: {client.id} par garage {g.garage_id}")
    return jsonify({"message": "Client supprimé"})
