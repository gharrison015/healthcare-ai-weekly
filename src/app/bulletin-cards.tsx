"use client";

import Link from "next/link";
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
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {bulletins.slice(0, 3).map((b) => (
        <Link
          key={b.slug}
          href={`/bulletins/${b.slug}`}
          className="block no-underline"
          style={{ color: "inherit" }}
        >
          <GlowCard glowColor="red" customSize={true} className="w-full p-7">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="text-xs font-bold uppercase tracking-wider"
                  style={{ color: "#dc2626" }}
                >
                  {b.source_name}
                </div>
                <div
                  className="text-xs font-semibold px-1.5 py-0.5 rounded-full"
                  style={{
                    background: "rgba(220, 38, 38, 0.08)",
                    color: "#dc2626",
                    border: "1px solid rgba(220, 38, 38, 0.2)",
                  }}
                >
                  {b.velocity_score}
                </div>
              </div>
              <div
                className="font-bold mb-3"
                style={{ color: "#0F1D35", fontSize: "18px", lineHeight: "1.3" }}
              >
                {b.headline}
              </div>
              <div className="flex flex-wrap gap-1">
                {b.tags.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="text-xs font-medium px-1.5 py-0.5 rounded-full"
                    style={{
                      background: "rgba(220, 38, 38, 0.06)",
                      color: "#b91c1c",
                      border: "1px solid rgba(220, 38, 38, 0.12)",
                    }}
                  >
                    {tag}
                  </span>
                ))}
              </div>
              <div
                className="mt-3"
                style={{ fontSize: "14px", fontWeight: 600, color: "#dc2626" }}
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
