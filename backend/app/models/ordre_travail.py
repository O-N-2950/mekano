from app.extensions import db
from datetime import datetime, timezone

STATUTS_VALIDES = ["ouvert", "en_cours", "termine", "facture"]
TRANSITIONS = {
    "ouvert": ["en_cours"],
    "en_cours": ["termine", "ouvert"],
    "termine": ["facture", "en_cours"],
    "facture": [],
}


class OrdreDeTravail(db.Model):
    __tablename__ = "ordres_travail"

    id = db.Column(db.Integer, primary_key=True)
    garage_id = db.Column(db.Integer, db.ForeignKey("garages.id"), nullable=False)
    vehicule_id = db.Column(db.Integer, db.ForeignKey("vehicules.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    numero = db.Column(db.String(20))
    statut = db.Column(db.String(20), default="ouvert")
    description_travaux = db.Column(db.Text)
    km_entree = db.Column(db.Integer)
    date_entree = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_sortie_prevue = db.Column(db.DateTime)
    date_sortie = db.Column(db.DateTime)
    notes_internes = db.Column(db.Text)
    montant_ht = db.Column(db.Numeric(10, 2))
    taux_tva = db.Column(db.Numeric(4, 2), default=8.1)
    montant_ttc = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    client = db.relationship("Client", backref="ordres")

    def peut_transiter(self, nouveau_statut):
        return nouveau_statut in TRANSITIONS.get(self.statut, [])

    def to_dict(self):
        return {
            "id": self.id,
            "vehicule_id": self.vehicule_id,
            "client_id": self.client_id,
            "numero": self.numero,
            "statut": self.statut,
            "description_travaux": self.description_travaux,
            "km_entree": self.km_entree,
            "date_entree": self.date_entree.isoformat() if self.date_entree else None,
            "date_sortie_prevue": self.date_sortie_prevue.isoformat() if self.date_sortie_prevue else None,
            "date_sortie": self.date_sortie.isoformat() if self.date_sortie else None,
            "notes_internes": self.notes_internes,
            "montant_ht": float(self.montant_ht) if self.montant_ht else None,
            "taux_tva": float(self.taux_tva) if self.taux_tva else None,
            "montant_ttc": float(self.montant_ttc) if self.montant_ttc else None,
            "transitions_possibles": TRANSITIONS.get(self.statut, []),
            "client_nom": None,
            "vehicule_desc": None,
        }

    def to_dict_full(self):
        d = self.to_dict()
        if self.client:
            d["client_nom"] = f"{self.client.prenom} {self.client.nom}"
        if self.vehicule:
            d["vehicule_desc"] = f"{self.vehicule.marque} {self.vehicule.modele} ({self.vehicule.plaque or ''})"
        return d
