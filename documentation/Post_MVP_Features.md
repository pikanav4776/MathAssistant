# Post-MVP feature notes

## User activity summaries (opt-in)

**Idea:** Per-account weekly or monthly email summaries of what the student worked on — topics practiced, problems attempted, common error types — sent only when the user opts in.

**Possible Azure stack:**

- **Azure Functions** — scheduled trigger (e.g. weekly cron) to aggregate data per user
- **Azure Communication Services** or **SendGrid** — transactional email delivery
- **Data source** — existing `sessions` and `attempts` tables in PostgreSQL (no new store required for a first version)

This is an architectural placeholder only; not in MVP scope.
