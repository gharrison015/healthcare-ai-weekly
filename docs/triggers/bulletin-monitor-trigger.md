# Bulletin Monitor Cloud Trigger — Prompt

This is the text to paste into `trig_01Jr3zP4zvYRnvKo2MmHAeto` at https://claude.ai/code/scheduled/trig_01Jr3zP4zvYRnvKo2MmHAeto

**Why this version:** Replaces the old prompt that did manual source queries and had no heartbeat. The new prompt:
- Uses `python -m bulletin.bulletin_pipeline --cloud-mode` for rigorous collection + velocity detection + credibility checking (runs the same Python module you use locally, so behavior is consistent)
- Always writes `content/bulletins/_last_run.json` to the repo — you can run `git log -- content/bulletins/_last_run.json` to see every run in history
- Still lets the cloud agent write bulletin bodies itself (no Anthropic API key needed in the cloud)
- Covers all 4 active sources (Newsdata, Hacker News, Reddit, Substack) — the old prompt missed Substack
- Half the length of the previous prompt

## Schedule

Keep the existing cron: `0 10,14,18,22 * * 1-5` (every 4 hours 6am/10am/2pm/6pm ET, Mon-Fri).

## Repository

`gharrison015/healthcare-ai-weekly`

## Instructions (paste this into the trigger)

```
You are the Healthcare AI Weekly bulletin monitor. Check for breaking healthcare AI news every 4 hours on weekdays. Run the vetted Python pipeline, then write bulletins yourself for any verified candidates.

SETUP:
cd healthcare-ai-weekly/pipeline
python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt
echo 'NEWSDATA_API_KEY=pub_c144dad1399648cf86abc01b99ffaa44' > .env

STEP 1 — Run the cloud-mode pipeline:
python -m bulletin.bulletin_pipeline --cloud-mode

This will run monitor + velocity detection + credibility check across Newsdata, Hacker News, Reddit, and Substack. It writes two files:
- data/bulletins/_last_run.json  (always written — heartbeat)
- data/bulletins/_candidates.json  (may be empty)

STEP 2 — Always propagate the heartbeat to content/ so it shows up in git:
mkdir -p ../content/bulletins
cp data/bulletins/_last_run.json ../content/bulletins/_last_run.json

STEP 3 — Read the candidates file:
cat data/bulletins/_candidates.json

If the file is "[]" (empty array), go directly to STEP 5.

STEP 4 — For EACH candidate in _candidates.json, write a bulletin:
You ARE the writer. Voice: direct, confident healthcare AI consultant. No em dashes ever. 3-5 sentences. Lead with what happened, then why it matters for healthcare.

For each candidate, create a file at ../content/bulletins/<slug>.json with exactly this shape:
{
  "timestamp": "<ISO 8601 UTC now>",
  "slug": "<slug-from-candidate>",
  "headline": "<hook style, 8-12 words>",
  "body": "<3-5 sentences, no em dashes, healthcare angle>",
  "source_url": "<real verified URL from the candidate>",
  "source_name": "<primary publisher>",
  "velocity_score": <integer 0-100>,
  "verification": "confirmed",
  "verified_sources": [<list of platform names from candidate>],
  "tags": [<relevant tags>]
}

Then update ../content/manifests/bulletins.json by adding a new entry for this bulletin at the top of the list. Read the existing file, prepend a new manifest entry with the same slug/headline/source_name/timestamp/tags fields, write it back.

Critical: Never fabricate source URLs. Every bulletin must link to a real, verifiable article from the candidate data. The two-source verification has already been enforced by the Python pipeline — if a candidate made it to _candidates.json, it passed. Just write well.

STEP 5 — Sunday archive (only if today is Sunday):
If today is Sunday UTC, move all ../content/bulletins/*.json EXCEPT _last_run.json to ../content/bulletins/archive/ and reset ../content/manifests/bulletins.json to {"bulletins":[]}.

STEP 6 — Commit and push:
cd ..
BULLETIN_COUNT=$(jq length data/bulletins/_candidates.json 2>/dev/null || echo "0")
git add content/
git commit -m "bulletin: run $(date -u '+%Y-%m-%d %H:%M') (${BULLETIN_COUNT} bulletins)" || echo "nothing to commit"
git push

STEP 7 — Report what you found. Zero bulletins is fine and expected most cycles. The heartbeat is the proof the run happened.
```

## How to verify it worked

After pasting and the next scheduled run, check:

1. **Git log has a new commit:**
   ```bash
   cd /Users/greg/Claude/healthcare-ai-weekly
   git pull
   git log -- content/bulletins/_last_run.json
   ```
   You should see a commit like `bulletin: run 2026-04-11 10:00 (0 bulletins)` within ~5 minutes of each scheduled time.

2. **Heartbeat file is present and fresh:**
   ```bash
   cat content/bulletins/_last_run.json
   ```
   `timestamp_utc` should be within the last 4 hours.

3. **Disposition matches expectations:**
   - `no_results` — all sources returned nothing (rare, suspicious)
   - `no_spikes` — data collected but no topic cluster crossed velocity thresholds (most common)
   - `no_credible` — spike detected but only on one platform (fine)
   - `candidates_ready` — verified candidates exist, check `content/bulletins/*.json` for new files

## If it fails

1. Open the trigger's run history on claude.ai and click into the failing run to see the output
2. Look for the first error in the output — usually missing dependency, wrong path, or API failure
3. Paste the error here and I'll debug
