import os
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def render_deep_dive(curated, all_articles):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=False)
    template = env.get_template("doc_template.html")

    sections = curated.get("sections", {})
    trend_watch = curated.get("trend_watch", {})
    trend_signal = trend_watch.get("emerging_signal") if trend_watch else None

    html = template.render(
        week_range=curated.get("week_range", ""),
        editorial_summary=curated.get("editorial_summary", ""),
        top_stories=sections.get("top_stories", []),
        vbc_watch=sections.get("vbc_watch", []),
        ma_partnerships=sections.get("ma_partnerships", []),
        consulting_intelligence=sections.get("consulting_intelligence", []),
        did_you_know=sections.get("did_you_know", []),
        trend_signal=trend_signal,
        all_articles=all_articles or [],
    )
    return html
