BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE channel_name AS ENUM ('telegram', 'bale');
CREATE TYPE subscription_status AS ENUM ('pending', 'active', 'revoked', 'expired');
CREATE TYPE pipeline_name AS ENUM ('tse', 'crypto', 'forex');
CREATE TYPE run_status AS ENUM ('started', 'succeeded', 'failed');
CREATE TYPE delivery_status AS ENUM ('queued', 'sent', 'failed', 'skipped');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel channel_name NOT NULL,
    chat_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (channel, chat_id),
    UNIQUE (user_id, channel)
);

CREATE TABLE subscriptions (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    status subscription_status NOT NULL DEFAULT 'pending',
    approved_by TEXT,
    approved_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    revoke_reason TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((status <> 'active') OR approved_at IS NOT NULL),
    CHECK ((expires_at IS NULL) OR expires_at > '1970-01-01 00:00:00+00'::timestamptz)
);

CREATE OR REPLACE FUNCTION enforce_active_user_cap() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status = 'active' AND (NEW.expires_at IS NULL OR NEW.expires_at > now()) THEN
    IF NOT EXISTS (SELECT 1 FROM subscriptions WHERE user_id = NEW.user_id AND status = 'active')
       AND (SELECT count(*) FROM subscriptions WHERE status = 'active' AND (expires_at IS NULL OR expires_at > now())) >= 100 THEN
      RAISE EXCEPTION 'active user limit (100) reached';
    END IF;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER subscription_user_cap
BEFORE INSERT OR UPDATE OF status, expires_at ON subscriptions
FOR EACH ROW EXECUTE FUNCTION enforce_active_user_cap();

CREATE TABLE pipeline_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline pipeline_name NOT NULL,
    status run_status NOT NULL DEFAULT 'started',
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    item_count INTEGER NOT NULL DEFAULT 0 CHECK (item_count >= 0),
    error_code TEXT,
    error_detail TEXT
);
CREATE INDEX pipeline_runs_recent ON pipeline_runs (pipeline, started_at DESC);

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pipeline pipeline_name NOT NULL,
    symbol TEXT NOT NULL,
    score NUMERIC(8, 3),
    body TEXT NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE deliveries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    channel channel_name NOT NULL,
    status delivery_status NOT NULL DEFAULT 'queued',
    provider_message_id TEXT,
    attempts SMALLINT NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    last_error TEXT,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (alert_id, user_id, channel)
);

COMMIT;
