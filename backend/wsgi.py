from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

# Run credential update on startup
with app.app_context():
    try:
        db.create_all()
        user = User.query.filter_by(email="admin@garageneo.ch").first()
        if user:
            user.email = "contact@mekano.ch"
            user.set_password("Cristal4you11++")
            db.session.commit()
            print("Credentials migrated to contact@mekano.ch")
    except Exception as e:
        print(f"Startup update skipped: {e}")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
