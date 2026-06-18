# MathAssistant

**Version:** v0.2 (MVP)

## Summary

Algebra step-validation tutor — guides students with hints instead of giving full answers.

MathAssistant is a **deterministic** tutoring system (FastAPI + SymPy + PostgreSQL). Students submit one algebraic step at a time; the backend parses, normalizes, compares, classifies errors, and returns contextual hints. It is **not** a chatbot or LLM answer engine in the current MVP.

**MVP scope:** algebra only, structured text input (no OCR), seed problem library (no auto-generation). See [documentation/Product_Spec.txt](documentation/Product_Spec.txt) for full product scope and [documentation/Technical_Architecture_Spec.txt](documentation/Technical_Architecture_Spec.txt) for detailed design.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI, SymPy |
| **Frontend** | Vanilla HTML/CSS/JS (`frontend/`); legacy Next.js in `app/` |
| **Database** | PostgreSQL via SQLAlchemy |
| **Deployment** | Render (API + static site), Neon (PostgreSQL), GitHub Actions (CI) |

---

## How to run it

### Prerequisites

- **Python 3.11+**
- **PostgreSQL**
- **Node.js** (only if you use the legacy Next.js UI in `app/`)

### 1. Database

Create a database and set `DATABASE_URL` in `backend/.env` (see `backend/.env.example`):

```env
DATABASE_URL=postgresql://user:password@localhost:5433/mathassistant
```

Tables are created and seed data loaded on backend startup when using a **local**
database (`DATABASE_URL` with localhost, or `ENVIRONMENT=development`, or
`SKIP_MIGRATIONS=true`). For production/staging, schema is applied by
`alembic upgrade head` on deploy; see
[documentation/Technical_Architecture_Spec.txt](documentation/Technical_Architecture_Spec.txt)
and [documentation/Database_Operations.md](documentation/Database_Operations.md).

### 2. Backend (port 8000)

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
.\start.ps1
```

Or manually:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Verify: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) · Readiness: [http://127.0.0.1:8000/ready](http://127.0.0.1:8000/ready) · API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Frontend (port 3000)

**Primary UI** — vanilla HTML/JS in `frontend/`:

```powershell
cd frontend
.\start.ps1
```

Open [http://localhost:3000](http://localhost:3000). You should see **"Algebra Step Validator"**.

> Do **not** open `frontend/index.html` via `file://` — the browser will block API calls.
> Do **not** use port 8000 for the frontend; that is the backend.

**Legacy UI** — Next.js demo in `app/` (optional):

```powershell
npm install
npm run dev
```

See [frontend/README.md](frontend/README.md) for the full user flow.

---

## How it works

### Backend

Each student step flows through a deterministic validation pipeline:

```text
Student step (^ for exponents, e.g. x^2)
  → parse → normalize → compare to expected
  → classify error (if wrong) → generate hint → JSON response
```

After **3** incorrect math attempts, hints escalate. After **5**, the expected final answer may be appended to the hint. Input notation uses `^` for exponents (`x^2`), not `**`.

### Frontend

The primary UI in `frontend/` loads a random problem, starts a tutoring session, and submits steps to the backend. It displays correctness, error types, and hints. See [frontend/README.md](frontend/README.md) for the user flow.

### Database

PostgreSQL stores problems, sessions, attempts, and wrong-answer benchmarks. Tables are defined in `backend/db/models.py`. Session state (attempt counts, hint level) persists across requests. Production schema is managed with Alembic; see [documentation/Database_Operations.md](documentation/Database_Operations.md).

### Deployment

Production runs on **Render** (Python API + static frontend) with **Neon** for PostgreSQL. **GitHub Actions** runs the test suite on every PR and push to `main`; merges to `main` trigger Render auto-deploy.

For CI/CD setup, Render Blueprint steps, staging (`render-staging.yaml`), environment variables, branch protection, Sentry, migrations, and Neon configuration, see [documentation/Technical_Architecture_Spec.txt](documentation/Technical_Architecture_Spec.txt).
