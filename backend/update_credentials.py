"""Startup script: seed DB if empty, then ensure correct admin credentials."""
import os
import sys

os.environ.setdefault("FLASK_ENV", "production")

from app import create_app
from app.extensions import db
from app.models.garage import Garage
from app.models.user import User
from app.models.client import Client
from app.models.vehicule import Vehicule

app = create_app()

with app.app_context():
    db.create_all()

    if not Garage.query.first():
        print("Empty DB - seeding...")
        garage = Garage(
            nom="Mekano Demo",
            adresse="Rue de la Gare 12",
            npa="1003",
            localite="Lausanne",
            canton="VD",
            telephone="021 312 00 00",
            email="contact@mekano.ch",
            numero_tva="CHE-123.456.789",
        )
        db.session.add(garage)
        db.session.flush()

        admin = User(
            garage_id=garage.id,
            email="contact@mekano.ch",
            prenom="Olivier",
            nom="Neukomm",
            role="admin",
        )
        admin.set_password("Cristal4you11++")
        db.session.add(admin)

        client = Client(
            garage_id=garage.id,
            prenom="Jean",
            nom="Dupont",
            adresse="Avenue de Cour 5",
            npa="1007",
            localite="Lausanne",
            telephone="079 123 45 67",
            email="jean.dupont@example.ch",
        )
        db.session.add(client)
        db.session.flush()

        vehicule = Vehicule(
            garage_id=garage.id,
            client_id=client.id,
            vin="WBA3A5C50CF256985",
            plaque="VD 345678",
            marque="BMW",
            modele="328i",
            annee=2012,
            carburant="essence",
            km_actuel=142000,
        )
        db.session.add(vehicule)
        db.session.commit()
        print("Seed OK: contact@mekano.ch / Cristal4you11++")
    else:
        user = User.query.filter_by(email="admin@garageneo.ch").first()
        if user:
            user.email = "contact@mekano.ch"
            user.set_password("Cristal4you11++")
            db.session.commit()
            print("Credentials updated OK")
        else:
            print("Admin already configured")
