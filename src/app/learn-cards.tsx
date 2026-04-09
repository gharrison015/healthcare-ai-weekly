"use client";

import Link from "next/link";
import { GlowCard } from "@/components/ui/spotlight-card";

function accentToGlow(accent: string): 'blue' | 'purple' | 'green' | 'red' | 'orange' {
  if (accent.includes('059669') || accent.includes('green')) return 'green';
  if (accent.includes('dc2626') || accent.includes('red')) return 'red';
  if (accent.includes('7c3aed') || accent.includes('purple')) return 'purple';
  if (accent.includes('d97706') || accent.includes('amber') || accent.includes('orange')) return 'orange';
  return 'blue';
}

interface LearningTopic {
  slug: string;
  title: string;
  description: string;
  accent_color: string;
  question_count: number;
}

export function LearnCards({ topics }: { topics: LearningTopic[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {topics.map((topic) => (
        <Link
          key={topic.slug}
          href={`/learn/${topic.slug}`}
          className="block no-underline"
          style={{ color: "inherit" }}
        >
          <GlowCard glowColor={accentToGlow(topic.accent_color)} customSize={true} className="w-full p-7">
            <div>
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
            </div>
          </GlowCard>
        </Link>
      ))}
    </div>
  );
}
