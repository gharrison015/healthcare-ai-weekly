# Cloud Trigger Failure Investigation — Handoff

**Date:** 2026-04-11 (Saturday)
**Author:** Claude Opus 4.6 session with Greg
**Context:** Greg has been unable to get a cloud-sent test email for 4 consecutive days. This doc captures the full investigation, current state, evidence, and the fallback plan.

---

## TL;DR

- **The pipeline code is working.** Generator bug fixed today. Full end-to-end validated locally. Two test emails successfully sent via `gws` CLI from Greg's Mac this morning.
- **The cloud trigger mechanism is broken.** Every cloud run this week either hangs indefinitely or exits silently without committing to git or sending email.
- **A minimal Gmail-MCP-only isolation test is scheduled for 10:07 AM ET 2026-04-11.** Result pending at time of writing.
- **Fallback plan:** migrate the Friday newsletter automation to **GitHub Actions** — free, reliable, visible logs, no daily quota.

---

## What's working ✅

| Component | Status | Evidence |
|---|---|---|
| Newsletter pipeline end-to-end (local) | ✅ | Ran at 9:49 AM ET, produced 18 KB email.html with all 5 sections |
| `render_email` function | ✅ | Fixed today; added missing `landing_url` kwarg |
| Email template rendering | ✅ | 4 top / 1 VBC / 1 M&A / 2 consulting / 2 DYK all rendered |
| `gws` CLI send to Guidehouse inbox | ✅ | Msg ids `19d7ccdcc58c5c1b`, `19d7cd934ea351fc` both returned SENT |
| Vercel site at `healthcareaibrief.com` | ✅ | Live, 200 on all routes, DNS configured |
| Legacy `.vercel.app` URL | ✅ | Still returns 200, preserves existing bookmarks |
| Bulletin trigger (`trig_01Jr3zP4zvYRnvKo2MmHAeto`) scheduler | ✅ | Fires 4x/weekday per schedule (run logs not inspectable, but `next_run_at` advances) |
| Inline hero search + /search page | ✅ | Shipped yesterday, live on production |

## What's broken ❌

| Component | Status | Evidence |
|---|---|---|
| Cloud trigger execution | ❌ | 4 triggered runs this week, zero successful commits or emails |
| `RemoteTrigger run` API action | ❌ | Returns HTTP 200 + trigger config, does not actually execute a run (verified 2x: once for bulletin trigger last night, once for test trigger this morning) |
| Cloud trigger run log visibility | ❌ | API does not expose run output. UI run-detail pages were "thinking forever" when Greg tried to open them. |
| Friday newsletter trigger (cloud path) | ❌ | Has never successfully committed an issue since repo consolidation; all committed issues on main were from Greg's local runs |

## What might be broken, TBD

| Component | Status | How we'd find out |
|---|---|---|
| Cloud `git push` auth | Suspected broken | If the 10:07 AM Gmail-only test SUCCEEDS, git was the problem |
| Cloud Gmail MCP connector | Suspected broken | If the 10:07 AM Gmail-only test FAILS, Gmail MCP was the problem |
| Cloud pip install in this project | Unclear | Local sim of pip install completes in ~5 seconds, but cloud env behavior unknown |

---

## Today's commits on `main`

```
7a529b76 fix: render_email accepts landing_url kwarg           ← critical bug fix
51d2e23d persona: rewrite with concrete Nate B Jones voice rules
ab267a69 fix: velocity_detector skips runtime state files in bulletins_dir
4a3a93f2 chore: switch primary URL to healthcareaibrief.com
17b93983 feat: fuzzy-match dedup for consulting intelligence
d41d5a21 fix: dedupe PwC AI governance certification entry
4c3b5cc3 fix: dedupe Bain/Palantir and PwC/Leah consulting intelligence entries
```

The `render_email` fix in `7a529b76` was almost certainly why every prior Friday run failed to produce an email. Before today, `pipeline.py` called `render_email(curated, landing_url=..., deep_dive_url=...)` but the function signature only accepted `deep_dive_url` → `TypeError` on every run → generator stage died → nothing reached commit or send.

---

## Trigger inventory (as of 2026-04-11 10:02 AM ET)

| ID | Name | Status | Cron | Next run |
|---|---|---|---|---|
| `trig_01JqnHVGb3gfV1judxMohq12` | Friday newsletter | ENABLED | `0 11 * * 5` (Fri 7 AM ET) | 2026-04-17 |
| `trig_01Jr3zP4zvYRnvKo2MmHAeto` | Bulletin monitor | ENABLED | `0 10,14,18,22 * * 1-5` | 2026-04-13 |
| `trig_013T91H7ViNqEX5mM9hSLHae` | SATURDAY-TEST-DRYRUN | DISABLED | `35 13 11 4 *` | 2027-04-11 |
| `trig_01UzdFUAUrqY4V5cUVcN4i1t` | MECHANISM-TEST-2 | DISABLED | `42 13 11 4 *` | 2027-04-11 |
| `trig_01Bsiq1j7rEhojMR2tdTVbcN` | gmail-mcp-isolation-test | ENABLED | `5 14 11 4 *` | **2026-04-11 10:07 AM ET** |

### Quota

Greg's plan has a **3 daily cloud scheduled sessions** limit. Hit this limit at 9:58 AM ET today when trying to create a new test. Had to disable two failed test triggers to fit the minimal isolation test.

---

## The 10:07 AM isolation test

**Purpose:** Remove all confounding variables and isolate whether Gmail MCP can send from the cloud environment at all. Previous test triggers included pipeline execution, venv setup, pip install, python heredocs, git push, AND Gmail MCP send. Impossible to know which step was hanging.

**This test does only:**
1. `Read` tool to load `pipeline/data/issues/2026-04-09/email.html` (a real pre-existing email from the last successful local run)
2. Gmail MCP connector to send it to `gharrison@guidehouse.com` with subject `[TEST-MINIMAL] Cloud Gmail MCP isolation test`
3. Report `SUCCESS: <msg id>` or `FAILED: <error>`

**Only tools allowed:** `Read`. No Bash, no Write, no Edit, no venv, no pipeline, no git.

**Prompt length:** ~200 words (vs. ~2000+ in prior test triggers).

**Expected duration:** under 30 seconds.

**Decision tree after the test:**

- **Email arrives** → Gmail MCP works from cloud. The prior hangs were in earlier steps (pip install, pipeline execution, OR more likely `git push` hanging on credential prompt). Fix: rebuild the Friday trigger to skip `git push` and have the cloud agent use the Gmail MCP to send but rely on a different mechanism for committing content (or skip committing altogether and use a different publish path).
- **Email doesn't arrive** → Gmail MCP cannot send from cloud. No point fighting the Anthropic trigger further. Immediately pivot to GitHub Actions.

---

## Fallback plan: GitHub Actions

If the Anthropic cloud trigger can't be made reliable, the replacement is **GitHub Actions**. Reasons this is the right answer:

- **Runs on GitHub's CI, not your Mac or Anthropic's cloud.** No daily quotas, no mystery hangs.
- **Logs are immediate and complete.** Every line of every run, visible in the GitHub Actions tab.
- **Native git auth.** The `GITHUB_TOKEN` secret gives the workflow push access without credential drama.
- **Secrets management.** Set `ANTHROPIC_API_KEY`, `NEWSDATA_API_KEY`, etc. as repo secrets. Never in the prompt, never in the code.
- **Cron syntax.** `0 11 * * 5` for Friday 7 AM ET (EDT), same cron as the Anthropic trigger.
- **Free** for public repos like `healthcare-ai-weekly`.
- **Email sending options:** (a) Gmail API via `gws` installed in the runner, (b) a dedicated send-email GitHub Action, (c) SendGrid/Mailgun/SES integration.

### Sketch of the workflow

```yaml
# .github/workflows/weekly-newsletter.yml
name: Weekly Newsletter
on:
  schedule:
    - cron: '0 11 * * 5'  # Friday 7 AM ET (EDT)
  workflow_dispatch:       # also allow manual fire

jobs:
  generate-and-send:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.13' }
      - run: pip install -r pipeline/requirements.txt
      - run: |
          cd pipeline
          python pipeline.py --date $(date -u '+%Y-%m-%d')
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          NEWSDATA_API_KEY: ${{ secrets.NEWSDATA_API_KEY }}
      - run: |
          DATE=$(date -u '+%Y-%m-%d')
          mkdir -p content/issues/$DATE
          cp pipeline/data/curated/$DATE.json content/issues/$DATE/data.json
          python -c "..."  # update manifest
      - run: |
          git config user.email 'gh-actions@healthcareaibrief.com'
          git config user.name  'Healthcare AI Weekly Bot'
          git add content/
          git commit -m "newsletter: $(date -u '+%Y-%m-%d')"
          git push
      - uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.SMTP_USER }}
          password: ${{ secrets.SMTP_PASSWORD }}
          subject: "Healthcare AI Weekly — Week of ..."
          to: gharrison@guidehouse.com
          from: "Healthcare AI Weekly"
          html_body: file://pipeline/data/issues/YYYY-MM-DD/email.html
```

Effort to build: ~30-45 minutes once we decide to pivot.

---

## How to run the pipeline locally RIGHT NOW (works, verified today)

```bash
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly/pipeline
source venv/bin/activate

# Option 1: Full real pipeline (collect + curate + generate + send)
python pipeline.py --date $(date -u '+%Y-%m-%d')

# Option 2: Reuse an existing issue's content as a test payload (fast, no API cost)
python3 -c "
import json
with open('../content/issues/2026-04-10/data.json') as f:
    data = json.load(f)
data['test'] = True
data['issue_date'] = '2026-04-11'
with open('data/curated/2026-04-11.json', 'w') as f:
    json.dump(data, f, indent=2)
"
python pipeline.py --date 2026-04-11 --stage generator

# Option 3: Send an existing generated email via gws
python3 -c "
import sys; sys.path.insert(0, '.')
from distributor.send_email import send_email
with open('data/issues/2026-04-11/email.html') as f:
    html = f.read()
send_email('gharrison@guidehouse.com', '[TEST] Healthcare AI Weekly', html)
"
```

Any of these three approaches reliably lands an email in Greg's Guidehouse inbox. The `gws` CLI lives at `/Users/greg/.nvm/versions/node/v20.19.0/bin/gws`, is authenticated against Greg's personal Gmail, and the Gmail API returns SENT labels on every attempt this morning.

---

## Root cause hypotheses (ranked by likelihood)

1. **`git push` hangs on credential prompt in cloud env.** The cloud session clones the repo fine (read-only HTTPS) but has no push credentials. When the prompt hits `git push`, it prompts for `Username for https://github.com:` on stdin and hangs forever because there's no interactive stdin to answer it.
   - **Evidence for:** Bulletin monitor's old prompt did manual source queries and reported to Greg rather than committing — those runs appeared in Greg's screenshot. My cloud-mode prompt adds `git push`, which is where the hangs started.
   - **Evidence against:** The `curator` Friday trigger has a `git push` step and fires 1x/week, but I haven't confirmed any of its runs actually pushed successfully after consolidation.
   - **Fix:** Either (a) use `GITHUB_TOKEN` auth explicitly in the prompt, (b) configure git to use a `.netrc` file with a token, (c) skip git push in the cloud agent and publish via another path, (d) abandon Anthropic cloud triggers entirely for GitHub Actions.

2. **Gmail MCP authentication is stale or broken in the cloud.** The Gmail MCP connector may be tied to a session that requires refresh auth Greg hasn't completed recently.
   - **Evidence for:** None direct yet. Waiting for 10:07 AM isolation test.
   - **Evidence against:** The Friday newsletter trigger is wired up with the same MCP connector and was working previously.
   - **Fix:** Re-auth the Gmail MCP connector in Greg's Claude.ai settings.

3. **Complex prompts cause model reasoning loops.** My test trigger prompts were 2000+ words with nested python heredocs, strict schema requirements, and multiple validation steps. The cloud agent may have gotten stuck second-guessing itself or hitting token limits during the curation step.
   - **Evidence for:** Run duration on two test fires was suspicious (~24 min on the first, then "thinking forever" on the second per Greg's observation). A normal run of this work should take 3-5 min.
   - **Evidence against:** The minimal 200-word isolation test should sidestep this entirely.
   - **Fix:** Always use minimal, imperative prompts in cloud triggers. No heredocs, no complex validation.

4. **Cloud session has a hard execution timeout shorter than the pipeline needs.** Unlikely because a `--cloud-mode` run of the bulletin pipeline completes in ~90 seconds locally, well under any reasonable timeout.

---

## Things to not forget to do next session

1. **Check the 10:07 AM isolation test result.** `RemoteTrigger get trig_01Bsiq1j7rEhojMR2tdTVbcN` → look at `next_run_at` (should be 2027 if it fired) and check Greg's inbox for `[TEST-MINIMAL]` subject.
2. **If isolation test worked** → the Friday trigger needs its prompt rewritten to skip `git push`, and we need a different way to publish content (maybe a separate GitHub Actions workflow triggered by comment or label).
3. **If isolation test failed** → start building the GitHub Actions replacement immediately. 30-45 min effort. Use the sketch above.
4. **Update the Friday trigger prompt** regardless of test outcome — it still references `deal_flow` (old schema) and doesn't ask for `consulting_intelligence`. These bugs would produce malformed issues even if the trigger mechanism was fine.
5. **Delete the disabled test triggers** (`trig_013T91H7ViNqEX5mM9hSLHae` and `trig_01UzdFUAUrqY4V5cUVcN4i1t`) to clean up the list. Can be done from the UI.
6. **Verify `content/issues/2026-04-11/` does NOT exist on main.** If the old cloud-mode test accidentally committed anything, revert it. (As of 2026-04-11 10:00 AM ET, latest commit is `7a529b76` and there's no 2026-04-11 issue dir on main — clean.)

---

## Files changed today

- `pipeline/generator/email_generator.py` — added `landing_url` kwarg to `render_email` (the bug fix)
- `pipeline/curator/persona.md` — rewritten with concrete Nate B Jones voice rules
- `docs/handoffs/2026-04-11-cloud-trigger-debug.md` — this file (new)

---

## Summary for future-me (or the next agent)

**The system almost works.** Local pipeline is validated end-to-end. Code bug fixed. Persona tuned. Custom domain live. The only thing between you and a reliable weekly email automation is the Anthropic cloud trigger execution environment, which has been opaque and unreliable this week.

**The fastest path to reliability is to stop fighting the Anthropic trigger and use GitHub Actions instead.** It's 30-45 minutes of work. Everything needed already exists in this repo. The workflow just needs to be written and some secrets added to the repo settings.

**Before switching, check the 10:07 AM isolation test.** If it proves Gmail MCP works from cloud, the path forward is simpler (rebuild Friday trigger to skip git push). If it doesn't, go straight to GitHub Actions.

Greg has been patient through a rough 4 days. Next session should aim for a concrete, verified weekly automation — not more diagnostics.
