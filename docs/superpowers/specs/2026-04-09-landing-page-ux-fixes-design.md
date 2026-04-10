# Landing Page UX Fixes - Design Spec

Date: 2026-04-09

## Problem Statement

Three UX issues on the Healthcare AI Weekly landing page:

1. **Email deep-links don't work.** Email article links include `?issue=YYYY-MM-DD` but the landing page ignores the param. On mobile, users land on the site with no guidance to the right weekly issue.
2. **Learning section layout is inconsistent.** Uses a CSS grid (vertical stack on mobile) while Issues, Bulletins, and Consulting all use horizontal scrollers.
3. **Level badges are hard to find and shift position.** The 100/200/300-level badges sit inline with other metadata, wrap unpredictably, and all look the same blue.
4. **Card shadows are clipped.** The GlowCard shadow (`0 1rem 2rem -1rem black`) gets cut by `overflow-x-auto` on the HorizontalScroller, creating a visible hard line.

## Changes

### 1. Issue Deep-Link with Mobile Sticky Banner

**Files:** `src/app/page.tsx`, `src/app/issues-carousel.tsx`, new `src/app/issue-banner.tsx`

**page.tsx:**
- Convert to async server component accepting `searchParams`
- Read `searchParams.issue` (the `YYYY-MM-DD` value from email links)
- Pass `highlightIssue={issueParam}` prop to `IssuesCarousel`
- Pass `highlightIssue={issueParam}` and `issues={issues}` to new `IssueBanner`

**issue-banner.tsx** (new client component):
- Renders only when `highlightIssue` is set and matches a valid issue date
- Sticky bar fixed to top of viewport (`position: sticky; top: 0; z-index: 50`)
- Content: "This article is from the **Week of {week_range}** issue" + "Read this issue" button linking to `/news/{date}`
- Blue background (#0284C7), white text, dismiss X button
- On dismiss, removes itself (client state) and strips `?issue=` from URL via `replaceState`
- Animates in with `caption-fade` keyframes (already in globals.css)

**issues-carousel.tsx:**
- Accept new `highlightIssue?: string` prop
- On mount, if `highlightIssue` matches an issue date:
  - Scroll the matching card into view (`scrollIntoView({ behavior: 'smooth', inline: 'center' })`)
  - Apply `highlight-pulse` animation class to the matching card (already in globals.css)
  - Animation runs for 3 seconds then stops

### 2. Learning Section Switches to Horizontal Scroller

**File:** `src/app/learn-cards.tsx`

- Replace CSS grid container with `HorizontalScroller` (same component used by Bulletins and Consulting)
- Cards become fixed-width (`340px`, `minHeight: 220px`, `scrollSnapAlign: "start"`) matching all other sections
- Cards use `flex-shrink-0` like bulletin/consulting cards
- Container gets `pb-10` class matching other sections

### 3. Level Badges Redesigned

**Files:** `src/app/learn-cards.tsx`, `src/app/learn/learn-archive-cards.tsx`, `src/lib/types.ts`

**types.ts** - add level color helper:
```typescript
export function getLevelColor(level: 100 | 200 | 300): { bg: string; border: string; text: string } {
  switch (level) {
    case 100: return { bg: 'rgba(22, 163, 74, 0.10)', border: 'rgba(22, 163, 74, 0.30)', text: '#16a34a' };
    case 200: return { bg: 'rgba(2, 132, 199, 0.10)', border: 'rgba(2, 132, 199, 0.30)', text: '#0284C7' };
    case 300: return { bg: 'rgba(124, 58, 237, 0.10)', border: 'rgba(124, 58, 237, 0.30)', text: '#7c3aed' };
  }
}
```

**Card layout change (both files):**
- Level badge moves to its own row, first element in the card (above everything else)
- Badge is a pill: `text-[11px] font-extrabold uppercase tracking-wider px-2.5 py-1 rounded-full`
- Uses `getLevelColor()` for per-level coloring (green/blue/purple)
- Format: `{level}-LEVEL : {labelText}` (e.g., "100-LEVEL : FUNDAMENTALS")
- Below the badge: "Learning" label + "X questions" pill on the same row (existing metadata, unchanged)
- This guarantees the level badge is always in the same position on every card regardless of title length

### 4. Card Shadow and Shape Consistency

**File:** `src/components/ui/spotlight-card.tsx`

The current shadow `shadow-[0_1rem_2rem_-1rem_black]` is heavy and gets clipped by overflow containers. Replace with a softer shadow that works within scroll containers:

- Change to: `shadow-[0_4px_16px_rgba(0,0,0,0.04)]` (the same shadow used in the highlight-pulse animation's base state)
- Add `inset 0 1px 0 rgba(255,255,255,0.6)` for consistent glass inner highlight
- Full value: `shadow-[0_4px_16px_rgba(0,0,0,0.04),inset_0_1px_0_rgba(255,255,255,0.6)]`

**File:** `src/components/ui/horizontal-scroller.tsx`

- Inner scroll container: increase padding from `pb-4` to `pb-6` for shadow clearance
- Add `pt-2` to prevent top shadow clipping

**Cross-section card audit - enforce consistency:**

All card containers across all sections must use:
- `width: 340px` (fixed)
- `minHeight: 220px`
- `scrollSnapAlign: "start"`
- `GlowCard glowColor="blue" customSize={true} className="w-full h-full p-7"`

Currently consistent across Issues, Bulletins, Consulting. Learning will match after change #2.

## Files Modified

| File | Change |
|---|---|
| `src/app/page.tsx` | Read searchParams, pass highlightIssue to carousel and banner |
| `src/app/issue-banner.tsx` | New - sticky deep-link banner |
| `src/app/issues-carousel.tsx` | Accept highlightIssue, auto-scroll, pulse animation |
| `src/app/learn-cards.tsx` | Grid to HorizontalScroller, new level badge layout |
| `src/app/learn/learn-archive-cards.tsx` | New level badge layout (keeps grid for archive page) |
| `src/lib/types.ts` | Add getLevelColor() helper |
| `src/components/ui/spotlight-card.tsx` | Softer shadow |
| `src/components/ui/horizontal-scroller.tsx` | More padding for shadow clearance |

## Out of Scope

- Fallback to direct deep-link on mobile (will evaluate after testing approach A)
- Supabase analytics integration
- Email template changes (links already send `?issue=` param correctly)
