from app.extensions import db
from datetime import datetime, timezone


class Vehicule(db.Model):
    __tablename__ = "vehicules"
    __table_args__ = (
        db.Index("ix_vehicules_garage_plaque", "garage_id", "plaque"),
        db.Index("ix_vehicules_garage_actif", "garage_id", "actif"),
    )

    id = db.Column(db.Integer, primary_key=True)
    garage_id = db.Column(db.Integer, db.ForeignKey("garages.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    vin = db.Column(db.String(17))
    plaque = db.Column(db.String(20))
    marque = db.Column(db.String(100))
    modele = db.Column(db.String(100))
    annee = db.Column(db.Integer)
    couleur = db.Column(db.String(50))
    carburant = db.Column(db.String(50))
    km_actuel = db.Column(db.Integer)
    date_mct = db.Column(db.Date)  # controle technique CH (MFK)
    notes = db.Column(db.Text)
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    ordres = db.relationship("OrdreDeTravail", backref="vehicule", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "vin": self.vin,
            "plaque": self.plaque,
            "marque": self.marque,
            "modele": self.modele,
            "annee": self.annee,
            "couleur": self.couleur,
            "carburant": self.carburant,
            "km_actuel": self.km_actuel,
            "date_mct": self.date_mct.isoformat() if self.date_mct else None,
            "notes": self.notes,
            "actif": self.actif,
            "client_nom": None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_dict_full(self):
        d = self.to_dict()
        if self.client:
            d["client_nom"] = f"{self.client.prenom} {self.client.nom}"
        return d
