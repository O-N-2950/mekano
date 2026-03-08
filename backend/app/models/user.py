from app.extensions import db
from datetime import datetime, timezone
import bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    garage_id = db.Column(db.Integer, db.ForeignKey("garages.id"), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    prenom = db.Column(db.String(100))
    nom = db.Column(db.String(100))
    role = db.Column(db.String(20), default="technicien")  # admin, technicien
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def to_dict(self):
        return {
            "id": self.id,
            "garage_id": self.garage_id,
            "email": self.email,
            "prenom": self.prenom,
            "nom": self.nom,
            "role": self.role,
            "actif": self.actif,
        }
