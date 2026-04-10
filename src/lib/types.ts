export interface IssueManifestEntry {
  date: string;
  week_range: string;
  editorial_summary: string;
  top_stories: number;
  vbc_watch: number;
  ma_partnerships: number;
  consulting_intelligence: number;
  did_you_know: number;
}

export interface BulletinManifestEntry {
  slug: string;
  headline: string;
  timestamp: string;
  source_name: string;
  velocity_score: number;
  tags: string[];
}

export interface LearnManifestEntry {
  slug: string;
  title: string;
  description: string;
  accent_color: string;
  question_count: number;
  created_at: string;
  level?: 100 | 200 | 300;
}

export function getTopicLevel(slug: string): 100 | 200 | 300 {
  if (slug.includes('101') || slug.includes('fundamentals')) return 100;
  if (slug.includes('strategy') || slug.includes('leaders')) return 300;
  return 200;
}

export function getLevelLabel(level: 100 | 200 | 300): string {
  switch (level) {
    case 100: return 'Fundamentals';
    case 200: return 'Applied';
    case 300: return 'Strategic';
  }
}

export function getLevelColor(level: 100 | 200 | 300): { bg: string; border: string; text: string } {
  switch (level) {
    case 100: return { bg: 'rgba(22, 163, 74, 0.10)', border: 'rgba(22, 163, 74, 0.30)', text: '#16a34a' };
    case 200: return { bg: 'rgba(2, 132, 199, 0.10)', border: 'rgba(2, 132, 199, 0.30)', text: '#0284C7' };
    case 300: return { bg: 'rgba(124, 58, 237, 0.10)', border: 'rgba(124, 58, 237, 0.30)', text: '#7c3aed' };
  }
}

export interface Bulletin {
  timestamp: string;
  slug: string;
  headline: string;
  body: string;
  source_url: string;
  source_name: string;
  velocity_score: number;
  verification: string;
  tags: string[];
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correct: number;
  explanation: string;
}

export interface Quiz {
  title: string;
  questions: QuizQuestion[];
}

export interface LearningTopic {
  slug: string;
  title: string;
  description: string;
  accent_color: string;
  sources: string[];
  source_count: number;
  summary: string;
  quiz: Quiz;
  created_at: string;
  updated_at: string;
}

export interface SourceArticle {
  id: string;
  title: string;
  source: string;
  url: string;
}

export interface Story {
  headline: string;
  source_article: SourceArticle;
  priority: string;
  so_what: string;
  risk_angle: string | null;
  consulting_signal: string;
  connections: string[];
  deep_dive_notes: string;
  email_summary: string;
}

export interface IssueData {
  editorial_summary: string;
  sections: {
    top_stories: Story[];
    vbc_watch: Story[];
    ma_partnerships: Story[];
    consulting_intelligence: Story[];
    did_you_know: Array<{
      headline: string;
      explainer: string;
      source_article?: SourceArticle;
    }>;
  };
  trend_to_watch?: {
    title: string;
    summary: string;
    indicators: string[];
  };
}
