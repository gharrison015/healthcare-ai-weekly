"use client";

import Link from "next/link";
import { GlowCard } from "@/components/ui/spotlight-card";

interface Bulletin {
  slug: string;
  source_name: string;
  velocity_score: number;
  headline: string;
  tags: string[];
  timestamp: string;
}

function timeAgo(timestamp: string): string {
  const now = new Date();
  const then = new Date(timestamp);
  const diffMs = now.getTime() - then.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return then.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function BulletinArchiveCards({ bulletins }: { bulletins: Bulletin[] }) {
  return (
    <div className="grid grid-cols-1 gap-4 pb-8">
      {bulletins.map((b) => (
        <Link
          key={b.slug}
          href={`/bulletins/${b.slug}`}
          className="block no-underline"
          style={{ color: "inherit" }}
        >
          <GlowCard glowColor="blue" customSize={true} className="w-full p-7">
            <div>
              <div className="flex items-center gap-3 mb-2">
                <div
                  className="text-xs font-bold uppercase tracking-wider"
                  style={{ color: "#0284C7" }}
                >
                  {timeAgo(b.timestamp)}
                </div>
                <div
                  className="text-xs font-semibold px-2 py-0.5 rounded-full"
                  style={{
                    background: "rgba(2, 132, 199, 0.08)",
                    color: "#0284C7",
                    border: "1px solid rgba(2, 132, 199, 0.2)",
                  }}
                >
                  Velocity: {b.velocity_score}
                </div>
                <div className="text-xs" style={{ color: "#94a3b8" }}>
                  {b.source_name}
                </div>
              </div>
              <div
                className="font-bold mb-3"
                style={{ color: "#0F1D35", fontSize: "20px", lineHeight: "1.3" }}
              >
                {b.headline}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {b.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs font-medium px-2 py-0.5 rounded-full"
                    style={{
                      background: "rgba(2, 132, 199, 0.06)",
                      color: "#0369a1",
                      border: "1px solid rgba(2, 132, 199, 0.12)",
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <div
                className="mt-3"
                style={{ fontSize: "14px", fontWeight: 600, color: "#0284C7" }}
              >
                Read bulletin &rarr;
              </div>
            </div>
          </GlowCard>
        </Link>
      ))}
    </div>
  );
}
