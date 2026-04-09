"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { HorizontalScroller } from "@/components/ui/horizontal-scroller";
import { GlowCard } from "@/components/ui/spotlight-card";
import type { IssueManifestEntry } from "@/lib/types";

interface IssuesCarouselProps {
  issues: IssueManifestEntry[];
}

function getMonthLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

export function IssuesCarousel({ issues }: IssuesCarouselProps) {
  const [visibleMonth, setVisibleMonth] = useState<string | null>(null);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef<Map<string, HTMLElement>>(new Map());

  const handleScroll = useCallback(() => {
    if (hideTimer.current) clearTimeout(hideTimer.current);

    const container = wrapperRef.current;
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    const centerX = containerRect.left + containerRect.width / 2;

    let closestDate: string | null = null;
    let closestDist = Infinity;

    cardRefs.current.forEach((el, date) => {
      const rect = el.getBoundingClientRect();
      const cardCenter = rect.left + rect.width / 2;
      const dist = Math.abs(cardCenter - centerX);
      if (dist < closestDist) {
        closestDist = dist;
        closestDate = date;
      }
    });

    if (closestDate) {
      setVisibleMonth(getMonthLabel(closestDate));
    }

    hideTimer.current = setTimeout(() => {
      setVisibleMonth(null);
    }, 1200);
  }, []);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;

    // Listen for scroll events on the inner scroller
    const scrollContainer = wrapper.querySelector("[data-scroll-container]")?.parentElement || wrapper;
    scrollContainer.addEventListener("scroll", handleScroll, { passive: true, capture: true });

    return () => {
      scrollContainer.removeEventListener("scroll", handleScroll, { capture: true });
      if (hideTimer.current) clearTimeout(hideTimer.current);
    };
  }, [handleScroll]);

  return (
    <div className="relative" ref={wrapperRef} onScrollCapture={handleScroll}>
      {/* Timeline month indicator */}
      {visibleMonth && (
        <div
          className="absolute -top-8 left-1/2 -translate-x-1/2 z-10 pointer-events-none"
          style={{
            animation: "timeline-fade-in 0.2s ease-out",
          }}
        >
          <div
            className="font-bold rounded-full px-4 py-1.5"
            style={{
              fontSize: "13px",
              color: "#fff",
              background: "#0284C7",
              boxShadow: "0 2px 12px rgba(2, 132, 199, 0.35)",
            }}
          >
            {visibleMonth}
          </div>
        </div>
      )}

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
              ref={(el) => {
                if (el) cardRefs.current.set(issue.date, el);
              }}
              style={{
                width: "340px",
                minHeight: "220px",
                scrollSnapAlign: "start",
                color: "inherit",
              }}
            >
              <GlowCard glowColor="blue" customSize={true} className="w-full h-full p-7">
                <div className="flex flex-col h-full">
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
                    className="mb-4 flex-1"
                    style={{
                      fontSize: "15px",
                      lineHeight: "1.55",
                      color: "#475569",
                    }}
                  >
                    {issue.editorial_summary || ""}
                  </div>
                  <div>
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
                </div>
              </GlowCard>
            </a>
          );
        })}
      </HorizontalScroller>
    </div>
  );
}
