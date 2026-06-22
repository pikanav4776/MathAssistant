# MathAssistant Frontend

React + TypeScript UI (Vite) for the MathAssistant **v1.0** algebra co-solver.

See the root [README.md](../README.md) for full project setup (database, backend, testing) and [documentation/v1.0_Scope.md](../documentation/v1.0_Scope.md) for in-scope vs deferred features.

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

You should see the subtitle **"Algebra Co-Solving (v1.0)"**.

### Environment

Copy `.env.example` to `.env` if you need a non-default API URL:

```powershell
copy .env.example .env
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | FastAPI backend base URL |

Backend auth-related variables (for when login endpoints ship) live in `backend/.env` — see `backend/.env.example`:

| Variable | Required | Purpose |
|----------|----------|---------|
| `JWT_SECRET` | Production | Signing key for access tokens (dev uses insecure placeholder if unset) |
| `JWT_ALGORITHM` | Optional | Default `HS256` |
| `JWT_EXPIRE_MINUTES` | Optional | Token lifetime (default 60) |

v1.0 has **auth foundation only** (User model, bcrypt, JWT utilities). There is no login UI or Bearer token handling in the frontend yet.

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

### Problem entry (text or calculator)

1. **Enter a problem** — Type in the problem field **or** use the **calculator keypad** below it.
2. **Calculator** — Tap keys to build an expression in the preview. Heuristic checks block empty input, text-like words, and unbalanced parentheses. Click **Use Expression** to copy the preview into the problem field (you still click **Start Session** separately).
3. **Start session** — Calls `POST /start-session` with `problem_expression`.
4. **Submit your next step** — Type one algebraic transformation in the step field and click **Check Step** (calculator on step entry is deferred to a later release).
5. **Get iterative feedback** — Server compares to the expected next step, classifies errors, and advances only on correct submissions.
6. **Finish** — Session completes once the final canonical step is reached (or reveal after repeated incorrect attempts).

### Library example

Click **Try an example from library** to load `GET /sample-problem` into the problem field, then start the session as above.

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
- Equations / inequalities and non-keyboard math symbols are intentionally rejected in v1.0.
- Calculator is on the **problem selection** screen only; step entry is keyboard-only for now.
- No authentication UI in v1.0; all session APIs are anonymous.
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
    hooks/
      useSession.ts       — session state and handlers
      useExpressionBuilder.ts — calculator expression state
    types/api.ts          — TypeScript types from backend models
    views/                — ProblemSelection, ActiveSession, SessionComplete
    components/
      CalculatorPanel.tsx — problem-entry keypad UI
      AttemptTracker, FeedbackPanel, MathExpression, etc.
    utils/
      algebraToLatex.ts   — keyboard algebra → LaTeX (display only)
      expressionHeuristic.ts — client-side validation for calculator
      expressionTokens.ts — keypad layout
      expressionTextLike.ts — shared text-like input guard
    styles/
      global.css          — app styles
      calculator.css      — calculator panel styles
  legacy/                 — original vanilla HTML/CSS/JS (reference only)
  README.md               — this file
```
