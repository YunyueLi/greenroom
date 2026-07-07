-- greenroom cloud worker — metering & entitlement (Cloudflare D1 / SQLite)
-- Apply:  npx wrangler d1 execute greenroom-meter --remote --file=schema.sql
-- Re-runnable (IF NOT EXISTS).

-- Per-user, per-day, per-endpoint usage. calls = the gate currency (legible free limits);
-- tok_in / tok_out = real model token usage (cost truth + future usage-based billing).
CREATE TABLE IF NOT EXISTS usage (
  user_id  TEXT    NOT NULL,
  day      TEXT    NOT NULL,            -- YYYY-MM-DD (UTC)
  endpoint TEXT    NOT NULL,            -- answer | setup | mock
  calls    INTEGER NOT NULL DEFAULT 0,
  tok_in   INTEGER NOT NULL DEFAULT 0,
  tok_out  INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, day, endpoint)
);
CREATE INDEX IF NOT EXISTS usage_by_day ON usage (day);

-- Tier per user. Default everyone is 'free' (no row needed). A paid Pass writes one row.
CREATE TABLE IF NOT EXISTS entitlement (
  user_id TEXT PRIMARY KEY,
  tier    TEXT NOT NULL DEFAULT 'free', -- free | pass (high finite cap) | unlimited (no cap — owner/comp)
  expires TEXT,                          -- YYYY-MM-DD; NULL = never expires
  note    TEXT
);
