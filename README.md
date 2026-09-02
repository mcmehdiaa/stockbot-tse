# StockBot TSE

Lightweight, production-oriented market monitoring bot for up to 100 approved users.

## Current phase

Phase 1 establishes configuration, database ownership, access rules, and contracts for three isolated pipelines. It deliberately does not contain credentials, polling loops, or unverified market-provider code.

## Components

- `tse`: TSETMC, Codal, and fund sources.
- `crypto`: independent provider and indicators.
- `forex`: independent provider and indicators.
- PostgreSQL: source of truth for users, subscriptions, runs, alerts, and deliveries.
- Telegram: primary delivery channel through the Vercel relay.
- Bale: independent secondary delivery channel.

## Local bootstrap

1. Copy `.env.example` to `.env` and fill values locally. Never commit `.env`.
2. Create the PostgreSQL schema: `psql "$DATABASE_URL" -f sql/001_init.sql`.
3. Install dependencies from `pyproject.toml` when the server is ready.

After setting a verified `TSE_MARKET_WATCH_URL`, run one isolated TSE ingestion:

```bash
python -m stockbot.main tse-once
```

It records success or failure in `pipeline_runs` and stores unmodified rows in
`market_snapshots`. It does not contact Telegram, Bale, crypto, or forex.

## Ubuntu worker

Use `python3` on Ubuntu 22.04. The worker is disabled by default, so it cannot
poll a provider until `TSE_SCHEDULE_ENABLED=true` and a verified source URL are
set in `/etc/stockbot-tse.env`. Deployment templates are in `deploy/`.

Telegram uses a separate `stockbot-telegram.service`; it performs long polling
only when `TELEGRAM_POLL_ENABLED=true`.

Bale is a separate worker and token (`stockbot-bale.service`), enabled only by
`BALE_POLL_ENABLED=true`.

See `docs/PHASE_1.md` for acceptance criteria and next decisions.
