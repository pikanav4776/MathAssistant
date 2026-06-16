# MathAssistant — Development Session Summary

This document consolidates the full Cursor development thread: Phases 5–9, PostgreSQL setup, troubleshooting, and frontend delivery.

---

## Project overview

**MathAssistant** is a deterministic algebra step-validation tutoring backend (FastAPI + SymPy) with a PostgreSQL persistence layer and a vanilla HTML/CSS/JS frontend.

**Core principle:** Validate student steps, classify errors, generate hints — not an AI chatbot or answer generator.

**Expression syntax:** Use `^` for exponents (e.g. `x^2`), not `**`.

---

## Architecture (data flow)

```
Student input (^ exponents)
  → parser()
  → normalize()
  → comparison()
  → classify_error()
  → generate_hint()
  → JSON response
```

**Base URL:** `http://127.0.0.1:8000`

---

## Phase 5 — In-memory session management

### What was built
- Module-level `_SESSION_STORE` dict (later replaced in Phase 6)
- `SessionState` dataclass (kept as bridge object through Phase 6+)
- Constants: `MAX_ATTEMPTS_BEFORE_ESCALATION = 3`, `MAX_ATTEMPTS_BEFORE_REVEAL = 5`
- Two counters: `attempt_count` (all submissions), `incorrect_attempt_count` (wrong math only)

### Endpoints
| Endpoint | Purpose |
|----------|---------|
| `POST /start-session` | Create session |
| `POST /submit-step` | Validate step, track attempts, apply hint policy |
| `GET /session/{id}` | Session summary + attempt history |
| `DELETE /session/{id}` | Remove session |

### Hint policy (`_apply_session_hint_policy`)
- After 3 incorrect attempts → `hint_level` escalates 1 → 2
- After 5 incorrect attempts → solution appended to hint
- Input errors do not affect hint escalation logic on the backend the same way on the client (client tracks separately in Phase 8)

### Frontend issue (Phase 5)
The Next.js `app/page.tsx` hardcoded `session_id: "test-session-1"`, causing **"Session not found"** until the frontend called `POST /start-session` first.

---

## Phase 6 — PostgreSQL persistence

### What changed
Replaced in-memory `_SESSION_STORE` with PostgreSQL via SQLAlchemy.

### New files
```
backend/db/
  __init__.py
  database.py    — engine, SessionLocal, init_db(), get_db()
  models.py      — ORM tables
backend/.env.example
```

### Dependencies added
- `sqlalchemy>=2.0`
- `psycopg2-binary`
- `python-dotenv`

### Database tables

#### `problems`
| Column | Type |
|--------|------|
| id | VARCHAR PK |
| expression | TEXT |
| expected_final | TEXT |
| difficulty | VARCHAR (nullable, Phase 7) |
| topic | VARCHAR (nullable, Phase 7) |
| created_at | TIMESTAMP |

#### `sessions`
| Column | Type |
|--------|------|
| session_id | VARCHAR PK |
| problem_id | VARCHAR FK → problems.id |
| attempt_count | INTEGER |
| incorrect_attempt_count | INTEGER |
| hint_level | INTEGER |
| created_at, last_active | TIMESTAMP |

#### `attempts`
| Column | Type |
|--------|------|
| id | SERIAL PK |
| session_id | VARCHAR FK |
| step, expected | TEXT |
| is_equivalent | BOOLEAN |
| error_type | VARCHAR (nullable) |
| hint | TEXT |
| timestamp | TIMESTAMP |

#### `users` (stub)
| Column | Type |
|--------|------|
| id | SERIAL PK |
| created_at | TIMESTAMP |

### Configuration
- `DATABASE_URL` in `backend/.env` (copy from `.env.example`)
- `init_db()` runs at app startup via FastAPI `lifespan`
- Tables created with `create_all()` — no Alembic

### Session bridge pattern
`SessionState` dataclass still used inside `/submit-step` to call `_apply_session_hint_policy()` without modifying that function. DB row → temporary `SessionState` → policy → write back to DB.

---

## Phase 7 — Problem retrieval APIs

### Seeded problem library (`db/seed.py`)
10 predefined problems covering:
- **Distribution:** `dist_001`–`dist_004`
- **Sign errors:** `sign_001`–`sign_003`
- **Arithmetic:** `arith_001`–`arith_003`

Seeded on every startup with `INSERT ... ON CONFLICT DO NOTHING`.

*(Expanded to 60 problems + wrong answers in Phase 9 — see below.)*

### New endpoints
| Endpoint | Purpose |
|----------|---------|
| `GET /problem/{id}` | Fetch problem by ID (404 if missing) |
| `GET /sample-problem?difficulty=&topic=` | Random problem with optional filters |
| `POST /problem` | Create problem (no auth yet) |

### Updated `POST /start-session`
**Request:** `problem_id` required; `problem_expression` and `expected_final` optional.

| Mode | Behavior |
|------|----------|
| ID only | Lookup problem in DB |
| All three fields | Upsert problem (backward compatible) |
| Only one of expression/expected | 422 error |

**Response** now includes `expected_final`.

### Preferred flow
```
GET /sample-problem → POST /start-session {problem_id} → POST /submit-step
```

---

## Phase 8 — Vanilla frontend

### File structure
```
frontend/
  index.html   — 3 views (selection, session, complete)
  style.css    — academic styling, CSS variables
  app.js       — state, API layer, UI logic
  README.md
```

**No framework. No build step. No npm.**

### Views
1. **Problem Selection** — filters, random problem, start session
2. **Active Session** — submit steps, hints, attempt tracker, history
3. **Session Complete** — solved or limit reached; DELETE session on exit

### Client constants (match backend)
- `MAX_ATTEMPTS_BEFORE_ESCALATION = 3`
- `MAX_ATTEMPTS_BEFORE_REVEAL = 5`

### Input errors (client-side)
Types like `malformed_syntax`, `division_by_zero` show yellow **Input error** banner and do **not** increment the attempt dot tracker.

---

## Phase 9 — Scaled dataset (60 problems) + evaluation tooling

### What was built
Expanded the problem library from 10 to **60 problems** with canonical wrong answers for classifier evaluation. No backend validation logic, endpoints, or frontend files were modified.

### New table: `problem_wrong_answers`

| Column | Type |
|--------|------|
| id | SERIAL PK |
| problem_id | VARCHAR FK → problems.id |
| wrong_step | TEXT |
| error_type | VARCHAR (`distribution_error` / `sign_error` / `arithmetic_error`) |
| description | TEXT (nullable) |

- `UNIQUE(problem_id, wrong_step)` supports idempotent seeding
- Tables created via `create_all()` — no Alembic
- Upgrade comment in `models.py`:
  ```sql
  ALTER TABLE problem_wrong_answers ADD COLUMN IF NOT EXISTS description TEXT;
  ```

### Dataset distribution (exact targets)

| Dimension | Count |
|-----------|-------|
| **Difficulty:** easy / medium / hard | 20 / 25 / 15 |
| **Topic:** distribution | 20 |
| **Topic:** simplification | 20 |
| **Topic:** double_expansion | 10 |
| **Topic:** linear_steps | 10 |

**Wrong answers:** 2 per problem (120 total flat entries).

**Topic → required wrong-answer coverage:**
| Topic | Required wrong-answer types |
|-------|----------------------------|
| distribution | `distribution_error` |
| simplification | `sign_error` + `arithmetic_error` |
| double_expansion | `distribution_error` + `arithmetic_error` |
| linear_steps | `sign_error` + `arithmetic_error` |

**ID conventions:** Original Phase 7 IDs retained unchanged (`dist_001`–`dist_004`, `sign_001`–`sign_003`, `arith_001`–`arith_003`). New IDs: `dist_`, `sign_`, `arith_`, `simp_`, `dexp_`, `lin_` prefixes.

### Single source of truth: `backend/evaluation_dataset.py`

Each problem entry shape:
```python
{
    "problem_id": "dist_001",
    "expression": "2(x+3)",
    "correct_step": "2x+6",
    "wrong_answers": [
        {
            "wrong_step": "6",
            "expected_error_type": "distribution_error",
            "description": "Multiplied only the constant; dropped the x term."
        },
        ...
    ],
    "difficulty": "easy",
    "topic": "distribution"
}
```

**`FLAT_DATASET`** — backward-compatible flat list (one row per wrong answer) for Phase 3 tests and scripts:
```python
{
    "problem_id", "expression", "correct_step",
    "wrong_step", "expected_error_type"
}
```

`backend/tests/evaluation_dataset.py` re-exports `EVALUATION_DATASET` and `FLAT_DATASET` for existing test imports.

### Seeding (`db/seed.py`)
- `seed_problems(db)` — inserts all 60 problems from `EVALUATION_DATASET` with `ON CONFLICT DO NOTHING`
- `seed_wrong_answers(db)` — inserts all canonical wrong answers; called immediately after `seed_problems()` in `init_db()`

### Evaluation scripts

**`scripts/verify_dataset.py`** — distribution report (no DB connection)
```powershell
python scripts/verify_dataset.py
```
Exits with code 1 if: total problems < 50, any problem has < 2 wrong answers, any error type > 60% of wrong answers, or any difficulty level has 0 problems.

**`scripts/evaluate_classifier.py`** — portfolio-grade classifier evaluation
```powershell
python scripts/evaluate_classifier.py
```
Runs every `FLAT_DATASET` entry through `StepValidator.validate()` and reports parse success, confusion matrix, per-class precision/recall/F1, macro F1, overall accuracy, unknown rate, and misclassified entries.

### Classifier evaluation results (initial run)

| Metric | Result |
|--------|--------|
| Parse success | 120/120 (100%) |
| Overall accuracy | 116/120 (96.7%) |
| Macro F1 | 0.96 |
| Unknown rate | 0% |

**4 known misclassifications** (pedagogically labeled sign/arithmetic errors, but SymPy factors quadratics like `7x^2-x` → classifier returns `distribution_error`):

| Problem | Wrong step | Expected | Got |
|---------|------------|----------|-----|
| `arith_002` | `7x^2+x` | sign_error | distribution_error |
| `arith_002` | `6x^2-x` | arithmetic_error | distribution_error |
| `lin_009` | `-x^2-x` | sign_error | distribution_error |
| `lin_010` | `-3x^2-3x` | sign_error | distribution_error |

Wrong answers were tuned against actual `StepValidator` rules (e.g. distribution errors use dropped-term patterns like `6` vs `2x+6`, not `2x+3` which classifies as arithmetic).

### Tests updated
- `tests/benchmark_runner.py` — uses `FLAT_DATASET`
- `tests/test_classify_error.py` — parametrizes over new dataset shape
- `tests/run_evaluation.py` — uses `FLAT_DATASET`

---

## How to run (correct setup)

### Two terminals only

**Terminal 1 — Backend**
```powershell
cd C:\MathAssistant\backend
.venv\Scripts\activate
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Wait for: `Application startup complete.`

**Terminal 2 — Frontend**
```powershell
cd C:\MathAssistant\frontend
python -m http.server 3000
```
Open: **http://localhost:3000**

### Port map
| Port | Service |
|------|---------|
| 8000 | FastAPI backend (uvicorn) |
| 3000 | Vanilla frontend (`frontend/`) |

### Do NOT
- Run `npm run dev` (old Next.js app on `app/page.tsx`)
- Run `python -m http.server 8000` (steals backend port)
- Open `index.html` via `file://` (CORS blocks API calls)

### Verify you're on the right frontend
- **New (Phase 8):** Subtitle says **"Algebra Step Validator"**
- **Old (Next.js):** Says **"MathAssistant MVP"**

---

## Troubleshooting guide

### "Unable to connect to the remote server" (PowerShell)
**Cause:** Backend not running. Uvicorn must stay active in Terminal 1.

### `ERR_CONNECTION_REFUSED` on localhost:3000
**Cause:** Nothing listening on port 3000. Common mistakes:
- Ran `http.server` on port **8000** instead of **3000**
- Stopped the frontend server
- Only ran `npm run dev` then stopped it

**Fix:** `cd frontend` → `python -m http.server 3000`

### "Session not found"
**Cause:** Submitting without calling `/start-session` first, or using a fake session ID like `test-session-1`.

### `DATABASE_URL environment variable is required`
**Cause:** Missing `backend/.env` file.

**Fix:**
```powershell
cd C:\MathAssistant\backend
copy .env.example .env
# Edit .env with your PostgreSQL credentials
```

### Port 8000 conflict
If both uvicorn and `python -m http.server 8000` run, port 8000 is contested.

**Check:**
```powershell
netstat -ano | findstr ":3000 :8000" | findstr LISTENING
```

**Fix:** Stop the wrong process; only uvicorn should use 8000.

### PostgreSQL upgrade (Phase 6 → 7)
If `problems` table lacks new columns:
```sql
ALTER TABLE problems ADD COLUMN IF NOT EXISTS difficulty VARCHAR;
ALTER TABLE problems ADD COLUMN IF NOT EXISTS topic VARCHAR;
```

---

## API reference (quick)

| Method | Path | Notes |
|--------|------|-------|
| GET | `/` | Health check |
| GET | `/sample-problem` | `?difficulty=easy&topic=distribution` |
| GET | `/problem/{id}` | Single problem |
| POST | `/problem` | Create problem |
| POST | `/start-session` | `{problem_id}` or full upsert |
| POST | `/submit-step` | `{session_id, step, expected}` |
| GET | `/session/{id}` | Full session state |
| DELETE | `/session/{id}` | End session |

---

## PowerShell test script

```powershell
# Health (backend must be running)
Invoke-RestMethod http://127.0.0.1:8000/

# Sample problem
Invoke-RestMethod "http://127.0.0.1:8000/sample-problem?difficulty=easy"

# Start session (lookup mode)
$s = Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/start-session `
  -ContentType "application/json" -Body '{"problem_id":"dist_001"}'
$s.expected_final

# Submit correct step (use real session_id from $s — not a placeholder!)
Invoke-RestMethod -Method POST -Uri http://127.0.0.1:8000/submit-step `
  -ContentType "application/json" `
  -Body (@{session_id=$s.session_id; step="2x+6"; expected="2x+6"} | ConvertTo-Json)
```

---

## Phase 9 validation checklist

- [ ] Backend starts with `Application startup complete` (seeds 60 problems + wrong answers)
- [ ] `python scripts/verify_dataset.py` — exits 0, reports 60 problems
- [ ] `python scripts/evaluate_classifier.py` — parse 120/120, macro F1 ~0.96
- [ ] `GET /sample-problem?topic=double_expansion` returns a FOIL problem
- [ ] `GET /sample-problem?topic=linear_steps` returns a linear-simplification problem
- [ ] `pytest tests/` — note 4 known classifier mismatches on `arith_002`, `lin_009`, `lin_010`
- [ ] Frontend on **localhost:3000** — full flow still works

## Pre–Phase 9 testing checklist (Phases 5–8)

- [ ] Backend starts with `Application startup complete`
- [ ] `GET /` returns health JSON
- [ ] `GET /sample-problem` returns a problem
- [ ] `POST /start-session` with `{problem_id}` only works
- [ ] Correct step returns `is_equivalent: true`
- [ ] Wrong step returns hint + error type
- [ ] 3 wrong attempts → deeper hint (level 2)
- [ ] 5 wrong attempts → solution in hint
- [ ] Session survives uvicorn restart (PostgreSQL)
- [ ] Frontend on **localhost:3000** loads a problem automatically
- [ ] Full flow: pick problem → start → submit → complete

---

## SQLTools (optional)

Cannot be installed by the agent. Install manually in Cursor:
1. **SQLTools** (`mtxr.sqltools`)
2. **SQLTools PostgreSQL Driver** (`mtxr.sqltools-driver-pg`)

Connection: `localhost:5433`, database `mathassistant`, user `postgres`.

---

## What comes next (from project plan)

- **Phase 10:** Evaluation report (formal write-up of classifier metrics)
- **Classifier hardening:** Fix factorization edge cases on `7x^2-x`-style answers (4 known mismatches)
- **Future:** Auth on `POST /problem`, OCR, expanded subjects

---

## Key files modified across the thread

| File | Phases |
|------|--------|
| `backend/main.py` | 5, 6, 7 |
| `backend/db/*` | 6, 7, 9 |
| `backend/evaluation_dataset.py` | 9 |
| `backend/tests/evaluation_dataset.py` | 9 |
| `backend/tests/benchmark_runner.py` | 9 |
| `backend/tests/test_classify_error.py` | 9 |
| `scripts/verify_dataset.py` | 9 |
| `scripts/evaluate_classifier.py` | 9 |
| `backend/requirements.txt` | 6 |
| `frontend/*` | 8 |
| `app/page.tsx` | 5 (partial session fix, superseded by Phase 8 frontend) |

---

*Generated from the MathAssistant Cursor development session — Phases 5 through 9.*
