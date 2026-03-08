from app.extensions import db
from datetime import datetime, timezone


class Client(db.Model):
    __tablename__ = "clients"

    id = db.Column(db.Integer, primary_key=True)
    garage_id = db.Column(db.Integer, db.ForeignKey("garages.id"), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    entreprise = db.Column(db.String(200))
    adresse = db.Column(db.String(500))
    npa = db.Column(db.String(10))
    localite = db.Column(db.String(200))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(200))
    date_naissance = db.Column(db.Date)
    notes = db.Column(db.Text)
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    vehicules = db.relationship("Vehicule", backref="client", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "prenom": self.prenom,
            "nom": self.nom,
            "entreprise": self.entreprise,
            "adresse": self.adresse,
            "npa": self.npa,
            "localite": self.localite,
            "telephone": self.telephone,
            "email": self.email,
            "date_naissance": self.date_naissance.isoformat() if self.date_naissance else None,
            "notes": self.notes,
            "actif": self.actif,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
