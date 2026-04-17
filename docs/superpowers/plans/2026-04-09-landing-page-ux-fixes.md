# Landing Page UX Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix four UX issues on the landing page: wire up email deep-links with a sticky banner, switch learning section to horizontal scroller, redesign level badges with per-level colors, and fix card shadow clipping.

**Architecture:** All changes are in the Next.js 14+ frontend (App Router, TypeScript, Tailwind). The landing page is a server component that delegates to client components for each section. We add one new client component (IssueBanner) and modify existing ones. No API or backend changes.

**Tech Stack:** Next.js 16, React 19, TypeScript, Tailwind CSS, existing GlowCard/HorizontalScroller components.

**Spec:** `docs/superpowers/specs/2026-04-09-landing-page-ux-fixes-design.md`

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `src/lib/types.ts` | Modify | Add `getLevelColor()` helper |
| `src/components/ui/spotlight-card.tsx` | Modify | Fix shadow to prevent clipping |
| `src/components/ui/horizontal-scroller.tsx` | Modify | Add padding for shadow clearance |
| `src/app/issue-banner.tsx` | Create | Sticky deep-link banner component |
| `src/app/issues-carousel.tsx` | Modify | Accept highlightIssue, auto-scroll + pulse |
| `src/app/page.tsx` | Modify | Read searchParams, pass to carousel + banner |
| `src/app/learn-cards.tsx` | Modify | Grid to HorizontalScroller, new badge layout |
| `src/app/learn/learn-archive-cards.tsx` | Modify | New badge layout (keeps grid) |

---

### Task 1: Fix Card Shadow (spotlight-card.tsx + horizontal-scroller.tsx)

**Why first:** This is the foundation - every other task renders cards, and we want the shadow fix in place before visually checking anything else.

**Files:**
- Modify: `src/components/ui/spotlight-card.tsx:129`
- Modify: `src/components/ui/horizontal-scroller.tsx:76`

- [ ] **Step 1: Fix GlowCard shadow**

In `src/components/ui/spotlight-card.tsx`, line 129, replace the heavy black shadow with a softer one that won't clip:

```tsx
// OLD (line 129):
className={`${getSizeClasses()} ${!customSize ? 'aspect-[3/4]' : ''} rounded-2xl relative grid grid-rows-[1fr_auto] shadow-[0_1rem_2rem_-1rem_black] p-4 gap-4 backdrop-blur-[5px] ${className}`}

// NEW:
className={`${getSizeClasses()} ${!customSize ? 'aspect-[3/4]' : ''} rounded-2xl relative grid grid-rows-[1fr_auto] shadow-[0_4px_16px_rgba(0,0,0,0.06),inset_0_1px_0_rgba(255,255,255,0.6)] p-4 gap-4 backdrop-blur-[5px] ${className}`}
```

- [ ] **Step 2: Add padding to HorizontalScroller for shadow clearance**

In `src/components/ui/horizontal-scroller.tsx`, line 76, add vertical padding so shadows aren't clipped by `overflow-x-auto`:

```tsx
// OLD (line 76):
className="horizontal-scroller flex gap-4 overflow-x-auto pb-4"

// NEW:
className="horizontal-scroller flex gap-4 overflow-x-auto pt-2 pb-6"
```

- [ ] **Step 3: Verify build**

```bash
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly && npm run build
```

Expected: Build succeeds with no errors.

- [ ] **Step 4: Commit**

```bash
git add src/components/ui/spotlight-card.tsx src/components/ui/horizontal-scroller.tsx
git commit -m "fix: soften card shadows and add scroll padding to prevent clipping"
```

---

### Task 2: Add getLevelColor() Helper (types.ts)

**Files:**
- Modify: `src/lib/types.ts:37` (after getLevelLabel)

- [ ] **Step 1: Add getLevelColor function**

Add after the `getLevelLabel` function (after line 43) in `src/lib/types.ts`:

```typescript
export function getLevelColor(level: 100 | 200 | 300): { bg: string; border: string; text: string } {
  switch (level) {
    case 100: return { bg: 'rgba(22, 163, 74, 0.10)', border: 'rgba(22, 163, 74, 0.30)', text: '#16a34a' };
    case 200: return { bg: 'rgba(2, 132, 199, 0.10)', border: 'rgba(2, 132, 199, 0.30)', text: '#0284C7' };
    case 300: return { bg: 'rgba(124, 58, 237, 0.10)', border: 'rgba(124, 58, 237, 0.30)', text: '#7c3aed' };
  }
}
```

- [ ] **Step 2: Verify build**

```bash
npm run build
```

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add src/lib/types.ts
git commit -m "feat: add getLevelColor helper for per-level badge styling"
```

---

### Task 3: Redesign Learning Cards with Horizontal Scroller + Level Badges (learn-cards.tsx)

**Files:**
- Modify: `src/app/learn-cards.tsx` (full rewrite)

- [ ] **Step 1: Rewrite learn-cards.tsx**

Replace the entire contents of `src/app/learn-cards.tsx` with:

```tsx
"use client";

import Link from "next/link";
import { HorizontalScroller } from "@/components/ui/horizontal-scroller";
import { GlowCard } from "@/components/ui/spotlight-card";
import { getTopicLevel, getLevelLabel, getLevelColor } from "@/lib/types";

interface LearningTopic {
  slug: string;
  title: string;
  description: string;
  accent_color: string;
  question_count: number;
}

export function LearnCards({ topics }: { topics: LearningTopic[] }) {
  return (
    <HorizontalScroller className="pb-10">
      {topics.map((topic) => {
        const level = getTopicLevel(topic.slug);
        const levelLabel = getLevelLabel(level);
        const levelColor = getLevelColor(level);

        return (
          <Link
            key={topic.slug}
            href={`/learn/${topic.slug}`}
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
                {/* Level badge - own row, always first */}
                <div className="mb-2">
                  <span
                    className="font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-full"
                    style={{
                      fontSize: "11px",
                      background: levelColor.bg,
                      color: levelColor.text,
                      border: `1px solid ${levelColor.border}`,
                    }}
                  >
                    {level}-level &middot; {levelLabel}
                  </span>
                </div>

                {/* Metadata row */}
                <div className="flex items-center gap-2 mb-2">
                  <div
                    className="text-xs font-bold uppercase tracking-wider"
                    style={{ color: "#0284C7" }}
                  >
                    Learning
                  </div>
                  <div
                    className="text-xs font-semibold px-1.5 py-0.5 rounded-full"
                    style={{
                      background: "rgba(2, 132, 199, 0.08)",
                      color: "#0284C7",
                      border: "1px solid rgba(2, 132, 199, 0.2)",
                    }}
                  >
                    {topic.question_count} questions
                  </div>
                </div>

                {/* Title */}
                <div
                  className="font-bold mb-2"
                  style={{ color: "#0F1D35", fontSize: "18px", lineHeight: "1.3" }}
                >
                  {topic.title}
                </div>

                {/* Description */}
                <div
                  className="mb-3 flex-1"
                  style={{
                    color: "#475569",
                    fontSize: "15px",
                    lineHeight: "1.55",
                    display: "-webkit-box",
                    WebkitLineClamp: 3,
                    WebkitBoxOrient: "vertical" as const,
                    overflow: "hidden",
                  }}
                >
                  {topic.description}
                </div>

                {/* CTA */}
                <div>
                  <div
                    className="inline-block font-bold rounded-lg"
                    style={{
                      fontSize: "13px",
                      color: "#0284C7",
                      padding: "6px 12px",
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
    </HorizontalScroller>
  );
}
```

Key changes from the old version:
- Grid container replaced with `HorizontalScroller`
- Cards are fixed 340px width with `flex-shrink-0` (matches issues/bulletins/consulting)
- Level badge is its own row at the top, uses `getLevelColor()` for green/blue/purple
- Description clamped to 3 lines to keep card heights consistent

- [ ] **Step 2: Verify build**

```bash
npm run build
```

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add src/app/learn-cards.tsx
git commit -m "feat: switch learning cards to horizontal scroller with color-coded level badges"
```

---

### Task 4: Update Learn Archive Cards with New Badge Layout (learn-archive-cards.tsx)

**Files:**
- Modify: `src/app/learn/learn-archive-cards.tsx`

- [ ] **Step 1: Update badge section in learn-archive-cards.tsx**

This file keeps its grid layout (it's the `/learn` archive page, not the landing page). Only the badge layout changes to match the new design.

Replace the entire contents of `src/app/learn/learn-archive-cards.tsx` with:

```tsx
"use client";

import Link from "next/link";
import { GlowCard } from "@/components/ui/spotlight-card";
import { getTopicLevel, getLevelLabel, getLevelColor } from "@/lib/types";

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
        const levelColor = getLevelColor(level);

        return (
          <Link
            key={topic.slug}
            href={`/learn/${topic.slug}`}
            className="block no-underline"
            style={{ color: "inherit" }}
          >
            <GlowCard glowColor="blue" customSize={true} className="w-full h-full p-7">
              <div className="flex flex-col h-full">
                {/* Level badge - own row, always first */}
                <div className="mb-2">
                  <span
                    className="font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-full"
                    style={{
                      fontSize: "11px",
                      background: levelColor.bg,
                      color: levelColor.text,
                      border: `1px solid ${levelColor.border}`,
                    }}
                  >
                    {level}-level &middot; {levelLabel}
                  </span>
                </div>

                {/* Metadata row */}
                <div className="flex items-center gap-2 mb-3">
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
                </div>

                {/* Title */}
                <div
                  className="font-bold mb-2"
                  style={{ color: "#0F1D35", fontSize: "20px", lineHeight: "1.3" }}
                >
                  {topic.title}
                </div>

                {/* Description */}
                <div
                  className="mb-4 flex-1"
                  style={{ color: "#475569", fontSize: "15px", lineHeight: "1.55" }}
                >
                  {topic.description}
                </div>

                {/* CTA */}
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
```

- [ ] **Step 2: Verify build**

```bash
npm run build
```

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add src/app/learn/learn-archive-cards.tsx
git commit -m "feat: update learn archive cards with color-coded level badges"
```

---

### Task 5: Create IssueBanner Component (issue-banner.tsx)

**Files:**
- Create: `src/app/issue-banner.tsx`

- [ ] **Step 1: Create the banner component**

Create `src/app/issue-banner.tsx`:

```tsx
"use client";

import { useState } from "react";
import type { IssueManifestEntry } from "@/lib/types";

interface IssueBannerProps {
  highlightIssue: string;
  issues: IssueManifestEntry[];
}

export function IssueBanner({ highlightIssue, issues }: IssueBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  const matchedIssue = issues.find((i) => i.date === highlightIssue);
  if (!matchedIssue || dismissed) return null;

  const weekLabel = matchedIssue.week_range || matchedIssue.date;

  const handleDismiss = () => {
    setDismissed(true);
    // Strip ?issue= from URL without reload
    const url = new URL(window.location.href);
    url.searchParams.delete("issue");
    window.history.replaceState({}, "", url.pathname);
  };

  return (
    <div
      className="sticky top-0 z-50 w-full"
      style={{ animation: "caption-fade 0.3s ease-out" }}
    >
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{
          background: "#0284C7",
          color: "#fff",
          boxShadow: "0 2px 12px rgba(2, 132, 199, 0.35)",
        }}
      >
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="text-sm font-medium truncate">
            This article is from the{" "}
            <span className="font-bold">Week of {weekLabel}</span> issue
          </div>
          <a
            href={`/news/${matchedIssue.date}`}
            className="flex-shrink-0 font-bold text-sm no-underline rounded-full px-4 py-1.5"
            style={{
              background: "rgba(255, 255, 255, 0.2)",
              color: "#fff",
              border: "1px solid rgba(255, 255, 255, 0.3)",
              backdropFilter: "blur(8px)",
            }}
          >
            Read this issue &rarr;
          </a>
        </div>
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 ml-3 p-1 rounded-full border-none cursor-pointer"
          style={{
            background: "rgba(255, 255, 255, 0.15)",
            color: "#fff",
            lineHeight: 1,
          }}
          aria-label="Dismiss"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify build**

```bash
npm run build
```

Expected: Build succeeds (component not yet used, but should compile).

- [ ] **Step 3: Commit**

```bash
git add src/app/issue-banner.tsx
git commit -m "feat: add IssueBanner component for email deep-links"
```

---

### Task 6: Wire Up IssuesCarousel Highlight (issues-carousel.tsx)

**Files:**
- Modify: `src/app/issues-carousel.tsx`

- [ ] **Step 1: Add highlightIssue prop and auto-scroll + pulse logic**

Replace the entire contents of `src/app/issues-carousel.tsx` with:

```tsx
"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import { HorizontalScroller } from "@/components/ui/horizontal-scroller";
import { GlowCard } from "@/components/ui/spotlight-card";
import type { IssueManifestEntry } from "@/lib/types";

interface IssuesCarouselProps {
  issues: IssueManifestEntry[];
  highlightIssue?: string;
}

function getMonthLabel(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

export function IssuesCarousel({ issues, highlightIssue }: IssuesCarouselProps) {
  const [visibleMonth, setVisibleMonth] = useState<string | null>(null);
  const [highlightedDate, setHighlightedDate] = useState<string | null>(highlightIssue || null);
  const hideTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef<Map<string, HTMLElement>>(new Map());

  // Auto-scroll to highlighted issue on mount
  useEffect(() => {
    if (!highlightIssue) return;
    const card = cardRefs.current.get(highlightIssue);
    if (card) {
      // Small delay to let the scroller render
      setTimeout(() => {
        card.scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
      }, 300);
    }
    // Clear highlight after 4 seconds
    const timer = setTimeout(() => setHighlightedDate(null), 4000);
    return () => clearTimeout(timer);
  }, [highlightIssue]);

  const handleScroll = useCallback(() => {
    if (hideTimer.current) clearTimeout(hideTimer.current);

    const container = wrapperRef.current;
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    const centerX = containerRect.left + containerRect.width / 2;

    let closestDate: string | null = null;
    let closestDist = Infinity;

    cardRefs.current.forEach((el, date) => {
      const rect = el.getBoundingClientRect();
      const cardCenter = rect.left + rect.width / 2;
      const dist = Math.abs(cardCenter - centerX);
      if (dist < closestDist) {
        closestDist = dist;
        closestDate = date;
      }
    });

    if (closestDate) {
      setVisibleMonth(getMonthLabel(closestDate));
    }

    hideTimer.current = setTimeout(() => {
      setVisibleMonth(null);
    }, 1200);
  }, []);

  useEffect(() => {
    const wrapper = wrapperRef.current;
    if (!wrapper) return;

    const scrollContainer = wrapper.querySelector("[data-scroll-container]")?.parentElement || wrapper;
    scrollContainer.addEventListener("scroll", handleScroll, { passive: true, capture: true });

    return () => {
      scrollContainer.removeEventListener("scroll", handleScroll, { capture: true });
      if (hideTimer.current) clearTimeout(hideTimer.current);
    };
  }, [handleScroll]);

  return (
    <div className="relative" ref={wrapperRef} onScrollCapture={handleScroll}>
      {/* Timeline month indicator */}
      {visibleMonth && (
        <div
          className="absolute -top-8 left-1/2 -translate-x-1/2 z-10 pointer-events-none"
          style={{
            animation: "timeline-fade-in 0.2s ease-out",
          }}
        >
          <div
            className="font-bold rounded-full px-4 py-1.5"
            style={{
              fontSize: "13px",
              color: "#fff",
              background: "#0284C7",
              boxShadow: "0 2px 12px rgba(2, 132, 199, 0.35)",
            }}
          >
            {visibleMonth}
          </div>
        </div>
      )}

      <HorizontalScroller className="pb-10">
        {issues.map((issue) => {
          const storyCount =
            (issue.top_stories || 0) +
            (issue.vbc_watch || 0) +
            (issue.ma_partnerships || 0) +
            (issue.consulting_intelligence || 0) +
            (issue.did_you_know || 0);

          const isHighlighted = highlightedDate === issue.date;

          return (
            <a
              key={issue.date}
              href={`/news/${issue.date}`}
              className="block flex-shrink-0 no-underline"
              ref={(el) => {
                if (el) cardRefs.current.set(issue.date, el);
              }}
              style={{
                width: "340px",
                minHeight: "220px",
                scrollSnapAlign: "start",
                color: "inherit",
                borderRadius: "16px",
                animation: isHighlighted ? "highlight-pulse 1.5s ease-in-out infinite" : undefined,
              }}
            >
              <GlowCard glowColor="blue" customSize={true} className="w-full h-full p-7">
                <div className="flex flex-col h-full">
                  <div
                    className="font-bold uppercase tracking-wider mb-3"
                    style={{
                      fontSize: "13px",
                      letterSpacing: "1.5px",
                      color: "#0284C7",
                    }}
                  >
                    Week of {issue.week_range || issue.date}
                  </div>
                  <div
                    className="mb-4 flex-1"
                    style={{
                      fontSize: "15px",
                      lineHeight: "1.55",
                      color: "#475569",
                    }}
                  >
                    {issue.editorial_summary || ""}
                  </div>
                  <div>
                    <div style={{ fontSize: "13px", color: "#94a3b8" }}>
                      {storyCount} stories curated
                    </div>
                    <div
                      className="mt-3"
                      style={{ fontSize: "14px", fontWeight: 600, color: "#0284C7" }}
                    >
                      Read deep dive &rarr;
                    </div>
                  </div>
                </div>
              </GlowCard>
            </a>
          );
        })}
      </HorizontalScroller>
    </div>
  );
}
```

Key changes from original:
- New `highlightIssue?: string` prop
- `highlightedDate` state that auto-clears after 4 seconds
- `useEffect` on mount that scrolls the matching card into view
- `highlight-pulse` animation applied to the matching card's outer anchor (uses existing CSS keyframes)

- [ ] **Step 2: Verify build**

```bash
npm run build
```

Expected: Build succeeds.

- [ ] **Step 3: Commit**

```bash
git add src/app/issues-carousel.tsx
git commit -m "feat: add highlight and auto-scroll for email deep-links in issues carousel"
```

---

### Task 7: Wire Up page.tsx with searchParams, Banner, and Carousel Highlight

**Files:**
- Modify: `src/app/page.tsx`

- [ ] **Step 1: Update page.tsx to read searchParams and pass props**

Replace the entire contents of `src/app/page.tsx` with:

```tsx
import Link from "next/link";
import { AmbientBackground } from "@/components/ui/ambient-background";
import { GlassCardStyles } from "@/components/ui/glass-card";
import { SourceTicker } from "@/components/ui/source-ticker";
import { PulseBeamCTA } from "@/components/ui/pulse-beam-cta";
import { BreakingNewsTicker } from "@/components/ui/breaking-news-ticker";
import { getIssuesManifest, getBulletins, getLearningTopics, getIssueData } from "@/lib/data";
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

  // Load consulting intelligence from the latest issue
  const latestIssueDate = issues.length > 0 ? issues[0].date : null;
  const latestIssueData = latestIssueDate ? getIssueData(latestIssueDate) : null;
  const consultingStories = latestIssueData?.sections?.consulting_intelligence ?? [];

  return (
    <>
      <AmbientBackground />
      <GlassCardStyles />

      {/* Deep-link banner from email */}
      {highlightIssue && (
        <IssueBanner highlightIssue={highlightIssue} issues={issues} />
      )}

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
        <div className="flex items-baseline justify-between pt-8 mb-5">
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
            <div className="flex items-baseline justify-between pt-8 mb-5">
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
            <LearnCards topics={learn} />
          </div>
        )}

        {/* Consulting Intelligence Section */}
        {consultingStories.length > 0 && latestIssueDate && (
          <div className="mt-12">
            <div className="flex items-baseline justify-between pt-8 mb-1">
              <div
                className="font-extrabold uppercase tracking-wider"
                style={{ fontSize: "28px", color: "#0284C7", letterSpacing: "-0.3px" }}
              >
                Consulting Intelligence
              </div>
              <Link
                href={`/news/${latestIssueDate}`}
                className="no-underline hover:underline font-semibold"
                style={{ fontSize: "14px", color: "#0284C7" }}
              >
                View full issue &rarr;
              </Link>
            </div>
            <div
              className="mb-5"
              style={{ fontSize: "15px", color: "#6b7280" }}
            >
              How consulting firms are moving in healthcare AI
            </div>
            <ConsultingCards stories={consultingStories} issueDate={latestIssueDate} />
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
```

Changes from original:
- `export default function` becomes `export default async function` with `searchParams` prop
- Imports `IssueBanner`
- Reads `params.issue` from searchParams (Next.js 16 uses `Promise<{...}>` for searchParams)
- Renders `IssueBanner` above the breaking news ticker when `highlightIssue` is set
- Passes `highlightIssue` to `IssuesCarousel`

- [ ] **Step 2: Verify full build**

```bash
npm run build
```

Expected: Build succeeds with all pages generated.

- [ ] **Step 3: Commit**

```bash
git add src/app/page.tsx src/app/issue-banner.tsx
git commit -m "feat: wire up issue deep-links with sticky banner and carousel highlight"
```

---

### Task 8: Final Verification

- [ ] **Step 1: Full build**

```bash
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly && npm run build
```

Expected: Build succeeds, all static pages generated.

- [ ] **Step 2: Visual smoke test**

```bash
npm run dev
```

Open in browser and verify:
1. Landing page loads, all sections render
2. Cards across all sections have consistent shadows (no hard clipping lines)
3. Learning section scrolls horizontally like issues/bulletins/consulting
4. Learning cards show color-coded level badges (green 100, blue 200, purple 300) in consistent position
5. `/learn` archive page shows updated badges in grid layout
6. Add `?issue=2026-04-04` to URL - banner appears, carousel scrolls to Apr 4 card with pulse
7. Dismiss banner - it disappears, URL cleans up
8. Test on mobile viewport (Chrome DevTools) - banner is prominent, scrollers work with touch

- [ ] **Step 3: Commit any fixes from visual testing**

Only if needed. Then stop dev server.
