# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Rules

**Debugging rules**: Never abandon a working approach on first failure. Give ONE best solution. Do not change the plan mid-way. Cross-verify before answering.

Before making any graph UI change, confirm it belongs in `html_generator.py` (backend). `index.html` is only relevant for the input form, progress bar, iframe injection, and the Railway API URL — not for graph appearance, buttons, filters, or watermarks.

---

## Development Commands

```bash
# Activate virtualenv (always required first)
source venv/bin/activate

# Run dev server (use 8001 if 8000 is busy)
python manage.py runserver 8001

# Apply migrations
python manage.py migrate

# Open Django shell for pipeline testing
python manage.py shell
```

## Architecture

Django backend API with no frontend — consumed by the Everclif website (`/Users/ashish/Downloads/graphlive/index.html`) via `POST /api/generate/`.

**Request/response flow:**
```
External frontend (index.html)
  → POST /api/generate/ { sitemap_url }
  → fetch_sitemap()      # parses sitemap XML recursively, max 100 URLs
  → categorize_urls()    # returns ALL urls as {'pages': [...]} — no filtering
  → extract_all_links()  # visits each page (threaded, 10 workers), strips nav/header/footer
  → build_graph_data()   # produces D3-compatible { nodes[], links[] }
  → generate_html()      # injects data into self-contained D3.js HTML string
  → JSON { html, stats }
```

**Key design decisions:**
- CORS is handled manually via `cors_response()` in `views.py` — every response must be wrapped with it. Do not rely on `django-cors-headers` middleware (it failed previously).
- API is `@csrf_exempt` because it is called cross-origin from the Everclif frontend.
- `generate_html()` returns a full standalone HTML page injected into an `<iframe>` on the frontend — required for D3.js scripts to execute correctly. All graph UI (buttons, filters, watermark, colors, node sizing) lives here.
- No database models — the entire pipeline is stateless.
- `categorize_urls()` is a no-op passthrough — it just wraps all URLs in `{'pages': [...]}`. Categorization by URL slug was intentionally removed.

## Scraper Utils Pipeline

| File | Function | Notes |
|------|----------|-------|
| `sitemap.py` | `fetch_sitemap(sitemap_url)` | Handles nested sitemap indexes recursively; hard cap of 100 URLs |
| `categorizer.py` | `categorize_urls(urls)` | Returns `{'pages': list(urls)}` — no filtering, all URLs included |
| `extractor.py` | `extract_links_from_page()` + `extract_all_links()` | Strips `<nav>/<header>/<footer>` to avoid nav link pollution; `ThreadPoolExecutor(max_workers=10)` |
| `graph_builder.py` | `build_graph_data(categorized, links)` | Auto-generates labels from URL slugs; no category coloring |
| `html_generator.py` | `generate_html(graph_data, domain)` | f-string template; uses `{{}}` to escape JS braces; computes orphan/inbound/outbound counts in Python before injection |

## Deployment

- **Railway** (Hobby plan): auto-deploys from `ashisheverclif/linkgraph` on push to `main`
- Start command: `gunicorn linkgraph.wsgi --bind 0.0.0.0:$PORT --timeout 120`
- Live URL: `https://web-production-005a8.up.railway.app`
- `--timeout 120` is required — scraping 100 pages exceeds gunicorn's default 30s timeout

## Testing the Pipeline

```python
# In manage.py shell
from scraper.utils.sitemap import fetch_sitemap
from scraper.utils.categorizer import categorize_urls
from scraper.utils.extractor import extract_all_links
from scraper.utils.graph_builder import build_graph_data
from scraper.utils.html_generator import generate_html
from pathlib import Path

urls = fetch_sitemap('https://piaxis.ai/sitemap_index.xml')
categorized = categorize_urls(urls)
links = extract_all_links(categorized)
graph = build_graph_data(categorized, links)
html = generate_html(graph, 'piaxis.ai')
Path('/Users/ashish/Desktop/test_graph.html').write_text(html)
```
