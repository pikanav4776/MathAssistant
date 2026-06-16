# MathAssistant

**Version:** v0.2 (MVP)

Algebra step-validation tutor — guides students with hints instead of giving full answers.

MathAssistant is a **deterministic** tutoring system (FastAPI + SymPy + PostgreSQL). Students submit one algebraic step at a time; the backend parses, normalizes, compares, classifies errors, and returns contextual hints. It is **not** a chatbot or LLM answer engine in the current MVP.

---

## Quick start

### Prerequisites

- **Python 3.11+**
- **PostgreSQL**
- **Node.js** (only if you use the legacy Next.js UI in `app/`)

### 1. Database

Create a database and set `DATABASE_URL` in `backend/.env` (see `backend/.env.example`):

```env
DATABASE_URL=postgresql://user:password@localhost:5433/mathassistant
```

Tables are created and seed data loaded on backend startup.

### 2. Backend (port 8000)

```powershell
cd backend
python -m venv ..\.venv
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
.\start.ps1
```

Or manually:

```powershell
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Verify: [http://127.0.0.1:8000](http://127.0.0.1:8000)

Interactive API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

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

## How it works (one request)

```text
Student step (^ for exponents, e.g. x^2)
  → parse → normalize → compare to expected
  → classify error (if wrong) → generate hint → JSON response
```

After **3** incorrect math attempts, hints escalate. After **5**, the expected final answer may be appended to the hint.

---

## Project structure

```text
MathAssistant/
├── backend/           FastAPI app, SymPy engine, PostgreSQL models
│   ├── main.py        API + validation pipeline
│   ├── db/            SQLAlchemy models and seed data
│   └── tests/         pytest suite and evaluation runners
├── frontend/          Primary UI (HTML/CSS/JS)
├── app/               Legacy Next.js UI
├── documentation/     Product and architecture specs
├── reports/           Evaluation reports
└── scripts/           Dataset verification utilities
```

---

## API overview

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/` | Health check |
| `GET` | `/sample-problem` | Random problem (optional `difficulty`, `topic` filters) |
| `GET` | `/problem/{problem_id}` | Fetch problem by ID |
| `POST` | `/problem` | Create problem (admin; no auth yet) |
| `POST` | `/start-session` | Start tutoring session |
| `POST` | `/submit-step` | Validate a student step |
| `GET` | `/session/{session_id}` | Session summary + attempt history |
| `DELETE` | `/session/{session_id}` | Delete session and attempts |

Full schemas: `/docs` on the running backend.

**Input notation:** use `^` for exponents (`x^2`), not `**`.

---

## Testing

From `backend/`:

```powershell
pytest
```

Evaluation benchmark:

```powershell
python tests/run_evaluation.py
```

Latest results: [reports/evaluation_report.md](reports/evaluation_report.md)

---

## Documentation

| Document | Contents |
|----------|----------|
| [documentation/Product_Spec.txt](documentation/Product_Spec.txt) | Problem statement, goals, users, MVP scope, metrics |
| [documentation/Technical_Architecture_Spec.txt](documentation/Technical_Architecture_Spec.txt) | System design, data models, API details, risks |
| [documentation/Current_Plan.txt](documentation/Current_Plan.txt) | Phased development plan and status |
| [frontend/README.md](frontend/README.md) | Frontend setup and user flow |

---

## MVP limits

- Algebra only (no geometry, calculus, statistics)
- Structured text input (no OCR)
- No automatic problem generation (library + seed data only)
- Systems limited to modest complexity (see product spec)

---

## License

TBD
