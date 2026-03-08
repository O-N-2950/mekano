from app.extensions import db
from datetime import datetime, timezone


class Garage(db.Model):
    __tablename__ = "garages"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    adresse = db.Column(db.String(500))
    npa = db.Column(db.String(10))
    localite = db.Column(db.String(200))
    canton = db.Column(db.String(2))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(200))
    numero_tva = db.Column(db.String(20))  # CHE-xxx.xxx.xxx
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    users = db.relationship("User", backref="garage", lazy="dynamic")
    clients = db.relationship("Client", backref="garage", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "adresse": self.adresse,
            "npa": self.npa,
            "localite": self.localite,
            "canton": self.canton,
            "telephone": self.telephone,
            "email": self.email,
            "numero_tva": self.numero_tva,
            "actif": self.actif,
        }
