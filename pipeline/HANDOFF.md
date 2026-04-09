# Healthcare AI Weekly — Context Handoff

Use this file when starting a new Claude Code session to work on this project.

## What This Is

An automated weekly newsletter pipeline that curates AI-in-healthcare news and delivers it as:
1. A card-based HTML email to gharrison@guidehouse.com
2. A liquid glass deep-dive HTML page hosted on Vercel
3. A LinkedIn seed file for the LinkedIn content agent

## Key URLs

- **Vercel site:** https://healthcare-ai-weekly.vercel.app
- **Archive repo:** https://github.com/gharrison015/healthcare-ai-weekly
- **Pipeline repo:** https://github.com/gharrison015/healthcare-ai-newsletter
- **Remote trigger:** https://claude.ai/code/scheduled/trig_01JqnHVGb3gfV1judxMohq12
- **Trigger ID:** `trig_01JqnHVGb3gfV1judxMohq12` (currently set to Wednesday 5 AM ET for testing; switch to Friday `0 9 * * 5` when validated)

## How to Run Locally

```bash
cd /Users/greg/Claude/healthcare-ai-newsletter
source venv/bin/activate

# Full pipeline
python pipeline.py --date 2026-04-11

# Individual stages
python pipeline.py --date 2026-04-11 --stage collector
python pipeline.py --date 2026-04-11 --stage curator
python pipeline.py --date 2026-04-11 --stage generator

# Skip email send (preview only)
python pipeline.py --date 2026-04-11 --skip-send
```

## How to Send a Test Email

```bash
source venv/bin/activate
python pipeline.py --date YYYY-MM-DD --stage generator
python -c "
from distributor.send_email import send_email
with open('data/issues/YYYY-MM-DD/email.html') as f:
    html = f.read()
send_email('gharrison@guidehouse.com', 'Healthcare AI Weekly — Week of ... [TEST]', html)
"
```

## How to Publish to Vercel

```bash
# Copy generated files to archive repo
cp data/issues/YYYY-MM-DD/index.html /Users/greg/Claude/healthcare-ai-weekly/issues/YYYY-MM-DD/index.html
cp data/curated/YYYY-MM-DD.json /Users/greg/Claude/healthcare-ai-weekly/issues/YYYY-MM-DD/data.json

# Rebuild manifest
python distributor/build_manifest.py

# Push (Vercel auto-deploys)
cd /Users/greg/Claude/healthcare-ai-weekly
git add -A && git commit -m "Add issue YYYY-MM-DD" && git push
```

## Key Files to Know

| File | Purpose |
|---|---|
| `pipeline.py` | Main orchestrator, CLI with --date, --stage, --skip-send |
| `collector/sources.json` | All RSS feeds, Google News queries, keywords (edit to add/remove sources) |
| `curator/persona.md` | Editorial voice and style guide (edit to tune tone) |
| `curator/guardrails.json` | Story counts per section (currently 4/4/4/2) |
| `curator/feedback.md` | Rolling editorial feedback (append after each issue) |
| `curator/curator_agent.py` | Claude API curation with validation, retry, and em-dash stripping |
| `generator/templates/email_template.html` | Email layout (inline styles, Jinja2 macros) |
| `generator/templates/doc_template.html` | Deep-dive layout (liquid glass design) |
| `generator/email_generator.py` | `LANDING_PAGE_URL` controls where email links point |
| `distributor/build_manifest.py` | Rebuilds issues.json for landing page |
| `data/source_scores.json` | Per-source reliability tracking |

## Design Decisions

- **Email uses inline styles** because Outlook strips `<style>` blocks on forward. All colors are on each element.
- **No em dashes anywhere.** Banned in persona prompt AND stripped in post-processing. Greg is adamant about this.
- **Headlines are hooks (8-10 words), summaries have the substance.** Don't repeat info between them. Summaries must include key data points and numbers.
- **Forward-safe email design.** Do NOT wrap entire cards in `<a>` tags. Outlook turns all text blue inside anchor tags on forward. Links go only on the headline text and an inline "Read more" link in the card footer. This was iterated many times; do not change this pattern.
- **Email cards link to landing page** with `?issue=YYYY-MM-DD` param, not directly to the deep-dive. Landing page highlights the matching issue card with a blue glow and shows a caption.
- **Aptos font** everywhere (falls back to Calibri).
- **4 cards per section** for What Matters, Value-Based Care Watch, and Acquisitions & Partnerships. 2 cards for Did You Know. Section names are spelled out (not VBC, not Deal Flow).
- **Light mode email** (white background, dark text) for Outlook compatibility and forwarding. No dark backgrounds on email body.
- **Liquid glass design** on Vercel (ambient gradient, backdrop-filter blur, glass cards). Matches MedicaidIQ design system.
- **Vercel landing page** has: pulse beam "Let's Talk AI" CTA (opens pre-populated mailto), scrolling source ticker, "All Issues" header (28px), issue cards with full summaries (no truncation).
- **FieldShield infrastructure is NEVER used** for this project. It's Greg's separate business.
- **`gws` CLI** for email sending locally, Gmail MCP for remote trigger.

## Remote Trigger Notes

The remote trigger runs in Anthropic's cloud. Key differences from local:
- The remote agent IS the curator (no Anthropic API key needed, it reasons directly)
- Uses Gmail MCP connector for email (not gws)
- Both repos cloned fresh each run
- Data committed back to repos for delta tracking persistence

The trigger prompt is embedded in the trigger config. To update it, use `RemoteTrigger` tool with `action: "update"`.

## Current Status (as of 2026-04-09, end of session 3)

### Consolidated Repo
Everything now lives in ONE repo: `/Users/greg/Claude/healthcare-ai-weekly`
- `pipeline/` — Python pipeline (collector, curator, generator, bulletin, learning)
- `src/` — Next.js app
- `content/` — Issue data, bulletins, learning content for Vercel
- `supabase/` — Schema SQL

Old `healthcare-ai-newsletter` repo still exists but is no longer used.

### Newsletter Pipeline
- 5 sections: What Matters, VBC Watch, M&A & Partnerships, Consulting Intelligence, Did You Know
- Every story MUST have an AI/technology angle (enforced in guardrails)
- Cross-issue dedup: curator reads last 4 weeks of headlines and won't repeat stories
- Spongy inline-block email layout (side by side desktop, stacks on mobile/forward)
- Google News redirect URLs auto-resolved to direct publisher links during collection
- All generated content stripped of `**` markdown and `[1,2]` citation brackets via `strip_formatting()`
- No Guidehouse branding anywhere — site is independent ("by Greg Harrison" only)
- "Let's Talk AI" CTA still emails gharrison@guidehouse.com (intentional for now)
- 4 issues published (Mar 21, Mar 28, Apr 4, Apr 9)
- Remote trigger: Fridays 9am ET (`trig_01JqnHVGb3gfV1judxMohq12`, cron `0 13 * * 5`)

### Sources (25+ feeds + Google News + APIs)
**Core RSS:** Fierce Healthcare, STAT News, Healthcare IT News, Healthcare Dive, Modern Healthcare, MobiHealthNews, HIT Consultant, Becker's Hospital Review, Health Affairs, AMA
**Policy:** CMS Newsroom, HHS.gov
**Tech:** Google Health, Microsoft Health, NVIDIA Healthcare, AWS Health
**AI:** OpenAI, Anthropic, Google AI, The Verge AI
**Consulting:** McKinsey Healthcare, Deloitte Health Insights
**APIs:** Newsdata.io (free, 2k articles/day), Hacker News, Reddit, Substack RSS
**Google News queries:** 25+ queries covering all 14 consulting firms, healthcare AI keywords, Hippocratic AI

### Consulting Intelligence
Tracks 14 firms: Guidehouse, Deloitte, McKinsey, BCG, Accenture, Chartis, Optum Advisory, EY Parthenon, Huron, BRG, Bain, Oliver Wyman, KPMG, PwC

Current stories: Chartis/Leap AI, BRG AI practice launch, Huron/Hippocratic AI, Accenture/Faculty acquisition

### Bulletin System (Free Multi-Source)
Monitors Newsdata, Hacker News, Reddit, Substack for breaking healthcare AI news.
Two-source verification: story must appear on 2+ platforms with 3+ unique authors.
X/Twitter and Bluesky disabled (Cloudflare blocked).
Remote trigger: every 4 hours weekdays (`trig_01Jr3zP4zvYRnvKo2MmHAeto`, cron `0 10,14,18,22 * * 1-5`)
Weekly cycle: bulletins accumulate Mon-Fri, archive on Sunday, fresh start Monday.

### Vercel Site
Live: https://healthcare-ai-weekly.vercel.app

**Pages:**
- `/` — Landing: breaking news ticker, hero, source ticker, Weekly AI Healthcare News carousel, AI Learning (by level), Consulting Intelligence, Bulletins, CTA
- `/news/[date]` — Deep-dive (SSG, 4 issues)
- `/bulletins` — Archive
- `/bulletins/[slug]` — Individual bulletin
- `/learn` — Topics organized by level (Fundamentals/Applied/Strategic)
- `/learn/[slug]` — Topic + interactive quiz (submits to Supabase)
- `/analytics?key=hcai2026analytics` — Quiz analytics dashboard

**Design:** Spotlight glow cards (mouse-tracking on desktop, disabled on mobile), ambient gradient background, glass morphism, uniform blue `#0284C7` palette, Aptos font. No Guidehouse branding — site is independent ("by Greg Harrison" only). Consulting Intelligence cards link directly to source articles (open in new tab).

### Supabase Analytics
Project: `healthcare-ai-weekly-analytics` (wjwubjahhbhhsctnpfcb) — NOT FieldShield
- `quiz_attempts` table with RLS (anon: INSERT only, service_role: SELECT)
- Quiz submissions wired via `QuizWrapper` client component
- Dashboard at `/analytics?key=hcai2026analytics`

### Env Files
- `pipeline/.env` — ANTHROPIC_API_KEY, X credentials, NEWSDATA_API_KEY, Reddit credentials
- `.env.local` — Supabase URL, anon key, service role key, analytics password
- Both gitignored. Vercel env vars set separately.

## Next Steps

1. **Fix remote trigger paths** — Friday trigger failed because cloud agent couldn't navigate consolidated repo structure. Needs path debugging.
2. **Microsoft Form for subscriptions** — create Form, link from Vercel, Power Automate distribution
3. **Custom domain** — optionally replace `healthcare-ai-weekly.vercel.app`
4. **Reddit API auth** — register app at reddit.com/prefs/apps for higher rate limits (works without auth at lower limits)
5. **Re-enable X/Bluesky** — monitor for Cloudflare blocks lifting, switch back on when possible
6. **Add more consulting firm blogs as RSS** — McKinsey, BCG, Bain, Oliver Wyman, PwC, KPMG, Accenture, Huron blogs need RSS discovery
