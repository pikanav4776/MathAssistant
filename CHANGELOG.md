# Changelog

All notable changes to MathAssistant are documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Version numbers align with git tags when released.

## [1.0.0] - 2026-06-22

### Added

- **Calculator UI** on the problem-entry screen: QWERTY-style keypad, live preview, client-side heuristic validation, and **Use Expression** to fill the problem field.
- **Calculator on active session** - same keypad under step input; **Use Expression** fills the step field.
- **Auth foundation** (scaffolding only): `User` model with roles, bcrypt password hashing, JWT create/decode helpers, Alembic migration `b2c8e4f01a23`, and `test_auth.py`. Login/register endpoints and session ownership are deferred.
- **Vitest** in CI: `expressionHeuristic` and `expressionTextLike` unit tests.
- Mobile calculator CSS: 44px touch targets, 10-column grid on narrow screens.
- **Session resume** after page refresh via `sessionStorage` and enriched `GET /session/{id}`.
- **Session summaries** persisted on complete/give-up via `POST /session/{id}/finalize`.
- **Signed-in session history** on problem selection (`GET /auth/me/sessions`, `SessionHistoryPanel`).
- **Friendly error messages** for unsupported problems, auth errors, and network failures.
- `friendlyErrorMessage` utility tests.

### Changed

- Product version unified to **v1.0 (Algebra Co-Solving)** across docs, API metadata, and UI subtitle.
- Sessions are **finalized** instead of deleted on complete, so `session_summaries` rows are retained.
- Session timestamps use timezone-aware UTC (`_utc_now`) instead of deprecated `datetime.utcnow()`.
- Calculator scope notes in UI: new problems stay algebra-only; sqrt/mod/comparisons not supported for problem entry.

### Documentation

- `CHANGELOG.md`, `documentation/v1.0_Scope.md`, and updated README / architecture / frontend docs.

---

## [0.5.0] - 2026-06-19

### Added

- Backend calculator path: expanded `expression_preprocess.py` (text-like input detection), calculator-aware validation in `main.py`, and `test_calculator_expressions.py`.

---

## [0.4.3] - 2026-06-18

### Fixed

- Render deploy and CORS configuration for production/staging frontends.

---

## [0.4.0] - 2026-06-17

### Added

- Primary **React + TypeScript + Vite** frontend in `frontend/` (replaces deprecated Next.js demo in `app/`).
- **KaTeX** for display-only math rendering.
- Render Blueprint (`render.yaml`, `render-staging.yaml`) and GitHub Actions CI (backend pytest + frontend build).

---

## [0.3.5] - 2026-06-16

### Added

- Multi-hop canonical solution paths in `step_engine.py` (distribute-then-combine, FOIL-then-combine).
- Expanded evaluation dataset and integration tests.

---

## [0.3.0] - 2026-06-15

### Added

- **Algebra co-solving MVP**: problem-only sessions, server-derived step validation against canonical paths, skip-ahead, `term_reorder` / `no_progress` handling.
- Session APIs: `POST /start-session`, `POST /submit-step`, `GET /session/{id}`.
- PostgreSQL persistence (problems, sessions, attempts, solution paths).
- Problem library: `GET /sample-problem`, `GET /problem/{id}`, `POST /problem` (admin, no auth).
- Deterministic pipeline: parse -> normalize -> compare -> classify -> hint.
- Structured keyboard input only (`^` for exponents); no OCR.

### Scope limits (carried into v1.0)

- Algebra only; no calculus, geometry, or statistics.
- No LLM at request time; no automatic problem generation.
- Seed problem library only.