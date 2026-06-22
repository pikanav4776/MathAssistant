# Production Security Notes

Concise security posture for MathAssistant v1.0.

**Last updated:** June 22, 2026

---

## Secrets

- **Never commit** `.env`, connection strings, JWT secrets, or Sentry DSNs.
- `.gitignore` excludes `.env*` (except `.env.example`).
- On Render (`RENDER=true`), the API **refuses to start** if `JWT_SECRET` is unset or still the development default.

Generate a production secret (example):

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Authentication

- Passwords hashed with **bcrypt** before storage.
- API uses **JWT** bearer tokens (`Authorization: Bearer …`).
- Guest tutoring allowed; owned sessions require matching user or admin role.

---

## CORS

- Production must set `CORS_ORIGINS` to explicit frontend origin(s).
- Local dev defaults allow `localhost:3000` / `127.0.0.1:3000` when `CORS_ORIGINS` is unset.
- Do not use `*` with credentials.

---

## Rate limiting

Per-IP sliding-window limits (in-memory, per worker):

| Endpoint | Limit |
|----------|-------|
| `POST /auth/login` | 10 / minute |
| `POST /auth/register` | 5 / minute |
| `POST /start-session` | 30 / minute |
| `POST /submit-step` | 120 / minute |

Returns `429` with `rate_limit_exceeded`. Disable locally with `RATE_LIMIT_ENABLED=false`.

---

## SQL injection

All database access uses **SQLAlchemy ORM** or parameterized queries. No raw SQL from user input.

---

## Error monitoring

- **Sentry** initializes only when `SENTRY_DSN` is set.
- Student-facing responses never expose raw SymPy tracebacks.

---

## Health probes

| Endpoint | Use |
|----------|-----|
| `GET /health` | Liveness (Render health check) |
| `GET /ready` | Readiness (includes DB `SELECT 1`) |

---

## Related docs

- [v1.0_Release_Checklist.md](v1.0_Release_Checklist.md)
- [Database_Operations.md](Database_Operations.md)
- [Technical_Architecture_Spec.txt](Technical_Architecture_Spec.txt)
