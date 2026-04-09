import { notFound } from "next/navigation";
import Link from "next/link";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { getLearningTopic, getLearnSlugs } from "@/lib/data";
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

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4 max-w-3xl mx-auto w-full">
        <div style={{ padding: "48px 0 32px" }}>
          <Link
            href="/learn"
            className="inline-block no-underline hover:underline rounded-lg mb-5"
            style={{
              fontSize: "16px",
              color: topic.accent_color,
              fontWeight: 700,
              padding: "8px 16px",
              background: `${topic.accent_color}0a`,
              border: `1px solid ${topic.accent_color}20`,
            }}
          >
            &larr; All Topics
          </Link>

          <div className="flex items-center gap-2 mb-4">
            <span
              className="text-xs font-bold uppercase tracking-wider px-2.5 py-1 rounded-md"
              style={{
                background: `${topic.accent_color}12`,
                color: topic.accent_color,
                border: `1px solid ${topic.accent_color}25`,
                letterSpacing: "0.8px",
              }}
            >
              Learning
            </span>
            <span
              className="text-xs font-semibold px-2 py-0.5 rounded-full"
              style={{
                background: `${topic.accent_color}12`,
                color: topic.accent_color,
                border: `1px solid ${topic.accent_color}25`,
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

        {/* Summary */}
        <div
          className="rounded-2xl mb-8"
          style={{
            padding: "28px 32px",
            background: "rgba(255, 255, 255, 0.5)",
            backdropFilter: "blur(16px) saturate(1.6)",
            border: "1px solid rgba(255, 255, 255, 0.55)",
            boxShadow:
              "0 1px 2px rgba(0, 0, 0, 0.03), 0 4px 16px rgba(0, 0, 0, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
            borderLeft: `4px solid ${topic.accent_color}`,
          }}
        >
          <div
            className="font-extrabold uppercase tracking-wider mb-4"
            style={{ fontSize: "13px", color: topic.accent_color, letterSpacing: "1.5px" }}
          >
            Overview
          </div>
          <div className="space-y-4">
            {paragraphs.map((p, idx) => (
              <p
                key={idx}
                style={{
                  fontSize: "17px",
                  lineHeight: "1.75",
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
        <div
          className="rounded-2xl mb-8"
          style={{
            padding: "28px 32px",
            background: "rgba(255, 255, 255, 0.45)",
            backdropFilter: "blur(20px) saturate(1.8)",
            border: "1px solid rgba(255, 255, 255, 0.5)",
            boxShadow:
              "0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.06), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
          }}
        >
          <Quiz
            questions={topic.quiz.questions}
            title={topic.quiz.title}
            accentColor={topic.accent_color}
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
