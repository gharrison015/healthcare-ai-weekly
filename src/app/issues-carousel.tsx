"use client";

import { HorizontalScroller } from "@/components/ui/horizontal-scroller";
import type { IssueManifestEntry } from "@/lib/types";

interface IssuesCarouselProps {
  issues: IssueManifestEntry[];
}

export function IssuesCarousel({ issues }: IssuesCarouselProps) {
  return (
    <HorizontalScroller className="pb-10">
      {issues.map((issue) => {
        const storyCount =
          (issue.top_stories || 0) +
          (issue.vbc_watch || 0) +
          (issue.deal_flow || 0) +
          (issue.did_you_know || 0);

        return (
          <a
            key={issue.date}
            href={`/issues/${issue.date}`}
            className="glass-card-hover block flex-shrink-0 no-underline"
            style={{
              width: "340px",
              scrollSnapAlign: "start",
              borderRadius: "16px",
              padding: "28px 24px",
              background: "rgba(255, 255, 255, 0.5)",
              backdropFilter: "blur(16px) saturate(1.6)",
              WebkitBackdropFilter: "blur(16px) saturate(1.6)",
              border: "1px solid rgba(255, 255, 255, 0.55)",
              boxShadow:
                "0 1px 2px rgba(0, 0, 0, 0.03), 0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
              transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
              color: "inherit",
            }}
          >
            <div
              className="font-bold uppercase tracking-wider mb-3"
              style={{
                fontSize: "13px",
                letterSpacing: "1.5px",
                color: "#0284C7",
              }}
            >
              Week of {issue.week_range || issue.date}
            </div>
            <div
              className="mb-4"
              style={{
                fontSize: "15px",
                lineHeight: "1.55",
                color: "#475569",
              }}
            >
              {issue.editorial_summary || ""}
            </div>
            <div style={{ fontSize: "13px", color: "#94a3b8" }}>
              {storyCount} stories curated
            </div>
            <div
              className="mt-3"
              style={{ fontSize: "14px", fontWeight: 600, color: "#0284C7" }}
            >
              Read deep dive &rarr;
            </div>
          </a>
        );
      })}
    </HorizontalScroller>
  );
}
