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

## Current Status (as of 2026-04-08, end of session 2)

### Newsletter Pipeline (unchanged)
- Pipeline fully built and tested (34+ unit tests)
- Email template v30, card-based 2x2 grids, forward-safe
- Email CTA button resized (was too big: 18px/14px-40px -> 14px/10px-28px)
- 3 issues published (Mar 21, Mar 28, Apr 4)
- Remote trigger set to Wednesday 5 AM for testing (needs validation, then switch to Friday)

### Bulletin System (BUILT)
Full spec: `docs/superpowers/specs/2026-04-08-bulletin-system-design.md`

5-stage pipeline: X Monitor -> Velocity Detection -> Credibility Check -> Bulletin Generator -> Publish

```
bulletin/
├── __init__.py
├── x_monitor.py           # X API v2 via tweepy, Bearer Token auth
├── velocity_detector.py   # Entity extraction, clustering, velocity/acceleration math
├── credibility_checker.py # Google News RSS, 4-tier source classification, decision matrix
├── bulletin_generator.py  # Anthropic SDK, Nate B Jones voice, em dash stripping
├── bulletin_config.json   # All thresholds tunable (25k impressions, 10 accounts, 5k/hr velocity)
└── bulletin_pipeline.py   # Orchestrator: --dry-run, --stage [monitor|velocity|credibility|generate|publish]
```

75 tests passing. Run: `python -m bulletin.bulletin_pipeline --dry-run`

### AI Learning Pipeline (BUILT)
Content sourced from NotebookLM "AI Learning" notebook (85d35a81-b05e-4a2d-921e-d11a0f6f6ca9, 26 sources).

```
learning/
├── __init__.py
├── content_extractor.py    # NotebookLM CLI subprocess, source guides, caching
├── topic_clusterer.py      # Keyword scoring, 5 topic clusters
├── quiz_generator.py       # NotebookLM quiz primary, Anthropic SDK fallback
├── learning_config.json    # Notebook ID, topic definitions, quiz settings
└── learning_pipeline.py    # Orchestrator: --skip-extract, --skip-quiz, --stage, --config
```

5 topics: AI Agents 101, AI Safety & Governance, AI in the Workplace, Healthcare AI, AI Strategy for Leaders
44 tests passing. Run: `python -m learning.learning_pipeline`

### Vercel Site — Next.js Conversion (BUILT)
Converted from static HTML to Next.js 14+ (App Router, TypeScript, Tailwind, shadcn/ui).
Repo: `/Users/greg/Claude/healthcare-ai-weekly`

**Pages:**
- `/` — Landing: hero, ticker, horizontal issues carousel, bulletins section (red), learning section (green), CTA
- `/issues/[date]` — Deep-dive (SSG, 3 issues)
- `/bulletins` — Archive (2 sample bulletins)
- `/bulletins/[slug]` — Individual bulletin (SSG)
- `/learn` — Topic archive (2 sample topics)
- `/learn/[slug]` — Topic + interactive quiz (SSG)
- `/analytics` — Password-protected quiz analytics dashboard

**Key components:** `glass-card`, `ambient-background`, `source-ticker`, `pulse-beam-cta`, `horizontal-scroller`, `quiz`, `nav`

Original static files backed up as `_old_index.html`, `_old_issues/`, `_old_issues.json`.

### Supabase Analytics (BUILT)
Separate Supabase project (NOT FieldShield). Schema at `supabase/setup.sql`.

- `quiz_attempts` table with RLS (anon: INSERT only, service_role: SELECT)
- No PII — random UUID session IDs
- Analytics views: `quiz_analytics`, `question_difficulty`
- Dashboard at `/analytics?key=<password>`

**Setup required:** Create Supabase project, run `setup.sql`, add env vars to `.env.local` and Vercel.

## Next Steps

1. **Validate the Wednesday 5 AM remote trigger** — check if email arrives with fresh content
2. **Switch trigger to Friday** once validated: update cron to `0 9 * * 5`
3. **Create Supabase project** — run setup.sql, configure env vars, restrict CORS to Vercel domain
4. **Set up X API credentials** — get Bearer Token, add to env as `X_BEARER_TOKEN`
5. **Run learning pipeline** — extract from NotebookLM, generate first batch of quizzes
6. **Set up bulletin remote trigger** — every 4 hours, runs bulletin pipeline
7. **Deploy Next.js site to Vercel** — push to GitHub, Vercel auto-detects Next.js
8. **Microsoft Form for subscriptions** — create Form, link from Vercel, Power Automate distribution
9. **Custom domain** — optionally replace `healthcare-ai-weekly.vercel.app`
