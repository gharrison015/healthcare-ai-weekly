"use client";

import Link from "next/link";
import { GlowCard } from "@/components/ui/spotlight-card";
import { getTopicLevel, getLevelLabel } from "@/lib/types";

interface LearningTopic {
  slug: string;
  title: string;
  description: string;
  accent_color: string;
  question_count: number;
}

export function LearnArchiveCards({ topics }: { topics: LearningTopic[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-5 pb-8" style={{ gridAutoRows: "1fr" }}>
      {topics.map((topic) => {
        const level = getTopicLevel(topic.slug);
        const levelLabel = getLevelLabel(level);

        return (
          <Link
            key={topic.slug}
            href={`/learn/${topic.slug}`}
            className="block no-underline"
            style={{ color: "inherit" }}
          >
            <GlowCard glowColor="blue" customSize={true} className="w-full h-full p-7">
              <div className="flex flex-col h-full">
                <div className="flex items-center gap-2 mb-3 flex-wrap">
                  <span
                    className="text-xs font-bold uppercase tracking-wider"
                    style={{ color: "#0284C7" }}
                  >
                    Learning
                  </span>
                  <span
                    className="text-xs font-semibold px-2 py-0.5 rounded-full"
                    style={{
                      background: "rgba(2, 132, 199, 0.08)",
                      color: "#0284C7",
                      border: "1px solid rgba(2, 132, 199, 0.2)",
                    }}
                  >
                    {topic.question_count} questions
                  </span>
                  <span
                    className="text-xs font-bold px-2 py-0.5 rounded-full"
                    style={{
                      background: "rgba(2, 132, 199, 0.12)",
                      color: "#0284C7",
                      border: "1px solid rgba(2, 132, 199, 0.25)",
                    }}
                  >
                    {level}-level &middot; {levelLabel}
                  </span>
                </div>
                <div
                  className="font-bold mb-2"
                  style={{ color: "#0F1D35", fontSize: "20px", lineHeight: "1.3" }}
                >
                  {topic.title}
                </div>
                <div
                  className="mb-4 flex-1"
                  style={{ color: "#475569", fontSize: "15px", lineHeight: "1.55" }}
                >
                  {topic.description}
                </div>
                <div>
                  <div
                    className="inline-block font-bold rounded-lg"
                    style={{
                      fontSize: "14px",
                      color: "#0284C7",
                      padding: "8px 16px",
                      background: "rgba(2, 132, 199, 0.06)",
                      border: "1px solid rgba(2, 132, 199, 0.15)",
                    }}
                  >
                    Take the Quiz &rarr;
                  </div>
                </div>
              </div>
            </GlowCard>
          </Link>
        );
      })}
    </div>
  );
}
