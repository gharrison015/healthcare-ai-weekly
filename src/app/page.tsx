import Link from "next/link";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { SourceTicker } from "@/components/ui/source-ticker";
import { PulseBeamCTA } from "@/components/ui/pulse-beam-cta";
import { getIssuesManifest, getBulletins, getLearningTopics } from "@/lib/data";
import { IssuesCarousel } from "./issues-carousel";
import { BulletinCards } from "./bulletin-cards";
import { LearnCards } from "./learn-cards";

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
            <BulletinCards bulletins={bulletins} />
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
            <LearnCards topics={learn} />
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
