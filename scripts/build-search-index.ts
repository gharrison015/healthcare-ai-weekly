/**
 * Build-time search index generator.
 *
 * Reads all static content under /content and produces a single flat
 * search-index.json file in /public that the client loads and feeds to
 * MiniSearch. Runs automatically via `predev` and `prebuild` hooks, and
 * can be invoked manually with `npm run build:search-index`.
 */

import fs from "fs";
import path from "path";

const ROOT = process.cwd();
const CONTENT_DIR = path.join(ROOT, "content");
const PUBLIC_DIR = path.join(ROOT, "public");
const OUTPUT_FILE = path.join(PUBLIC_DIR, "search-index.json");

export interface SearchRecord {
  id: string;
  type: "issue_story" | "bulletin" | "consulting" | "learn";
  title: string;
  body: string;
  url: string;
  date: string;
  tags: string[];
  section?: string;
  source?: string;
  firm?: string;
}

function stripEmDashes(s: string): string {
  if (!s) return "";
  return s.replace(/—/g, "-").replace(/–/g, "-");
}

function clean(s: unknown): string {
  if (typeof s !== "string") return "";
  return stripEmDashes(s).trim();
}

function readJson<T>(filePath: string): T | null {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as T;
  } catch {
    return null;
  }
}

function listFiles(dir: string, predicate: (name: string) => boolean): string[] {
  if (!fs.existsSync(dir)) return [];
  return fs.readdirSync(dir).filter(predicate);
}

const SECTION_ANCHORS: Record<string, string> = {
  top_stories: "top-stories",
  vbc_watch: "vbc-watch",
  ma_partnerships: "ma-partnerships",
  consulting_intelligence: "consulting-intelligence",
  did_you_know: "did-you-know",
};

const SECTION_LABELS: Record<string, string> = {
  top_stories: "What Matters This Week",
  vbc_watch: "Value-Based Care Watch",
  ma_partnerships: "Acquisitions & Partnerships",
  consulting_intelligence: "Consulting Intelligence",
  did_you_know: "Did You Know",
};

function indexIssues(): SearchRecord[] {
  const records: SearchRecord[] = [];
  const issuesDir = path.join(CONTENT_DIR, "issues");
  if (!fs.existsSync(issuesDir)) return records;

  const dates = fs
    .readdirSync(issuesDir)
    .filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d));

  for (const date of dates) {
    const data = readJson<{
      editorial_summary?: string;
      sections?: Record<string, unknown[]>;
    }>(path.join(issuesDir, date, "data.json"));
    if (!data || !data.sections) continue;

    for (const [sectionKey, stories] of Object.entries(data.sections)) {
      if (!Array.isArray(stories)) continue;
      const anchor = SECTION_ANCHORS[sectionKey] || sectionKey;
      const label = SECTION_LABELS[sectionKey] || sectionKey;

      stories.forEach((raw, idx) => {
        const story = raw as Record<string, unknown>;
        const headline = clean(story.headline);
        if (!headline) return;

        // Stories vs DYK items have different body fields.
        const body =
          clean(story.email_summary as string) ||
          clean(story.explainer as string) ||
          clean(story.so_what as string) ||
          clean(story.deep_dive_notes as string);

        const sourceArticle = story.source_article as
          | { source?: string }
          | undefined;

        records.push({
          id: `issue:${date}:${sectionKey}:${idx}`,
          type: "issue_story",
          title: headline,
          body,
          url: `/?issue=${date}#${anchor}`,
          date,
          tags: [sectionKey, label],
          section: label,
          source: sourceArticle?.source,
        });
      });
    }
  }

  return records;
}

function indexBulletins(): SearchRecord[] {
  const records: SearchRecord[] = [];
  const dir = path.join(CONTENT_DIR, "bulletins");
  const files = listFiles(dir, (f) => f.endsWith(".json") && f !== "manifest.json");

  for (const file of files) {
    const data = readJson<{
      slug?: string;
      headline?: string;
      body?: string;
      timestamp?: string;
      source_name?: string;
      tags?: string[];
    }>(path.join(dir, file));
    if (!data || !data.headline) continue;

    const slug = data.slug || file.replace(/\.json$/, "");
    records.push({
      id: `bulletin:${slug}`,
      type: "bulletin",
      title: clean(data.headline),
      body: clean(data.body),
      url: `/bulletins/${slug}`,
      date: (data.timestamp || "").slice(0, 10),
      tags: Array.isArray(data.tags) ? data.tags : [],
      source: data.source_name,
    });
  }

  return records;
}

function indexConsulting(): SearchRecord[] {
  const records: SearchRecord[] = [];
  const dir = path.join(CONTENT_DIR, "consulting-intelligence");
  const files = listFiles(
    dir,
    (f) => f.endsWith(".json") && f !== "manifest.json"
  );

  for (const file of files) {
    const data = readJson<{
      slug?: string;
      firm?: string;
      headline?: string;
      summary?: string;
      so_what?: string;
      relevance?: string;
      published_date?: string;
    }>(path.join(dir, file));
    if (!data || !data.headline) continue;

    const slug = data.slug || file.replace(/\.json$/, "");
    const firm = clean(data.firm);
    const body = [clean(data.summary), clean(data.so_what)]
      .filter(Boolean)
      .join(" ");

    records.push({
      id: `consulting:${slug}`,
      type: "consulting",
      title: clean(data.headline),
      body,
      url: `/#consulting-${slug}`,
      date: data.published_date || "",
      tags: [firm, data.relevance || ""].filter(Boolean),
      firm,
    });
  }

  return records;
}

function indexLearn(): SearchRecord[] {
  const records: SearchRecord[] = [];
  const dir = path.join(CONTENT_DIR, "learn");
  const files = listFiles(dir, (f) => f.endsWith(".json") && f !== "manifest.json");

  for (const file of files) {
    const data = readJson<{
      slug?: string;
      title?: string;
      description?: string;
      summary?: string;
      created_at?: string;
    }>(path.join(dir, file));
    if (!data || !data.title) continue;

    const slug = data.slug || file.replace(/\.json$/, "");
    records.push({
      id: `learn:${slug}`,
      type: "learn",
      title: clean(data.title),
      body: [clean(data.description), clean(data.summary)]
        .filter(Boolean)
        .join(" "),
      url: `/learn/${slug}`,
      date: (data.created_at || "").slice(0, 10),
      tags: ["learn"],
    });
  }

  return records;
}

function main(): void {
  const records: SearchRecord[] = [
    ...indexIssues(),
    ...indexBulletins(),
    ...indexConsulting(),
    ...indexLearn(),
  ];

  if (!fs.existsSync(PUBLIC_DIR)) fs.mkdirSync(PUBLIC_DIR, { recursive: true });

  const json = JSON.stringify(records);
  fs.writeFileSync(OUTPUT_FILE, json);

  const sizeKb = (json.length / 1024).toFixed(1);
  const byType: Record<string, number> = {};
  for (const r of records) byType[r.type] = (byType[r.type] || 0) + 1;

  console.log(
    `[search-index] Wrote ${records.length} records (${sizeKb} KB) to public/search-index.json`
  );
  console.log(
    `[search-index] By type: ${Object.entries(byType)
      .map(([k, v]) => `${k}=${v}`)
      .join(", ")}`
  );

  if (json.length > 800 * 1024) {
    console.warn(
      `[search-index] WARNING: index exceeds 800 KB (${sizeKb} KB). Consider splitting by type.`
    );
  }
}

main();
