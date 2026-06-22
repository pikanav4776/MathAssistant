# MathAssistant

**Version:** v1.0 (Algebra Co-Solving)

## Summary

Algebra step-validation tutor — guides students through multi-step simplification with hints instead of giving full answers.

MathAssistant is a **deterministic** tutoring system (FastAPI + SymPy + PostgreSQL). Students submit one algebraic step at a time; the backend parses, normalizes, compares against the canonical solution path, classifies errors, and returns contextual hints. Skip-ahead is accepted when a later canonical step is submitted. It is **not** a chatbot or LLM answer engine.

**v1.0 scope:** algebra co-solving with single- and multi-hop canonical paths, calculator UI, 72-problem library with starter set, optional auth (guest or account), session resume and history, production rate limits and deploy checks. See [documentation/v1.0_Scope.md](documentation/v1.0_Scope.md) for in-scope vs deferred, [documentation/Product_Spec.txt](documentation/Product_Spec.txt) for product goals, and [documentation/Technical_Architecture_Spec.txt](documentation/Technical_Architecture_Spec.txt) for detailed design. Version history: [CHANGELOG.md](CHANGELOG.md). Release: [documentation/v1.0_Release_Checklist.md](documentation/v1.0_Release_Checklist.md).

---

## Tech stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+, FastAPI, SymPy |
| **Frontend** | React + TypeScript (Vite) in `frontend/`; deprecated Next.js demo in `app/` |
| **Database** | PostgreSQL via SQLAlchemy |
| **Deployment** | Render (API + static site), Neon (PostgreSQL), GitHub Actions (CI) |

---

## How to run it

### Prerequisites

- **Python 3.11+**
- **PostgreSQL**
- **Node.js 18+** (for the Vite frontend in `frontend/`)

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

**Primary UI** — React + Vite in `frontend/`:

```powershell
cd frontend
npm install
npm run dev
```

Or use the helper script:

```powershell
cd frontend
.\start.ps1
```

Open [http://localhost:3000](http://localhost:3000). You should see **"Algebra Co-Solving (v1.0)"**.

> Do **not** open `frontend/index.html` via `file://` — the browser will block API calls.
> Do **not** use port 8000 for the frontend; that is the backend.
> Do **not** run `npm run dev` from the repo root — that starts the deprecated Next.js demo in `app/`.

**Deprecated** — Next.js demo in `app/` (superseded by `frontend/`):

```powershell
npm install
npm run dev
```

See [frontend/README.md](frontend/README.md) for the full user flow and production deploy notes.

---

## How it works

### Backend

Each student step flows through a deterministic validation pipeline against the session's current canonical line and solution path:

```text
Student step (^ for exponents, e.g. x^2)
  → parse → normalize → compare to expected (or skip-ahead target)
  → classify error (if wrong) → generate hint → JSON response
```

Multi-hop problems advance through intermediate canonical steps (e.g. `2(x+3)+4` → `2x+6+4` → `2x+10`). After **3** incorrect math attempts, hints escalate. After **5**, the expected final answer may be appended to the hint. Input notation uses `^` for exponents (`x^2`), not `**`.

### Frontend

The primary UI in `frontend/` is a React + Vite app. It loads a random problem, starts a tutoring session, and submits steps to the backend. It displays correctness, error types, and hints (with KaTeX for math display). See [frontend/README.md](frontend/README.md) for the user flow.

### Database

PostgreSQL stores problems, sessions, attempts, and wrong-answer benchmarks. Tables are defined in `backend/db/models.py`. Session state (attempt counts, hint level) persists across requests. Production schema is managed with Alembic; see [documentation/Database_Operations.md](documentation/Database_Operations.md).

### Deployment

Production runs on **Render** (Python API + Vite static frontend) with **Neon** for PostgreSQL. **GitHub Actions** runs backend tests and a frontend build on every PR and push to `main`; merges to `main` trigger Render auto-deploy.

For CI/CD setup, Render Blueprint steps, staging (`render-staging.yaml`), environment variables, branch protection, Sentry, migrations, and Neon configuration, see [documentation/Technical_Architecture_Spec.txt](documentation/Technical_Architecture_Spec.txt).
