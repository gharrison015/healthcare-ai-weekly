import os
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def format_subject_line(week_display):
    return f"Healthcare AI Weekly \u2014 Week of {week_display}"

LANDING_PAGE_URL = "https://healthcareaibrief.com"


def _with_utm(url, campaign="weekly", content=None):
    """Append UTM params to a URL without clobbering existing query string."""
    if not url:
        return url
    parsed = urlparse(url)
    params = dict(parse_qsl(parsed.query))
    params.update({
        "utm_source": "email",
        "utm_medium": "newsletter",
        "utm_campaign": campaign,
    })
    if content:
        params["utm_content"] = content
    return urlunparse(parsed._replace(query=urlencode(params)))


def _build_tldr(curated):
    """Three scannable bullets from curated top picks across sections.

    Mixes top_stories + vbc_watch + ma_partnerships so scrollers see breadth,
    not just the lead section. Falls back to whatever is available.
    """
    sections = curated.get("sections") or {}
    candidates = []
    for key in ("top_stories", "vbc_watch", "ma_partnerships", "consulting_intelligence"):
        for story in (sections.get(key) or []):
            headline = (story.get("headline") or "").strip()
            if headline:
                candidates.append({"headline": headline, "section": key})
                break
    return candidates[:3]


def _build_preheader(curated):
    """First ~120 chars of editorial summary — drives open rate via inbox preview."""
    summary = (curated.get("editorial_summary") or "").strip()
    if not summary:
        return "This week in healthcare AI."
    if len(summary) <= 130:
        return summary
    cut = summary[:130].rsplit(" ", 1)[0]
    return f"{cut}\u2026"


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
    card_link_url = _with_utm(landing_url or deep_dive_url, content="card")
    footer_deep_dive = _with_utm(landing_url or deep_dive_url, content="footer_cta")
    subscribe_url = _with_utm(f"{LANDING_PAGE_URL}/subscribe", content="forwarded_subscribe")
    forward_url = (
        f"mailto:?subject={format_subject_line(curated.get('week_range', '')).replace(' ', '%20')}"
        f"&body=Thought%20you'd%20find%20this%20valuable%3A%20{footer_deep_dive}"
    )

    html = template.render(
        week_range=curated.get("week_range", ""),
        editorial_summary=curated.get("editorial_summary", ""),
        preheader=_build_preheader(curated),
        tldr=_build_tldr(curated),
        top_stories=sections.get("top_stories", []),
        vbc_watch=sections.get("vbc_watch", []),
        ma_partnerships=ma_partnerships,
        consulting_intelligence=sections.get("consulting_intelligence", []),
        did_you_know=sections.get("did_you_know", []),
        trend_signal=trend_signal,
        deep_dive_url=card_link_url,
        footer_deep_dive_url=footer_deep_dive,
        landing_url=landing_url,
        subscribe_url=subscribe_url,
        forward_url=forward_url,
    )
    return html
