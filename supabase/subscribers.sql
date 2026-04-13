-- Healthcare AI Weekly — Subscribers Schema
-- Run this in Supabase SQL Editor (same project as quiz analytics).

CREATE TABLE subscribers (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT NOT NULL UNIQUE,
  active BOOLEAN DEFAULT true,
  unsubscribe_token UUID DEFAULT gen_random_uuid(),
  subscribed_at TIMESTAMPTZ DEFAULT now(),
  unsubscribed_at TIMESTAMPTZ
);

ALTER TABLE subscribers ENABLE ROW LEVEL SECURITY;

-- Anyone can subscribe (insert)
CREATE POLICY "Allow anonymous subscribe"
  ON subscribers
  FOR INSERT
  WITH CHECK (true);

-- Only service_role can read (GitHub Actions + analytics)
CREATE POLICY "Service role can read subscribers"
  ON subscribers
  FOR SELECT
  USING (auth.role() = 'service_role');

-- Only service_role can update (unsubscribe endpoint)
CREATE POLICY "Service role can update subscribers"
  ON subscribers
  FOR UPDATE
  USING (auth.role() = 'service_role');

CREATE INDEX idx_subscribers_active ON subscribers(active) WHERE active = true;
CREATE INDEX idx_subscribers_token ON subscribers(unsubscribe_token);
