"use client";

import { useEffect, useState } from "react";
import { HorizontalScroller } from "@/components/ui/horizontal-scroller";
import { GlowCard } from "@/components/ui/spotlight-card";
import type { ConsultingIntelEntry } from "@/lib/data";

interface ConsultingCardsProps {
  entries: ConsultingIntelEntry[];
}

function relevanceLabel(relevance: string): { label: string; color: string; bg: string; border: string } {
  switch (relevance) {
    case "healthcare_direct":
      return {
        label: "Healthcare",
        color: "#16a34a",
        bg: "rgba(22, 163, 74, 0.10)",
        border: "rgba(22, 163, 74, 0.30)",
      };
    case "healthcare_adjacent":
      return {
        label: "Health-Adjacent",
        color: "#0284C7",
        bg: "rgba(2, 132, 199, 0.10)",
        border: "rgba(2, 132, 199, 0.30)",
      };
    default:
      return {
        label: "AI Strategy",
        color: "#7c3aed",
        bg: "rgba(124, 58, 237, 0.10)",
        border: "rgba(124, 58, 237, 0.30)",
      };
  }
}

function formatDate(dateStr: string): string {
  try {
    const d = new Date(dateStr + "T00:00:00");
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

export function ConsultingCards({ entries }: ConsultingCardsProps) {
  const [highlightedId, setHighlightedId] = useState<string | null>(null);

  useEffect(() => {
    function handleHash() {
      const hash = window.location.hash.replace("#", "");
      if (hash.startsWith("consulting-")) {
        const slug = hash.replace("consulting-", "");
        setHighlightedId(slug);
        const el = document.getElementById(`consulting-${slug}`);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
        }
        // Clear highlight after 2 seconds
        const t = setTimeout(() => setHighlightedId(null), 2000);
        return () => clearTimeout(t);
      }
    }
    handleHash();
    window.addEventListener("hashchange", handleHash);
    return () => window.removeEventListener("hashchange", handleHash);
  }, []);

  return (
    <HorizontalScroller className="pb-10">
      {entries.map((entry) => {
        const rel = relevanceLabel(entry.relevance);
        const isHighlighted = highlightedId === entry.slug;
        return (
          <a
            key={entry.slug}
            id={`consulting-${entry.slug}`}
            href={entry.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block flex-shrink-0 no-underline"
            style={{
              width: "340px",
              minHeight: "220px",
              scrollSnapAlign: "start",
              color: "inherit",
              outline: isHighlighted ? "3px solid #0284C7" : "none",
              outlineOffset: isHighlighted ? "4px" : "0",
              borderRadius: "18px",
              transition: "outline 300ms ease",
            }}
          >
            <GlowCard glowColor="blue" customSize={true} className="w-full h-full p-7">
              <div className="flex flex-col h-full">
                {/* Relevance badge */}
                <div className="mb-2">
                  <span
                    className="font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-full"
                    style={{
                      fontSize: "11px",
                      background: rel.bg,
                      color: rel.color,
                      border: `1px solid ${rel.border}`,
                    }}
                  >
                    {rel.label}
                  </span>
                </div>

                {/* Firm + date row */}
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="text-xs font-bold uppercase tracking-wider"
                    style={{ color: "#0284C7" }}
                  >
                    {entry.firm}
                  </div>
                  <div style={{ fontSize: "12px", color: "#94a3b8" }}>
                    {formatDate(entry.published_date)}
                  </div>
                </div>

                {/* Headline */}
                <div
                  className="font-bold mb-2"
                  style={{ color: "#0F1D35", fontSize: "18px", lineHeight: "1.3" }}
                >
                  {entry.headline}
                </div>

                {/* Summary */}
                <div
                  className="mb-3 flex-1"
                  style={{
                    color: "#475569",
                    fontSize: "14px",
                    lineHeight: "1.55",
                    display: "-webkit-box",
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: "vertical" as const,
                    overflow: "hidden",
                  }}
                >
                  {entry.summary}
                </div>

                {/* CTA */}
                <div
                  style={{ fontSize: "14px", fontWeight: 600, color: "#0284C7" }}
                >
                  Read source &rarr;
                </div>
              </div>
            </GlowCard>
          </a>
        );
      })}
    </HorizontalScroller>
  );
}
