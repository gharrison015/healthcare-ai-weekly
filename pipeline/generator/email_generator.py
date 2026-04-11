import os
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def format_subject_line(week_display):
    return f"Healthcare AI Weekly \u2014 Week of {week_display}"

LANDING_PAGE_URL = "https://healthcareaibrief.com"

def render_email(curated, deep_dive_url=None, landing_url=None):
    """Render the weekly HTML email.

    Args:
        curated: the curated issue dict with sections, trend_watch, etc.
        deep_dive_url: URL of the deep-dive issue page (used in card links)
        landing_url: URL that cards route through (e.g. /?issue=YYYY-MM-DD).
            Falls back to deep_dive_url if not provided. Historically the
            cards linked to the landing page with a ?issue= param so a
            single entry point handled highlighting; deep_dive_url is
            the direct per-issue page.
    """
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    template = env.get_template("email_template.html")

    sections = curated.get("sections", {})
    trend_watch = curated.get("trend_watch", {})
    trend_signal = trend_watch.get("emerging_signal") if trend_watch else None

    # Support both old (deal_flow) and new (ma_partnerships) key names
    ma_partnerships = sections.get("ma_partnerships") or sections.get("deal_flow", [])

    # Card links route through landing_url when set (issue highlighting),
    # otherwise fall back to deep_dive_url directly.
    card_link_url = landing_url or deep_dive_url

    html = template.render(
        week_range=curated.get("week_range", ""),
        editorial_summary=curated.get("editorial_summary", ""),
        top_stories=sections.get("top_stories", []),
        vbc_watch=sections.get("vbc_watch", []),
        ma_partnerships=ma_partnerships,
        consulting_intelligence=sections.get("consulting_intelligence", []),
        did_you_know=sections.get("did_you_know", []),
        trend_signal=trend_signal,
        deep_dive_url=card_link_url,
        landing_url=landing_url,
    )
    return html
