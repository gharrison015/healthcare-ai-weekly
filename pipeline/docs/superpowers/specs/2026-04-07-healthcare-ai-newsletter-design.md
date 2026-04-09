# Healthcare AI Weekly Newsletter — Design Spec (Updated 2026-04-08)

## Overview

An automated weekly newsletter pipeline that collects, curates, and delivers AI-in-healthcare intelligence every Friday at 5 AM ET. Produces three outputs:
1. **Executive HTML email** sent to gharrison@guidehouse.com (card-based layout, forwardable)
2. **Deep-dive HTML document** hosted on Vercel with liquid glass Apple-like design
3. **LinkedIn seed file** for cross-pollination with the LinkedIn content agent

The Vercel site also serves as a growing archive with a landing page, scrolling source ticker, "Let's Talk AI" CTA, and issue highlighting from email clicks.

## Architecture

```
COLLECTOR ──▶ CURATOR AGENT ──▶ GENERATOR ──▶ DISTRIBUTOR
(RSS + Google News)  (Claude API)     (Email + HTML)  (gws + git + Vercel)
```

Scheduled as a Claude Code remote trigger (runs in Anthropic's cloud). The remote agent IS the curator (no API key needed). Each stage reads the previous stage's JSON output from disk. Any stage can be re-run independently.

### Remote Trigger Architecture
- Trigger: `healthcare-ai-weekly-TEST` (currently Wednesday 5 AM for testing, switch to Friday when validated)
- Trigger ID: `trig_01JqnHVGb3gfV1judxMohq12`
- The remote agent clones both repos, installs deps, runs collector via Python, does curation itself (it IS Claude), runs generator via Python, sends email via Gmail MCP, pushes to both repos
- Manage at: https://claude.ai/code/scheduled/trig_01JqnHVGb3gfV1judxMohq12

## Repositories

1. **`healthcare-ai-newsletter`** (private) — Pipeline code, templates, curator config
   - GitHub: gharrison015/healthcare-ai-newsletter
   
2. **`healthcare-ai-weekly`** (public) — Published HTML issues, landing page, archive
   - GitHub: gharrison015/healthcare-ai-weekly
   - Vercel: https://healthcare-ai-weekly.vercel.app
   - Auto-deploys on push

## Stage 1: Collector

RSS feeds via `feedparser` + Google News queries for sources that block RSS.

### Sources (17 RSS feeds + 19 Google News queries)

**RSS Feeds:**
- Fierce Healthcare, STAT News, Healthcare Dive, Health Affairs Blog (core)
- CMS Newsroom, HHS.gov (policy)
- Rock Health (funding)
- Google Health, Google Cloud Health, Microsoft Health, NVIDIA Healthcare, AWS Health (tech)
- OpenAI, Anthropic, Google AI, The Verge AI (general AI)

**Google News Queries:**
- Healthcare AI catch-all queries
- Company-specific: OpenAI, Anthropic, Google, Epic + healthcare
- Becker's Hospital Review (RSS blocked, use `site:` search)
- Consulting firms: Guidehouse, Deloitte, McKinsey, BCG, Accenture, Chartis, Optum, EY
- EHR vendors: Epic, Oracle Health/Cerner
- Big tech partnerships: Microsoft/Nuance, Amazon/AWS
- M&A catch-all: "healthcare AI merger OR acquisition"

### Filtering
- Date range: past 7 days
- Keyword match with configurable list (30+ keywords including AI terms, VBC terms, consulting firms)
- URL deduplication
- Fuzzy title deduplication (SequenceMatcher, 0.65 threshold, prefers higher-tier source)
- Source reliability scoring adjusts thresholds after 8+ weeks

### Source Reliability Scoring
- Tracks per-source hit rate (collected vs. curated)
- After 8 weeks: low-hit sources get tighter keyword filtering
- After 12 weeks: sources below 5% flagged for manual review
- Never auto-removes, only adjusts and flags

## Stage 2: Curator Agent

Claude API-powered editorial agent with persona, guardrails, feedback loop, and delta tracking.

### Persona (`curator/persona.md`)
- Senior healthcare AI consultant voice
- Nate B Jones communication style: direct, confident, strategic provocateur
- Consulting competitive lens: tracks Deloitte, McKinsey, BCG, Accenture, Chartis, Optum, EY moves
- Absolute ban on em dashes (enforced in prompt + post-processing strip)
- Headlines: short punchy hooks (8-10 words)
- Summaries: substantive with key data points, numbers, names

### Guardrails (`curator/guardrails.json`)
- 4 top stories (act_now / watch_this priority)
- 4 Value-Based Care Watch stories
- 4 Acquisitions & Partnerships stories
- 2 Did You Know? items (general AI)
- At least 1 risk/contrarian take
- LinkedIn seed with top story hook

### Editorial Feedback Loop (`curator/feedback.md`)
- Rolling log of editorial corrections after each issue
- Injected into curator prompt as context
- Calibrates editorial taste over 4-6 weeks

### Delta Tracker (`data/curated/delta_tracker.py`)
- Compares week-over-week: recurring companies, themes, new entrants, dropped threads
- Feeds optional "Trend Watch" section

### Post-processing
- Strips all em dashes (unicode and ASCII variants) from all string values
- Replaces with commas

## Stage 3: Generator

### Executive Email (`email_template.html`)
- Aptos/Calibri font family
- White background, inline styles (forward-safe)
- Card-based layout with 2x2 grids
- "This Week's Impact" (red) and "Emerging" (blue) badges
- Sections: What Matters (2x2), Value-Based Care Watch (2x2), Acquisitions & Partnerships (2x2), Did You Know? (1x2)
- Full-width Trend Watch with blue border
- "Read the Full Deep Dive" CTA button
- Forward-safe: links ONLY on headline text and inline "Read more" in card footer (NOT wrapping entire card in `<a>` tag, which causes Outlook to turn all text blue on forward)
- Email links point to landing page with `?issue=` param (not directly to deep-dive)
- "Click any headline for the full analysis" hints
- Mobile responsive: cards stack to single column
- Min-height on cards for visual consistency (220px story cards, 140px DYK cards)
- Section headers: 22px bold uppercase
- Card headlines: 22px blue underlined (obviously clickable)
- Card body: 18px
- Card footer: 14px with source name + "Read more" inline link
- Footer: 15px
- 32px side padding on content area

### Deep-Dive HTML (`doc_template.html`)
- Liquid glass Apple-like design (from MedicaidIQ design system)
- Ambient mesh gradient background with drifting blue/purple orbs
- Glass-morphism section boxes and story cards with backdrop-filter blur
- Hover effects: cards lift, background opacity increases
- "This Week's Impact" / "Emerging" badges (translucent)
- Risk angle boxes in amber
- Source links on all cards including DYK
- "All Issues" back link (20px, prominent)
- Floating "Let's Talk AI" button on deep-dive pages
- 40px side padding, no max-width (fills screen)
- Mobile responsive

### LinkedIn Seed (`linkedin_seed.py`)
- Exports top story with hook and angle
- Saves to `data/linkedin-seed/` and copies to `/Users/greg/Claude/linkedin-agent/newsletter-seeds/`

## Stage 4: Distributor

### Email Send
- `gws` CLI via Gmail API (base64 MIME encoding)
- Sends to gharrison@guidehouse.com

### HTML Publish
- Copies HTML + data.json to `healthcare-ai-weekly` repo
- Rebuilds `issues.json` manifest (for landing page)
- Git commit + push (triggers Vercel auto-deploy)

### Source Score Update
- Updates `data/source_scores.json` after each issue

## Vercel Site (healthcare-ai-weekly.vercel.app)

### Landing Page (`index.html`)
- Hero: title, tagline, byline
- "Let's Talk AI" button with pulse beam SVG animation (6 animated gradient beams radiating from button)
- Opens pre-populated mailto to gharrison@guidehouse.com
- Scrolling source ticker: infinite CSS animation of all source names with progressive blur fade on edges
- "All Issues" section header (28px bold) with issue count
- Glass-card grid of all published issues
- Each card shows: week range, editorial summary preview (4-line clamp), story count, "Read deep dive" link
- `?issue=YYYY-MM-DD` param support: highlights matching card with pulsing blue glow, shows caption, auto-scrolls

### Issue Pages (`issues/YYYY-MM-DD/index.html`)
- Full deep-dive content with liquid glass design
- Floating "Let's Talk AI" button

### Data
- `issues.json` — manifest for landing page (rebuilt each publish)
- `issues/YYYY-MM-DD/data.json` — curated data per issue (queryable archive)

## Project Structure

```
/Users/greg/Claude/healthcare-ai-newsletter/
├── collector/
│   ├── rss_collector.py          # RSS + Google News collection
│   ├── filters.py                # Dedup, fuzzy match, tier priority
│   ├── source_scorer.py          # Per-source reliability tracking
│   ├── sources.json              # Feed URLs, queries, keywords
│   └── __init__.py
├── curator/
│   ├── curator_agent.py          # Claude API curation + validation + retry
│   ├── persona.md                # Editorial voice (editable)
│   ├── guardrails.json           # Section counts, required fields
│   ├── feedback.md               # Rolling editorial feedback
│   └── __init__.py
├── generator/
│   ├── email_generator.py        # Jinja2 email builder
│   ├── html_generator.py         # Jinja2 deep-dive builder
│   ├── linkedin_seed.py          # LinkedIn agent export
│   ├── templates/
│   │   ├── email_template.html   # Card-based email (inline styles)
│   │   └── doc_template.html     # Liquid glass deep-dive
│   └── __init__.py
├── distributor/
│   ├── send_email.py             # gws CLI email send
│   ├── publish_html.py           # Git commit to archive repo
│   ├── build_manifest.py         # Rebuilds issues.json
│   └── __init__.py
├── data/
│   ├── raw/                      # Weekly raw collections
│   ├── curated/
│   │   ├── delta_tracker.py      # Week-over-week comparison
│   │   └── __init__.py
│   ├── issues/                   # Local HTML copies
│   ├── linkedin-seed/            # LinkedIn seed files
│   └── source_scores.json        # Reliability tracking
├── pipeline.py                   # Orchestrator with CLI
├── requirements.txt              # feedparser, anthropic, jinja2, python-dotenv
├── .env                          # ANTHROPIC_API_KEY
├── SKILL.md                      # Scheduled trigger config
├── tests/                        # 34+ tests
└── docs/
    └── superpowers/
        ├── specs/
        │   └── 2026-04-07-healthcare-ai-newsletter-design.md
        └── plans/
            └── 2026-04-07-healthcare-ai-newsletter-plan.md
```

## Dependencies

- Python 3.13, feedparser, anthropic SDK, jinja2, python-dotenv
- `gws` CLI (email), `gh` CLI (GitHub), Vercel CLI
- Claude Code remote triggers with Gmail MCP connector

## Competitive Advantages Over Healthcare AI Guy Weekly

| Gap | Our Solution |
|---|---|
| Everything weighted equally | "This Week's Impact" vs "Emerging" priority system |
| ~80% aggregation | Every story gets substantive "so what" with data points |
| No consulting lens | Tracks Deloitte, McKinsey, BCG, Accenture, Chartis, Optum moves |
| No risk analysis | Risk angles on major stories |
| No general AI education | "Did You Know?" bridges healthcare and broader AI |
| No deep-dive companion | Full liquid glass HTML document |
| No archive | Vercel-hosted searchable archive with issue history |
| No engagement mechanism | "Let's Talk AI" CTA with pre-populated email |
| No self-improvement | Feedback loop, delta tracking, source scoring |
| No longitudinal tracking | Delta tracker surfaces recurring themes and dropped threads |
| No breaking news | Bulletin system detects velocity spikes on X/Twitter (Phase 2, see bulletin-system-design.md) |

## Phase 2: Bulletin System (Designed, Not Yet Built)

Near-real-time breaking news bulletins that detect high-velocity healthcare AI stories on X/Twitter, verify against credible sources, and publish to the Vercel site between weekly issues. See full spec: `docs/superpowers/specs/2026-04-08-bulletin-system-design.md`

Architecture: X API monitor (every 2-4 hrs) -> velocity detection -> credibility verification -> Claude writes 3-5 sentence take -> publish to Vercel with "Breaking" card on landing page.

Key design decisions:
- Two-stage filter: velocity first, credibility second
- Auto-publish only when both velocity AND credible source confirmed
- High velocity without credible source gets flagged for Greg's review, not auto-published
- Max 2 bulletins per day, 6-hour cooldown per topic
- Bulletins feed into the weekly issue for deeper treatment
- Red/orange accent on Vercel (distinct from blue weekly issues)
