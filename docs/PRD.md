# Healthcare AI Weekly - Product Requirements Document

**Owner:** Greg Harrison
**Last Updated:** 2026-04-10
**Status:** In Development (Pre-Launch)

---

## 1. Product Vision

Healthcare AI Weekly is an automated intelligence platform for consultants, strategists, and health system leaders who need to track what matters in AI and healthcare. It delivers weekly curated newsletters, a live web archive, real-time bulletins on breaking news, structured AI learning content, and competitive intelligence on consulting firm moves in healthcare AI.

The product exists to solve one problem: **the signal-to-noise ratio in healthcare AI news is terrible**, and the people who need to act on this information don't have time to filter it themselves. Healthcare AI Weekly does the filtering, the analysis, and the strategic framing on their behalf.

## 2. Target Audience

**Primary:** Senior consultants at Guidehouse and peer firms (Deloitte, McKinsey, BCG, Accenture, Chartis, Huron, BRG, Bain, Oliver Wyman, KPMG, PwC, Optum Advisory, EY-Parthenon) who advise health systems and payers on AI and technology strategy.

**Secondary:**
- Health system executives (CTOs, CIOs, Chief AI Officers)
- Payer strategy teams
- Digital health investors
- AI product managers targeting healthcare

## 3. Product Components

### 3.1 Weekly Newsletter

**Cadence:** Every Friday at 7 AM ET.

**Delivery:**
1. Email to subscribers (starting with gharrison@guidehouse.com)
2. Card-based responsive HTML, inline styles for Outlook compatibility
3. No em dashes anywhere (editorial rule)
4. Forward-safe design (headline links only, no full-card anchor tags)

**Content Structure (per issue):**
- **Top Stories** (3-5): Major AI healthcare stories with strategic "so what" framing, classified as `act_now` or `watch_this`
- **Value-Based Care Watch** (1-4): AI intersecting with VBC, payment models, risk adjustment, quality measures
- **Acquisitions & Partnerships** (0-4): M&A and partnerships with a clear AI/tech angle
- **Consulting Intelligence** (0-3): Consulting firm activity specifically in healthcare AI
- **Did You Know?** (exactly 2): General AI capability news, educational tone

**Editorial Voice:** Direct, confident, insider authority. Channel Nate B Jones. Opinionated, not summarizing. Every story answers "why should a health system exec care about this AI development?"

**Filtering Rule:** EVERY story in EVERY section MUST have an AI, machine learning, or technology angle. No exceptions. Pure health system M&A without AI = rejected.

### 3.2 Vercel Web Archive

**URL:** https://healthcare-ai-weekly.vercel.app

**Pages:**
- **Landing page** (`/`) - Hero, source ticker, Weekly News carousel, AI Learning section, Consulting Intelligence section, Bulletins section
- **Deep-dive issue pages** (`/news/[date]`) - Full analysis of each weekly issue
- **Bulletins archive** (`/bulletins`) and individual bulletins (`/bulletins/[slug]`)
- **Learning archive** (`/learn`) and individual topics with interactive quizzes (`/learn/[slug]`)
- **Analytics dashboard** (`/analytics`) - Password-protected quiz performance data

**Design System:**
- Liquid glass aesthetic (ambient gradient background, glass cards, backdrop blur)
- Color-coded level badges: 100 = Fundamentals (green), 200 = Applied (blue), 300 = Strategic (purple)
- Cards use GlowCard component with cursor-following radial color spotlight and a glossy white overlay highlight on hover (no pseudo-element border mask, to avoid rectangular hard-line artifacts)
- Horizontal scrollers for Issues, Bulletins, Consulting Intelligence, and Learning sections
- Mobile responsive

**Email Deep-Link Integration:**
- Email article links include `?issue=YYYY-MM-DD` parameter
- On desktop: landing page shows an inline caption under "Weekly AI Healthcare News" header identifying which issue the article is from, plus a "Read this issue" button
- On mobile: automatic redirect to `/news/YYYY-MM-DD` (skips landing page entirely for faster access)

### 3.3 Real-Time Bulletins

**Purpose:** Surface breaking news BEFORE it makes the weekly newsletter.

**Pipeline (5 stages):**
1. **X Monitor** - Scrapes X/Twitter via API for healthcare AI signals
2. **Velocity Detector** - Entity extraction + clustering + velocity/acceleration math
3. **Credibility Checker** - Google News RSS validation, 4-tier source classification
4. **Bulletin Generator** - Writes bulletin copy in editorial voice
5. **Publisher** - Commits to archive repo, appears on Vercel site

**Cadence:** Every 4 hours (target, not yet activated).

**Display:** Breaking news ticker at top of Vercel site; dedicated Bulletins section in carousel.

### 3.4 AI Learning Content

**Purpose:** Educational content with interactive quizzes to keep leaders sharp on AI concepts.

**Source:** NotebookLM notebook ID `85d35a81-b05e-4a2d-921e-d11a0f6f6ca9` with 26+ curated sources.

**Topics (4):**
- AI Agents: What You Need to Know (100-level / Fundamentals)
- AI Safety and Governance (200-level / Applied)
- AI in the Workplace (200-level / Applied)
- AI Strategy for Leaders (300-level / Strategic)

**Cadence:** New quizzes published twice a week with fresh questions. Never recycle questions across runs.

**Rotation:**
- Tues Week 1: AI Agents 101 (level 100)
- Fri Week 1: AI Strategy for Leaders (level 300)
- Tues Week 2: AI Safety and Governance (level 200)
- Fri Week 2: AI in the Workplace (level 200)
- Repeat

**Quiz Format:** 10 trivia-style multiple choice questions per topic. Each question includes 4 options, correct answer index, and explanation. Questions tracked in `content/learn/question-history.json` to prevent repetition across runs.

**Analytics:** Quiz attempts stored in Supabase with anonymous session IDs. Dashboard at `/analytics` shows per-topic performance, question difficulty, and engagement metrics. (Pending Supabase project setup.)

### 3.5 Consulting Intelligence

**Purpose:** Competitive radar tracking how consulting firms are moving in healthcare AI. This is strategic signal for Guidehouse and peer firms.

**Tracked Firms (14):** Guidehouse, Deloitte, McKinsey, BCG, Accenture, Chartis, Optum Advisory, EY Parthenon, Huron Consulting, Berkeley Research Group (BRG), Bain, Oliver Wyman, KPMG, PwC.

**Pipeline:**
1. `consulting_intel_collector.py` - Google News searches per firm, 60-day lookback
2. `consulting_intel_enricher.py` - Claude filters false positives, deduplicates, writes clean headlines and summaries, classifies relevance

**Relevance Classification:**
- **healthcare_direct** - Directly about healthcare/clinical AI (green badge)
- **healthcare_adjacent** - General AI move with obvious healthcare implications (blue badge)
- **ai_strategy** - General consulting firm AI strategy move signaling direction (purple badge)

**Storage:** Standalone `content/consulting-intelligence/*.json` files, independent of weekly issues. Displayed as a dedicated landing page section showing all tracked moves, not just the latest week's.

**Current State:** 22 backfilled stories from the past 60 days (February 16 - April 10, 2026).

## 4. Technical Architecture

### 4.1 Repositories

**`healthcare-ai-newsletter`** (Python pipeline)
- URL: https://github.com/gharrison015/healthcare-ai-newsletter
- Local: `/Users/greg/Claude/healthcare-ai-newsletter`
- Purpose: Content generation pipeline (collect, curate, generate, distribute)
- Language: Python 3
- Key modules: `collector/`, `curator/`, `generator/`, `distributor/`, `bulletin/`, `learning/`

**`healthcare-ai-weekly`** (Next.js site + archive)
- URL: https://github.com/gharrison015/healthcare-ai-weekly
- Local: `/Users/greg/Claude/healthcare-ai-weekly`
- Purpose: Public Vercel site + content archive + pipeline copy for remote runs
- Stack: Next.js 16, React 19, TypeScript, Tailwind v4, shadcn/ui
- Hosts: All published content under `content/`, pipeline code duplicated under `pipeline/` for remote agent runs

### 4.2 Data Flow

```
┌─────────────────────────────┐            ┌──────────────────────────────┐
│ healthcare-ai-newsletter    │  copy HTML │ healthcare-ai-weekly         │
│ (pipeline repo)             │ ─────────> │ (archive + Vercel)           │
│                             │  git push  │                              │
│ collector/ → curator/ →     │            │ content/issues/<date>/       │
│ generator/ → distributor/   │            │ content/bulletins/           │
│                             │            │ content/learn/               │
│ bulletin/ pipeline          │            │ content/consulting-intel/    │
│ learning/ pipeline          │            │ content/manifests/           │
│ consulting intel collector  │            │                              │
└─────────────────────────────┘            │ src/app/ (Next.js pages)     │
  Runs locally or via remote                └──────────────────────────────┘
  trigger (Anthropic cloud)                   Auto-deploys on push via Vercel
```

### 4.3 Remote Trigger

**Trigger ID:** `trig_01JqnHVGb3gfV1judxMohq12`
**Schedule:** Fridays at 7 AM ET (`0 11 * * 5` UTC)
**Environment:** Anthropic cloud, clones both repos fresh each run
**Model:** Claude Sonnet 4.6
**Email:** Gmail MCP connector
**Curation:** Remote agent IS the curator (reads persona.md, guardrails.json, feedback.md, then curates from raw articles — no API key needed)

### 4.4 Key Infrastructure

| Service | Purpose | Status |
|---|---|---|
| Vercel | Web hosting | Live |
| GitHub | Repos + CI | Live |
| Anthropic Remote Trigger | Scheduled weekly runs | Live |
| Gmail MCP | Email sending | Live |
| NotebookLM CLI | Learning content source | Live |
| Supabase | Quiz analytics | Not yet deployed |
| X API | Bulletin velocity detection | Not yet configured |

## 5. Design Principles

**Editorial:**
- No em dashes (banned in curator persona, stripped in post-processing)
- Every story must have an AI angle
- Direct, opinionated voice — never summarize without a take
- Headlines are hooks (8-10 words). Summaries deliver the substance with numbers and facts.

**Email:**
- Inline styles only (Outlook compatibility)
- Forward-safe: links only on headline text and "Read more", never full-card anchors
- Light mode only, Aptos font (falls back to Calibri)
- 4 cards per section max for main sections, 2 for Did You Know
- Unique subject lines per send to avoid Gmail threading (which triggers the 102KB clip limit)

**Web:**
- Liquid glass aesthetic, ambient gradient background
- Fixed 340px cards with consistent shape across all sections
- 14px border-radius on all cards (matches GlowCard effect)
- GlowCard uses a cursor-tracking radial background gradient (not pseudo-element border glow) to avoid rectangular edge artifacts
- Mobile: email deep-links bypass the landing page and jump straight to the issue deep-dive

**Code:**
- FieldShield infrastructure is NEVER used for this project (Greg's separate business)
- Gmail MCP for remote trigger email, `gws` CLI for local sending
- No mocking in integration tests — hit real APIs/feeds

## 6. Current Status (as of 2026-04-10)

### Shipped

- [x] Weekly newsletter pipeline (4 issues published: March 21, 28, April 4, 10)
- [x] Vercel site with landing page, deep-dives, bulletins archive, learning archive
- [x] AI-only curation filter across all sections
- [x] Consulting Intelligence as a standalone aggregated data source (22 backfilled stories)
- [x] Email deep-link integration (`?issue=` param, inline caption on desktop, mobile redirect)
- [x] Glow card cursor highlight with cursor-following color spotlight + glossy white outer highlight (pseudo-element hard-line artifact fixed)
- [x] Level-coded learning badges (100 green / 200 blue / 300 purple)
- [x] Question history tracker to prevent quiz repetition
- [x] Single-topic refresh (`--only-topic` flag) for twice-weekly learning rotation
- [x] Forbes Healthcare RSS feed integration
- [x] Fresh landing page copy ("New quizzes twice a week")

### In Progress

- [ ] Validate Friday 7 AM ET remote trigger end-to-end (initial test runs silently failed; manual runs successful)
- [ ] Set up twice-weekly learning pipeline remote trigger with topic rotation
- [ ] Activate bulletin pipeline remote trigger (every 4 hours)
- [ ] Debug Gmail MCP behavior in cloud environment
- [ ] Create Supabase project and deploy quiz analytics

### Not Started

- [ ] Custom domain (currently `healthcare-ai-weekly.vercel.app`)
- [ ] Microsoft Form for public subscription intake
- [ ] Power Automate distribution flow for subscribers
- [ ] X API credentials for bulletin pipeline

## 7. Success Metrics

**Content Quality (editorial):**
- Every story passes the AI filter (manual review)
- Headlines avg ≤ 10 words
- Summaries include key numbers/names
- Consulting Intelligence section populated with at least 2 stories per week

**Distribution:**
- Email delivered on schedule (Fridays 7 AM ET)
- Vercel deploy succeeds on push
- No Gmail clipping (stay under 102KB, unique subjects)

**Engagement (once launched):**
- Email open rate > 40%
- Article click-through rate > 15%
- Quiz completion rate > 30%
- Time-on-site for deep-dive pages > 2 min

## 8. Non-Goals

- This is NOT a general healthcare news product. AI angle is mandatory.
- This is NOT for consumers or patients. Audience is professional strategists.
- This is NOT a marketing tool for a specific vendor or consulting firm. Editorial independence matters.
- This is NOT built on or connected to FieldShield Tractor infrastructure. Separate projects, separate credentials, separate everything.

## 9. Open Questions

- When to switch from manual/test sends to the public launch? (Gating on remote trigger reliability + subscription system.)
- Does the Consulting Intelligence section need its own archive page at `/consulting-intelligence`, or is the landing page section sufficient?
- How should we handle non-AI consulting moves that are strategically relevant but don't fit the AI-only filter? (Currently classified as `ai_strategy` relevance and included.)
- Should the newsletter ever include a dedicated "Consulting Intelligence" section in the email body, or keep it web-only?
