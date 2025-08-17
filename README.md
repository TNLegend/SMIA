# SMIA

SMIA is a full-stack platform for managing AI projects, tracking ISO 42001 compliance, evaluating models and generating audit reports.

The repository is split into a FastAPI backend and a Vite/React front-end.

---

## Repository Structure

```
backend/
  app/            FastAPI application
    auth.py       JWT authentication & user management
    db.py         SQLModel database setup (SQLite by default)
    main.py       API entry point, middleware and router registration
    models.py     ORM models for users, teams, projects, documents, runs, …
    routers/      Endpoints for projects, teams, documents, templates, etc.
    metrics/      Pipeline for performance, fairness and drift analysis
    tasks/        Background schedulers & cleanup jobs
    utils/        File helpers, PDF/report generation, dependencies
  config/         ISO 42001 requirements and document templates
  requirements.txt        Full API dependency list
  requirements-ml.txt     ML runtime dependencies
  Dockerfile.smia-runtime Docker image for ML tasks
  storage/        Persistent storage for uploaded data and models
  smia.db         Default SQLite database

frontend/
  src/            React + TypeScript source
    pages/        Project, team, document, dashboard pages…
    components/   Reusable UI components
    context/      Auth and team selection contexts
    api/          Centralised API client
  package.json    Web client dependencies & scripts
  vite.config.ts  Vite build configuration

README.md
.gitignore
```

---

## Backend

The backend is a FastAPI & SQLModel application exposing a REST/JSON API.

### Highlights

* **Authentication**: OAuth2 + JWT tokens stored in an `smia_token` cookie.
* **Teams & Projects**: CRUD operations with access control via team membership.
* **ISO 42001 Checklist**: Configurable controls and evidence requirements for audits.
* **Document Management**: Upload, version and store documents and images.
* **Model Runs & Evaluations**: Track training/evaluation runs, compute metrics, fairness, drift and attack robustness.
* **Notifications & Dashboard**: Dedicated routers for user notifications and dashboard data.
* **Scheduled Tasks**: Periodic cleanup of runs/logs and Docker containers.
* **Report Generation**: Build audit and risk-analysis reports in HTML/PDF.
* **Storage Utilities**: Helpers for file handling and PDF conversions.

### Running the API

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional environment variables
export DATABASE_URL="sqlite:///./smia.db"
export JWT_SECRET="change_me"   # also JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

uvicorn app.main:app --reload
```

The API listens on **[http://127.0.0.1:8000](http://127.0.0.1:8000)**.
Switch databases by overriding `DATABASE_URL`.

### Optional ML Runtime

`Dockerfile.smia-runtime` installs heavy ML dependencies (`requirements-ml.txt`) in a slim image used for training/evaluation jobs.

---

## Frontend

The frontend is a Vite + React + TypeScript application styled with Material UI (MUI) and Tailwind utilities.

### Running the Client

```bash
cd frontend
npm install
npx vite --port 3000
```

The client runs on **[http://localhost:3000](http://localhost:3000)**.
Use the `VITE_API_URL` environment variable to point to a different backend URL.

### Key Pages

* **Login / Signup** – user authentication
* **Teams** – browse and create teams, manage invitations
* **Projects** – list/create/edit AI projects with search and filtering
* **Documents** – upload, version and view documents & history
* **Dashboard & Reports** – visualise metrics, generate compliance reports
* **Settings** – user profile and application settings

---

## Configuration

* **Database**: set via `DATABASE_URL` (defaults to SQLite file `smia.db`).
* **JWT Security**: `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`.
* **Frontend API base**: `VITE_API_URL`.
* **Storage**: uploaded data/models/logs under `backend/storage/`.

---

## Contributing

1. Fork the repo.
2. Create a feature branch.
3. Commit and push your changes.
4. Open a pull request.
