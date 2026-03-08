# GarageNEO

SaaS de gestion de garage pour garagistes independants en Suisse romande.

**Groupe NEO** | Stack: Flask + React + PostgreSQL | Deploy: Railway

---

## Structure

```
GarageNEO/
  backend/          Flask API REST
  frontend/         React 18 + Vite + TailwindCSS
```

## Setup local

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Editer DATABASE_URL si necessaire

# Creer la DB
createdb garageneo

# Init migrations + seed
flask --app wsgi:app db init
flask --app wsgi:app db migrate -m "init"
flask --app wsgi:app db upgrade
python seed.py

# Lancer
python wsgi.py
```

API disponible sur http://localhost:5000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App disponible sur http://localhost:3000

### Login dev

| Email | Password |
|-------|----------|
| admin@garageneo.ch | admin123 |

## Deploy Railway

### 1. Creer un projet Railway

Creer 3 services :
- **PostgreSQL** (plugin Railway)
- **Backend** (connecter au dossier `backend/`)
- **Frontend** (connecter au dossier `frontend/`)

### 2. Variables d'environnement Backend

```
DATABASE_URL        → Reference PostgreSQL (auto-inject par Railway)
SECRET_KEY          → Generer: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY      → Generer: python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Variables d'environnement Frontend

```
VITE_API_URL        → URL du service backend Railway
```

### 4. Seed initial

Dans le shell Railway du backend :
```bash
python seed.py
```

## API Routes (MVP)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /api/auth/login | Non | Login, retourne JWT |
| GET | /api/clients | JWT | Liste clients du garage |
| GET | /api/vehicules/:id | JWT | Detail vehicule |
| GET | /health | Non | Health check |

## Multi-tenant

Chaque requete authentifiee porte un `garage_id` dans le JWT.
Le decorator `@tenant_required` filtre automatiquement les donnees par tenant.
Aucun garage ne peut voir les donnees d'un autre.

## Stack

- **Backend**: Flask 3.1, SQLAlchemy, Flask-JWT-Extended, Flask-Migrate, Gunicorn
- **Frontend**: React 18, Vite, TailwindCSS, Redux Toolkit, React Router 7, Lucide Icons
- **DB**: PostgreSQL 15+
- **Deploy**: Railway (Nixpacks)
- **Design**: Outfit + JetBrains Mono, accent #3176A6, sidebar #1a2332

## Roadmap

- [x] Auth multi-tenant JWT
- [x] Modeles: Garage, User, Client, Vehicule, OrdreDeTravail
- [x] API REST de base
- [x] Frontend layout sidebar
- [ ] CRUD complet clients/vehicules/OT
- [ ] VIN decode (NHTSA + SwissCarInfo)
- [ ] Facturation + QR-Facture suisse
- [ ] Catalogue pieces (TecDoc)
- [ ] Temps baremes (TecRMI)
- [ ] Multilingue FR/DE
