# 🎯 AI-Based Adaptive Competency & Career Assessment Platform

A production-ready full-stack platform that delivers adaptive multiple-choice assessments, evaluates competency using a custom scoring engine, and predicts learner level using a Machine-Learning (RandomForest) classifier trained from real attempt data.

---

## ✨ Features

- **JWT Authentication** — student/admin roles, bcrypt password hashing
- **Test Management** — admins create tests and questions tagged easy/medium/hard
- **Adaptive Engine** — starts at medium; correct answer → harder, wrong → easier (max 10 questions/attempt)
- **Weighted Scoring** — easy=1, medium=2, hard=3 → competency level (Beginner < 50, Intermediate 50–80, Expert 80+)
- **Recommendation Engine** — flags weak difficulty levels (< 60 % accuracy) and suggests next steps
- **ML Pipeline** — exports DB → CSV → trains RandomForest on `accuracy / avg_difficulty / attempt_time` → predicts competency
- **React Dashboard** — login/register, dashboard, adaptive test UI, result page, analytics charts (Recharts), full admin panel
- **Dark mode**, responsive UI, optimized DB queries (joinedload + grouped subqueries — no N+1)
- **Docker-ready** — single `docker-compose up` boots PostgreSQL + FastAPI + React

---

## 🧱 Tech Stack

| Layer    | Technology                                                      |
|----------|-----------------------------------------------------------------|
| Backend  | FastAPI · SQLAlchemy 2 · PostgreSQL · Pydantic v2 · python-jose |
| ML       | scikit-learn · pandas · joblib · numpy                          |
| Frontend | React 18 (Vite) · TailwindCSS · Axios · Recharts · React Router |
| Infra    | Docker · docker-compose                                         |

---

## 📁 Project Structure

```
project/
├── backend/
│   ├── app/
│   │   ├── main.py              # Single FastAPI instance
│   │   ├── config.py            # Env settings
│   │   ├── database.py          # Engine, SessionLocal, Base
│   │   ├── models.py            # ORM only (no ML)
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routes/              # auth · tests · adaptive · results · admin · ml
│   │   ├── ai/                  # scoring · adaptive_engine · recommendation
│   │   ├── ml/                  # pipeline · train · predict
│   │   └── utils/               # auth · security
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── pages/               # Login · Register · Dashboard · Test · Result · Analytics · AdminPanel
│   │   ├── components/          # Navbar · ProtectedRoute
│   │   ├── services/            # api · auth
│   │   ├── App.jsx · main.jsx · index.css
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── .env.example
└── docker-compose.yml
```

---

## 🚀 Quick Start — Docker (recommended)

```bash
# from project root
docker-compose up --build
```

That's it. Three containers come up:

| Service   | URL                              |
|-----------|----------------------------------|
| Frontend  | http://localhost:5173            |
| Backend   | http://localhost:8000            |
| API docs  | http://localhost:8000/docs       |
| Postgres  | localhost:5432                   |

Default admin (auto-seeded on first start):
- Email: `admin@example.com`
- Password: `admin123`

---

## 🔧 Manual Setup (without Docker)

### 1. PostgreSQL
Make sure Postgres is running and create the database:
```sql
CREATE DATABASE assessment_db;
```

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # edit DATABASE_URL etc.
uvicorn app.main:app --reload
```
Runs on http://localhost:8000 — Swagger UI at /docs.

### 3. Frontend
```bash
cd frontend
npm install
cp .env.example .env              # VITE_API_URL=http://localhost:8000
npm run dev
```
Runs on http://localhost:5173.

---

## 🎮 Workflow

1. **Login as admin** (`admin@example.com / admin123`)
2. **Admin → Tests tab** → create a test (e.g. "Python Fundamentals")
3. Click **Manage Q&A** → add questions, mix easy/medium/hard difficulties
4. **Register a student account** (or open another browser)
5. **Dashboard → Start Test** → take the adaptive test (10 questions, difficulty auto-adjusts)
6. Land on the **Result page** — competency level, weak areas, recommendations, ML prediction
7. **Analytics** page — score trend, level distribution, score-by-attempt charts
8. Back to **Admin → ML tab** → after at least 5 completed attempts:
   - Click **Generate Dataset CSV** (exports DB → `app/ml/dataset.csv`)
   - Click **Train Model** (RandomForest → saved to `app/ml/model.joblib`)
9. From now on every new attempt also gets an **AI-predicted level** alongside the rule-based one

---

## 🔌 Key API Endpoints

| Method | Path                               | Description                          |
|--------|------------------------------------|--------------------------------------|
| POST   | /api/auth/register                 | Register user                        |
| POST   | /api/auth/login-json               | Login (JSON, used by frontend)       |
| POST   | /api/auth/login                    | Login (OAuth2 form, used by Swagger) |
| GET    | /api/auth/me                       | Current user                         |
| GET    | /api/tests/                        | List all tests                       |
| POST   | /api/tests/                        | Create test (admin)                  |
| POST   | /api/tests/{id}/questions          | Add question (admin)                 |
| POST   | /api/adaptive/start                | Start an adaptive attempt            |
| POST   | /api/adaptive/submit-answer        | Submit answer & get next question    |
| GET    | /api/results/me                    | My past attempts                     |
| GET    | /api/results/{attempt_id}          | Detailed result + recommendations    |
| GET    | /api/results/me/analytics          | Personal analytics                   |
| GET    | /api/admin/users                   | All users (admin)                    |
| GET    | /api/admin/stats                   | Platform stats (admin)               |
| POST   | /api/ml/generate-dataset           | DB → CSV                             |
| POST   | /api/ml/train                      | Train RandomForest                   |
| POST   | /api/ml/predict                    | Predict competency level             |

Full interactive docs at `/docs`.

---

## 🧠 ML Details

- **Features**: `accuracy`, `avg_difficulty`, `attempt_time`
- **Target**: `competency_level` (Beginner / Intermediate / Expert)
- **Model**: `RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)`
- **Min samples to train**: 5 completed attempts
- **Fallback**: If no model exists yet, prediction uses the same 50/80 rule thresholds — system works from day 1

---

## 🛡️ Architecture Rules Followed

- ✅ Single FastAPI instance (no duplicates)
- ✅ Single set of ORM models in `app/models.py`
- ✅ Zero ML code inside `models.py` — ML is isolated to `app/ml/`
- ✅ Optimized queries via `joinedload` and grouped subqueries (no N+1)
- ✅ Proper exception handling on every route
- ✅ Frontend matches mandated layout: `pages/`, `components/`, `services/`, `App.jsx`, `main.jsx`

---

## ⚙️ Environment Variables

Backend (`backend/.env`):
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/assessment_db
SECRET_KEY=your-long-random-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ML_MODEL_PATH=app/ml/model.joblib
DATASET_PATH=app/ml/dataset.csv
**Default Admin Setup:**
On first run, an admin user is auto-seeded using the `ADMIN_EMAIL` and `ADMIN_PASSWORD` values from your `.env` file. See `backend/.env.example` for the format.

⚠️ **Important:** Always change the default admin password before deploying to production.

Frontend (`frontend/.env`):
```
VITE_API_URL=http://localhost:8000
```

---

## 📝 License

MIT — use freely for learning, projects, or production.

Developer Ayyaz Qamar
