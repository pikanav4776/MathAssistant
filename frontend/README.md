# MathAssistant Frontend

React + TypeScript UI (Vite) for the MathAssistant v0.3 algebra co-solver.

See the root [README.md](../README.md) for full project setup (database, backend, testing).

## Prerequisites

1. **Backend** running at `http://127.0.0.1:8000` (see root README)
2. **PostgreSQL** configured via `backend/.env` (`DATABASE_URL`; see `backend/.env.example`)
3. **Node.js** 18+ for the Vite dev server

## Development

**Do not open `index.html` directly** (`file://`) — browsers block API requests.

### Ports

| Service | Port | Command | URL |
|---------|------|---------|-----|
| **Backend** (FastAPI) | **8000** | `.\start.ps1` from `backend/` | http://127.0.0.1:8000 |
| **Frontend** (Vite) | **3000** | `npm run dev` from `frontend/` | http://localhost:3000 |

**Do NOT** run `python -m http.server 8000` — that steals the backend port.
**Do NOT** run `npm run dev` from the repo root — that is the deprecated Next.js demo in `app/`, not this frontend.

```powershell
cd frontend
npm install
npm run dev
```

Or:

```powershell
cd frontend
.\start.ps1
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

## Production deploy (Render)

The static site service (`mathassistant-frontend` in [render.yaml](../render.yaml)) builds from this directory:

1. **Build command:** `npm ci && VITE_API_BASE_URL=$API_BASE_URL npm run build`
2. **Publish path:** `dist/`
3. **Dashboard env var:** `API_BASE_URL` — backend public HTTPS URL (e.g. `https://mathassistant-api.onrender.com`, no trailing slash). Render injects this as `VITE_API_BASE_URL` at build time.

Staging uses the same pattern via [render-staging.yaml](../render-staging.yaml) (`mathassistant-frontend-staging`).

Set the backend `CORS_ORIGINS` env var to your frontend URL (e.g. `https://mathassistant-frontend.onrender.com`) so the browser can call the API. Port **3000** is already allowed in backend defaults for local dev.

After deploy, verify:

- Frontend loads at the Render static site URL.
- Browser network tab shows API calls to `API_BASE_URL` (not localhost).
- No CORS errors when submitting a step.

## Legacy vanilla app

The original HTML/CSS/JS UI is preserved under `legacy/` for reference only (not deployed). It used `window.API_BASE` from `config.js`; the React app uses `VITE_API_BASE_URL` instead.

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
  start.ps1               — npm run dev helper
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
    styles/global.css     — app styles
  legacy/                 — original vanilla HTML/CSS/JS (reference only)
  README.md               — this file
```
