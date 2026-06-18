# Database Operations

Operational guide for MathAssistant PostgreSQL (Neon in production/staging).

See also: [Technical_Architecture_Spec.txt](Technical_Architecture_Spec.txt) (migrations, deploy, staging).

---

## Schema migrations (Alembic)

Migrations live in `backend/alembic/versions/`. Run all commands from `backend/` (where `alembic.ini` lives):

```powershell
cd backend
alembic upgrade head
```

**Fresh database:** `alembic upgrade head` applies the baseline no-op revision and the `create_initial_schema` revision (full DDL).

**Existing production database** (schema already created via prior `create_all()` or manual SQL): run a **one-time** stamp so Alembic matches reality without re-creating tables:

```powershell
cd backend
# DATABASE_URL must point at the existing prod database
alembic stamp head
```

After stamping, future schema changes use new Alembic revisions and `alembic upgrade head` on deploy (see `render.yaml` `startCommand`).

**Local development:** `init_db()` still calls `create_all()` when `ENVIRONMENT=development`, `SKIP_MIGRATIONS=true`, or `DATABASE_URL` points at localhost — see `backend/db/database.py`.

---

## Pre-migration snapshot (production)

Before running `alembic upgrade head` against production (or any manual migration):

1. **Neon console:** Project → Branches → select production branch → **Create branch** (instant copy) or note current time for PITR (below).
2. **Optional logical dump** (portable backup):

   ```powershell
   pg_dump "$env:DATABASE_URL" -Fc -f mathassistant-pre-migration.dump
   ```

3. Run migration on a **staging** Neon branch first when possible; smoke-test `/ready` and core API flows.
4. Apply to production during a low-traffic window; monitor Render logs and Sentry.

If upgrade fails, restore from PITR or the pre-migration branch/dump — do not re-run blindly.

---

## Neon point-in-time recovery (PITR)

Neon retains history on paid plans (and limited history on free tier — check your Neon plan).

**When to rely on PITR**

- Accidental data loss or bad migration on production
- Need to recover to a time before a destructive change

**Restore (high level)**

1. Neon Dashboard → your project → **Branches**.
2. **Restore** or **Create branch from time** — pick timestamp **before** the incident.
3. Update Render `DATABASE_URL` on `mathassistant-api` to the restored branch connection string (or swap branch roles per Neon docs).
4. Verify `/ready`, sample API calls, then re-point traffic or merge data as needed.

**When to enable / upgrade PITR**

- Before first production migration after MVP
- When storing non-recreatable user/session data at scale
- Align retention with your RPO (how far back you must be able to restore)

---

## pg_dump alternative

For off-Neon backups or migration archives:

```powershell
# Custom format (recommended for pg_restore)
pg_dump "postgresql://..." -Fc -f backup.dump

# Plain SQL
pg_dump "postgresql://..." -f backup.sql
```

Restore (custom format):

```powershell
pg_restore -d "postgresql://..." --clean --if-exists backup.dump
```

Store dumps encrypted; never commit connection strings or dump files to the repo.

---

## Health checks

| Endpoint   | Purpose | DB check |
|-----------|---------|----------|
| `GET /health` | Liveness (Render health check) | No |
| `GET /ready`  | Readiness (DB up) | `SELECT 1` |

Render uses `/health` per `render.yaml` `healthCheckPath`.
