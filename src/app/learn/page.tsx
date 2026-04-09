import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { getLearningTopics } from "@/lib/data";
import { LearnArchiveCards } from "./learn-archive-cards";

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
          <LearnArchiveCards topics={topics} />
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
