"use client";

import Link from "next/link";
import { HorizontalScroller } from "@/components/ui/horizontal-scroller";
import { GlowCard } from "@/components/ui/spotlight-card";

interface Bulletin {
  slug: string;
  source_name: string;
  velocity_score: number;
  headline: string;
  tags: string[];
}

export function BulletinCards({ bulletins }: { bulletins: Bulletin[] }) {
  return (
    <HorizontalScroller className="pb-10">
      {bulletins.map((b) => (
        <Link
          key={b.slug}
          href={`/bulletins/${b.slug}`}
          className="block flex-shrink-0 no-underline"
          style={{
            width: "340px",
            minHeight: "220px",
            scrollSnapAlign: "start",
            color: "inherit",
          }}
        >
          <GlowCard glowColor="blue" customSize={true} className="w-full h-full p-7">
            <div className="flex flex-col h-full">
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="text-xs font-bold uppercase tracking-wider"
                  style={{ color: "#0284C7" }}
                >
                  {b.source_name}
                </div>
                <div
                  className="text-xs font-semibold px-1.5 py-0.5 rounded-full"
                  style={{
                    background: "rgba(2, 132, 199, 0.08)",
                    color: "#0284C7",
                    border: "1px solid rgba(2, 132, 199, 0.2)",
                  }}
                >
                  {b.velocity_score}
                </div>
              </div>
              <div
                className="font-bold mb-3 flex-1"
                style={{ color: "#0F1D35", fontSize: "18px", lineHeight: "1.3" }}
              >
                {b.headline}
              </div>
              <div>
                <div className="flex flex-wrap gap-1">
                  {b.tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="text-xs font-medium px-1.5 py-0.5 rounded-full"
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
            </div>
          </GlowCard>
        </Link>
      ))}
    </HorizontalScroller>
  );
}
