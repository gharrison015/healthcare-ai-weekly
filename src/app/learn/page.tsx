import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { getLearningTopics } from "@/lib/data";
import { getTopicLevel } from "@/lib/types";
import { LearnArchiveCards } from "./learn-archive-cards";

export default function LearnPage() {
  const topics = getLearningTopics();

  const fundamentals = topics.filter((t) => getTopicLevel(t.slug) === 100);
  const applied = topics.filter((t) => getTopicLevel(t.slug) === 200);
  const strategic = topics.filter((t) => getTopicLevel(t.slug) === 300);

  const sections = [
    { level: 100, label: "Fundamentals", sublabel: "Basic AI concepts and terminology", topics: fundamentals },
    { level: 200, label: "Applied", sublabel: "AI in healthcare, practical applications", topics: applied },
    { level: 300, label: "Strategic", sublabel: "Leadership, vendor evaluation, implementation strategy", topics: strategic },
  ];

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
          <div className="space-y-12">
            {sections.map(
              (section) =>
                section.topics.length > 0 && (
                  <div key={section.level}>
                    <div className="flex items-baseline gap-3 mb-5">
                      <div
                        className="font-extrabold"
                        style={{ fontSize: "24px", color: "#0F1D35", letterSpacing: "-0.3px" }}
                      >
                        {section.label}
                      </div>
                      <div
                        className="font-bold px-2.5 py-0.5 rounded-full"
                        style={{
                          fontSize: "12px",
                          color: "#0284C7",
                          background: "rgba(2, 132, 199, 0.1)",
                          border: "1px solid rgba(2, 132, 199, 0.2)",
                        }}
                      >
                        {section.level}-level
                      </div>
                      <div style={{ fontSize: "15px", color: "#6b7280" }}>
                        {section.sublabel}
                      </div>
                    </div>
                    <LearnArchiveCards topics={section.topics} />
                  </div>
                )
            )}
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
