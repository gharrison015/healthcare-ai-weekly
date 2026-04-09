import Link from "next/link";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { SourceTicker } from "@/components/ui/source-ticker";
import { PulseBeamCTA } from "@/components/ui/pulse-beam-cta";
import { getIssuesManifest, getBulletins, getLearningTopics } from "@/lib/data";
import { IssuesCarousel } from "./issues-carousel";

export default function HomePage() {
  const issues = getIssuesManifest();
  const bulletins = getBulletins();
  const learn = getLearningTopics();

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4">
        {/* Hero */}
        <div className="pt-20 pb-8 text-center">
          <h1
            className="font-extrabold mb-2"
            style={{ color: "#0F1D35", letterSpacing: "-1px", fontSize: "48px" }}
          >
            Healthcare AI Weekly
          </h1>
          <div
            className="font-normal leading-relaxed max-w-[700px] mx-auto mb-3"
            style={{ color: "#6b7280", fontSize: "20px", lineHeight: "1.5" }}
          >
            Weekly intelligence on AI in healthcare. Curated for consultants,
            strategists, and health system leaders who need to know what matters
            and why.
          </div>
          <div style={{ color: "#94a3b8", fontSize: "14px" }}>
            By Greg Harrison, Guidehouse
          </div>
        </div>

        {/* Pulse Beam CTA */}
        <PulseBeamCTA />

        {/* Source Ticker */}
        <SourceTicker />

        {/* Issues Section - Horizontal Carousel */}
        <div className="flex items-baseline justify-between pt-8 mb-5">
          <div
            className="font-extrabold"
            style={{ fontSize: "28px", color: "#0F1D35", letterSpacing: "-0.3px" }}
          >
            All Issues
          </div>
          <div
            className="font-semibold"
            style={{ fontSize: "14px", color: "#94a3b8" }}
          >
            {issues.length > 0
              ? `${issues.length} issue${issues.length !== 1 ? "s" : ""} published`
              : ""}
          </div>
        </div>

        {issues.length > 0 ? (
          <IssuesCarousel issues={issues} />
        ) : (
          <div
            className="text-center py-16"
            style={{ color: "#94a3b8", fontSize: "16px" }}
          >
            No issues published yet. Check back Friday.
          </div>
        )}

        {/* Bulletins Section - hidden when empty */}
        {bulletins.length > 0 && (
          <div className="mt-12">
            <div className="flex items-baseline justify-between pt-8 mb-5">
              <div
                className="font-extrabold uppercase tracking-wider"
                style={{ fontSize: "28px", color: "#dc2626", letterSpacing: "-0.3px" }}
              >
                Bulletins
              </div>
              <Link
                href="/bulletins"
                className="no-underline hover:underline font-semibold"
                style={{ fontSize: "14px", color: "#dc2626" }}
              >
                View all bulletins &rarr;
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {bulletins.slice(0, 3).map((b) => (
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
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* AI Learning Section - hidden when empty */}
        {learn.length > 0 && (
          <div className="mt-12">
            <div className="flex items-baseline justify-between pt-8 mb-5">
              <div
                className="font-extrabold uppercase tracking-wider"
                style={{ fontSize: "28px", color: "#059669", letterSpacing: "-0.3px" }}
              >
                AI Learning
              </div>
              <Link
                href="/learn"
                className="no-underline hover:underline font-semibold"
                style={{ fontSize: "14px", color: "#059669" }}
              >
                View all topics &rarr;
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {learn.map((topic) => (
                <Link
                  key={topic.slug}
                  href={`/learn/${topic.slug}`}
                  className="glass-card-hover block no-underline rounded-2xl p-7"
                  style={{
                    background: "rgba(255, 255, 255, 0.5)",
                    backdropFilter: "blur(16px) saturate(1.6)",
                    border: "1px solid rgba(255, 255, 255, 0.55)",
                    boxShadow:
                      "0 1px 2px rgba(0, 0, 0, 0.03), 0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
                    borderLeft: `4px solid ${topic.accent_color}`,
                    color: "inherit",
                  }}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div
                      className="text-xs font-bold uppercase tracking-wider"
                      style={{ color: topic.accent_color }}
                    >
                      Learning
                    </div>
                    <div
                      className="text-xs font-semibold px-1.5 py-0.5 rounded-full"
                      style={{
                        background: `${topic.accent_color}12`,
                        color: topic.accent_color,
                        border: `1px solid ${topic.accent_color}25`,
                      }}
                    >
                      {topic.question_count} questions
                    </div>
                  </div>
                  <div
                    className="font-bold mb-2"
                    style={{ color: "#0F1D35", fontSize: "18px", lineHeight: "1.3" }}
                  >
                    {topic.title}
                  </div>
                  <div
                    className="mb-3"
                    style={{ color: "#475569", fontSize: "15px", lineHeight: "1.55" }}
                  >
                    {topic.description}
                  </div>
                  <div
                    className="inline-block font-bold rounded-lg"
                    style={{
                      fontSize: "13px",
                      color: topic.accent_color,
                      padding: "6px 12px",
                      background: `${topic.accent_color}0a`,
                      border: `1px solid ${topic.accent_color}20`,
                    }}
                  >
                    Take the Quiz &rarr;
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
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
