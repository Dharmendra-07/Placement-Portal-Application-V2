# Placement Portal Application — V2

A campus recruitment management system built with **Flask** (backend) and **VueJS** (frontend).

---

## Tech Stack

| Layer     | Technology                                    |
|-----------|-----------------------------------------------|
| Backend   | Flask, SQLAlchemy, Flask-JWT-Extended, SQLite |
| Frontend  | VueJS 3, Vue Router, Vuex, Bootstrap 5        |
| Jobs      | Celery + Redis                                |
| Caching   | Redis                                         |

---

## Project Structure

```
ppa/
├── backend/
│   ├── app.py            # Flask app factory
│   ├── config.py         # Configuration
│   ├── run.py            # Entry point
│   ├── seed.py           # DB creation + admin seeding
│   ├── models/
│   │   └── models.py     # All SQLAlchemy models
│   ├── routes/
│   │   ├── auth.py       # Login, register
│   │   ├── admin.py      # Admin endpoints
│   │   ├── company.py    # Company endpoints
│   │   └── student.py    # Student endpoints
│   └── utils/
│       └── decorators.py # Role-based JWT decorators
└── frontend/
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── main.js
        ├── App.vue
        ├── api.js           # Axios with JWT interceptor
        ├── router/index.js  # Vue Router + guards
        ├── store/index.js   # Vuex auth store
        ├── components/
        │   └── NavBar.vue
        └── views/
            ├── LoginView.vue
            ├── RegisterStudentView.vue
            ├── RegisterCompanyView.vue
            ├── admin/  (Dashboard, Companies, Students, Drives)
            ├── company/ (Dashboard, Drives, Applicants)
            └── student/ (Dashboard, Drives, Profile, History)
```

---

## Setup & Run

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env

# Create tables and seed admin user
python seed.py

# Run Flask
python run.py
```

**Default admin credentials:**
- Email: `admin@ppa.com`
- Password: `Admin@1234`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:5173

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login` | — | Login (all roles) |
| POST | `/api/auth/register/student` | — | Student self-register |
| POST | `/api/auth/register/company` | — | Company register (pending) |
| GET  | `/api/auth/me` | JWT | Current user info |
| GET  | `/api/admin/dashboard` | Admin | Dashboard stats |
| GET  | `/api/admin/companies` | Admin | List companies |
| PUT  | `/api/admin/companies/:id/approve` | Admin | Approve company |
| PUT  | `/api/admin/companies/:id/blacklist` | Admin | Blacklist company |
| GET  | `/api/admin/drives` | Admin | List drives |
| PUT  | `/api/admin/drives/:id/approve` | Admin | Approve drive |
| GET  | `/api/company/dashboard` | Company | Company dashboard |
| POST | `/api/company/drives` | Company | Create drive |
| GET  | `/api/company/drives/:id/applications` | Company | View applicants |
| PUT  | `/api/company/applications/:id/status` | Company | Update app status |
| GET  | `/api/student/dashboard` | Student | Student dashboard |
| POST | `/api/student/drives/:id/apply` | Student | Apply for drive |
| GET  | `/api/student/applications` | Student | Application history |
| PUT  | `/api/student/profile` | Student | Update profile |

---

## Git Commit Messages (Milestones)

```
Milestone-0 PPA-V2 Setup
Milestone-PPA-V2 DB-Relationship
Milestone-PPA-V2 Auth-RBAC
```
