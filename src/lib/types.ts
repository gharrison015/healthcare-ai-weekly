export interface IssueManifestEntry {
  date: string;
  week_range: string;
  editorial_summary: string;
  top_stories: number;
  vbc_watch: number;
  deal_flow: number;
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
    deal_flow: Story[];
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
