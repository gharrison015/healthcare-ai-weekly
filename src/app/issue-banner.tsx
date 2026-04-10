"use client";

import { useState } from "react";
import type { IssueManifestEntry } from "@/lib/types";

interface IssueBannerProps {
  highlightIssue: string;
  issues: IssueManifestEntry[];
}

export function IssueBanner({ highlightIssue, issues }: IssueBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  const matchedIssue = issues.find((i) => i.date === highlightIssue);
  if (!matchedIssue || dismissed) return null;

  const weekLabel = matchedIssue.week_range || matchedIssue.date;

  const handleDismiss = () => {
    setDismissed(true);
    const url = new URL(window.location.href);
    url.searchParams.delete("issue");
    window.history.replaceState({}, "", url.pathname);
  };

  return (
    <div
      className="sticky top-0 z-50 w-full"
      style={{ animation: "caption-fade 0.3s ease-out" }}
    >
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{
          background: "#0284C7",
          color: "#fff",
          boxShadow: "0 2px 12px rgba(2, 132, 199, 0.35)",
        }}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="text-sm font-medium truncate">
            This article is from the{" "}
            <span className="font-bold">Week of {weekLabel}</span> issue
          </div>
          <a
            href={`/news/${matchedIssue.date}`}
            className="flex-shrink-0 font-bold text-sm no-underline rounded-full px-4 py-1.5"
            style={{
              background: "rgba(255, 255, 255, 0.2)",
              color: "#fff",
              border: "1px solid rgba(255, 255, 255, 0.3)",
              backdropFilter: "blur(8px)",
            }}
          >
            Read this issue &rarr;
          </a>
        </div>
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 ml-3 p-1 rounded-full border-none cursor-pointer"
          style={{
            background: "rgba(255, 255, 255, 0.15)",
            color: "#fff",
            lineHeight: 1,
          }}
          aria-label="Dismiss"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    </div>
  );
}
