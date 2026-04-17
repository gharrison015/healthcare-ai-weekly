# Healthcare AI Weekly

> [!tip] Navigation
> [[../CLAUDE|Content]]

Automated weekly newsletter pipeline that curates AI-in-healthcare news and delivers it as a card-based HTML email, a liquid glass deep-dive page on Vercel, and a LinkedIn seed file.

## Tech Stack

- **Frontend/Archive**: Next.js 16, React 19, Tailwind, shadcn/ui, MiniSearch
- **Pipeline**: Python (`pipeline/`) -- collector, curator, generator, distributor stages
- **Bulletin Monitor**: Multi-source breaking news monitor between weekly issues
- **Data**: Supabase (subscriber accounts), SQLite (`accounts.db`)
- **Hosting**: Vercel at https://healthcareaibrief.com
- **GitHub**: `gharrison015/healthcare-ai-weekly` (public)

## Key Paths

- `pipeline/` -- Full Python pipeline: collector, curator, generator, distributor, learning, bulletin
- `src/` -- Next.js archive site
- `content/` -- Newsletter issue data
- `scripts/` -- Build helpers (search index)

## Automation

- **Friday newsletter**: GitHub Actions (`.github/workflows/weekly-newsletter.yml`), Fridays 5am ET
- **Bulletin monitor**: Anthropic cloud trigger `trig_01Jr3zP4zvYRnvKo2MmHAeto`, every 4 hours weekdays

## Integration

Newsletter research seeds LinkedIn content via `linkedin_seed.py` in the pipeline.
