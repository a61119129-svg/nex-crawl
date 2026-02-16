"""FastAPI REST API — the main HTTP interface for nexcrawl."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from nexcrawl.browser import close_browser
from nexcrawl.crawler import crawl_sync, get_crawl_job, start_crawl
from nexcrawl.extractor import extract
from nexcrawl.models import (
    CrawlRequest,
    CrawlResult,
    ExtractRequest,
    ExtractResult,
    ScrapeRequest,
    ScrapeResult,
)
from nexcrawl.scraper import scrape

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    logger.info("nexcrawl API starting …")
    yield
    logger.info("nexcrawl API shutting down …")
    await close_browser()


# ---------------------------------------------------------------------------
# App & middleware
# ---------------------------------------------------------------------------

app = FastAPI(
    title="nexcrawl",
    description="Crawl, scrape, and extract structured data from any website.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Scrape
# ---------------------------------------------------------------------------

@app.post("/v1/scrape", response_model=ScrapeResult)
async def scrape_endpoint(request: ScrapeRequest):
    """Scrape a single URL and return content in the requested formats."""
    result = await scrape(request)
    if result.error:
        raise HTTPException(status_code=500, detail=result.error)
    return result


# ---------------------------------------------------------------------------
# Crawl
# ---------------------------------------------------------------------------

@app.post("/v1/crawl", response_model=CrawlResult)
async def crawl_endpoint(request: CrawlRequest):
    """
    Start a crawl job.  Returns immediately with a job id.

    For the MVP, the crawl runs synchronously and the full result is returned.
    A production version would run the crawl in a background task and let the
    client poll ``GET /v1/crawl/{id}``.
    """
    result = await crawl_sync(request)
    if result.error:
        raise HTTPException(status_code=500, detail=result.error)
    return result


@app.get("/v1/crawl/{job_id}", response_model=CrawlResult)
async def crawl_status(job_id: str):
    """Check the status of a crawl job."""
    job = get_crawl_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

@app.post("/v1/extract", response_model=ExtractResult)
async def extract_endpoint(request: ExtractRequest):
    """Extract structured data from a URL using a CSS/XPath schema."""
    result = await extract(request)
    if result.error:
        raise HTTPException(status_code=500, detail=result.error)
    return result
