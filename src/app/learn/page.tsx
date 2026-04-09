import Link from "next/link";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { getLearningTopics } from "@/lib/data";

export default function LearnPage() {
  const topics = getLearningTopics();

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      <div className="px-10 max-sm:px-4">
        <div style={{ padding: "48px 0 32px" }}>
          <h1
            className="font-extrabold mb-2"
            style={{ fontSize: "38px", color: "#0F1D35", letterSpacing: "-0.5px" }}
          >
            AI Learning
          </h1>
          <div style={{ fontSize: "20px", lineHeight: "1.6", color: "#374151" }}>
            Educational resources on AI in healthcare. Guides, explainers, and
            quizzes for leaders who want to stay sharp.
          </div>
        </div>

        {topics.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pb-8">
            {topics.map((topic) => (
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
                <div className="flex items-center gap-2 mb-3">
                  <span
                    className="text-xs font-bold uppercase tracking-wider"
                    style={{ color: topic.accent_color }}
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
                    {topic.question_count} questions
                  </span>
                </div>
                <div
                  className="font-bold mb-2"
                  style={{ color: "#0F1D35", fontSize: "20px", lineHeight: "1.3" }}
                >
                  {topic.title}
                </div>
                <div
                  className="mb-4"
                  style={{ color: "#475569", fontSize: "15px", lineHeight: "1.55" }}
                >
                  {topic.description}
                </div>
                <div
                  className="inline-block font-bold rounded-lg"
                  style={{
                    fontSize: "14px",
                    color: topic.accent_color,
                    padding: "8px 16px",
                    background: `${topic.accent_color}0a`,
                    border: `1px solid ${topic.accent_color}20`,
                  }}
                >
                  Take the Quiz &rarr;
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div
            className="text-center py-16"
            style={{ color: "#94a3b8", fontSize: "16px" }}
          >
            No learning resources published yet.
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
