from flask import Blueprint, jsonify, request, g
from app.extensions import db
from app.models.vehicule import Vehicule
from app.models.client import Client
from app.middleware.tenant import tenant_required
from app.utils.validation import validate_required, validate_plaque_ch, parse_date

vehicules_bp = Blueprint("vehicules", __name__, url_prefix="/vehicules")


@vehicules_bp.route("", methods=["GET"])
@tenant_required
def list_vehicules():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    client_id = request.args.get("client_id", type=int)
    search = request.args.get("search", "", type=str).strip()

    query = Vehicule.query.filter_by(garage_id=g.garage_id, actif=True)

    if client_id:
        query = query.filter_by(client_id=client_id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(
                Vehicule.marque.ilike(like),
                Vehicule.modele.ilike(like),
                Vehicule.plaque.ilike(like),
                Vehicule.vin.ilike(like),
            )
        )

    query = query.order_by(Vehicule.marque, Vehicule.modele)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [v.to_dict_full() for v in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@vehicules_bp.route("", methods=["POST"])
@tenant_required
def create_vehicule():
    data = request.get_json() or {}

    errors = validate_required(data, ["client_id", "marque", "modele"])

    plaque = data.get("plaque", "").strip().upper()
    if plaque and not validate_plaque_ch(plaque):
        errors["plaque"] = "Format plaque CH invalide (ex: VD 345678)"

    client_id = data.get("client_id")
    if client_id:
        client = Client.query.filter_by(id=client_id, garage_id=g.garage_id, actif=True).first()
        if not client:
            errors["client_id"] = "Client non trouve"

    if errors:
        return jsonify({"errors": errors}), 422

    vehicule = Vehicule(
        garage_id=g.garage_id,
        client_id=client_id,
        vin=data.get("vin", "").strip().upper() or None,
        plaque=plaque or None,
        marque=data["marque"].strip(),
        modele=data["modele"].strip(),
        annee=data.get("annee", type=int) if isinstance(data.get("annee"), int) else (int(data["annee"]) if data.get("annee") else None),
        couleur=data.get("couleur", "").strip() or None,
        carburant=data.get("carburant", "").strip() or None,
        km_actuel=data.get("km_actuel"),
        date_mct=parse_date(data.get("date_mct")),
        notes=data.get("notes", "").strip() or None,
    )
    db.session.add(vehicule)
    db.session.commit()
    return jsonify(vehicule.to_dict_full()), 201


@vehicules_bp.route("/<int:vehicule_id>", methods=["GET"])
@tenant_required
def get_vehicule(vehicule_id):
    vehicule = Vehicule.query.filter_by(
        id=vehicule_id, garage_id=g.garage_id, actif=True
    ).first()
    if not vehicule:
        return jsonify({"error": "Vehicule non trouve"}), 404
    return jsonify(vehicule.to_dict_full())


@vehicules_bp.route("/<int:vehicule_id>", methods=["PUT"])
@tenant_required
def update_vehicule(vehicule_id):
    vehicule = Vehicule.query.filter_by(
        id=vehicule_id, garage_id=g.garage_id, actif=True
    ).first()
    if not vehicule:
        return jsonify({"error": "Vehicule non trouve"}), 404

    data = request.get_json() or {}

    errors = validate_required(data, ["marque", "modele"])
    plaque = data.get("plaque", "").strip().upper()
    if plaque and not validate_plaque_ch(plaque):
        errors["plaque"] = "Format plaque CH invalide (ex: VD 345678)"

    if errors:
        return jsonify({"errors": errors}), 422

    vehicule.vin = data.get("vin", "").strip().upper() or None
    vehicule.plaque = plaque or None
    vehicule.marque = data["marque"].strip()
    vehicule.modele = data["modele"].strip()
    vehicule.annee = int(data["annee"]) if data.get("annee") else None
    vehicule.couleur = data.get("couleur", "").strip() or None
    vehicule.carburant = data.get("carburant", "").strip() or None
    vehicule.km_actuel = data.get("km_actuel")
    vehicule.date_mct = parse_date(data.get("date_mct"))
    vehicule.notes = data.get("notes", "").strip() or None

    db.session.commit()
    return jsonify(vehicule.to_dict_full())
