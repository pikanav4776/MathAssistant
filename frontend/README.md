# MathAssistant Frontend

Vanilla HTML, CSS, and JavaScript UI for the MathAssistant v0.3 algebra co-solver.

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

You should see the subtitle **"Algebra Co-Solving (v0.3)"**.

## Production API URL

The backend URL is set in `config.js` (loaded before `app.js`). Local dev defaults to `http://127.0.0.1:8000` via the committed `config.js` — no extra setup.

For deployment, Render's build step (see root [render.yaml](../render.yaml)) overwrites `config.js` from the `API_BASE_URL` env var:

```bash
echo "window.API_BASE = \"$API_BASE_URL\";" > config.js
```

Set the backend `CORS_ORIGINS` env var to your frontend URL so the browser can call the API (see `backend/.env.example`). See [documentation/Technical_Architecture_Spec.txt](../documentation/Technical_Architecture_Spec.txt) for the full Render + Neon checklist.

## User flow

1. **Enter a problem** — Type a keyboard-style algebra expression (e.g. `2(x+3)`).
2. **Start session** — The app calls `POST /start-session` with `problem_expression` only.
3. **Submit your next step** — Type one algebraic transformation and click "Check Step".
4. **Get iterative feedback** — The server compares to the expected next step, classifies errors, and advances only on correct submissions.
5. **Finish** — Session completes once the final canonical step is reached (or reveal after repeated incorrect attempts).

## API endpoints used

| Action | Endpoint |
|--------|----------|
| Load example problem | `GET /sample-problem` |
| Start tutoring | `POST /start-session` |
| Check step | `POST /submit-step` |
| Clean up | `DELETE /session/{id}` |

## Known limitations

- The frontend must be served over HTTP (not `file://`) for API calls to work.
- If the backend is not running, all requests fail with a connection error.
- Refreshing the page mid-session loses client state (the session may still exist in the database until deleted).
- Input notation errors (e.g. using `**` instead of `^`) show a warning and do not count toward the 5-attempt limit.
- Equations / inequalities and non-keyboard math symbols are intentionally rejected in v0.3.

## File structure

```
frontend/
  index.html   — page shell and three views
  config.js    — API base URL (override for production)
  style.css    — all styles (CSS variables, mobile-friendly)
  app.js       — state, API layer, and UI logic
  README.md    — this file
```
