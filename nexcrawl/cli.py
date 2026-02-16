"""nexcrawl CLI — command-line interface powered by Click + Rich."""

from __future__ import annotations

import asyncio
import json
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from nexcrawl.models import (
    CrawlRequest,
    ExtractRequest,
    OutputFormat,
    ScrapeRequest,
)

console = Console()


def _run(coro):
    """Run an async coroutine from sync Click commands."""
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="nexcrawl")
def cli():
    """nexcrawl — crawl, scrape, and extract data from any website."""


# ---------------------------------------------------------------------------
# scrape
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("url")
@click.option("-f", "--format", "fmt", type=click.Choice(["markdown", "html", "text", "raw_html"]), default="markdown", help="Output format")
@click.option("--browser", is_flag=True, help="Use headless browser for JS rendering")
@click.option("--wait", default=0, type=int, help="Extra ms to wait after page load")
@click.option("--no-main", is_flag=True, help="Include full page (don't strip boilerplate)")
@click.option("-o", "--output", type=click.Path(), default=None, help="Save output to file")
def scrape(url: str, fmt: str, browser: bool, wait: int, no_main: bool, output: str | None):
    """Scrape a single URL."""
    from nexcrawl.scraper import scrape as do_scrape

    request = ScrapeRequest(
        url=url,
        formats=[OutputFormat(fmt)],
        use_browser=browser,
        wait_for=wait,
        only_main_content=not no_main,
    )

    with console.status("[bold green]Scraping…"):
        result = _run(do_scrape(request))

    if result.error:
        console.print(f"[bold red]Error:[/] {result.error}")
        sys.exit(1)

    content = getattr(result, fmt) or ""

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(content)
        console.print(f"[green]Saved to {output}")
    else:
        if fmt == "markdown":
            console.print(Panel(content, title=result.metadata.get("title", url), border_style="blue"))
        elif fmt in ("html", "raw_html"):
            console.print(Syntax(content[:5000], "html", theme="monokai"))
        else:
            console.print(content)

    # Show metadata
    meta_table = Table(title="Metadata", show_lines=True)
    meta_table.add_column("Key", style="cyan")
    meta_table.add_column("Value")
    for k, v in result.metadata.items():
        meta_table.add_row(k, str(v))
    console.print(meta_table)


# ---------------------------------------------------------------------------
# crawl
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("url")
@click.option("-d", "--depth", default=2, type=int, help="Max crawl depth")
@click.option("-n", "--max-pages", default=50, type=int, help="Max pages to crawl")
@click.option("-f", "--format", "fmt", type=click.Choice(["markdown", "html", "text"]), default="markdown")
@click.option("--browser", is_flag=True, help="Use headless browser")
@click.option("-o", "--output", type=click.Path(), default=None, help="Save JSON results to file")
def crawl(url: str, depth: int, max_pages: int, fmt: str, browser: bool, output: str | None):
    """Crawl a website starting from URL."""
    from nexcrawl.crawler import crawl_sync

    request = CrawlRequest(
        url=url,
        max_depth=depth,
        max_pages=max_pages,
        formats=[OutputFormat(fmt)],
        use_browser=browser,
    )

    with console.status("[bold green]Crawling…"):
        result = _run(crawl_sync(request))

    if result.error:
        console.print(f"[bold red]Error:[/] {result.error}")
        sys.exit(1)

    console.print(f"[green]Crawled {result.completed} pages (status: {result.status.value})")

    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, ensure_ascii=False)
        console.print(f"[green]Results saved to {output}")
    else:
        for page in result.pages:
            title = page.metadata.get("title", page.url)
            console.print(Panel(f"[bold]{title}[/]\n{page.url}", border_style="blue"))
            content = getattr(page, fmt, None) or ""
            console.print(content[:500] + ("…" if len(content) > 500 else ""))
            console.print()


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("url")
@click.option("-s", "--schema", required=True, help="JSON schema string or @filepath")
@click.option("--browser", is_flag=True, help="Use headless browser")
@click.option("-o", "--output", type=click.Path(), default=None, help="Save JSON output to file")
def extract(url: str, schema: str, browser: bool, output: str | None):
    """Extract structured data from a URL using a selector schema."""
    from nexcrawl.extractor import extract as do_extract

    # Load schema
    if schema.startswith("@"):
        with open(schema[1:], encoding="utf-8") as f:
            schema_dict = json.load(f)
    else:
        schema_dict = json.loads(schema)

    request = ExtractRequest(url=url, schema=schema_dict, use_browser=browser)

    with console.status("[bold green]Extracting…"):
        result = _run(do_extract(request))

    if result.error:
        console.print(f"[bold red]Error:[/] {result.error}")
        sys.exit(1)

    formatted = json.dumps(result.data, indent=2, ensure_ascii=False)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(formatted)
        console.print(f"[green]Saved to {output}")
    else:
        console.print(Syntax(formatted, "json", theme="monokai"))


# ---------------------------------------------------------------------------
# serve (run the API server)
# ---------------------------------------------------------------------------

@cli.command()
@click.option("-h", "--host", default="0.0.0.0", help="Bind host")
@click.option("-p", "--port", default=8000, type=int, help="Bind port")
@click.option("--reload", "do_reload", is_flag=True, help="Auto-reload on code changes")
def serve(host: str, port: int, do_reload: bool):
    """Start the nexcrawl API server."""
    import uvicorn

    console.print(f"[bold green]Starting nexcrawl API on {host}:{port}")
    uvicorn.run("nexcrawl.api:app", host=host, port=port, reload=do_reload)


if __name__ == "__main__":
    cli()
