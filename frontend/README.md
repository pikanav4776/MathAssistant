# MathAssistant Frontend

Vanilla HTML, CSS, and JavaScript UI for the MathAssistant algebra step validator.

See the root [README.md](../README.md) for full project setup (database, backend, testing).

## Prerequisites

1. **Backend** running at `http://127.0.0.1:8000` (see root README)
2. **PostgreSQL** configured via `backend/.env` (`DATABASE_URL`; see `backend/.env.example`)

## Serve the frontend

**Do not open `index.html` directly** (`file://`) — browsers block API requests.

### IMPORTANT — correct ports

| Service | Port | Command | URL |
|---------|------|---------|-----|
| **Backend** (FastAPI) | **8000** | `.\start.ps1` from `backend/` | http://127.0.0.1:8000 |
| **Frontend** (this app) | **3000** | `.\start.ps1` from `frontend/` | http://localhost:3000 |

**Do NOT** run `python -m http.server 8000` — that steals the backend port.
**Do NOT** run `npm run dev` — that is the legacy Next.js app in `app/`, not this frontend.

```powershell
cd frontend
.\start.ps1
```

Open: **http://localhost:3000**

You should see the subtitle **"Algebra Step Validator"** (not "MathAssistant MVP").

## User flow

1. **Pick a problem** — A random problem loads on startup. Use Difficulty/Topic filters and "Get a Problem" to fetch another.
2. **Start session** — Click "Start Session". The app calls `POST /start-session` with the problem ID.
3. **Submit steps** — Type your simplified expression and click "Check Step" (or press Enter).
4. **Get feedback** — See correctness, error type, and hints. After 3 wrong math answers, hints go deeper. After 5, the solution is revealed.
5. **Finish** — Correct answer or limit reached shows the completion screen. "Reveal solution" ends early.
6. **Try again** — "Try another problem" resets everything and returns to problem selection.

## API endpoints used

| Action | Endpoint |
|--------|----------|
| Load problem | `GET /sample-problem` |
| Start tutoring | `POST /start-session` |
| Check answer | `POST /submit-step` |
| Clean up | `DELETE /session/{id}` |

## Known limitations

- The frontend must be served over HTTP (not `file://`) for API calls to work.
- If the backend is not running, all requests fail with a connection error.
- Refreshing the page mid-session loses client state (the session may still exist in the database until deleted).
- Input notation errors (e.g. using `**` instead of `^`) show a warning but do not count toward the 5-attempt limit.

## File structure

```
frontend/
  index.html   — page shell and three views
  style.css    — all styles (CSS variables, mobile-friendly)
  app.js       — state, API layer, and UI logic
  README.md    — this file
```
