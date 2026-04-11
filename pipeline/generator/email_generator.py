import os
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def format_subject_line(week_display):
    return f"Healthcare AI Weekly \u2014 Week of {week_display}"

LANDING_PAGE_URL = "https://healthcareaibrief.com"

def render_email(curated, deep_dive_url=None):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    template = env.get_template("email_template.html")

    sections = curated.get("sections", {})
    trend_watch = curated.get("trend_watch", {})
    trend_signal = trend_watch.get("emerging_signal") if trend_watch else None

    # Support both old (deal_flow) and new (ma_partnerships) key names
    ma_partnerships = sections.get("ma_partnerships") or sections.get("deal_flow", [])

    html = template.render(
        week_range=curated.get("week_range", ""),
        editorial_summary=curated.get("editorial_summary", ""),
        top_stories=sections.get("top_stories", []),
        vbc_watch=sections.get("vbc_watch", []),
        ma_partnerships=ma_partnerships,
        consulting_intelligence=sections.get("consulting_intelligence", []),
        did_you_know=sections.get("did_you_know", []),
        trend_signal=trend_signal,
        deep_dive_url=deep_dive_url,
    )
    return html
