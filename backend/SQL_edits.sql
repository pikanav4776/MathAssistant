-- MathAssistant schema migrations (manual SQL)
-- Run against mathassistant on localhost:5433
-- Phases A/B use sol_path_id, sol_path_name, sol_step_id, sol_step_expression naming.

-- =============================================================================
-- Phase A — Auth (users + link on sessions)
-- =============================================================================
BEGIN;

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS email           VARCHAR,
    ADD COLUMN IF NOT EXISTS password_hash   VARCHAR,
    ADD COLUMN IF NOT EXISTS display_name    VARCHAR,
    ADD COLUMN IF NOT EXISTS role            VARCHAR NOT NULL DEFAULT 'student',
    ADD COLUMN IF NOT EXISTS last_login_at   TIMESTAMPTZ;

UPDATE users SET email = 'legacy_' || id || '@local.invalid', password_hash = 'CHANGE_ME' WHERE email IS NULL;

ALTER TABLE users
    ALTER COLUMN email SET NOT NULL,
    ALTER COLUMN password_hash SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_users_email ON users (email);

ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS user_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_sessions_user_id'
    ) THEN
        ALTER TABLE sessions
            ADD CONSTRAINT fk_sessions_user_id
            FOREIGN KEY (user_id) REFERENCES users (id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_sessions_user_id ON sessions (user_id);

COMMIT;

-- =============================================================================
-- Phase B — Multi-step solution paths
-- =============================================================================
BEGIN;

CREATE TABLE IF NOT EXISTS solution_paths (
    sol_path_id     SERIAL PRIMARY KEY,
    problem_id      VARCHAR NOT NULL REFERENCES problems (id) ON DELETE CASCADE,
    sol_path_name   VARCHAR NOT NULL DEFAULT 'default',
    is_primary      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_solution_paths_problem_id ON solution_paths (problem_id);

CREATE TABLE IF NOT EXISTS solution_steps (
    sol_step_id           SERIAL PRIMARY KEY,
    path_id               INTEGER NOT NULL REFERENCES solution_paths (sol_path_id) ON DELETE CASCADE,
    step_order            INTEGER NOT NULL,
    sol_step_expression   TEXT NOT NULL,
    hint_template         TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_solution_steps_path_order UNIQUE (path_id, step_order)
);

CREATE INDEX IF NOT EXISTS ix_solution_steps_path_id ON solution_steps (path_id);

ALTER TABLE sessions
    ADD COLUMN IF NOT EXISTS current_step_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_sessions_current_step_id'
    ) THEN
        ALTER TABLE sessions
            ADD CONSTRAINT fk_sessions_current_step_id
            FOREIGN KEY (current_step_id) REFERENCES solution_steps (sol_step_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_sessions_current_step_id ON sessions (current_step_id);

ALTER TABLE problem_wrong_answers
    ADD COLUMN IF NOT EXISTS solution_step_id INTEGER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_pwa_solution_step_id'
    ) THEN
        ALTER TABLE problem_wrong_answers
            ADD CONSTRAINT fk_pwa_solution_step_id
            FOREIGN KEY (solution_step_id) REFERENCES solution_steps (sol_step_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS ix_pwa_solution_step_id ON problem_wrong_answers (solution_step_id);

INSERT INTO solution_paths (problem_id, sol_path_name, is_primary)
SELECT p.id, 'default', TRUE
FROM problems p
WHERE NOT EXISTS (
    SELECT 1 FROM solution_paths sp WHERE sp.problem_id = p.id AND sp.is_primary = TRUE
);

INSERT INTO solution_steps (path_id, step_order, sol_step_expression)
SELECT sp.sol_path_id, 1, p.expected_final
FROM problems p
JOIN solution_paths sp ON sp.problem_id = p.id AND sp.is_primary = TRUE
WHERE NOT EXISTS (
    SELECT 1 FROM solution_steps ss WHERE ss.path_id = sp.sol_path_id AND ss.step_order = 1
);

-- Optional: stop requiring expected_final on problems once app reads solution_steps
-- ALTER TABLE problems ALTER COLUMN expected_final DROP NOT NULL;

COMMIT;

-- =============================================================================
-- Phase C — Analytics / reporting
-- Column names aligned with Phase A/B sessions table (attempt_count, etc. used in backfill)
-- =============================================================================
BEGIN;

CREATE TABLE IF NOT EXISTS session_summaries (
    session_id          VARCHAR PRIMARY KEY REFERENCES sessions (session_id) ON DELETE CASCADE,
    user_id             INTEGER REFERENCES users (id),
    problem_id          VARCHAR NOT NULL REFERENCES problems (id),
    total_attempts      INTEGER NOT NULL DEFAULT 0,
    incorrect_attempts  INTEGER NOT NULL DEFAULT 0,
    completed           BOOLEAN NOT NULL DEFAULT FALSE,
    revealed_solution   BOOLEAN NOT NULL DEFAULT FALSE,
    duration_seconds    INTEGER,
    final_error_type    VARCHAR,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_session_summaries_problem_id ON session_summaries (problem_id);
CREATE INDEX IF NOT EXISTS ix_session_summaries_user_id ON session_summaries (user_id);

CREATE TABLE IF NOT EXISTS daily_problem_stats (
    stat_date           DATE NOT NULL,
    problem_id          VARCHAR NOT NULL REFERENCES problems (id),
    sessions_started    INTEGER NOT NULL DEFAULT 0,
    sessions_completed  INTEGER NOT NULL DEFAULT 0,
    avg_attempts        NUMERIC(10, 2),
    top_error_type      VARCHAR,
    PRIMARY KEY (stat_date, problem_id)
);

CREATE TABLE IF NOT EXISTS daily_error_stats (
    stat_date   DATE NOT NULL,
    error_type  VARCHAR NOT NULL,
    count       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (stat_date, error_type)
);

COMMIT;

-- =============================================================================
-- Backfill session_summaries from existing sessions/attempts
-- Maps sessions.attempt_count -> total_attempts, incorrect_attempt_count -> incorrect_attempts
-- =============================================================================
INSERT INTO session_summaries (
    session_id,
    user_id,
    problem_id,
    total_attempts,
    incorrect_attempts,
    completed,
    revealed_solution,
    completed_at
)
SELECT
    s.session_id,
    s.user_id,
    s.problem_id,
    s.attempt_count,
    s.incorrect_attempt_count,
    EXISTS (
        SELECT 1 FROM attempts a
        WHERE a.session_id = s.session_id AND a.is_equivalent = TRUE
    ) AS completed,
    s.incorrect_attempt_count >= 5 AS revealed_solution,
    s.last_active
FROM sessions s
ON CONFLICT (session_id) DO NOTHING;
