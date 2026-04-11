# Site-Wide Search + Outlook Classic Email Fix

**Date:** 2026-04-10
**Status:** Draft — ready for implementation planning
**Author:** Greg + Claude

## Summary

Two independent improvements to Healthcare AI Weekly:

1. **Site-wide search** — instant dropdown in the top nav plus a full-page `/search` with filters, covering weekly issue stories, bulletins, consulting intelligence, and learn topics. Zero external dependencies; client-side MiniSearch over a build-time static index.
2. **Outlook Classic email fix** — rewrite the email template so it renders correctly in Outlook Classic on Windows (Word rendering engine). Current template uses div-based cards with `border-radius`, `box-shadow`, and `min-height`, which Word strips or ignores, causing broken layout for colleagues on Outlook Classic.

Both are motivated by real user feedback: Greg wants search at the top of the site for fast cross-content lookup, and a colleague viewing the Friday newsletter in Outlook Classic reported a "terrible" rendering.

## Non-goals

- **No third-party search service.** No Algolia, no Elasticsearch, no hosted search. Static index only.
- **No CMS or dynamic content layer.** Content stays as static JSON files in `/content/`.
- **No email platform migration.** Still sending via `gws` CLI / Gmail MCP. No Mailchimp, no SendGrid.
- **No support for Outlook 2007/2010.** Target is Outlook Classic 2016+ on Windows, which is the corporate default.
- **No redesign of the current "liquid glass" site aesthetic.** Search UI must match existing visual language.

---

## Feature 1 — Site-Wide Search

### 1.1 Architecture

```
BUILD TIME (runs during `next build`):
  content/issues/*/data.json       ──┐
  content/bulletins/*.json         ──┼──> scripts/build-search-index.ts
  content/consulting-intelligence/*.json ──┤                │
  content/learn/*.json             ──┘                     ▼
                                                    public/search-index.json

RUNTIME (browser):
  Page loads ──> nav shows 🔍 button
  User focuses search ──> lazy-load /search-index.json (cached after first load)
  User types ──> MiniSearch runs in-memory ──> dropdown shows top 8 grouped
  User hits Enter or clicks "See all results" ──> /search?q=... full-page view
```

### 1.2 Index record schema

One flat schema for all content types:

```ts
interface SearchRecord {
  id: string;            // unique: "issue:2026-04-10:top:0", "bulletin:anthropic-mythos", etc.
  type: "issue_story" | "bulletin" | "consulting" | "learn";
  title: string;         // headline, story title, topic title — boosted highest
  body: string;          // email_summary / summary / so_what / description
  url: string;           // where clicking takes the user
  date: string;          // ISO 8601; used for sort and date-range filter
  tags: string[];        // firm name, section name, relevance tag, custom tags
  section?: string;      // for issue_story: "What Matters This Week", "VBC", etc.
  source?: string;       // publisher name for issue_story/bulletin
}
```

**URL routing for each record type:**

| Type | URL pattern | Example |
|---|---|---|
| `issue_story` | `/?issue=YYYY-MM-DD#<section-anchor>` (existing pattern) | `/?issue=2026-04-10#top-stories` |
| `bulletin` | `/bulletins` (existing list page; anchor to slug) | `/bulletins#anthropic-mythos` |
| `consulting` | `/` (homepage consulting cards; anchor to slug) | `/#consulting-accenture-palantir` |
| `learn` | `/learn/<slug>` (existing topic page) | `/learn/ai-agents-101` |

Bulletins and consulting currently live on parent pages (no per-item pages) — add scroll-to-anchor behavior for search results. This requires a small edit to `src/app/bulletin-cards.tsx` and `src/app/consulting-cards.tsx` to wrap each card in an element with `id={slug}` so the browser scrolls to the right card when the URL contains a hash. Also add a subtle highlight effect (class toggled for ~2 seconds) when the hash matches, so users know which card the search brought them to. No need for dedicated per-item routes yet; we can add them later if desired.

### 1.3 Index builder

**New file:** `scripts/build-search-index.ts`

**Responsibilities:**
1. Read all JSON files from the four content directories.
2. For each issue, flatten stories across `top_stories`, `vbc_watch`, `ma_partnerships`, `consulting_intelligence`, `did_you_know` into individual records.
3. For bulletins, one record per file.
4. For consulting-intelligence, one record per file (skip `manifest.json`).
5. For learn topics, one record per topic (title + description; do NOT index quiz questions — too noisy).
6. Strip em dashes from all text (existing project rule).
7. Write combined array to `public/search-index.json`.

**How it runs:**
- Add as a `predev` and `prebuild` hook in `package.json` so it runs automatically.
- Standalone script invokable via `npm run build:search-index` for manual rebuild.

**Index size budget:** Target under 500 KB uncompressed for current content (~4 issues × 14 stories + 1 bulletin + 22 consulting + 4 learn = ~83 records). MiniSearch's serialized form is compact; expected actual size is well under budget.

### 1.4 Search UI components

**New files:**

| File | Purpose |
|---|---|
| `src/components/search/search-provider.tsx` | React context that lazy-loads `search-index.json`, initializes MiniSearch, exposes `search(query, filters)` |
| `src/components/search/search-button.tsx` | The nav-bar search trigger (icon + "Search" label, `⌘K` hint on hover) |
| `src/components/search/search-dropdown.tsx` | Instant-results dropdown shown under the nav when active; closes on outside click and `Esc` |
| `src/components/search/search-result-card.tsx` | Shared card used in dropdown and on the full-page results view |
| `src/app/search/page.tsx` | Full-page `/search?q=...` route with filter sidebar |

**Edit existing:**
- `src/components/nav.tsx` — add search button between brand and links on desktop; collapse brand to icon on mobile to make room.
- `src/app/layout.tsx` — wrap children in `<SearchProvider>`.

### 1.5 Interaction model

**Nav-bar search button:**
- Shows a magnifying-glass icon and the word "Search" (desktop) or icon only (mobile).
- Displays `⌘K` / `Ctrl+K` keyboard shortcut hint.
- Clicking or pressing the shortcut from anywhere on the site opens an overlay with a focused text input.

**Instant dropdown (as user types):**
- Fires on every keystroke after the query reaches 2+ characters.
- Debounced 120 ms.
- Shows up to 8 results grouped by type with a small section header for each group: "Weekly Issues", "Bulletins", "Consulting Intelligence", "Learn".
- Each result shows: type badge, title (with matched terms highlighted), 1-line body snippet, date.
- Last row: "See all N results →" link to `/search?q=...`.
- Empty state (no query): recently-added content across all types (top 5).
- Zero-results state: "No matches for 'X'. Try different keywords or check spelling."

**Full-page `/search?q=...`:**
- Uses existing liquid-glass page shell (ambient background, nav).
- Hero: large search input pre-filled with `q`.
- Filter sidebar (left on desktop, drawer on mobile):
  - Content type (checkboxes: Issues, Bulletins, Consulting, Learn)
  - Date range (preset: Last week, Last month, Last 3 months, All time)
  - Consulting firm (multi-select, shown only when Consulting is selected)
  - Sort: Relevance (default), Newest, Oldest
- Results: glass cards, same `SearchResultCard` component as dropdown but larger and with more body text.
- URL reflects state: `/search?q=diabetes&type=issue_story&type=consulting&firm=mckinsey&sort=relevance`
- No server-side rendering of results — all filtering happens client-side from the loaded index.

### 1.6 Visual design

- Match the existing glass-card aesthetic.
- Search dropdown: `rgba(255, 255, 255, 0.85)` background, `backdrop-filter: blur(24px)`, 14 px border radius, subtle elevation shadow, same as existing glass cards.
- Primary accent for highlighted query matches: `#0284C7` (existing blue).
- Type badges use existing consulting-card color conventions.
- `⌘K` shortcut uses the existing mono font stack.

### 1.7 Dependencies

- Add `minisearch` to `package.json` (~7 KB gzipped, zero sub-dependencies).
- No other new libraries. Use existing Tailwind + shadcn/ui primitives where possible.

---

## Feature 2 — Outlook Classic Email Fix

### 2.1 Root cause

Outlook Classic on Windows uses **Microsoft Word** as its HTML rendering engine (not a browser engine). This means:

- `<div>` elements have inconsistent box behavior.
- `border-radius` is silently dropped.
- `box-shadow` is silently dropped.
- `min-height` is ignored — cards collapse to content height, producing ragged grids.
- Background colors on nested divs sometimes drop.
- `border-spacing` on tables works inconsistently.
- Modern CSS (flexbox, grid) is entirely unsupported.
- Inline styles are respected (mostly), but certain properties need explicit attribute equivalents (`width=`, `height=`, `cellpadding=`, `cellspacing=`).
- VML (Microsoft's vector markup from Office) DOES work inside `<!--[if mso]>...<![endif]-->` conditionals, and is the standard way to get rounded corners and buttons in Outlook Classic.

The current template (`pipeline/generator/templates/email_template.html`) hits every one of these pitfalls: div-based card wrappers, `border-radius`, `box-shadow`, `min-height:220px`, and inconsistent widths.

### 2.2 Solution — hybrid table scaffolding + VML for Outlook

**Approach:**

1. **Outer layout:** wrap the entire email body in a 600 px centered table (standard bulletproof pattern). All major sections nest inside `<td>` cells of that outer table.
2. **Section boxes:** each section (What Matters, VBC, M&A, Consulting, DYK) becomes its own nested table with explicit `width="600"` and `cellpadding`/`cellspacing`. Replace the current `<div class="section-box">` divs entirely.
3. **Story cards:** replace div-based cards with `<table>` cells. Use `cellpadding="18"` on the card table instead of CSS `padding`. Use explicit `height=` attribute (with CSS `height:` as backup) instead of `min-height`, so all cards in a row match.
4. **Rounded corners in Outlook:** wrap section boxes and cards in `<!--[if mso]><v:roundrect>...<![endif]-->` VML blocks. Modern clients see the underlying CSS `border-radius`, Outlook Classic sees the VML rounded rect.
5. **Drop `box-shadow` entirely.** It never worked in Outlook Classic and adds nothing. Section differentiation comes from borders + colored top rules.
6. **Explicit dimensions everywhere.** Every `<td>` gets `width=`, every card gets `height=`.
7. **`mso-line-height-rule: exactly;`** on all text containers to stop Word's line-spacing from bloating rows.
8. **Bulletproof buttons:** the "Read the Full Deep Dive" footer button gets a VML `<v:roundrect>` fallback too, using the standard Campaign Monitor buttons.cm pattern.

### 2.3 Template structure (after rewrite)

```html
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "...">
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:v="urn:schemas-microsoft-com:vml"
      xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <!-- existing meta tags + MSO conditional for font -->
</head>
<body>
  <!-- Outer 100% wrapper table -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
    <tr>
      <td align="center" style="padding:0;">

        <!-- Main 600px container table -->
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0">
          <tr><td><!-- Header (h1 + week range + editorial summary) --></td></tr>

          <!-- Section: What Matters -->
          <tr><td>
            {% if top_stories %}
              {{ section_header("What Matters This Week", "Click any headline for the full analysis") }}
              {{ card_grid(top_stories, "top-stories", has_badges=true) }}
            {% endif %}
          </td></tr>

          <!-- ... other sections follow the same pattern ... -->

          <tr><td><!-- Trend Watch --></td></tr>
          <tr><td><!-- Footer CTA (bulletproof button) --></td></tr>
        </table>

      </td>
    </tr>
  </table>
</body>
</html>
```

### 2.4 Jinja macros to add/rewrite

| Macro | Purpose |
|---|---|
| `section_header(title, caption)` | Renders the blue-underlined section title row |
| `card_grid(stories, anchor, has_badges)` | Renders a 2-column, N-row grid of story cards (handles 2, 3, and 4 card cases) |
| `story_card(story, anchor, has_badge)` | Single card with VML roundrect fallback, explicit height, forward-safe link pattern |
| `dyk_card(item, anchor)` | Did-You-Know variant (shorter, no badge) |
| `bulletproof_button(url, label)` | Footer CTA with VML roundrect for Outlook |

### 2.5 Preserved project rules

- **No em dashes anywhere.** Continue stripping in post-processing.
- **Aptos font stack.** Keep existing `@font-face` + MSO font family.
- **Links only on headlines and "Read more" text.** Do NOT wrap entire cards in `<a>` tags (Outlook colors all wrapped text blue on forward).
- **Light mode only** (white body, dark text).
- **Email cards link to landing page** with `?issue=YYYY-MM-DD` param, not directly to deep-dive.
- **Remove "Guidehouse" from footer byline** — the current footer reads "Healthcare AI Weekly by Greg Harrison, Guidehouse" which violates the project rule `no Guidehouse in bylines/footers`. Since we're touching the footer line anyway, fix it: change to "Healthcare AI Weekly by Greg Harrison".

### 2.6 Dependencies

- No new dependencies. Pure template edits in `pipeline/generator/templates/email_template.html`.

---

## Feature 3 — Email Preview Workflow

Needed to validate the email fix before shipping. Two layers:

### 3.1 Local browser preview (fast loop)

**New file:** `pipeline/generator/preview_email.py`

**Behavior:**
1. Accepts a `--date YYYY-MM-DD` argument.
2. Loads that issue's curated data (or dummy data if the date doesn't exist).
3. Renders the Jinja template to a temp file `/tmp/email_preview.html`.
4. Opens it in the default browser via `webbrowser.open()`.

**Purpose:** instant visual check in Chrome/Safari. Catches layout regressions in modern clients. Does NOT validate Outlook Classic — the Litmus step below handles that.

**Usage:**
```bash
python pipeline/generator/preview_email.py --date 2026-04-10
```

### 3.2 Litmus / Email on Acid validation (ground truth)

**Process:**
1. Run `preview_email.py` to generate the HTML file.
2. Copy the HTML contents.
3. Paste into Litmus (or Email on Acid) on the 7-day free trial.
4. Inspect the Outlook Classic 2016 / 2019 / 365 renders.
5. Iterate template fixes until all Outlook Classic renders are acceptable.
6. Final sanity check: send the fixed email to Greg's work inbox (New Outlook) AND to the colleague who flagged the original issue (Outlook Classic). Confirm both approve before merging.

**Not automated.** Manual copy-paste loop is fine for a one-time template fix. If the template changes significantly again in the future, we can automate via Litmus API.

---

## File-by-file change list

### New files

- `scripts/build-search-index.ts` — index builder
- `src/components/search/search-provider.tsx`
- `src/components/search/search-button.tsx`
- `src/components/search/search-dropdown.tsx`
- `src/components/search/search-result-card.tsx`
- `src/app/search/page.tsx`
- `pipeline/generator/preview_email.py`

### Edited files

- `package.json` — add `minisearch` dep; add `predev` and `prebuild` scripts calling the index builder
- `src/components/nav.tsx` — add search button; responsive collapse on mobile
- `src/app/layout.tsx` — wrap children in `SearchProvider`
- `src/lib/types.ts` — add `SearchRecord` interface
- `src/app/bulletin-cards.tsx` — add `id={slug}` to each card wrapper; add hash-based highlight effect
- `src/app/consulting-cards.tsx` — add `id={slug}` to each card wrapper; add hash-based highlight effect
- `pipeline/generator/templates/email_template.html` — full rewrite to table-based layout with VML fallbacks; drop "Guidehouse" from footer

### Files to leave alone

- All content JSON files
- All pipeline Python (collector, curator, bulletin, learning) — the email template rewrite is isolated to the generator templates dir
- All existing page routes except nav, layout, and the new `/search` route
- Supabase schema

---

## Testing strategy

### Search

1. **Build-time index validation:** `scripts/build-search-index.ts` logs record count per type and total index size. If index > 800 KB uncompressed, fail the build with a warning.
2. **Manual smoke tests:** after implementation, try representative queries:
   - `"diabetes"` (should match issue stories)
   - `"mckinsey"` (should match consulting intelligence)
   - `"agent"` (should match learn topics)
   - Empty query (dropdown shows recent items)
   - Gibberish (`"xzqwjk"`) (zero-results state)
3. **Filter tests on `/search` page:**
   - Toggle each content-type checkbox, confirm result count updates
   - Change date range, confirm stale results drop out
   - Change sort order, confirm order changes
4. **Keyboard tests:** `⌘K` from anywhere opens search; `Esc` closes; arrow keys navigate dropdown; Enter selects.
5. **Mobile:** nav collapses cleanly; dropdown covers viewport width; filters become a drawer on `/search`.

### Email

1. **Local render check:** `preview_email.py` renders without Jinja errors; opens in browser; modern layout matches current live email exactly.
2. **Litmus render check:** paste HTML into Litmus; confirm acceptable rendering in:
   - Outlook Classic 2016 (Windows)
   - Outlook Classic 2019 (Windows)
   - Outlook Classic 365 (Windows)
   - New Outlook for Windows
   - Outlook for Mac
   - Gmail web
   - Apple Mail iOS
3. **Real-world confirmation:** send fixed email to Greg's work inbox AND the colleague who flagged the original issue; both must approve before merging to main.
4. **No regression in the automated pipeline:** run `python pipeline.py --date <test-date> --skip-send` and confirm generator stage produces valid HTML.

---

## Rollout

1. All work on a feature branch: `feature/search-and-outlook-fix`.
2. Implement search first (lower risk, no user-visible email path changes).
3. Merge search to main after approval; let it deploy to Vercel.
4. Implement email template rewrite on the same branch (or a fresh one).
5. Hold email changes until Litmus validation passes AND colleague confirms.
6. Merge email changes; next Friday trigger uses the new template automatically.
7. Monitor first Friday send — if anything looks off, `git revert` the template commit.

## Open questions (none blocking)

None — all decisions made inline. The one piece that could change during implementation is index size; if it blows past 500 KB we'll switch to splitting the index by type and lazy-loading per content type, but this is unlikely given current content volume.

## Appendix — why not alternatives

- **Algolia:** overkill for current volume and adds an external dependency. Revisit if content grows past ~5000 records.
- **Option 1 full table rewrite:** overkill for Outlook 2016+; a hybrid with VML is just as reliable with a single source of truth.
- **Option 2 dual-template MSO overrides:** maintenance burden doubles forever; rejected.
- **Server-side search API route:** loses instant-dropdown feel on Vercel cold starts; static index is strictly faster.
