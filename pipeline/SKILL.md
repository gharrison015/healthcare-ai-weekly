# Healthcare AI Weekly Newsletter

## What This Does

Runs the Healthcare AI Weekly newsletter pipeline:
1. Collects AI healthcare news from RSS feeds
2. Curates and ranks stories using Claude as an editorial agent
3. Generates an executive HTML email and deep-dive HTML document
4. Sends email to gharrison@guidehouse.com
5. Publishes deep-dive to private GitHub repo
6. Exports LinkedIn seed file for the LinkedIn content agent

## How to Run

```bash
cd /Users/greg/Claude/personal/content/healthcare-ai-weekly/pipeline
source venv/bin/activate
python pipeline.py
```

## Manual Override

```bash
# Specific date
python pipeline.py --date 2026-04-04

# Single stage
python pipeline.py --date 2026-04-04 --stage collector

# Skip email send (preview only)
python pipeline.py --date 2026-04-04 --skip-send
```

## Schedule

Cron: `0 5 * * 5` (every Friday at 5:00 AM Eastern)
