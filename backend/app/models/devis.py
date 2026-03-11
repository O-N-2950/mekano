from app.extensions import db
from datetime import datetime, timezone, timedelta


STATUTS_DEVIS = ["brouillon", "envoye", "accepte", "refuse", "expire"]


class LigneDevis(db.Model):
    __tablename__ = "lignes_devis"
    __table_args__ = (
        db.Index("ix_lignes_devis_id", "devis_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    devis_id = db.Column(db.Integer, db.ForeignKey("devis.id", ondelete="CASCADE"), nullable=False)
    ordre = db.Column(db.Integer, default=0)
    type = db.Column(db.String(20), default="piece")  # piece|main_oeuvre|peinture|forfait
    reference = db.Column(db.String(100))
    designation = db.Column(db.String(300), nullable=False)
    quantite = db.Column(db.Numeric(10, 2), default=1)
    prix_unitaire = db.Column(db.Numeric(10, 2), default=0)
    remise_pct = db.Column(db.Numeric(5, 2), default=0)
    total_ht = db.Column(db.Numeric(10, 2), default=0)

    def calculer_total(self):
        qty = float(self.quantite or 1)
        pu = float(self.prix_unitaire or 0)
        remise = float(self.remise_pct or 0)
        self.total_ht = round(qty * pu * (1 - remise / 100), 2)
        return float(self.total_ht)

    def to_dict(self):
        return {
            "id": self.id,
            "ordre": self.ordre,
            "type": self.type,
            "reference": self.reference,
            "designation": self.designation,
            "quantite": float(self.quantite) if self.quantite else 1,
            "prix_unitaire": float(self.prix_unitaire) if self.prix_unitaire else 0,
            "remise_pct": float(self.remise_pct) if self.remise_pct else 0,
            "total_ht": float(self.total_ht) if self.total_ht else 0,
        }


class Devis(db.Model):
    __tablename__ = "devis"
    __table_args__ = (
        db.Index("ix_devis_garage_statut", "garage_id", "statut"),
        db.Index("ix_devis_numero", "numero"),
    )

    id = db.Column(db.Integer, primary_key=True)
    garage_id = db.Column(db.Integer, db.ForeignKey("garages.id"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)
    vehicule_id = db.Column(db.Integer, db.ForeignKey("vehicules.id"), nullable=True)
    numero = db.Column(db.String(20), nullable=False)
    statut = db.Column(db.String(20), default="brouillon")

    vehicule_km = db.Column(db.Integer)
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_validite = db.Column(db.DateTime)

    petites_fournitures_pct = db.Column(db.Numeric(5, 2), default=4.0)
    taux_tva = db.Column(db.Numeric(4, 2), default=8.1)

    sous_total_pieces_ht = db.Column(db.Numeric(10, 2), default=0)
    sous_total_mo_ht = db.Column(db.Numeric(10, 2), default=0)
    sous_total_peinture_ht = db.Column(db.Numeric(10, 2), default=0)
    sous_total_forfait_ht = db.Column(db.Numeric(10, 2), default=0)
    petites_fournitures_ht = db.Column(db.Numeric(10, 2), default=0)
    total_ht = db.Column(db.Numeric(10, 2), default=0)
    montant_tva = db.Column(db.Numeric(10, 2), default=0)
    total_ttc = db.Column(db.Numeric(10, 2), default=0)

    notes_client = db.Column(db.Text)
    conditions = db.Column(db.Text, default="Devis valable 30 jours. Prix sous réserve de modification. Des indications précises ne pourront être données qu'après démontage.")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    lignes = db.relationship("LigneDevis", backref="devis", cascade="all, delete-orphan", order_by="LigneDevis.ordre")
    client = db.relationship("Client", backref="devis")
    vehicule = db.relationship("Vehicule", backref="devis")

    def recalculer(self):
        """Recalcule tous les totaux depuis les lignes."""
        pieces = mo = peinture = forfait = 0.0
        for l in self.lignes:
            l.calculer_total()
            t = float(l.total_ht or 0)
            if l.type == "piece":
                pieces += t
            elif l.type == "main_oeuvre":
                mo += t
            elif l.type == "peinture":
                peinture += t
            else:
                forfait += t

        self.sous_total_pieces_ht = round(pieces, 2)
        self.sous_total_mo_ht = round(mo, 2)
        self.sous_total_peinture_ht = round(peinture, 2)
        self.sous_total_forfait_ht = round(forfait, 2)

        base_pf = pieces  # petites fournitures sur les pièces
        pf_pct = float(self.petites_fournitures_pct or 0)
        pf = round(base_pf * pf_pct / 100, 2)
        self.petites_fournitures_ht = pf

        total_ht = round(pieces + mo + peinture + forfait + pf, 2)
        self.total_ht = total_ht

        tva_pct = float(self.taux_tva or 8.1)
        tva = round(total_ht * tva_pct / 100, 2)
        self.montant_tva = tva
        self.total_ttc = round(total_ht + tva, 2)

    def to_dict(self):
        return {
            "id": self.id,
            "numero": self.numero,
            "statut": self.statut,
            "client_id": self.client_id,
            "vehicule_id": self.vehicule_id,
            "vehicule_km": self.vehicule_km,
            "client_nom": f"{self.client.prenom} {self.client.nom}" if self.client else None,
            "vehicule_desc": f"{self.vehicule.marque} {self.vehicule.modele} ({self.vehicule.plaque or ''})" if self.vehicule else None,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
            "date_validite": self.date_validite.isoformat() if self.date_validite else None,
            "petites_fournitures_pct": float(self.petites_fournitures_pct or 4),
            "taux_tva": float(self.taux_tva or 8.1),
            "sous_total_pieces_ht": float(self.sous_total_pieces_ht or 0),
            "sous_total_mo_ht": float(self.sous_total_mo_ht or 0),
            "sous_total_peinture_ht": float(self.sous_total_peinture_ht or 0),
            "sous_total_forfait_ht": float(self.sous_total_forfait_ht or 0),
            "petites_fournitures_ht": float(self.petites_fournitures_ht or 0),
            "total_ht": float(self.total_ht or 0),
            "montant_tva": float(self.montant_tva or 0),
            "total_ttc": float(self.total_ttc or 0),
            "notes_client": self.notes_client,
            "conditions": self.conditions,
            "lignes": [l.to_dict() for l in self.lignes],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
