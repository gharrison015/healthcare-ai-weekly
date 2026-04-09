'use server';

import { createServiceClient } from './supabase';

// --- Types ---

export interface QuizAnalyticsRow {
  quiz_slug: string;
  attempts: number;
  avg_score_pct: number;
  first_attempt: string;
  last_attempt: string;
}

export interface QuestionDifficultyRow {
  quiz_slug: string;
  question_id: string;
  attempts: number;
  correct_rate_pct: number;
}

export interface RecentAttemptRow {
  id: string;
  quiz_slug: string;
  score: number;
  total_questions: number;
  session_id: string | null;
  created_at: string;
}

export interface AttemptsByDayRow {
  day: string;
  count: number;
}

// --- Data Fetchers (server-side only, uses service_role key) ---

export async function getQuizAnalytics(): Promise<QuizAnalyticsRow[]> {
  const client = createServiceClient();
  if (!client) return [];
  const { data, error } = await client
    .from('quiz_analytics')
    .select('*')
    .order('attempts', { ascending: false });

  if (error) {
    console.error('Failed to fetch quiz analytics:', error.message);
    return [];
  }
  return data ?? [];
}

export async function getQuestionDifficulty(
  quizSlug?: string
): Promise<QuestionDifficultyRow[]> {
  const client = createServiceClient();
  if (!client) return [];
  let query = client
    .from('question_difficulty')
    .select('*')
    .order('correct_rate_pct', { ascending: true });

  if (quizSlug) {
    query = query.eq('quiz_slug', quizSlug);
  }

  const { data, error } = await query;

  if (error) {
    console.error('Failed to fetch question difficulty:', error.message);
    return [];
  }
  return data ?? [];
}

export async function getRecentAttempts(
  limit: number = 20
): Promise<RecentAttemptRow[]> {
  const client = createServiceClient();
  if (!client) return [];
  const { data, error } = await client
    .from('quiz_attempts')
    .select('id, quiz_slug, score, total_questions, session_id, created_at')
    .order('created_at', { ascending: false })
    .limit(limit);

  if (error) {
    console.error('Failed to fetch recent attempts:', error.message);
    return [];
  }
  return data ?? [];
}

export async function getAttemptsByDay(
  days: number = 30
): Promise<AttemptsByDayRow[]> {
  const client = createServiceClient();
  if (!client) return [];
  const since = new Date();
  since.setDate(since.getDate() - days);

  const { data, error } = await client
    .from('quiz_attempts')
    .select('created_at')
    .gte('created_at', since.toISOString())
    .order('created_at', { ascending: true });

  if (error) {
    console.error('Failed to fetch attempts by day:', error.message);
    return [];
  }

  // Group by day client-side
  const grouped: Record<string, number> = {};
  for (const row of data ?? []) {
    const day = row.created_at.slice(0, 10);
    grouped[day] = (grouped[day] ?? 0) + 1;
  }

  return Object.entries(grouped)
    .map(([day, count]) => ({ day, count }))
    .sort((a, b) => a.day.localeCompare(b.day));
}

// --- Aggregate helpers ---

export async function getDashboardSummary() {
  const client = createServiceClient();
  if (!client) return { totalAttempts: 0, uniqueSessions: 0, avgScorePct: 0, topicsCovered: 0 };

  const { count: totalAttempts } = await client
    .from('quiz_attempts')
    .select('*', { count: 'exact', head: true });

  const { data: sessionData } = await client
    .from('quiz_attempts')
    .select('session_id');

  const uniqueSessions = new Set(
    (sessionData ?? []).map((r) => r.session_id).filter(Boolean)
  ).size;

  const analytics = await getQuizAnalytics();
  const topicsCovered = analytics.length;

  const overallAvg =
    analytics.length > 0
      ? Math.round(
          (analytics.reduce((sum, a) => sum + (a.avg_score_pct ?? 0), 0) /
            analytics.length) *
            10
        ) / 10
      : 0;

  return {
    totalAttempts: totalAttempts ?? 0,
    uniqueSessions,
    avgScorePct: overallAvg,
    topicsCovered,
  };
}
