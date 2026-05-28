# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workflow Rules

Before building anything, follow this staged workflow (from Claude.md):

- **Stage 1 — Clarify**: Ask about use case, inputs/outputs, AI model, evaluation, constraints, data
- **Stage 2 — Roadmap**: Milestones, tech stack with reasons, data pipeline, evaluation, deployment
- **Stage 3 — Execution Plan**: List every function (name, purpose, I/O, dependencies) — wait for approval
- **Stage 4 — Build fn by fn**: One function at a time; explain what, why, how to verify, where reused
- **Stage 5 — Interview Docs**: Design decisions, Gen AI components, prompt engineering, error handling, scaling

**Debugging rules**: Never abandon a working approach on first failure. Give ONE best solution. Do not change the plan mid-way. Cross-verify before answering.

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

Django backend API with no frontend — consumed by an external Everclif website (`/Users/ashish/Downloads/graphlive/index.html`) via `POST /api/generate/`.

**Request/response flow:**
```
External frontend (index.html)
  → POST /api/generate/ { sitemap_url }
  → fetch_sitemap()      # parses sitemap XML, max 100 URLs
  → categorize_urls()    # buckets URLs into blog/features/compare/solutions by path pattern
  → extract_all_links()  # visits each page (threaded, 10 workers), strips nav/header/footer
  → build_graph_data()   # produces D3-compatible { nodes[], links[] }
  → generate_html()      # injects data into self-contained D3.js HTML string
  → JSON { html, stats }
```

**Key design decisions:**
- CORS is handled manually via `cors_response()` in `views.py` — every response must be wrapped with it. Do not rely on `django-cors-headers` middleware (it failed on Render free tier).
- API is `@csrf_exempt` because it is called cross-origin from the Everclif frontend.
- `generate_html()` returns a full standalone HTML page injected into an `<iframe>` on the frontend — required for D3.js scripts to execute correctly.
- No database models — the entire pipeline is stateless.

## Scraper Utils Pipeline

| File | Function | Notes |
|------|----------|-------|
| `sitemap.py` | `fetch_sitemap(sitemap_url)` | Handles nested sitemap indexes recursively; hard cap of 100 URLs |
| `categorizer.py` | `categorize_urls(urls)` | Pattern matching on URL path; edit `PATTERNS` dict to add new categories |
| `extractor.py` | `extract_links_from_page()` + `extract_all_links()` | Strips `<nav>/<header>/<footer>` to avoid nav link pollution; `ThreadPoolExecutor(max_workers=10)` |
| `graph_builder.py` | `build_graph_data(categorized, links)` | Auto-generates labels from URL slugs |
| `html_generator.py` | `generate_html(graph_data, domain)` | f-string template; uses `{{}}` to escape JS braces; computes orphan/inbound/outbound counts in Python |

## Deployment

- **Render** (free tier): auto-deploys from `ashish047r/linkgraph` on push to `main`
- Start command: `gunicorn linkgraph.wsgi --bind 0.0.0.0:$PORT`
- Live URL: `https://linkgraph.onrender.com`
- Free tier sleeps after 15 min inactivity — first request takes ~50s to wake

## Testing the Pipeline

```python
# In manage.py shell
from scraper.utils.sitemap import fetch_sitemap
from scraper.utils.categorizer import categorize_urls
from scraper.utils.extractor import extract_all_links
from scraper.utils.graph_builder import build_graph_data
from scraper.utils.html_generator import generate_html
from pathlib import Path

urls = fetch_sitemap('https://recharm.com/sitemap.xml')
categorized = categorize_urls(urls)
links = extract_all_links(categorized)
graph = build_graph_data(categorized, links)
html = generate_html(graph, 'recharm.com')
Path('/Users/ashish/Desktop/test_graph.html').write_text(html)
```
