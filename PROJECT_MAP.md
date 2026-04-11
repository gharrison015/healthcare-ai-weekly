# Project Map — Healthcare AI Weekly

**Single source of truth for where every piece of this project lives.** If you're confused about "where does X live," start here. If you change the architecture, update this file in the same commit.

---

## TL;DR

**One repo. One local folder. Two cloud triggers. One Vercel site.**

```
┌─────────────────────────────────────────────────────────────┐
│ /Users/greg/Claude/healthcare-ai-weekly    (ONE repo, ONE   │
│ github.com/gharrison015/healthcare-ai-weekly  working dir)  │
│                                                             │
│  pipeline/    ← Python: collect, curate, generate, bulletin │
│  src/         ← Next.js site (deploys to Vercel)           │
│  content/     ← Static JSON for issues, bulletins, learn    │
│  supabase/    ← Quiz analytics schema                       │
│  docs/        ← PRD, specs, plans                           │
└─────────────────────────────────────────────────────────────┘
          │                         │
          │ git push main           │ git push main
          ▼                         ▼
  ┌──────────────┐        ┌────────────────────┐
  │ Vercel build │        │ Cloud triggers     │
  │ auto-deploys │        │ clone fresh each   │
  │              │        │ run, commit back   │
  └──────────────┘        └────────────────────┘
```

Nothing runs "locally for production." Every scheduled job runs in Anthropic's cloud. Your Mac can be off and the newsletter still ships.

---

## The repos

| Repo | Purpose | Status |
|---|---|---|
| [`gharrison015/healthcare-ai-weekly`](https://github.com/gharrison015/healthcare-ai-weekly) (public) | **Source of truth.** Pipeline + site + content + triggers target this. | ✅ Active |
| [`gharrison015/healthcare-ai-newsletter`](https://github.com/gharrison015/healthcare-ai-newsletter) (private) | Legacy X-only bulletin pipeline from before consolidation. | ❌ **Stale. Do not edit.** Left alive as historical reference; should eventually be archived. |

**Local folders:**
- `/Users/greg/Claude/healthcare-ai-weekly` — work here
- `/Users/greg/Claude/healthcare-ai-newsletter` — leave alone, will be deleted during cleanup

---

## What lives where inside `healthcare-ai-weekly/`

| Path | What it is | Who reads it |
|---|---|---|
| `pipeline/collector/` | RSS/API sources, raw collection | Python pipeline, cloud newsletter trigger |
| `pipeline/curator/` | Persona, guardrails, feedback, Claude-based curation | Python pipeline (when local Anthropic API available) |
| `pipeline/generator/` | Jinja2 templates for email + deep-dive HTML | Python pipeline, cloud newsletter trigger |
| `pipeline/bulletin/` | Multi-source monitor, velocity detector, credibility checker | Python pipeline, cloud bulletin trigger (via `--cloud-mode`) |
| `pipeline/distributor/` | `gws` email sender, manifest builder | Python pipeline |
| `pipeline/learning/` | Quiz generator for Learn topics | Python pipeline |
| `pipeline/data/` | Runtime outputs (raw, curated, bulletins) — `.gitignore`'d except for heartbeat | Pipeline only |
| `pipeline/venv/` | Local Python virtualenv | Local dev only, gitignored |
| `pipeline/.env` | API keys (Anthropic, Newsdata, Reddit) | Local dev only, gitignored |
| `src/app/` | Next.js App Router pages | Vercel build |
| `src/components/` | React components (nav, search, cards) | Vercel build |
| `src/lib/` | Data loaders, types, Supabase client | Vercel build |
| `content/issues/<date>/data.json` | Curated weekly issue content | Next.js site + search index |
| `content/bulletins/*.json` | Individual bulletins | Next.js site + search index |
| `content/bulletins/_last_run.json` | **Bulletin trigger heartbeat** — always updated | Read it to see when bulletin last ran and what it found |
| `content/consulting-intelligence/*.json` | Consulting firm moves | Next.js site + search index |
| `content/learn/*.json` | Learn topics + quiz questions | Next.js site |
| `content/manifests/*.json` | Index files for each content type | Next.js site |
| `public/search-index.json` | Built at `next build` by `scripts/build-search-index.ts` | Browser (client-side search) |
| `scripts/build-search-index.ts` | Search index builder | npm `predev` and `prebuild` hooks |
| `supabase/` | SQL schema for quiz analytics | Supabase project `wjwubjahhbhhsctnpfcb` |
| `docs/PRD.md` | Product requirements doc | Humans + agents |
| `docs/superpowers/specs/` | Design docs | Humans + agents |
| `docs/superpowers/plans/` | Implementation plans | Humans + agents |
| `pipeline/HANDOFF.md` | Operational runbook (how to do things) | Humans + agents |
| `PROJECT_MAP.md` (this file) | Architecture reference | Humans + agents |

---

## Cloud triggers (the only things that run on a schedule)

Both triggers run in Anthropic's cloud. They clone `healthcare-ai-weekly` fresh each run, execute their prompt, commit output back to the repo, and exit. Your Mac is not involved.

### 1. Friday newsletter

- **Trigger ID:** `trig_01JqnHVGb3gfV1judxMohq12`
- **URL:** https://claude.ai/code/scheduled/trig_01JqnHVGb3gfV1judxMohq12
- **Schedule:** Fridays 9am ET (`cron: 0 13 * * 5` UTC)
- **What it does:** Runs the full collector → curator → generator → distributor pipeline, writes the week's issue to `content/issues/<date>/`, sends the HTML email via Gmail MCP, commits to main.
- **Health:** flagged in HANDOFF as needing path debugging after consolidation; verify it ran successfully by checking for a new `content/issues/<this-Friday>/` directory.

### 2. Bulletin monitor

- **Trigger ID:** `trig_01Jr3zP4zvYRnvKo2MmHAeto`
- **URL:** https://claude.ai/code/scheduled/trig_01Jr3zP4zvYRnvKo2MmHAeto
- **Schedule:** Every 4 hours, weekdays (`cron: 0 10,14,18,22 * * 1-5` UTC = 6am, 10am, 2pm, 6pm ET)
- **What it does:**
  1. `cd pipeline && python -m bulletin.bulletin_pipeline --cloud-mode` (runs monitor → velocity → credibility, writes `_candidates.json` and `_last_run.json`)
  2. Copies `_last_run.json` from `pipeline/data/bulletins/` to `content/bulletins/_last_run.json` (heartbeat in git)
  3. Reads `_candidates.json`. If empty: commit heartbeat only and exit.
  4. For each candidate: writes bulletin body (agent writes, no API key needed), saves to `content/bulletins/<slug>.json`, updates `content/manifests/bulletins.json`
  5. `git add content/ && git commit && git push`
- **Health check:** `git log content/bulletins/_last_run.json` — you'll see a commit for every run, every 4 hours. If no commit in >6 hours during a weekday, the trigger failed.

---

## Other services

| Service | Purpose | URL / ID |
|---|---|---|
| **Vercel** | Hosts the Next.js site, auto-deploys on `git push main` | https://healthcare-ai-weekly.vercel.app |
| **Supabase** | Quiz analytics (submissions + dashboard) | Project `wjwubjahhbhhsctnpfcb` (NOT FieldShield) |
| **Gmail (via `gws` CLI locally, MCP connector in cloud)** | Send the weekly newsletter | Sends to `gharrison@guidehouse.com` |
| **Analytics dashboard** | Password-gated quiz stats | `/analytics?key=hcai2026analytics` |

---

## Secrets

| Secret | Lives in | Used by |
|---|---|---|
| `ANTHROPIC_API_KEY` | `pipeline/.env` (local only) | Local curator + bulletin generator runs |
| `NEWSDATA_API_KEY` | `pipeline/.env` (local) AND inline in cloud trigger prompts | Collector + bulletin monitor |
| `REDDIT_*` | `pipeline/.env` (local only) | Reddit monitor (optional, higher rate limits) |
| `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` | `.env.local` AND Vercel env vars | Next.js site (quiz analytics) |
| `ANALYTICS_PASSWORD` (`hcai2026analytics`) | URL query param | `/analytics` dashboard gate |

**Both `pipeline/.env` and `.env.local` are gitignored.** Never commit them.

**FieldShield infrastructure is never used for this project.** If you see a FieldShield Supabase URL, Gmail account, or GCP project referenced anywhere in this repo, that's a bug — remove it.

---

## "How do I..." quick reference

Operational recipes live in `pipeline/HANDOFF.md`. This doc is the map; HANDOFF is the runbook.

- **Run the pipeline locally:** see HANDOFF § "How to Run Locally"
- **Send a test email:** see HANDOFF § "How to Send a Test Email"
- **Check if the bulletin trigger ran:** `git log -- content/bulletins/_last_run.json` (committed every 4 hours regardless of output)
- **Update a cloud trigger prompt:** open the trigger URL on claude.ai and edit the instructions panel — the trigger lives in Anthropic's cloud, not this repo
- **Debug why something isn't on the Vercel site:** check that the underlying JSON exists in `content/`, the manifest is updated, `next build` succeeded in Vercel dashboard

---

## Anti-goals (things this project deliberately does NOT do)

- ❌ **No local cron.** Scheduled work runs in cloud triggers. Your Mac may be off.
- ❌ **No second pipeline codebase.** The old `healthcare-ai-newsletter` folder/repo is dead. Don't edit it.
- ❌ **No Guidehouse branding.** Site is independent ("by Greg Harrison"). The email CTA still routes to his Guidehouse inbox intentionally.
- ❌ **No em dashes anywhere** in generated content. Enforced by curator prompt + post-processing strip.
- ❌ **No FieldShield infra.** Separate business, separate project, separate everything.
