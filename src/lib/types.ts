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
  date: string;
  title: string;
  summary: string;
}

export interface LearnManifestEntry {
  date: string;
  title: string;
  summary: string;
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
