import { notFound } from "next/navigation";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { getIssueData, getIssueDates, getIssuesManifest } from "@/lib/data";

export async function generateStaticParams() {
  const dates = getIssueDates();
  return dates.map((date) => ({ date }));
}

interface PageProps {
  params: Promise<{ date: string }>;
}

export default async function IssuePage({ params }: PageProps) {
  const { date } = await params;
  const data = getIssueData(date);
  const manifest = getIssuesManifest();
  const issueInfo = manifest.find((i) => i.date === date);

  if (!data) {
    notFound();
  }

  const renderStory = (story: typeof data.sections.top_stories[0], idx: number) => (
    <div
      key={idx}
      className="glass-card-hover rounded-xl mb-3 last:mb-0"
      style={{
        padding: "24px 28px",
        background: "rgba(255, 255, 255, 0.5)",
        backdropFilter: "blur(16px) saturate(1.6)",
        border: "1px solid rgba(255, 255, 255, 0.55)",
        boxShadow:
          "0 1px 2px rgba(0, 0, 0, 0.03), 0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
      }}
    >
      {story.priority === "act_now" && (
        <span
          className="inline-block text-xs font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-md mb-2.5"
          style={{
            background: "rgba(2, 132, 199, 0.1)",
            color: "#0284C7",
            border: "1px solid rgba(2, 132, 199, 0.2)",
            letterSpacing: "0.8px",
          }}
        >
          Act Now
        </span>
      )}
      {story.priority === "watch_this" && (
        <span
          className="inline-block text-xs font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-md mb-2.5"
          style={{
            background: "rgba(2, 132, 199, 0.1)",
            color: "#0284C7",
            border: "1px solid rgba(2, 132, 199, 0.2)",
            letterSpacing: "0.8px",
          }}
        >
          Watch This
        </span>
      )}
      <h3 className="mb-2.5" style={{ fontSize: "24px", fontWeight: 700, color: "#0F1D35", lineHeight: "1.3" }}>
        {story.source_article?.url ? (
          <a
            href={story.source_article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="no-underline hover:text-sky-600"
            style={{ color: "#0F1D35" }}
          >
            {story.headline}
          </a>
        ) : (
          story.headline
        )}
      </h3>
      <div
        className="italic mb-3"
        style={{ fontSize: "18px", fontWeight: 600, color: "#6b7280" }}
      >
        {story.so_what}
      </div>
      <div style={{ fontSize: "18px", lineHeight: "1.7", color: "#374151" }}>
        {story.deep_dive_notes}
      </div>
      {story.risk_angle && (
        <div
          className="mt-3.5 rounded-lg"
          style={{
            background: "rgba(245, 158, 11, 0.08)",
            border: "1px solid rgba(245, 158, 11, 0.2)",
            padding: "14px 18px",
            fontSize: "17px",
            color: "#92400e",
          }}
        >
          <strong style={{ color: "#78350f" }}>Risk angle:</strong> {story.risk_angle}
        </div>
      )}
      <div className="mt-3.5" style={{ fontSize: "14px", color: "#94a3b8" }}>
        Source:{" "}
        {story.source_article?.url ? (
          <a
            href={story.source_article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="no-underline hover:underline"
            style={{ color: "#0284C7", fontWeight: 600 }}
          >
            {story.source_article.source} &middot; {story.source_article.title}
          </a>
        ) : (
          story.source_article?.source || "Unknown"
        )}
      </div>
    </div>
  );

  const sections = [
    { key: "top_stories", label: "Top Stories" },
    { key: "vbc_watch", label: "VBC Watch" },
    { key: "deal_flow", label: "Deal Flow" },
  ] as const;

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4 max-w-4xl mx-auto">
        {/* Header */}
        <div style={{ padding: "48px 0 32px" }}>
          <a
            href="/"
            className="inline-block no-underline hover:underline rounded-lg mb-5"
            style={{
              fontSize: "20px",
              color: "#0284C7",
              fontWeight: 700,
              padding: "8px 16px",
              background: "rgba(2, 132, 199, 0.08)",
              border: "1px solid rgba(2, 132, 199, 0.15)",
            }}
          >
            &larr; All Issues
          </a>
          <h1
            className="font-extrabold mb-1"
            style={{ fontSize: "38px", color: "#0F1D35", letterSpacing: "-0.5px" }}
          >
            Healthcare AI Weekly Deep Dive
          </h1>
          <div
            className="font-semibold uppercase tracking-wider mb-5"
            style={{ fontSize: "16px", color: "#6b7280", letterSpacing: "1.5px" }}
          >
            {issueInfo?.week_range || date}
          </div>
          <div style={{ fontSize: "20px", lineHeight: "1.6", color: "#374151" }}>
            {data.editorial_summary}
          </div>
        </div>

        {/* TOC */}
        <div
          className="rounded-2xl mb-6"
          style={{
            padding: "20px 24px",
            background: "rgba(255, 255, 255, 0.45)",
            backdropFilter: "blur(20px) saturate(1.8)",
            border: "1px solid rgba(255, 255, 255, 0.5)",
            boxShadow:
              "0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
          }}
        >
          <div
            className="font-extrabold uppercase tracking-widest mb-2.5"
            style={{ fontSize: "13px", color: "#94a3b8", letterSpacing: "2px" }}
          >
            In This Issue
          </div>
          <div className="flex flex-wrap gap-x-4 gap-y-1">
            {sections.map(
              (s) =>
                data.sections[s.key]?.length > 0 && (
                  <a
                    key={s.key}
                    href={`#${s.key}`}
                    className="inline-block no-underline hover:underline font-semibold"
                    style={{ fontSize: "16px", color: "#0284C7", padding: "4px 0" }}
                  >
                    {s.label}
                  </a>
                )
            )}
            {data.sections.did_you_know?.length > 0 && (
              <a
                href="#did_you_know"
                className="inline-block no-underline hover:underline font-semibold"
                style={{ fontSize: "16px", color: "#0284C7", padding: "4px 0" }}
              >
                Did You Know?
              </a>
            )}
          </div>
        </div>

        {/* Sections */}
        {sections.map(
          (s) =>
            data.sections[s.key]?.length > 0 && (
              <div
                key={s.key}
                id={s.key}
                className="rounded-2xl mb-5"
                style={{
                  padding: "32px",
                  background: "rgba(255, 255, 255, 0.45)",
                  backdropFilter: "blur(20px) saturate(1.8)",
                  border: "1px solid rgba(255, 255, 255, 0.5)",
                  boxShadow:
                    "0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
                }}
              >
                <div
                  className="font-extrabold uppercase tracking-wider pb-3 mb-5"
                  style={{
                    fontSize: "24px",
                    color: "#0F1D35",
                    letterSpacing: "1.5px",
                    borderBottom: "2px solid #0284C7",
                  }}
                >
                  {s.label}
                </div>
                {data.sections[s.key].map((story, idx) =>
                  renderStory(story, idx)
                )}
              </div>
            )
        )}

        {/* Did You Know */}
        {data.sections.did_you_know?.length > 0 && (
          <div
            id="did_you_know"
            className="rounded-2xl mb-5"
            style={{
              padding: "32px",
              background: "rgba(255, 255, 255, 0.45)",
              backdropFilter: "blur(20px) saturate(1.8)",
              border: "1px solid rgba(255, 255, 255, 0.5)",
              boxShadow:
                "0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
            }}
          >
            <div
              className="font-extrabold uppercase tracking-wider pb-3 mb-5"
              style={{
                fontSize: "24px",
                color: "#0F1D35",
                letterSpacing: "1.5px",
                borderBottom: "2px solid #0284C7",
              }}
            >
              Did You Know?
            </div>
            {data.sections.did_you_know.map((item, idx) => (
              <div
                key={idx}
                className="rounded-xl mb-3 last:mb-0"
                style={{
                  padding: "24px 28px",
                  background: "rgba(255, 255, 255, 0.5)",
                  backdropFilter: "blur(16px) saturate(1.6)",
                  border: "1px solid rgba(255, 255, 255, 0.55)",
                  boxShadow:
                    "0 1px 2px rgba(0, 0, 0, 0.03), 0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
                }}
              >
                <h3
                  className="mb-2.5"
                  style={{ fontSize: "22px", fontWeight: 700, color: "#0F1D35" }}
                >
                  {item.headline}
                </h3>
                <div style={{ fontSize: "18px", lineHeight: "1.7", color: "#374151" }}>
                  {item.explainer}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Trend to Watch */}
        {data.trend_to_watch && (
          <div
            className="rounded-2xl mb-5"
            style={{
              padding: "28px 32px",
              border: "2px solid rgba(2, 132, 199, 0.2)",
              background: "rgba(255, 255, 255, 0.45)",
              backdropFilter: "blur(20px) saturate(1.8)",
            }}
          >
            <div
              className="font-extrabold uppercase tracking-wider mb-2"
              style={{ fontSize: "24px", color: "#0284C7", letterSpacing: "1.5px" }}
            >
              Trend to Watch
            </div>
            <h3
              className="mb-2"
              style={{ fontSize: "22px", fontWeight: 700, color: "#0F1D35" }}
            >
              {data.trend_to_watch.title}
            </h3>
            <div style={{ fontSize: "18px", lineHeight: "1.7", color: "#374151" }}>
              {data.trend_to_watch.summary}
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
