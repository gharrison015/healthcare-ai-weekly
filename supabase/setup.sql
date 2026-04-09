-- Healthcare AI Weekly — Quiz Analytics Schema
-- Run this in Supabase SQL Editor after creating the project.
-- Project: healthcare-ai-weekly-analytics (NOT FieldShield)

-- Quiz attempts (anonymous, no PII)
CREATE TABLE quiz_attempts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  quiz_slug TEXT NOT NULL,
  score INTEGER NOT NULL,
  total_questions INTEGER NOT NULL,
  answers JSONB NOT NULL,
  session_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE quiz_attempts ENABLE ROW LEVEL SECURITY;

-- Policy: anyone can INSERT (anonymous quiz submissions)
CREATE POLICY "Allow anonymous quiz submissions"
  ON quiz_attempts
  FOR INSERT
  WITH CHECK (true);

-- Policy: only service_role can SELECT (analytics dashboard only)
-- The anon key CANNOT read quiz data
CREATE POLICY "Service role can read all"
  ON quiz_attempts
  FOR SELECT
  USING (auth.role() = 'service_role');

-- Aggregate analytics view
CREATE VIEW quiz_analytics AS
SELECT
  quiz_slug,
  COUNT(*) as attempts,
  ROUND(AVG(score::float / NULLIF(total_questions, 0)) * 100, 1) as avg_score_pct,
  MIN(created_at) as first_attempt,
  MAX(created_at) as last_attempt
FROM quiz_attempts
GROUP BY quiz_slug;

-- Per-question difficulty view
CREATE VIEW question_difficulty AS
SELECT
  quiz_slug,
  q->>'question_id' as question_id,
  COUNT(*) as attempts,
  ROUND(AVG(CASE WHEN (q->>'correct')::boolean THEN 1.0 ELSE 0.0 END) * 100, 1) as correct_rate_pct
FROM quiz_attempts, jsonb_array_elements(answers) as q
GROUP BY quiz_slug, q->>'question_id';

-- Index for common queries
CREATE INDEX idx_quiz_attempts_slug ON quiz_attempts(quiz_slug);
CREATE INDEX idx_quiz_attempts_created ON quiz_attempts(created_at DESC);
