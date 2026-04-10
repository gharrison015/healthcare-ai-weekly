import Link from "next/link";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { SourceTicker } from "@/components/ui/source-ticker";
import { PulseBeamCTA } from "@/components/ui/pulse-beam-cta";
import { BreakingNewsTicker } from "@/components/ui/breaking-news-ticker";
import { getIssuesManifest, getBulletins, getLearningTopics, getConsultingIntelligence } from "@/lib/data";
import { IssuesCarousel } from "./issues-carousel";
import { BulletinCards } from "./bulletin-cards";
import { LearnCards } from "./learn-cards";
import { ConsultingCards } from "./consulting-cards";
import { IssueBanner } from "./issue-banner";

export default async function HomePage({
  searchParams,
}: {
  searchParams: Promise<{ issue?: string }>;
}) {
  const params = await searchParams;
  const highlightIssue = params.issue || null;

  const issues = getIssuesManifest();
  const bulletins = getBulletins();
  const learn = getLearningTopics();
  const consultingStories = getConsultingIntelligence();
  const latestIssueDate = issues.length > 0 ? issues[0].date : null;

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      {/* Breaking News Ticker */}
      <BreakingNewsTicker bulletins={bulletins} />

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
            By Greg Harrison
          </div>
        </div>

        {/* Pulse Beam CTA */}
        <PulseBeamCTA />

        {/* Source Ticker */}
        <SourceTicker />

        {/* Issues Section - Horizontal Carousel */}
        <div className="flex items-baseline justify-between pt-8 mb-2">
          <div
            className="font-extrabold"
            style={{ fontSize: "28px", color: "#0F1D35", letterSpacing: "-0.3px" }}
          >
            Weekly AI Healthcare News
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
        {highlightIssue && (
          <IssueBanner highlightIssue={highlightIssue} issues={issues} />
        )}

        {issues.length > 0 ? (
          <IssuesCarousel issues={issues} highlightIssue={highlightIssue || undefined} />
        ) : (
          <div
            className="text-center py-16"
            style={{ color: "#94a3b8", fontSize: "16px" }}
          >
            No issues published yet. Check back Friday.
          </div>
        )}

        {/* AI Learning Section */}
        {learn.length > 0 && (
          <div className="mt-12">
            <div className="flex items-baseline justify-between pt-8 mb-1">
              <div
                className="font-extrabold uppercase tracking-wider"
                style={{ fontSize: "28px", color: "#0284C7", letterSpacing: "-0.3px" }}
              >
                AI Learning
              </div>
              <Link
                href="/learn"
                className="no-underline hover:underline font-semibold"
                style={{ fontSize: "14px", color: "#0284C7" }}
              >
                View all topics &rarr;
              </Link>
            </div>
            <div
              className="mb-5"
              style={{ fontSize: "15px", color: "#6b7280" }}
            >
              New quizzes twice a week. Fresh questions every time, no repeats.
            </div>
            <LearnCards topics={learn} />
          </div>
        )}

        {/* Consulting Intelligence Section */}
        {consultingStories.length > 0 && (
          <div className="mt-12">
            <div className="flex items-baseline justify-between pt-8 mb-1">
              <div
                className="font-extrabold uppercase tracking-wider"
                style={{ fontSize: "28px", color: "#0284C7", letterSpacing: "-0.3px" }}
              >
                Consulting Intelligence
              </div>
              <div
                className="font-semibold"
                style={{ fontSize: "14px", color: "#94a3b8" }}
              >
                {consultingStories.length} tracked moves
              </div>
            </div>
            <div
              className="mb-5"
              style={{ fontSize: "15px", color: "#6b7280" }}
            >
              How consulting firms are moving in healthcare AI. Tracking Guidehouse, Deloitte, McKinsey, BCG, Accenture, Chartis, Optum, EY, Huron, BRG, Bain, Oliver Wyman, KPMG, and PwC.
            </div>
            <ConsultingCards entries={consultingStories} />
          </div>
        )}

        {/* Bulletins Section */}
        {bulletins.length > 0 && (
          <div className="mt-12">
            <div className="flex items-baseline justify-between pt-8 mb-5">
              <div
                className="font-extrabold uppercase tracking-wider"
                style={{ fontSize: "28px", color: "#0284C7", letterSpacing: "-0.3px" }}
              >
                Bulletins
              </div>
              <Link
                href="/bulletins"
                className="no-underline hover:underline font-semibold"
                style={{ fontSize: "14px", color: "#0284C7" }}
              >
                View all bulletins &rarr;
              </Link>
            </div>
            <BulletinCards bulletins={bulletins} />
          </div>
        )}

        {/* Footer */}
        <div
          className="text-center"
          style={{ fontSize: "14px", color: "#94a3b8", padding: "32px 0 48px" }}
        >
          Healthcare AI Weekly by Greg Harrison
        </div>
      </div>
    </>
  );
}
