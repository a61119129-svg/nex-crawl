"""Site crawler — follow links within the same domain up to max depth/pages."""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import uuid
from urllib.parse import urljoin, urlparse

from aiolimiter import AsyncLimiter
from bs4 import BeautifulSoup

from nexcrawl.config import config
from nexcrawl.models import (
    CrawlRequest,
    CrawlResult,
    CrawlStatus,
    OutputFormat,
    ScrapeRequest,
    ScrapeResult,
)
from nexcrawl.scraper import scrape

logger = logging.getLogger(__name__)

# In-memory store for crawl jobs (swap for Redis/DB in production)
_jobs: dict[str, CrawlResult] = {}


def _same_domain(base: str, candidate: str) -> bool:
    return urlparse(base).netloc == urlparse(candidate).netloc


def _matches_globs(path: str, patterns: list[str] | None) -> bool:
    if not patterns:
        return True
    return any(fnmatch.fnmatch(path, p) for p in patterns)


def _extract_links(html: str, base_url: str) -> set[str]:
    """Return absolute URLs found in anchor tags."""
    soup = BeautifulSoup(html, "lxml")
    links: set[str] = set()
    for a in soup.find_all("a", href=True):
        href: str = a["href"]
        # Skip fragments, mailto, tel, javascript
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        absolute = urljoin(base_url, href)
        # Strip fragments
        absolute = absolute.split("#")[0]
        if _same_domain(base_url, absolute):
            links.add(absolute)
    return links


async def _crawl_worker(
    request: CrawlRequest,
    job: CrawlResult,
    limiter: AsyncLimiter,
) -> None:
    """BFS crawl worker that populates *job* in place."""
    visited: set[str] = set()
    queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
    await queue.put((request.url, 0))

    while not queue.empty() and job.completed < request.max_pages:
        url, depth = await queue.get()

        if url in visited:
            continue
        visited.add(url)

        path = urlparse(url).path

        # Include / exclude path filters
        if not _matches_globs(path, request.include_paths):
            continue
        if request.exclude_paths and _matches_globs(path, request.exclude_paths):
            continue

        async with limiter:
            scrape_req = ScrapeRequest(
                url=url,
                formats=request.formats + ([OutputFormat.raw_html] if OutputFormat.raw_html not in request.formats else []),
                only_main_content=request.only_main_content,
                use_browser=request.use_browser,
                wait_for=request.wait_for,
            )
            result: ScrapeResult = await scrape(scrape_req)

        job.pages.append(result)
        job.completed += 1

        # Discover more links if we haven't hit max depth
        if depth < request.max_depth and result.raw_html:
            for link in _extract_links(result.raw_html, url):
                if link not in visited:
                    await queue.put((link, depth + 1))

    job.status = CrawlStatus.completed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def start_crawl(request: CrawlRequest) -> CrawlResult:
    """Start a crawl job and return the result handle (id populated)."""
    job = CrawlResult(id=str(uuid.uuid4()), status=CrawlStatus.running, total=request.max_pages)
    _jobs[job.id] = job

    limiter = AsyncLimiter(max_rate=config.rate_limit, time_period=1)

    try:
        await _crawl_worker(request, job, limiter)
    except Exception as exc:
        logger.exception("Crawl failed for %s", request.url)
        job.status = CrawlStatus.failed
        job.error = str(exc)

    return job


def get_crawl_job(job_id: str) -> CrawlResult | None:
    return _jobs.get(job_id)


async def crawl_sync(request: CrawlRequest) -> CrawlResult:
    """Run a crawl and wait for completion (used by CLI)."""
    return await start_crawl(request)
