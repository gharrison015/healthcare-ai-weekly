-- Healthcare AI Weekly, Newsletter Send Ledger (double-send guard)
-- Apply once via Supabase SQL Editor:
--   https://supabase.com/dashboard/project/wjwubjahhbhhsctnpfcb/sql
--
-- Purpose: a DURABLE, atomic dedup marker for the Friday send, independent
-- of the git push. send_newsletter.py claims the issue_date here BEFORE it
-- sends a single email. The UNIQUE primary key means a second run that tries
-- to claim the same date gets a 409 conflict and skips sending entirely.
--
-- Why this table exists (2026-07-17 incident): the old dedup relied on the
-- run pushing content/issues/<date>/index.html to main. On 2026-07-17 the
-- 6:03am ET run SENT the issue but its `git push` was REJECTED (another bot
-- had advanced main), so the marker never landed; a later stacked-cron
-- attempt at 7:41am ET saw no marker and sent the whole issue a SECOND time.
-- A claim written right before the irreversible send closes that window.

CREATE TABLE IF NOT EXISTS newsletter_sends (
  issue_date  DATE PRIMARY KEY,
  claimed_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  sent_count  INT,
  status      TEXT NOT NULL DEFAULT 'claimed'   -- 'claimed' -> 'sent'
);

-- service_role (used by GitHub Actions) bypasses RLS; enable + force so the
-- public anon key can never read or write the ledger. No policies needed.
ALTER TABLE newsletter_sends ENABLE ROW LEVEL SECURITY;
ALTER TABLE newsletter_sends FORCE ROW LEVEL SECURITY;
