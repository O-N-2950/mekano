from flask import Blueprint, jsonify, request, g
from app.extensions import db
from app.models.ordre_travail import OrdreDeTravail, STATUTS_VALIDES
from app.models.vehicule import Vehicule
from app.models.client import Client
from app.middleware.tenant import tenant_required
from app.utils.validation import validate_required, parse_datetime
from datetime import datetime, timezone

ordres_bp = Blueprint("ordres", __name__, url_prefix="/ordres")


def _gen_numero(garage_id):
    year = datetime.now(timezone.utc).year
    last = (
        OrdreDeTravail.query
        .filter_by(garage_id=garage_id)
        .filter(OrdreDeTravail.numero.like(f"OT-{year}-%"))
        .order_by(OrdreDeTravail.id.desc())
        .first()
    )
    if last and last.numero:
        try:
            seq = int(last.numero.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"OT-{year}-{seq:03d}"


@ordres_bp.route("", methods=["GET"])
@tenant_required
def list_ordres():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 25, type=int)
    statut = request.args.get("statut", type=str)
    client_id = request.args.get("client_id", type=int)
    vehicule_id = request.args.get("vehicule_id", type=int)

    query = OrdreDeTravail.query.filter_by(garage_id=g.garage_id)

    if statut and statut in STATUTS_VALIDES:
        query = query.filter_by(statut=statut)
    if client_id:
        query = query.filter_by(client_id=client_id)
    if vehicule_id:
        query = query.filter_by(vehicule_id=vehicule_id)

    query = query.order_by(OrdreDeTravail.date_entree.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [o.to_dict_full() for o in pagination.items],
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
    })


@ordres_bp.route("", methods=["POST"])
@tenant_required
def create_ordre():
    data = request.get_json() or {}

    errors = validate_required(data, ["vehicule_id", "client_id", "description_travaux"])

    vehicule_id = data.get("vehicule_id")
    client_id = data.get("client_id")

    if vehicule_id:
        vehicule = Vehicule.query.filter_by(id=vehicule_id, garage_id=g.garage_id, actif=True).first()
        if not vehicule:
            errors["vehicule_id"] = "Vehicule non trouve"
    if client_id:
        client = Client.query.filter_by(id=client_id, garage_id=g.garage_id, actif=True).first()
        if not client:
            errors["client_id"] = "Client non trouve"

    if errors:
        return jsonify({"errors": errors}), 422

    ordre = OrdreDeTravail(
        garage_id=g.garage_id,
        vehicule_id=vehicule_id,
        client_id=client_id,
        numero=_gen_numero(g.garage_id),
        statut="ouvert",
        description_travaux=data["description_travaux"].strip(),
        km_entree=data.get("km_entree"),
        date_entree=parse_datetime(data.get("date_entree")) or datetime.now(timezone.utc),
        date_sortie_prevue=parse_datetime(data.get("date_sortie_prevue")),
        notes_internes=data.get("notes_internes", "").strip() or None,
    )
    db.session.add(ordre)
    db.session.commit()
    return jsonify(ordre.to_dict_full()), 201


@ordres_bp.route("/<int:ordre_id>", methods=["GET"])
@tenant_required
def get_ordre(ordre_id):
    ordre = OrdreDeTravail.query.filter_by(id=ordre_id, garage_id=g.garage_id).first()
    if not ordre:
        return jsonify({"error": "Ordre non trouve"}), 404
    return jsonify(ordre.to_dict_full())


@ordres_bp.route("/<int:ordre_id>", methods=["PUT"])
@tenant_required
def update_ordre(ordre_id):
    ordre = OrdreDeTravail.query.filter_by(id=ordre_id, garage_id=g.garage_id).first()
    if not ordre:
        return jsonify({"error": "Ordre non trouve"}), 404

    data = request.get_json() or {}
    errors = validate_required(data, ["description_travaux"])
    if errors:
        return jsonify({"errors": errors}), 422

    ordre.description_travaux = data["description_travaux"].strip()
    ordre.km_entree = data.get("km_entree")
    ordre.date_sortie_prevue = parse_datetime(data.get("date_sortie_prevue"))
    ordre.notes_internes = data.get("notes_internes", "").strip() or None

    db.session.commit()
    return jsonify(ordre.to_dict_full())


@ordres_bp.route("/<int:ordre_id>/statut", methods=["PATCH"])
@tenant_required
def change_statut(ordre_id):
    ordre = OrdreDeTravail.query.filter_by(id=ordre_id, garage_id=g.garage_id).first()
    if not ordre:
        return jsonify({"error": "Ordre non trouve"}), 404

    data = request.get_json() or {}
    nouveau = data.get("statut")

    if not nouveau or nouveau not in STATUTS_VALIDES:
        return jsonify({"error": f"Statut invalide. Valeurs: {', '.join(STATUTS_VALIDES)}"}), 422

    if not ordre.peut_transiter(nouveau):
        return jsonify({
            "error": f"Transition {ordre.statut} → {nouveau} non autorisee",
            "transitions_possibles": ordre.to_dict()["transitions_possibles"],
        }), 422

    ordre.statut = nouveau
    if nouveau == "termine":
        ordre.date_sortie = datetime.now(timezone.utc)

    db.session.commit()
    return jsonify(ordre.to_dict_full())
