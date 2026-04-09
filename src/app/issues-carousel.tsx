"use client";

import { HorizontalScroller } from "@/components/ui/horizontal-scroller";
import { GlowCard } from "@/components/ui/spotlight-card";
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
            className="block flex-shrink-0 no-underline"
            style={{
              width: "340px",
              scrollSnapAlign: "start",
              color: "inherit",
            }}
          >
            <GlowCard glowColor="blue" customSize={true} className="w-full p-7">
              <div>
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
              </div>
            </GlowCard>
          </a>
        );
      })}
    </HorizontalScroller>
  );
}
