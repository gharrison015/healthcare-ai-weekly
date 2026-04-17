# Healthcare AI Weekly — Bulletin System Design Spec

## Overview

A near-real-time breaking news bulletin system that detects high-velocity healthcare AI stories on X/Twitter, verifies them against credible sources, and publishes short punchy takes to the Vercel site between weekly issues.

The weekly newsletter is the analysis layer. The bulletin is the signal layer.

## Problem

Major healthcare AI stories break on X/Twitter hours before they hit traditional publications. Examples:
- Claude Mythos security vulnerability discovery (blew up on X within hours)
- Claude Code data harness leak
- Surprise FDA AI clearances
- Major acquisitions announced via tweet before press release

By the time these make the Friday newsletter, they're old news. The audience needs to know about them when they happen.

## What Triggers a Bulletin

Not everything. High bar only:
- Engagement velocity spike: a topic goes from 0 to high impressions within 2-4 hours
- Everyone in healthcare AI is talking about it right now
- It changes how people should think about something
- It can't wait until Friday because it'll be stale by then

Examples that qualify: major model releases with healthcare implications, security vulnerabilities in clinical AI, surprise acquisitions, FDA actions, major data breaches, policy bombshells.

Examples that don't qualify: routine product updates, minor funding rounds, conference announcements, opinion pieces.

## Architecture

```
X API MONITOR ──▶ VELOCITY DETECTION ──▶ CREDIBILITY CHECK ──▶ BULLETIN GENERATOR ──▶ PUBLISH
(every 2-4 hrs)   (engagement spike?)    (verified source?)     (Claude writes take)    (Vercel + alert)
```

### Stage 1: X/Twitter Monitor

**Implementation:** Python using `tweepy` library with X API v2 (free tier).

**What to monitor:**

Key accounts (healthcare AI thought leaders and orgs):
- @EricTopol, @JohnHalamka, @zelosforclinical
- @AnthropicAI, @OpenAI, @GoogleHealth, @Microsoft, @EpicSystems
- @FierceHealth, @BeckersHR, @staaborian
- Healthcare AI journalists and VCs

Hashtags and keywords:
- #healthcareAI, #clinicalAI, #healthtech, #digitalhealth
- "healthcare" + "AI" with high engagement
- Company names + "healthcare" or "clinical"

**Polling frequency:** Every 2-4 hours via a scheduled trigger or cron loop.

**Output:** List of candidate topics with engagement metrics (impressions, retweets, quote tweets, reply count, velocity score).

### Stage 2: Velocity Detection

**Algorithm:**
1. For each topic cluster (grouped by keywords/entities), calculate engagement velocity:
   - `velocity = total_impressions / hours_since_first_post`
   - `acceleration = velocity_now / velocity_1hr_ago`
2. Threshold: topic must exceed a minimum velocity AND show acceleration (getting hotter, not cooling off)
3. Minimum engagement: at least N impressions across M posts within the window (tunable, start conservative)
4. Dedup: don't re-trigger on topics already published as bulletins

**Topic clustering:** Group tweets by entity extraction (company names, product names, policy terms). Multiple tweets about the same thing = one topic.

### Stage 3: Credibility Verification

Before publishing, cross-reference the claim:
1. **Google News check:** Search for the topic. Are credible outlets covering it?
2. **Primary source check:** Is there a blog post, press release, FDA filing, SEC filing, or official announcement?
3. **Account credibility:** Are verified accounts with real credentials discussing it, or is it rumor mill?

**Decision matrix:**
- High velocity + credible source confirmed → **Auto-publish bulletin**
- High velocity + no credible source yet → **Flag for Greg's review** (send alert, don't publish)
- Moderate velocity + credible source → **Queue for next weekly issue** (not bulletin-worthy)

### Stage 4: Bulletin Generator

Claude writes a short, punchy take:
- 3-5 sentences max
- Same Nate B Jones voice as the newsletter
- Lead with what happened, then why it matters
- Include the primary source link
- Timestamp

**Output:** JSON file saved to `data/bulletins/YYYY-MM-DD-HH-slug.json`

```json
{
  "timestamp": "2026-04-08T14:32:00Z",
  "slug": "claude-mythos-security",
  "headline": "Claude Mythos Is Finding Real Security Vulnerabilities",
  "body": "3-5 sentence take...",
  "source_url": "https://...",
  "source_name": "Anthropic Blog",
  "velocity_score": 87,
  "verification": "confirmed",
  "tags": ["anthropic", "security", "model-release"]
}
```

### Stage 5: Publish

1. **Vercel site:** Add bulletin to `/bulletins/` directory, update `bulletins.json` manifest
2. **Landing page:** Show latest bulletin in a "Breaking" card at the top, distinct from weekly issues
3. **Alert to Greg:** Email notification so Greg knows a bulletin was published (or flagged for review)
4. **Future:** Push to subscriber distribution list

## Vercel Site Changes

### Landing Page

Add a "Breaking" section above "All Issues":

```
┌──────────────────────────────────────────┐
│  BULLETIN                    2 hours ago  │
│  Claude Mythos Is Finding Real Vulns      │
│  3-5 sentence take...                     │
│  Source: Anthropic Blog                   │
└──────────────────────────────────────────┘
```

- Red/orange accent color (distinct from blue weekly issues)
- "BULLETIN" label with timestamp (relative: "2 hours ago", "yesterday")
- Shows only the most recent bulletin (or last 2-3)
- Older bulletins accessible via a "View all bulletins" link
- When no active bulletin, section is hidden

### Bulletin Archive Page

`/bulletins/` page listing all past bulletins chronologically. Same glass design as issues but with red/orange accent.

## Data Flow

```
/Users/greg/Claude/healthcare-ai-newsletter/
├── bulletin/
│   ├── x_monitor.py          # X API polling and engagement tracking
│   ├── velocity_detector.py  # Spike detection algorithm
│   ├── credibility_checker.py # Cross-ref against credible sources
│   ├── bulletin_generator.py # Claude writes the take
│   ├── bulletin_config.json  # Accounts, hashtags, thresholds (tunable)
│   └── __init__.py
├── data/
│   └── bulletins/            # Published bulletins (JSON)
```

```
/Users/greg/Claude/personal/content/healthcare-ai-weekly/
├── bulletins/
│   ├── YYYY-MM-DD-slug/
│   │   └── index.html        # Individual bulletin page
│   └── index.html            # Bulletin archive page
├── bulletins.json             # Manifest for landing page
```

## X API Requirements

- **API tier:** Free tier (v2) allows 500k tweet reads/month, search recent tweets
- **Library:** `tweepy` for Python
- **Auth:** OAuth 2.0 Bearer Token (app-only auth sufficient for reading public tweets)
- **Rate limits:** 450 requests per 15-minute window for search
- **Cost:** Free

## Scheduling

Option A: **Claude Code remote trigger** running every 2-4 hours
- Same pattern as newsletter trigger
- Agent runs monitor, checks velocity, publishes if warranted

Option B: **Local cron** polling X API, with Claude Code session triggered only when a velocity spike is detected
- Lighter weight, but has the "computer off" problem

Option C: **Hybrid** — lightweight X API polling runs on a cheap cloud function (AWS Lambda, Vercel serverless), triggers Claude Code only when a spike is detected
- Most reliable, decouples monitoring from content generation

**Recommendation:** Start with Option A (remote trigger every 4 hours). If it's too costly or slow, move to Option C.

## Content Relationship

Bulletins and weekly issues are connected:
- A bulletin topic that's still developing by Friday gets deeper treatment in the weekly issue
- The weekly curator agent reads `data/bulletins/` to know what already broke this week
- The weekly issue can reference "As we reported in Tuesday's bulletin..." for continuity
- Bulletin tags enable topic tracking across both formats

## Thresholds (Starting Conservative)

All tunable in `bulletin_config.json`:
- Minimum impressions for velocity trigger: 25,000 across topic cluster
- Minimum unique accounts discussing: 10
- Velocity threshold: 5,000 impressions/hour
- Acceleration required: velocity must be increasing (not decaying)
- Maximum bulletins per day: 2 (prevent spam)
- Cooldown after publish: 6 hours before same topic can trigger again

## Success Criteria

- Bulletin publishes within 4-6 hours of a story breaking on X
- Zero false positives (no bulletins about non-stories)
- Credibility verification catches rumors before they publish
- Weekly newsletter references bulletins for continuity
- Readers associate the Vercel site with being first, not just thorough
