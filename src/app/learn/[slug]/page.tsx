import { notFound } from "next/navigation";
import Link from "next/link";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { getLearningTopic, getLearnSlugs } from "@/lib/data";
import { getTopicLevel, getLevelLabel } from "@/lib/types";
import { Quiz } from "@/components/quiz";

export async function generateStaticParams() {
  const slugs = getLearnSlugs();
  return slugs.map((slug) => ({ slug }));
}

interface PageProps {
  params: Promise<{ slug: string }>;
}

export default async function LearnTopicPage({ params }: PageProps) {
  const { slug } = await params;
  const topic = getLearningTopic(slug);

  if (!topic) {
    notFound();
  }

  const paragraphs = topic.summary.split("\n\n").filter(Boolean);
  const level = getTopicLevel(topic.slug);
  const levelLabel = getLevelLabel(level);
  const accent = "#0284C7";

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4">
        <div style={{ padding: "48px 0 32px" }}>
          <Link
            href="/learn"
            className="inline-block no-underline hover:underline rounded-lg mb-5"
            style={{
              fontSize: "16px",
              color: accent,
              fontWeight: 700,
              padding: "8px 16px",
              background: "rgba(2, 132, 199, 0.06)",
              border: "1px solid rgba(2, 132, 199, 0.15)",
            }}
          >
            &larr; All Topics
          </Link>

          <div className="flex items-center gap-2 mb-4">
            <span
              className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-md"
              style={{
                background: "rgba(2, 132, 199, 0.1)",
                color: accent,
                border: "1px solid rgba(2, 132, 199, 0.2)",
                letterSpacing: "0.8px",
              }}
            >
              Learning
            </span>
            <span
              className="text-xs font-bold px-2 py-0.5 rounded-full"
              style={{
                background: "rgba(2, 132, 199, 0.12)",
                color: accent,
                border: "1px solid rgba(2, 132, 199, 0.25)",
              }}
            >
              {level}-level &middot; {levelLabel}
            </span>
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{
                background: "rgba(2, 132, 199, 0.08)",
                color: accent,
                border: "1px solid rgba(2, 132, 199, 0.2)",
              }}
            >
              {topic.quiz.questions.length} questions
            </span>
            <span className="text-xs" style={{ color: "#94a3b8" }}>
              {topic.source_count} source{topic.source_count !== 1 ? "s" : ""}
            </span>
          </div>

          <h1
            className="font-extrabold mb-3"
            style={{
              fontSize: "34px",
              color: "#0F1D35",
              letterSpacing: "-0.5px",
              lineHeight: "1.2",
            }}
          >
            {topic.title}
          </h1>

          <div style={{ fontSize: "18px", lineHeight: "1.5", color: "#6b7280" }}>
            {topic.description}
          </div>
        </div>

        {/* Overview */}
        <div className="mb-8">
          <div
            className="font-extrabold uppercase tracking-wider pb-3 mb-5"
            style={{
              fontSize: "24px",
              color: "#0F1D35",
              letterSpacing: "1.5px",
              borderBottom: "2px solid #0284C7",
            }}
          >
            Overview
          </div>
          <div className="space-y-4">
            {paragraphs.map((p, idx) => (
              <p
                key={idx}
                style={{
                  fontSize: "18px",
                  lineHeight: "1.7",
                  color: "#374151",
                  margin: 0,
                }}
              >
                {p}
              </p>
            ))}
          </div>
        </div>

        {/* Quiz */}
        <div className="mb-8">
          <div
            className="font-extrabold uppercase tracking-wider pb-3 mb-5"
            style={{
              fontSize: "24px",
              color: "#0F1D35",
              letterSpacing: "1.5px",
              borderBottom: "2px solid #0284C7",
            }}
          >
            Quick Check
          </div>
          <Quiz
            questions={topic.quiz.questions}
            title={topic.quiz.title}
            accentColor={accent}
          />
        </div>

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
