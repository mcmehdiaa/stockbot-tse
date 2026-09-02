BEGIN;

CREATE TABLE service_cursors (
    name TEXT PRIMARY KEY,
    cursor_value BIGINT NOT NULL DEFAULT 0 CHECK (cursor_value >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;
