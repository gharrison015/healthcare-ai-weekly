"use client";

import Link from "next/link";
import { HorizontalScroller } from "@/components/ui/horizontal-scroller";
import { GlowCard } from "@/components/ui/spotlight-card";

interface ConsultingStory {
  headline: string;
  email_summary: string;
  source_article: {
    source: string;
    url?: string;
  };
}

interface ConsultingCardsProps {
  stories: ConsultingStory[];
  issueDate: string;
}

export function ConsultingCards({ stories, issueDate }: ConsultingCardsProps) {
  return (
    <HorizontalScroller className="pb-10">
      {stories.map((story, idx) => (
        <a
          key={idx}
          href={story.source_article.url || `/news/${issueDate}`}
          target={story.source_article.url ? "_blank" : undefined}
          rel={story.source_article.url ? "noopener noreferrer" : undefined}
          className="block flex-shrink-0 no-underline"
          style={{
            width: "340px",
            minHeight: "220px",
            scrollSnapAlign: "start",
            color: "inherit",
          }}
        >
          <GlowCard glowColor="blue" customSize={true} className="w-full h-full p-7">
            <div className="flex flex-col h-full">
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="text-xs font-bold uppercase tracking-wider"
                  style={{ color: "#0284C7" }}
                >
                  {story.source_article.source}
                </div>
              </div>
              <div
                className="font-bold mb-3"
                style={{ color: "#0F1D35", fontSize: "18px", lineHeight: "1.3" }}
              >
                {story.headline}
              </div>
              <div
                className="flex-1 mb-3"
                style={{
                  color: "#6b7280",
                  fontSize: "14px",
                  lineHeight: "1.5",
                  display: "-webkit-box",
                  WebkitLineClamp: 4,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                }}
              >
                {story.email_summary}
              </div>
              <div
                style={{ fontSize: "14px", fontWeight: 600, color: "#0284C7" }}
              >
                Read source &rarr;
              </div>
            </div>
          </GlowCard>
        </a>
      ))}
    </HorizontalScroller>
  );
}
