-- Healthcare AI Weekly — Keepalive Log
-- Apply once via Supabase SQL Editor:
--   https://supabase.com/dashboard/project/wjwubjahhbhhsctnpfcb/sql
--
-- Used by .github/workflows/supabase-keepalive.yml to do a real WRITE
-- against the DB each day. Free-tier inactivity heuristic ignores trivial
-- read-only pings, so we update a sentinel row instead.

CREATE TABLE IF NOT EXISTS keepalive_log (
  id INT PRIMARY KEY DEFAULT 1,
  pinged_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT keepalive_log_single_row CHECK (id = 1)
);

ALTER TABLE keepalive_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE keepalive_log FORCE ROW LEVEL SECURITY;

-- Seed the single sentinel row so the workflow's PATCH always has a target.
-- service_role (used by GitHub Actions) bypasses RLS; no policies needed.
INSERT INTO keepalive_log (id, pinged_at) VALUES (1, now())
  ON CONFLICT (id) DO NOTHING;
