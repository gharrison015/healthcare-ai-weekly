# Healthcare AI Weekly — Operational Runbook

Use this file when starting a new Claude Code session to work on this project. This is the "how do I do things" reference. For "where does X live," see [`../PROJECT_MAP.md`](../PROJECT_MAP.md) at the repo root — that is the architectural source of truth.

## What This Is

An automated weekly newsletter pipeline that curates AI-in-healthcare news and delivers it as:
1. A card-based HTML email to gharrison@guidehouse.com
2. A liquid glass deep-dive HTML page hosted on Vercel
3. A LinkedIn seed file for the LinkedIn content agent

Plus a multi-source bulletin monitor that surfaces breaking news between weekly issues.

## Repo + paths (consolidated — single source of truth)

**Everything lives in one repo.** There is no second pipeline folder.

- **Repo:** [`gharrison015/healthcare-ai-weekly`](https://github.com/gharrison015/healthcare-ai-weekly) (public)
- **Local:** `/Users/greg/Claude/personal/content/healthcare-ai-weekly`
- **Primary site:** https://healthcareaibrief.com
- **Legacy URL:** https://healthcare-ai-weekly.vercel.app (still active, 308-redirects to primary)
- **Friday newsletter trigger:** `trig_01JqnHVGb3gfV1judxMohq12` — https://claude.ai/code/scheduled/trig_01JqnHVGb3gfV1judxMohq12
- **Bulletin monitor trigger:** `trig_01Jr3zP4zvYRnvKo2MmHAeto` — https://claude.ai/code/scheduled/trig_01Jr3zP4zvYRnvKo2MmHAeto

> ⚠️ **The old `gharrison015/healthcare-ai-newsletter` repo and `/Users/greg/Claude/healthcare-ai-newsletter` local folder are DEAD.** Legacy X-only code from before consolidation. Do not edit them. They will be archived in cleanup.

## How to run the pipeline locally

```bash
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly/pipeline
source venv/bin/activate

# Full weekly newsletter pipeline
python pipeline.py --date 2026-04-11

# Individual stages
python pipeline.py --date 2026-04-11 --stage collector
python pipeline.py --date 2026-04-11 --stage curator
python pipeline.py --date 2026-04-11 --stage generator

# Skip email send (preview only)
python pipeline.py --date 2026-04-11 --skip-send
```

## How to run the bulletin pipeline locally

```bash
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly/pipeline
source venv/bin/activate

# Local full run (needs ANTHROPIC_API_KEY in .env)
python -m bulletin.bulletin_pipeline

# Dry run (no writes) — safe for poking around
python -m bulletin.bulletin_pipeline --dry-run

# Cloud mode — writes _candidates.json + _last_run.json, skips Claude writer
# This is what the remote trigger uses
python -m bulletin.bulletin_pipeline --cloud-mode
```

After a `--cloud-mode` run, check the output:
- `pipeline/data/bulletins/_last_run.json` — heartbeat (always written)
- `pipeline/data/bulletins/_candidates.json` — verified topics ready for the agent to write (empty array on quiet days)

## How to send a test email

```bash
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly/pipeline
source venv/bin/activate

# Regenerate the email HTML for a specific date
python pipeline.py --date YYYY-MM-DD --stage generator

# Then send it via gws (the local Gmail CLI — see memory: "Use gws CLI")
python -c "
from distributor.send_email import send_email
with open('data/issues/YYYY-MM-DD/email.html') as f:
    html = f.read()
send_email('gharrison@guidehouse.com', 'Healthcare AI Weekly — Week of ... [TEST]', html)
"
```

For manual one-off sends of an already-generated issue, you can also do it from the repo root:

```bash
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly
python3 -c "
import sys; sys.path.insert(0, 'pipeline')
from distributor.send_email import send_email
with open('pipeline/data/issues/2026-04-09/email.html') as f:
    html = f.read()
send_email('gharrison@guidehouse.com', 'Healthcare AI Weekly [TEST]', html)
"
```

## How to publish new content

All content lives in `content/` at the repo root. When you push to `main`, Vercel auto-deploys. That's it — there is no separate "push to archive" step anymore.

```bash
# After generating an issue with the pipeline:
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly

# Confirm content/ has the new files (usually pipeline writes them directly)
ls content/issues/YYYY-MM-DD/

# Commit and push
git add content/ && git commit -m "Add issue YYYY-MM-DD" && git push

# Vercel picks it up automatically
```

## Key files to know

### Pipeline (Python)
| File | Purpose |
|---|---|
| `pipeline/pipeline.py` | Main orchestrator (newsletter), CLI with `--date`, `--stage`, `--skip-send` |
| `pipeline/bulletin/bulletin_pipeline.py` | Bulletin orchestrator with `--cloud-mode` for remote trigger |
| `pipeline/collector/sources.json` | All RSS feeds, Google News queries, keywords |
| `pipeline/curator/persona.md` | Editorial voice and style guide |
| `pipeline/curator/guardrails.json` | Story counts per section |
| `pipeline/curator/feedback.md` | Rolling editorial feedback |
| `pipeline/curator/curator_agent.py` | Claude curation with validation, retry, em-dash stripping |
| `pipeline/bulletin/bulletin_config.json` | Bulletin sources + verification thresholds |
| `pipeline/generator/templates/email_template.html` | Email layout (inline styles, Jinja2 macros) |
| `pipeline/generator/templates/doc_template.html` | Deep-dive HTML layout (liquid glass) |
| `pipeline/generator/email_generator.py` | `LANDING_PAGE_URL` controls where email links point |
| `pipeline/distributor/send_email.py` | `gws`-based email sender |
| `pipeline/distributor/build_manifest.py` | Rebuilds manifests for the site |
| `pipeline/data/source_scores.json` | Per-source reliability tracking |

### Site (Next.js)
| File | Purpose |
|---|---|
| `src/app/page.tsx` | Home page (hero, search, issues, learn, consulting, bulletins) |
| `src/app/layout.tsx` | Root layout with nav + search provider |
| `src/components/search/` | Site-wide search (inline hero, nav dropdown, `/search` page) |
| `scripts/build-search-index.ts` | Build-time search index generator |
| `src/lib/data.ts` | Content loaders (reads `content/*.json`) |
| `src/lib/types.ts` | TypeScript types for content |

### Content
| Path | What |
|---|---|
| `content/issues/<date>/data.json` | Curated weekly issue |
| `content/bulletins/*.json` | Individual bulletins |
| `content/bulletins/_last_run.json` | Bulletin trigger heartbeat (commit every 4 hours) |
| `content/consulting-intelligence/*.json` | Consulting firm tracked moves |
| `content/learn/*.json` | Learn topics + quizzes |
| `content/manifests/*.json` | Index files consumed by the site |

## Design decisions (do not break)

- **Email uses inline styles** because Outlook strips `<style>` blocks on forward.
- **No em dashes anywhere.** Banned in persona prompt AND stripped in post-processing.
- **Headlines are hooks (8-10 words), summaries have the substance.**
- **Forward-safe email design.** Do NOT wrap entire cards in `<a>` tags. Links go only on the headline text and an inline "Read more" link.
- **Email cards link to landing page** with `?issue=YYYY-MM-DD` param.
- **Aptos font** everywhere (falls back to Calibri).
- **4 cards per section** for What Matters, Value-Based Care Watch, Acquisitions & Partnerships; 2 cards for Did You Know.
- **Light mode email** (white background) for Outlook compatibility and forwarding.
- **Liquid glass design** on the Vercel site (ambient gradient, backdrop-filter blur, glass cards).
- **No Guidehouse branding anywhere in the byline/footer.** The "Let's Talk AI" CTA still routes to `gharrison@guidehouse.com` intentionally.
- **FieldShield infrastructure is NEVER used** for this project.
- **`gws` CLI** for email sending locally; **Gmail SMTP** for GitHub Actions.

## Automation notes

### Friday newsletter (GitHub Actions)

- **Workflow:** `.github/workflows/weekly-newsletter.yml`
- **Schedule:** Fridays 5am ET (`0 9 * * 5` UTC)
- **How it works:** GitHub runner checks out repo, installs Python deps, runs collector → curator → generator, publishes to `content/`, sends email via SMTP, commits and pushes. Vercel auto-deploys.
- **Scripts:** `.github/scripts/publish_issue.py` and `.github/scripts/send_newsletter.py`
- **Secrets:** `ANTHROPIC_API_KEY`, `SMTP_USER`, `SMTP_PASSWORD` in GitHub repo secrets (never in code)
- **Manual fire:** Actions tab → Weekly Newsletter → Run workflow (supports `dry_run` and `date_override`)
- **Logs:** Full step-by-step logs visible in the Actions tab for every run
- **Old Anthropic Friday trigger (`trig_01JqnHVGb3gfV1judxMohq12`):** Disabled 2026-04-12. Do not re-enable.

### Bulletin monitor (Anthropic cloud trigger)

- **Trigger ID:** `trig_01Jr3zP4zvYRnvKo2MmHAeto`
- Still runs in Anthropic's cloud. The cloud agent IS Claude (no API key needed). Clones repo fresh, runs `--cloud-mode`, writes bulletins, commits and pushes.
- To update the trigger prompt, open its URL on claude.ai and edit the instructions panel.

### AI Learning (manual, Greg's laptop)

- Requires `notebooklm` CLI + local Chrome. Cannot be automated in CI yet.
- Run: `cd pipeline && source venv/bin/activate && python -m learning.learning_pipeline`
- Copy output to `content/learn/`, commit, push. Vercel auto-deploys.

## Current status (as of 2026-04-12)

### Newsletter pipeline
- 5 sections: What Matters, VBC Watch, M&A & Partnerships, Consulting Intelligence, Did You Know
- Every story MUST have an AI/technology angle (enforced in guardrails)
- Cross-issue dedup: curator reads last 4 weeks of headlines and won't repeat
- 4 issues published (Mar 21, Mar 28, Apr 4, Apr 10)
- **Fully automated via GitHub Actions** — end-to-end tested 2026-04-12 with laptop closed
- RSS collector parallelized (10 threads, 3s timeout) for CI reliability

### Bulletin monitor
- Sources: Newsdata, Hacker News, Reddit, Substack (X and Bluesky disabled — Cloudflare blocked)
- Keywords widened 2026-04-12 to cover broad AI news: Anthropic, OpenAI, Gemini, Nvidia, foundation models, AI safety, AI regulation
- Two-source verification: min 2 platforms, 3 unique authors, 24-hour window
- Cloud mode with heartbeat — every 4-hour run commits `_last_run.json` to git regardless of output
- Weekly cycle: bulletins accumulate Mon-Fri, archive on Sunday, fresh start Monday

### Vercel site
- Home page with inline hero search (new 2026-04-10): search across issues, bulletins, consulting intelligence, and learn topics
- `⌘K` nav search also available from any page
- Full `/search` page with filter sidebar (type, date range, firm, sort)
- Pages: `/`, `/news/[date]`, `/bulletins`, `/bulletins/[slug]`, `/learn`, `/learn/[slug]`, `/analytics`
- Design: glass cards, ambient gradient, Aptos font, uniform blue `#0284C7` palette

### Supabase analytics
- Project `wjwubjahhbhhsctnpfcb` (NOT FieldShield)
- `quiz_attempts` table with RLS
- Dashboard at `/analytics?key=hcai2026analytics`

### Env files
- `pipeline/.env` — `ANTHROPIC_API_KEY`, `NEWSDATA_API_KEY`, optional Reddit creds
- `.env.local` — Supabase URL, anon key, service role key
- Both gitignored. Vercel env vars set separately in Vercel dashboard.

## Open items

1. ~~**Friday newsletter trigger path audit.**~~ Resolved: migrated to GitHub Actions 2026-04-12. Old Anthropic trigger disabled.
2. **Delete `/Users/greg/Claude/healthcare-ai-newsletter` local folder** — safe to delete now. Old repo is stale.
3. **Outlook Classic email rewrite.** Current template breaks in Word-rendered Outlook Classic. Fix pending colleague's screenshots.
4. **Microsoft Form for subscriptions.** Create Form, link from site, Power Automate distribution.
5. **Reddit API auth.** Register app for higher rate limits (Reddit rate-limits unauthenticated requests, especially on r/singularity).
6. **Re-enable X/Bluesky** when Cloudflare blocks lift.
7. **Automate AI Learning quizzes** — deferred. Anthropic API fallback for summaries + quizzes is built but Greg prefers manual NotebookLM workflow for now. See memory note `project_learning_automation.md` for full resume checklist.
