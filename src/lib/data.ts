import fs from "fs";
import path from "path";
import type { IssueManifestEntry, BulletinManifestEntry, LearnManifestEntry, IssueData } from "./types";

const CONTENT_DIR = path.join(process.cwd(), "content");

export function getIssuesManifest(): IssueManifestEntry[] {
  try {
    const raw = fs.readFileSync(
      path.join(CONTENT_DIR, "manifests", "issues.json"),
      "utf-8"
    );
    const issues: IssueManifestEntry[] = JSON.parse(raw);
    return issues.sort((a, b) => b.date.localeCompare(a.date));
  } catch {
    return [];
  }
}

export function getBulletinsManifest(): BulletinManifestEntry[] {
  try {
    const raw = fs.readFileSync(
      path.join(CONTENT_DIR, "manifests", "bulletins.json"),
      "utf-8"
    );
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : (parsed.bulletins || []);
  } catch {
    return [];
  }
}

export function getLearnManifest(): LearnManifestEntry[] {
  try {
    const raw = fs.readFileSync(
      path.join(CONTENT_DIR, "manifests", "learn.json"),
      "utf-8"
    );
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : (parsed.topics || []);
  } catch {
    return [];
  }
}

export function getIssueData(date: string): IssueData | null {
  try {
    const raw = fs.readFileSync(
      path.join(CONTENT_DIR, "issues", date, "data.json"),
      "utf-8"
    );
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function getIssueDates(): string[] {
  try {
    const dirs = fs.readdirSync(path.join(CONTENT_DIR, "issues"));
    return dirs.filter((d) => /^\d{4}-\d{2}-\d{2}$/.test(d)).sort().reverse();
  } catch {
    return [];
  }
}
