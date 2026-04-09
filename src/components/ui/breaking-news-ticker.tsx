"use client";

import type { BulletinManifestEntry } from "@/lib/types";

interface BreakingNewsTickerProps {
  bulletins: BulletinManifestEntry[];
}

export function BreakingNewsTicker({ bulletins }: BreakingNewsTickerProps) {
  if (!bulletins || bulletins.length === 0) return null;

  // Sort by timestamp descending and pick the latest
  const sorted = [...bulletins].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
  const latest = sorted[0];

  const tickerText = `${latest.headline} — ${latest.tags.slice(0, 2).join(", ")}`;
  // Duplicate for seamless loop
  const items = [tickerText, tickerText, tickerText, tickerText];

  return (
    <div
      style={{
        background: "#0F1D35",
        borderBottom: "2px solid #0284C7",
        overflow: "hidden",
        position: "relative",
      }}
    >
      <div
        className="flex items-center"
        style={{
          width: "max-content",
          animation: "breaking-ticker-scroll 30s linear infinite",
        }}
      >
        {items.map((text, i) => (
          <div key={i} className="flex items-center gap-4 px-8 py-2.5">
            <span
              className="font-extrabold uppercase tracking-wider whitespace-nowrap"
              style={{
                fontSize: "12px",
                letterSpacing: "1.5px",
                color: "#0284C7",
                background: "rgba(2, 132, 199, 0.15)",
                padding: "3px 10px",
                borderRadius: "4px",
                border: "1px solid rgba(2, 132, 199, 0.3)",
              }}
            >
              LATEST
            </span>
            <a
              href={`/bulletins/${latest.slug}`}
              className="whitespace-nowrap no-underline hover:underline"
              style={{
                fontSize: "14px",
                fontWeight: 700,
                color: "rgba(255, 255, 255, 0.95)",
              }}
            >
              {text}
            </a>
          </div>
        ))}
      </div>
    </div>
  );
}
