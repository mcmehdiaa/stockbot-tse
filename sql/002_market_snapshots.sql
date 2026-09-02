BEGIN;

CREATE TABLE market_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider TEXT NOT NULL,
    symbol TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (provider, symbol, observed_at)
);

CREATE INDEX market_snapshots_lookup
    ON market_snapshots (provider, symbol, observed_at DESC);

COMMIT;
