# Healthcare AI Weekly — Platform Expansion Design Spec

## Overview

Three interconnected changes to the Healthcare AI Weekly platform:

1. **Next.js Conversion** — Convert the static Vercel site to a Next.js app with React, Tailwind, shadcn/ui, TypeScript
2. **Bulletin System** — Near-real-time breaking news from X/Twitter (see `2026-04-08-bulletin-system-design.md` for full spec)
3. **AI Literacy Section** — Educational content + quizzes sourced from NotebookLM, generated via Gemini, with anonymous analytics in Supabase
4. **Email CTA Fix** — Shrink the oversized "Read the Full Deep Dive" button in the email template

## Audience

Guidehouse colleagues — consultants across practices who need practical AI fluency to serve their clients.

## 1. Next.js Conversion

### Framework

- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- shadcn/ui components
- Static generation (SSG) for all content pages

### Pages

| Route | Purpose |
|---|---|
| `/` | Landing page: hero, source ticker, issues carousel, bulletins, learning section, CTA |
| `/issues/[date]` | Deep-dive page (migrated from current static HTML template) |
| `/bulletins` | Bulletin archive (chronological) |
| `/bulletins/[slug]` | Individual bulletin page |
| `/learn` | Full learning archive with all topics + quiz history |
| `/learn/[slug]` | Individual topic page with embedded quiz |
| `/analytics` | Protected dashboard — quiz completion rates, topic difficulty, engagement |

### Design System

Migrate the existing glass morphism CSS into Tailwind + reusable components:

- `GlassCard` — `backdrop-filter: blur(20px) saturate(1.8)`, white translucent borders, hover lift
- `AmbientBackground` — mesh gradient + floating blurred circles with parallax
- `SourceTicker` — auto-scrolling editorial source list
- `PulseBeamCTA` — "Let's Talk AI" mailto button with pulse animation

**Color palette (unchanged):**
- Primary: `#0284C7` (sky blue — links, borders, accents)
- Dark: `#0F1D35` (headlines, text)
- Body: `#374151` / `#6b7280` (text, secondary)
- Background: `#f0f2f5` (off-white)
- Glass: `rgba(255,255,255,0.45)` with blur
- Bulletin accent: `#dc2626` (red/orange, distinct from blue)
- Learning accent: TBD (suggest green `#059669` to distinguish from issues blue and bulletin red)

**Font:** Aptos, fallback Calibri, system fonts

### Landing Page Layout

```
┌─────────────────────────────────────────────────┐
│  Hero: Healthcare AI Weekly                      │
│  Tagline + byline                                │
├─────────────────────────────────────────────────┤
│  Source Ticker (auto-scroll)                     │
├─────────────────────────────────────────────────┤
│  ◀  [Issue Card] [Issue Card] [Issue Card]  ▶   │
│     Horizontal carousel — weekly issues          │
├─────────────────────────────────────────────────┤
│  BULLETINS                                       │
│  [Bulletin Card] [Bulletin Card]                 │
│  Red/orange accent, "View all" link              │
├─────────────────────────────────────────────────┤
│  AI LEARNING                                     │
│  [Topic Card + Quiz] [Topic Card + Quiz]         │
│  Green accent, "View all" link                   │
├─────────────────────────────────────────────────┤
│  Pulse Beam CTA: "Let's Talk AI"                 │
├─────────────────────────────────────────────────┤
│  Footer                                          │
└─────────────────────────────────────────────────┘
```

### Data Model

All content stored as JSON in the repo, read at build time:

- `content/issues/[date]/data.json` — weekly issue data (migrated from current `issues/` structure)
- `content/issues/[date]/index.html` — deep-dive HTML (kept as-is, rendered in an iframe or dangerouslySetInnerHTML)
- `content/bulletins/[slug].json` — bulletin data
- `content/learn/[slug].json` — learning topic + quiz questions
- `content/manifests/issues.json` — issue manifest
- `content/manifests/bulletins.json` — bulletin manifest
- `content/manifests/learn.json` — learning content manifest

### Deployment

Same Vercel project (`healthcare-ai-weekly`). Vercel auto-detects Next.js and builds accordingly. The GitHub repo structure changes but the deploy URL stays the same.

## 2. Bulletin System

Full spec in `2026-04-08-bulletin-system-design.md`. No changes to the architecture — the 5-stage pipeline (X Monitor -> Velocity Detection -> Credibility Check -> Bulletin Generator -> Publish) remains as designed.

**Integration with Next.js:**
- Bulletin pipeline writes JSON to `content/bulletins/[slug].json`
- Updates `content/manifests/bulletins.json`
- Pushes to GitHub, Vercel rebuilds
- Landing page shows latest 2-3 bulletins in red/orange accent section
- `/bulletins` archive page lists all chronologically

**New files in newsletter repo:**
```
bulletin/
├── __init__.py
├── x_monitor.py
├── velocity_detector.py
├── credibility_checker.py
├── bulletin_generator.py
└── bulletin_config.json
```

## 3. AI Literacy Section

### Content Source

**NotebookLM notebook:** "AI Learning" (`85d35a81-b05e-4a2d-921e-d11a0f6f6ca9`)
- 26 sources (mostly YouTube, some web pages, one markdown doc)
- Topics: AI agents, AI safety, AI tools/productivity, business impact, healthcare AI, AI skills/literacy
- Shared notebook (Greg is not owner)

### Content Pipeline

Automated on a schedule (weekly, aligned with or offset from the newsletter):

1. **Extract** — Pull content summaries from NotebookLM sources using `notebooklm ask` to generate topic summaries
2. **Cluster** — Group sources into learning topics (e.g., "AI Agents 101", "AI Safety & Governance", "AI in Healthcare")
3. **Generate Quiz** — Use Gemini (via NotebookLM `generate quiz` or direct Gemini API) to create 5-10 trivia/"did you know" style questions per topic
4. **Format** — Structure as JSON with topic metadata, summary, quiz questions, source references
5. **Publish** — Write to `content/learn/[slug].json`, update manifest, push to GitHub

### Quiz Format

Light, trivia-style. Not a test — more "did you know?":

```json
{
  "slug": "ai-agents-101",
  "title": "AI Agents: What You Need to Know",
  "description": "How autonomous AI systems are reshaping work",
  "accent_color": "#059669",
  "sources": ["source_id_1", "source_id_2"],
  "summary": "2-3 paragraph overview of the topic...",
  "quiz": {
    "title": "Quick Check: AI Agents",
    "questions": [
      {
        "id": "q1",
        "question": "What did McKinsey estimate AI agents will handle in annual sales?",
        "options": ["$100 billion", "$500 billion", "$1 trillion", "$5 trillion"],
        "correct": 2,
        "explanation": "McKinsey's 2026 report projected $1 trillion in sales will flow through AI agents, fundamentally changing how businesses reach customers."
      }
    ]
  },
  "created_at": "2026-04-08",
  "updated_at": "2026-04-08"
}
```

### Quiz UX

- Cards on landing page show topic title + "Take the quiz" prompt
- Click opens `/learn/[slug]` with topic summary + inline quiz
- Multiple choice, instant feedback per question
- Score shown at end: "You got 7/10 — here's what you missed"
- Explanations shown for wrong answers (and optionally right ones)
- No login required — anonymous

### Supabase Analytics

**Tables:**

```sql
-- Quiz attempts (anonymous)
CREATE TABLE quiz_attempts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  quiz_slug TEXT NOT NULL,
  score INTEGER NOT NULL,
  total_questions INTEGER NOT NULL,
  answers JSONB NOT NULL,  -- [{"question_id": "q1", "selected": 2, "correct": true}, ...]
  session_id TEXT,          -- browser fingerprint or random session ID (not PII)
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Aggregate analytics view
CREATE VIEW quiz_analytics AS
SELECT
  quiz_slug,
  COUNT(*) as attempts,
  AVG(score::float / total_questions) as avg_score,
  MIN(created_at) as first_attempt,
  MAX(created_at) as last_attempt
FROM quiz_attempts
GROUP BY quiz_slug;

-- Per-question difficulty
CREATE VIEW question_difficulty AS
SELECT
  quiz_slug,
  q->>'question_id' as question_id,
  COUNT(*) as attempts,
  AVG(CASE WHEN (q->>'correct')::boolean THEN 1.0 ELSE 0.0 END) as correct_rate
FROM quiz_attempts, jsonb_array_elements(answers) as q
GROUP BY quiz_slug, q->>'question_id';
```

**Analytics dashboard (`/analytics`):**
- Quiz completion rates per topic
- Average scores per topic
- Hardest questions (lowest correct rate)
- Attempts over time
- Protected by a simple password or Supabase auth (just for Greg)

## 4. Email CTA Fix

The "Read the Full Deep Dive" button in `generator/templates/email_template.html` is too large. Fix:
- Reduce padding from current size to something proportional to other email elements
- Reduce font size if needed
- Keep the blue background, white text, and link to deep-dive page
- Test in email preview to verify it looks balanced

## Integration Points

### Newsletter Pipeline Updates

The existing `pipeline.py` needs to know about the new repo structure:
- Generator output goes to `content/issues/[date]/` instead of `issues/[date]/`
- `build_manifest.py` writes to `content/manifests/issues.json`
- Bulletin pipeline writes to `content/bulletins/` and `content/manifests/bulletins.json`
- Learning pipeline writes to `content/learn/` and `content/manifests/learn.json`

### Bulletin-to-Newsletter Connection

- Weekly curator reads `content/bulletins/` to know what broke this week
- Weekly issue can reference: "As we reported in Tuesday's bulletin..."
- Bulletin tags enable topic tracking across formats

### Learning-to-Newsletter Connection

- "Did You Know" section in weekly email can link to relevant learning topics
- Quiz questions can reference recent newsletter stories for timeliness

## Success Criteria

1. Vercel site looks identical to current version after Next.js conversion (same glass morphism, same colors, same content)
2. Issues carousel scrolls horizontally with smooth behavior
3. Bulletins appear within 4-6 hours of a story breaking on X
4. Learning topics generated automatically from NotebookLM content
5. Quizzes are engaging, light, trivia-style — not intimidating
6. Analytics dashboard shows which topics resonate and which questions are hard
7. Email CTA button is appropriately sized
