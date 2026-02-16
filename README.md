# nexcrawl 🔥

A powerful Python web scraper inspired by [Firecrawl](https://firecrawl.dev). Crawl, scrape, and extract structured data from any website — with optional JavaScript rendering.

## Features

| Feature | Description |
|---|---|
| **Single-page scrape** | Fetch any URL → clean Markdown, HTML, or plain text |
| **Site crawl** | BFS crawl following same-domain links with depth/page limits |
| **Structured extraction** | Pull data using CSS selectors, XPath, or attribute selectors |
| **JS rendering** | Headless Chromium via Playwright for SPA / dynamic pages |
| **REST API** | FastAPI server with `/v1/scrape`, `/v1/crawl`, `/v1/extract` |
| **CLI** | Full command-line interface (`nexcrawl scrape`, `crawl`, `extract`, `serve`) |
| **Rate limiting** | Per-domain async rate limiter (configurable RPS) |
| **Auto retries** | Exponential back-off retries on transient failures |
| **Content cleaning** | Readability-based main-content extraction, boilerplate stripping |
| **Metadata** | Title, description, OG image, canonical URL, language |

---

## Quick Start

### 1. Install

```bash
# Clone & install
git clone <repo-url> && cd nexcrawl-pyhton
pip install -e .

# Install Playwright browsers (needed only for JS rendering)
playwright install chromium
```

### 2. CLI Usage

```bash
# Scrape a page to markdown
nexcrawl scrape https://example.com

# Scrape with JS rendering
nexcrawl scrape https://example.com --browser

# Save output to file
nexcrawl scrape https://example.com -o page.md

# Crawl a site (max 20 pages, depth 2)
nexcrawl crawl https://example.com -n 20 -d 2

# Extract structured data
nexcrawl extract https://news.ycombinator.com -s '{"title": "a.titlelink", "scores": {"_list": true, "selector": ".score"}}'

# Start the API server
nexcrawl serve --port 8000
```

### 3. API Usage

Start the server:

```bash
nexcrawl serve
```

#### Scrape

```bash
curl -X POST http://localhost:8000/v1/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "formats": ["markdown"]
  }'
```

#### Crawl

```bash
curl -X POST http://localhost:8000/v1/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "max_depth": 2,
    "max_pages": 10,
    "formats": ["markdown"]
  }'
```

#### Extract

```bash
curl -X POST http://localhost:8000/v1/extract \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://news.ycombinator.com",
    "schema": {
      "title": "title",
      "links": {"_list": true, "selector": "a.titlelink"}
    }
  }'
```

### 4. Python SDK Usage

```python
import asyncio
from nexcrawl.models import ScrapeRequest, OutputFormat
from nexcrawl.scraper import scrape

async def main():
    result = await scrape(ScrapeRequest(
        url="https://example.com",
        formats=[OutputFormat.markdown],
    ))
    print(result.markdown)

asyncio.run(main())
```

---

## API Reference

### `POST /v1/scrape`

| Field | Type | Default | Description |
|---|---|---|---|
| `url` | string | *required* | URL to scrape |
| `formats` | list | `["markdown"]` | `markdown`, `html`, `text`, `raw_html` |
| `use_browser` | bool | `false` | Force headless browser |
| `wait_for` | int | `0` | Extra ms to wait (implies browser) |
| `only_main_content` | bool | `true` | Strip navs/footers/boilerplate |
| `include_tags` | list | `null` | CSS selectors to include |
| `exclude_tags` | list | `null` | CSS selectors to exclude |
| `headers` | object | `null` | Custom request headers |

### `POST /v1/crawl`

| Field | Type | Default | Description |
|---|---|---|---|
| `url` | string | *required* | Starting URL |
| `max_depth` | int | `2` | Max link-follow depth |
| `max_pages` | int | `50` | Max pages to crawl |
| `formats` | list | `["markdown"]` | Output formats |
| `include_paths` | list | `null` | Glob patterns for allowed paths |
| `exclude_paths` | list | `null` | Glob patterns to skip |

### `POST /v1/extract`

| Field | Type | Default | Description |
|---|---|---|---|
| `url` | string | *required* | URL to extract from |
| `schema` | object | *required* | Selector schema (see below) |
| `use_browser` | bool | `false` | Force headless browser |

#### Schema Syntax

```json
{
  "title": "h1",                                // CSS → first match text
  "prices": {"_list": true, "selector": ".price"}, // CSS → all matches
  "author": "attr::.author::data-name",         // Attribute value
  "items": "xpath:://div[@class='item']/text()" // XPath
}
```

---

## Project Structure

```
nexcrawl/
├── __init__.py           # Package init
├── api.py                # FastAPI REST API
├── browser.py            # Playwright headless browser
├── cli.py                # Click CLI
├── config.py             # Global configuration
├── crawler.py            # Site crawler (BFS)
├── extractor.py          # Structured data extraction
├── markdown_converter.py # HTML → Markdown
├── models.py             # Pydantic models
└── scraper.py            # Core single-page scraper
```

## Configuration

Edit `nexcrawl/config.py` or set values programmatically:

```python
from nexcrawl.config import config

config.rate_limit = 5.0       # 5 requests/sec
config.max_retries = 5
config.user_agent = "MyBot/1.0"
```

## License

MIT
