# Phase 1: architecture and data ownership

## Decisions already fixed

1. The database is authoritative; neither Telegram nor Bale state grants access.
2. A person can link one Telegram identity and one Bale identity, independently.
3. A subscription begins `pending`; an administrator approves it to `active`.
4. Revocation is immediate. An expiry timestamp is evaluated before every delivery.
5. The database trigger prevents more than 100 currently active, non-expired users.
6. Telegram delivery is primary. Bale delivery failures must not block Telegram.
7. `tse`, `crypto`, and `forex` run independently and record separate executions.
8. Telegram is selected before Bale for a user who linked both identities; a failed Telegram delivery may fall back to Bale.
9. Telegram commands are `/start`, `/status`, `/approve USER_UUID [YYYY-MM-DD]`, and `/revoke USER_UUID`; the latter two are restricted to configured admin IDs.

## Before Phase 2

- Verify the PostgreSQL database name and apply `sql/001_init.sql` on a disposable database first.
- Put the already-tested TSETMC endpoint in `TSE_MARKET_WATCH_URL`; no endpoint is hard-coded.
- Choose one provider each for crypto and forex; their APIs must be configured independently.
- Obtain admin chat IDs after each bot receives a `/start` message.
- Fix and test the Vercel relay separately before Telegram delivery is enabled.

## Acceptance criteria

- Configuration validation succeeds with secrets supplied only through `.env` or service environment variables.
- The database accepts pending users, approval, expiry, and revocation.
- An attempt to create a 101st active, unexpired subscription fails transactionally.
- Each pipeline can fail and report its own run without stopping another pipeline.
