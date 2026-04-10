"use client";

import { useEffect } from "react";
import type { IssueManifestEntry } from "@/lib/types";

interface IssueBannerProps {
  highlightIssue: string;
  issues: IssueManifestEntry[];
}

export function IssueBanner({ highlightIssue, issues }: IssueBannerProps) {
  const matchedIssue = issues.find((i) => i.date === highlightIssue);

  // Mobile: redirect straight to the deep-dive page
  useEffect(() => {
    if (matchedIssue && window.innerWidth < 768) {
      window.location.replace(`/news/${matchedIssue.date}`);
    }
  }, [matchedIssue]);

  if (!matchedIssue) return null;

  const weekLabel = matchedIssue.week_range || matchedIssue.date;

  return (
    <div
      className="mb-4"
      style={{ animation: "caption-fade 0.3s ease-out" }}
    >
      <div
        className="inline-flex items-center gap-3 rounded-full px-4 py-2"
        style={{
          background: "rgba(2, 132, 199, 0.08)",
          border: "1px solid rgba(2, 132, 199, 0.2)",
        }}
      >
        <span
          className="text-sm font-medium"
          style={{ color: "#0284C7" }}
        >
          This article is from the{" "}
          <span className="font-bold">Week of {weekLabel}</span> issue
        </span>
        <a
          href={`/news/${matchedIssue.date}`}
          className="font-bold text-sm no-underline rounded-full px-3 py-1"
          style={{
            background: "#0284C7",
            color: "#fff",
          }}
        >
          Read this issue &rarr;
        </a>
      </div>
    </div>
  );
}
