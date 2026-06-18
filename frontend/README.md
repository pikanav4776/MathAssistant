# MathAssistant Frontend

React + TypeScript UI (Vite) for the MathAssistant v0.3 algebra co-solver.

See the root [README.md](../README.md) for full project setup (database, backend, testing).

## Prerequisites

1. **Backend** running at `http://127.0.0.1:8000` (see root README)
2. **PostgreSQL** configured via `backend/.env` (`DATABASE_URL`; see `backend/.env.example`)
3. **Node.js** 18+ for the Vite dev server

## Development (React app — recommended)

**Do not open `index.html` directly** (`file://`) — browsers block API requests.

### IMPORTANT — correct ports

| Service | Port | Command | URL |
|---------|------|---------|-----|
| **Backend** (FastAPI) | **8000** | `.\start.ps1` from `backend/` | http://127.0.0.1:8000 |
| **Frontend** (Vite) | **3000** | `npm run dev` from `frontend/` | http://localhost:3000 |

**Do NOT** run `python -m http.server 8000` — that steals the backend port.
**Do NOT** run `npm run dev` from the repo root — that is the legacy Next.js app in `app/`, not this frontend.

```powershell
cd frontend
npm install
npm run dev
```

Open: **http://localhost:3000**

You should see the subtitle **"Algebra Co-Solving (v0.3)"**.

### Environment

Copy `.env.example` to `.env` if you need a non-default API URL:

```powershell
copy .env.example .env
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | FastAPI backend base URL |

### Build

```powershell
cd frontend
npm run build
```

Output goes to `frontend/dist/`. Preview locally with `npm run preview`.

## Legacy vanilla app

The original HTML/CSS/JS UI is kept for reference:

- Root copies: `app.js`, `style.css`, `config.js`
- Mirror in `legacy/` (includes the old `index.html` shell)

Serve the legacy app with Python (no build step):

```powershell
cd frontend
.\start.ps1
```

Legacy uses `window.API_BASE` from `config.js` instead of `VITE_API_BASE_URL`.

## Production API URL

**Stage 1:** Production still deploys the vanilla static site via root [render.yaml](../render.yaml) (unchanged). Stage 3 will switch Render to the Vite build output.

For the React app locally, set `VITE_API_BASE_URL` in `.env`. For legacy deployment, Render overwrites `config.js` from the `API_BASE_URL` env var:

```bash
echo "window.API_BASE = \"$API_BASE_URL\";" > config.js
```

Set the backend `CORS_ORIGINS` env var to your frontend URL so the browser can call the API (see `backend/.env.example`). Port **3000** is already allowed for local dev.

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
| Load session (give up) | `GET /session/{id}` |
| Load problem (give up) | `GET /problem/{id}` |
| Clean up | `DELETE /session/{id}` |

## Known limitations

- The frontend must be served over HTTP (not `file://`) for API calls to work.
- If the backend is not running, all requests fail with a connection error.
- Refreshing the page mid-session loses client state (the session may still exist in the database until deleted).
- Input notation errors (e.g. using `**` instead of `^`) show a warning and do not count toward the 5-attempt limit.
- Equations / inequalities and non-keyboard math symbols are intentionally rejected in v0.3.
- Display-only expressions (current problem, history steps, completion screen) render with **KaTeX** via `algebraToLatex` + `MathExpression`. Step and problem inputs stay plain keyboard algebra; API payloads are unchanged.

## File structure

```
frontend/
  index.html              — Vite entry (React app)
  package.json            — npm scripts and dependencies
  vite.config.ts          — dev server on port 3000
  .env.example            — VITE_API_BASE_URL template
  src/
    App.tsx               — view router
    main.tsx              — React entry
    api/client.ts         — typed API client
    constants.ts          — attempt limits and error type sets
    hooks/useSession.ts   — session state and handlers
    types/api.ts          — TypeScript types from backend models
    views/                — ProblemSelection, ActiveSession, SessionComplete
    components/           — AttemptTracker, FeedbackPanel, MathExpression, etc.
    utils/algebraToLatex.ts — keyboard algebra → LaTeX (display only)
    styles/global.css     — ported from style.css
  legacy/                 — vanilla index.html mirror
  app.js, style.css, ...  — original vanilla files (reference)
  README.md               — this file
```
