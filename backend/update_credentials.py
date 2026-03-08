"""Update credentials script - runs once at startup."""
from app import create_app
from app.extensions import db
from app.models import User, Garage

app = create_app()

with app.app_context():
    db.create_all()
    
    user = User.query.filter_by(email="admin@garageneo.ch").first()
    if not user:
        user = User.query.first()
    
    if user:
        user.email = "contact@mekano.ch"
        user.set_password("Cristal4you11++")
        db.session.commit()
        print("Credentials updated: contact@mekano.ch")
    else:
        # No user exists - run full seed
        from seed import *
        print("Seed completed")

