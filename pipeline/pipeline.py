import argparse
import json
import os
import sys
from datetime import datetime, timedelta

def compute_date_range(date_str):
    end_date = datetime.strptime(date_str, "%Y-%m-%d")
    start_date = end_date - timedelta(days=7)
    display = f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d"), display

def get_data_paths(date_str):
    return {
        "raw": f"data/raw/{date_str}.json",
        "curated": f"data/curated/{date_str}.json",
        "delta": f"data/curated/{date_str}-delta.json",
        "issue_dir": f"data/issues/{date_str}",
        "email_html": f"data/issues/{date_str}/email.html",
        "doc_html": f"data/issues/{date_str}/index.html",
        "linkedin_seed": f"data/linkedin-seed/{date_str}.json",
    }

def run_collector(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 1: COLLECTOR")
    print(f"{'='*60}")

    from collector.rss_collector import collect_rss
    from collector.filters import deduplicate_articles

    articles = collect_rss("collector/sources.json")
    articles = deduplicate_articles(articles)

    start, end, display = compute_date_range(date_str)
    raw_data = {
        "collection_date": date_str,
        "week_range": display,
        "article_count": len(articles),
        "articles": articles,
    }

    os.makedirs(os.path.dirname(paths["raw"]), exist_ok=True)
    with open(paths["raw"], "w") as f:
        json.dump(raw_data, f, indent=2)

    print(f"Collected {len(articles)} articles")
    print(f"Saved to {paths['raw']}")
    return raw_data

def run_delta(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 1.5: DELTA TRACKER")
    print(f"{'='*60}")

    from data.curated.delta_tracker import load_history, compute_delta

    history = load_history("data/curated")

    raw_articles = []
    if os.path.exists(paths["raw"]):
        with open(paths["raw"]) as f:
            raw_articles = json.load(f).get("articles", [])

    delta = compute_delta(history, raw_articles)

    os.makedirs(os.path.dirname(paths["delta"]), exist_ok=True)
    with open(paths["delta"], "w") as f:
        json.dump(delta, f, indent=2)

    print(f"Analyzed {delta.get('weeks_analyzed', 0)} prior weeks")
    print(f"Recurring companies: {len(delta.get('recurring_companies', []))}")
    print(f"Saved to {paths['delta']}")
    return delta

def run_curator(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 2: CURATOR AGENT")
    print(f"{'='*60}")

    from curator.curator_agent import run_curator as curator_run

    delta_path = paths["delta"] if os.path.exists(paths["delta"]) else None

    curated = curator_run(
        raw_data_path=paths["raw"],
        output_path=paths["curated"],
        delta_path=delta_path,
    )

    story_count = sum(
        len(curated.get("sections", {}).get(s, []))
        for s in ["top_stories", "vbc_watch", "ma_partnerships", "consulting_intelligence", "did_you_know"]
    )
    print(f"Curated {story_count} stories across all sections")
    print(f"Saved to {paths['curated']}")
    return curated

def run_generator(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 3: GENERATOR")
    print(f"{'='*60}")

    from generator.email_generator import render_email, LANDING_PAGE_URL
    from generator.html_generator import render_deep_dive
    from generator.linkedin_seed import generate_seed, save_seed, copy_to_linkedin_agent

    with open(paths["curated"]) as f:
        curated = json.load(f)

    raw_articles = []
    if os.path.exists(paths["raw"]):
        with open(paths["raw"]) as f:
            raw_articles = json.load(f).get("articles", [])

    os.makedirs(os.path.dirname(paths["email_html"]), exist_ok=True)

    landing_url = f"{LANDING_PAGE_URL}?issue={date_str}"
    deep_dive_url = f"{LANDING_PAGE_URL}/news/{date_str}"
    email_html = render_email(curated, landing_url=landing_url, deep_dive_url=deep_dive_url)
    with open(paths["email_html"], "w") as f:
        f.write(email_html)
    print(f"Email generated: {paths['email_html']}")

    doc_html = render_deep_dive(curated, raw_articles)
    with open(paths["doc_html"], "w") as f:
        f.write(doc_html)
    print(f"Deep dive generated: {paths['doc_html']}")

    seed = generate_seed(curated)
    save_seed(seed)
    try:
        copy_to_linkedin_agent(seed)
        print("LinkedIn seed exported")
    except Exception as e:
        print(f"LinkedIn seed export skipped: {e}")

    return email_html, doc_html

def run_distributor(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 4: DISTRIBUTOR")
    print(f"{'='*60}")

    from distributor.send_email import send_email
    from distributor.publish_html import publish_to_repo
    from generator.email_generator import format_subject_line

    with open(paths["curated"]) as f:
        curated = json.load(f)

    with open(paths["email_html"]) as f:
        email_html = f.read()

    with open(paths["doc_html"]) as f:
        doc_html = f.read()

    _, _, display = compute_date_range(date_str)
    subject = format_subject_line(display)

    send_email("gharrison@guidehouse.com", subject, email_html)
    print("Email sent to gharrison@guidehouse.com")

    publish_to_repo(doc_html, curated, date_str)
    print(f"HTML published for {date_str}")

def run_score_update(date_str, paths):
    print(f"\n{'='*60}")
    print(f"STAGE 5: SOURCE SCORE UPDATE")
    print(f"{'='*60}")

    from collector.source_scorer import load_scores, update_scores, save_scores, get_flagged_sources

    if not os.path.exists(paths["raw"]) or not os.path.exists(paths["curated"]):
        print("Skipping score update (missing data)")
        return

    with open(paths["raw"]) as f:
        raw = json.load(f)
    with open(paths["curated"]) as f:
        curated = json.load(f)

    collected = raw.get("articles", [])
    curated_sources = []
    for section in curated.get("sections", {}).values():
        for story in section:
            src = story.get("source_article", {}).get("source")
            if src:
                curated_sources.append(src)

    scores = load_scores()
    scores = update_scores(scores, collected, curated_sources)
    save_scores(scores)

    flagged = get_flagged_sources(scores)
    if flagged:
        print(f"Flagged low-performing sources: {[f['source'] for f in flagged]}")
    print("Source scores updated")

def main():
    parser = argparse.ArgumentParser(description="Healthcare AI Weekly Newsletter Pipeline")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                        help="Issue date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--stage", choices=["collector", "curator", "generator", "distributor", "all"],
                        default="all", help="Run a specific stage or all")
    parser.add_argument("--skip-send", action="store_true", help="Skip email send (for testing)")
    args = parser.parse_args()

    date_str = args.date
    paths = get_data_paths(date_str)

    print(f"Healthcare AI Weekly — {date_str}")
    print(f"Stage: {args.stage}")

    if args.stage in ("collector", "all"):
        run_collector(date_str, paths)

    if args.stage in ("curator", "all"):
        run_delta(date_str, paths)
        run_curator(date_str, paths)

    if args.stage in ("generator", "all"):
        run_generator(date_str, paths)

    if args.stage in ("distributor", "all"):
        if args.skip_send:
            print("\nSkipping distributor (--skip-send)")
        else:
            run_distributor(date_str, paths)

    if args.stage == "all":
        run_score_update(date_str, paths)

    print(f"\nDone. Issue date: {date_str}")

if __name__ == "__main__":
    main()
