from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required
from app.extensions import db, limiter
from app.models.devis import Devis, LigneDevis
from app.models.client import Client
from app.models.vehicule import Vehicule
from app.middleware.tenant import tenant_required
from app.utils.pdf_devis import generate_devis_pdf
from datetime import datetime, timezone, timedelta
import io
import logging

logger = logging.getLogger(__name__)
devis_bp = Blueprint("devis", __name__, url_prefix="/devis")


def _next_numero(garage_id):
    year = datetime.now().year
    count = Devis.query.filter(
        Devis.garage_id == garage_id,
        db.extract("year", Devis.date_creation) == year
    ).count()
    return f"DEV-{year}-{count + 1:03d}"


@devis_bp.get("")
@jwt_required()
@tenant_required
@limiter.limit("60/minute")
def list_devis(garage_id):
    statut = request.args.get("statut")
    client_id = request.args.get("client_id")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))

    q = Devis.query.filter_by(garage_id=garage_id)
    if statut:
        q = q.filter_by(statut=statut)
    if client_id:
        q = q.filter_by(client_id=client_id)

    q = q.order_by(Devis.created_at.desc())
    paginated = q.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "items": [d.to_dict() for d in paginated.items],
        "total": paginated.total,
        "page": page,
        "pages": paginated.pages,
    })


@devis_bp.post("")
@jwt_required()
@tenant_required
@limiter.limit("20/minute")
def create_devis(garage_id):
    data = request.get_json() or {}

    client_id = data.get("client_id")
    if not client_id:
        return jsonify({"error": "client_id requis"}), 400
    client = Client.query.filter_by(id=client_id, garage_id=garage_id).first()
    if not client:
        return jsonify({"error": "Client introuvable"}), 404

    validite = datetime.now(timezone.utc) + timedelta(days=30)

    devis = Devis(
        garage_id=garage_id,
        client_id=client_id,
        vehicule_id=data.get("vehicule_id"),
        numero=_next_numero(garage_id),
        statut="brouillon",
        vehicule_km=data.get("vehicule_km"),
        date_validite=validite,
        petites_fournitures_pct=data.get("petites_fournitures_pct", 4.0),
        taux_tva=data.get("taux_tva", 8.1),
        notes_client=data.get("notes_client", "")[:3000],
        conditions=data.get("conditions", ""),
    )
    db.session.add(devis)
    db.session.flush()

    for i, l in enumerate(data.get("lignes", [])):
        ligne = LigneDevis(
            devis_id=devis.id,
            ordre=i,
            type=l.get("type", "piece"),
            reference=(l.get("reference") or "")[:100],
            designation=(l.get("designation") or "")[:300],
            quantite=l.get("quantite", 1),
            prix_unitaire=l.get("prix_unitaire", 0),
            remise_pct=l.get("remise_pct", 0),
        )
        db.session.add(ligne)

    db.session.flush()
    devis.recalculer()
    db.session.commit()
    logger.info(f"[AUDIT] Devis créé: {devis.numero} garage={garage_id}")
    return jsonify(devis.to_dict()), 201


@devis_bp.get("/<int:devis_id>")
@jwt_required()
@tenant_required
@limiter.limit("60/minute")
def get_devis(garage_id, devis_id):
    d = Devis.query.filter_by(id=devis_id, garage_id=garage_id).first_or_404()
    return jsonify(d.to_dict())


@devis_bp.put("/<int:devis_id>")
@jwt_required()
@tenant_required
@limiter.limit("20/minute")
def update_devis(garage_id, devis_id):
    d = Devis.query.filter_by(id=devis_id, garage_id=garage_id).first_or_404()
    if d.statut not in ("brouillon", "envoye"):
        return jsonify({"error": "Devis non modifiable dans cet état"}), 400

    data = request.get_json() or {}

    if "client_id" in data:
        c = Client.query.filter_by(id=data["client_id"], garage_id=garage_id).first()
        if not c:
            return jsonify({"error": "Client introuvable"}), 404
        d.client_id = data["client_id"]

    if "vehicule_id" in data:
        d.vehicule_id = data["vehicule_id"]
    if "vehicule_km" in data:
        d.vehicule_km = data["vehicule_km"]
    if "petites_fournitures_pct" in data:
        d.petites_fournitures_pct = data["petites_fournitures_pct"]
    if "taux_tva" in data:
        d.taux_tva = data["taux_tva"]
    if "notes_client" in data:
        d.notes_client = (data["notes_client"] or "")[:3000]
    if "conditions" in data:
        d.conditions = data["conditions"]

    if "lignes" in data:
        LigneDevis.query.filter_by(devis_id=d.id).delete()
        for i, l in enumerate(data["lignes"]):
            ligne = LigneDevis(
                devis_id=d.id,
                ordre=i,
                type=l.get("type", "piece"),
                reference=(l.get("reference") or "")[:100],
                designation=(l.get("designation") or "")[:300],
                quantite=l.get("quantite", 1),
                prix_unitaire=l.get("prix_unitaire", 0),
                remise_pct=l.get("remise_pct", 0),
            )
            db.session.add(ligne)
        db.session.flush()

    d.recalculer()
    d.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    logger.info(f"[AUDIT] Devis modifié: {d.numero} garage={garage_id}")
    return jsonify(d.to_dict())


@devis_bp.patch("/<int:devis_id>/statut")
@jwt_required()
@tenant_required
@limiter.limit("20/minute")
def change_statut(garage_id, devis_id):
    d = Devis.query.filter_by(id=devis_id, garage_id=garage_id).first_or_404()
    data = request.get_json() or {}
    nouveau = data.get("statut")
    valides = ["brouillon", "envoye", "accepte", "refuse", "expire"]
    if nouveau not in valides:
        return jsonify({"error": f"Statut invalide. Valeurs: {valides}"}), 400
    d.statut = nouveau
    db.session.commit()
    logger.info(f"[AUDIT] Devis statut: {d.numero} → {nouveau} garage={garage_id}")
    return jsonify(d.to_dict())


@devis_bp.post("/<int:devis_id>/dupliquer")
@jwt_required()
@tenant_required
@limiter.limit("20/minute")
def dupliquer_devis(garage_id, devis_id):
    original = Devis.query.filter_by(id=devis_id, garage_id=garage_id).first_or_404()
    validite = datetime.now(timezone.utc) + timedelta(days=30)

    copie = Devis(
        garage_id=garage_id,
        client_id=original.client_id,
        vehicule_id=original.vehicule_id,
        numero=_next_numero(garage_id),
        statut="brouillon",
        vehicule_km=original.vehicule_km,
        date_validite=validite,
        petites_fournitures_pct=original.petites_fournitures_pct,
        taux_tva=original.taux_tva,
        notes_client=original.notes_client,
        conditions=original.conditions,
    )
    db.session.add(copie)
    db.session.flush()

    for l in original.lignes:
        nl = LigneDevis(
            devis_id=copie.id,
            ordre=l.ordre,
            type=l.type,
            reference=l.reference,
            designation=l.designation,
            quantite=l.quantite,
            prix_unitaire=l.prix_unitaire,
            remise_pct=l.remise_pct,
        )
        db.session.add(nl)

    db.session.flush()
    copie.recalculer()
    db.session.commit()
    return jsonify(copie.to_dict()), 201


@devis_bp.get("/<int:devis_id>/pdf")
@jwt_required()
@tenant_required
def get_pdf(garage_id, devis_id):
    from app.models.garage import Garage
    d = Devis.query.filter_by(id=devis_id, garage_id=garage_id).first_or_404()
    garage = Garage.query.get(garage_id)
    pdf_bytes = generate_devis_pdf(d, garage)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{d.numero}.pdf"
    )
