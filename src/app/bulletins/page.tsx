import Link from "next/link";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { getBulletins } from "@/lib/data";

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

export default function BulletinsPage() {
  const bulletins = getBulletins();

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4">
        <div style={{ padding: "48px 0 32px" }}>
          <h1
            className="font-extrabold mb-2"
            style={{ fontSize: "38px", color: "#dc2626", letterSpacing: "-0.5px" }}
          >
            Bulletins
          </h1>
          <div style={{ fontSize: "20px", lineHeight: "1.6", color: "#374151" }}>
            Breaking healthcare AI developments and urgent alerts.
          </div>
        </div>

        {bulletins.length > 0 ? (
          <div className="grid grid-cols-1 gap-4 pb-8">
            {bulletins.map((b) => (
              <Link
                key={b.slug}
                href={`/bulletins/${b.slug}`}
                className="glass-card-hover block no-underline rounded-2xl p-7"
                style={{
                  background: "rgba(255, 255, 255, 0.5)",
                  backdropFilter: "blur(16px) saturate(1.6)",
                  border: "1px solid rgba(255, 255, 255, 0.55)",
                  boxShadow:
                    "0 1px 2px rgba(0, 0, 0, 0.03), 0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
                  borderLeft: "4px solid #dc2626",
                  color: "inherit",
                }}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="text-xs font-bold uppercase tracking-wider"
                    style={{ color: "#dc2626" }}
                  >
                    {timeAgo(b.timestamp)}
                  </div>
                  <div
                    className="text-xs font-semibold px-2 py-0.5 rounded-full"
                    style={{
                      background: "rgba(220, 38, 38, 0.08)",
                      color: "#dc2626",
                      border: "1px solid rgba(220, 38, 38, 0.2)",
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
              </Link>
            ))}
          </div>
        ) : (
          <div
            className="text-center py-16"
            style={{ color: "#94a3b8", fontSize: "16px" }}
          >
            No bulletins published yet.
          </div>
        )}

        <div
          className="text-center"
          style={{ fontSize: "14px", color: "#94a3b8", padding: "32px 0 48px" }}
        >
          Healthcare AI Weekly by Greg Harrison, Guidehouse
        </div>
      </div>
    </>
  );
}
