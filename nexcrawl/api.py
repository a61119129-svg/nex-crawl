"""FastAPI REST API — the main HTTP interface for nexcrawl."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from nexcrawl.browser import close_browser
from nexcrawl.crawler import crawl_sync, get_crawl_job, start_crawl
from nexcrawl.extractor import extract
from nexcrawl.formatter import format_scraped_data
from nexcrawl.ai_analyzer import analyze_content, analyze_with_prompt
from nexcrawl.deep_scan import deep_scan
from nexcrawl.models import (
    AnalyzeRequest,
    AnalyzeResult,
    CrawlRequest,
    CrawlResult,
    ExtractRequest,
    ExtractResult,
    FormatRequest,
    FormatResult,
    OutputFormat,
    ScanRequest,
    ScanResult,
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


# ---------------------------------------------------------------------------
# Format (structured data extraction)
# ---------------------------------------------------------------------------

@app.post("/v1/format", response_model=FormatResult)
async def format_endpoint(request: FormatRequest):
    """Scrape a URL and extract all structured data (tables, lists, etc.)."""
    try:
        # First scrape the page to get HTML + text
        scrape_req = ScrapeRequest(
            url=request.url,
            formats=[OutputFormat.html, OutputFormat.text, OutputFormat.markdown],
            use_browser=request.use_browser,
            wait_for=request.wait_for,
            only_main_content=request.only_main_content,
        )
        scrape_result = await scrape(scrape_req)

        if scrape_result.error:
            return FormatResult(url=request.url, error=scrape_result.error)

        # Run formatter
        formatted = format_scraped_data(
            html=scrape_result.html,
            text=scrape_result.text,
            markdown=scrape_result.markdown,
            url=request.url,
        )

        return FormatResult(**formatted)

    except Exception as exc:
        logger.exception("Format failed for %s", request.url)
        return FormatResult(url=request.url, error=str(exc))


# ---------------------------------------------------------------------------
# AI Analyze
# ---------------------------------------------------------------------------

@app.post("/v1/analyze", response_model=AnalyzeResult)
async def analyze_endpoint(request: AnalyzeRequest):
    """Scrape a URL and use AI to provide valuable insights."""
    try:
        # First scrape the page
        scrape_req = ScrapeRequest(
            url=request.url,
            formats=[OutputFormat.markdown, OutputFormat.text],
            use_browser=request.use_browser,
            wait_for=request.wait_for,
            only_main_content=request.only_main_content,
        )
        scrape_result = await scrape(scrape_req)

        if scrape_result.error:
            return AnalyzeResult(url=request.url, error=scrape_result.error)

        content = scrape_result.markdown or scrape_result.text or ""

        if not content.strip():
            return AnalyzeResult(
                url=request.url,
                error="No content could be extracted from the page",
            )

        # Run AI analysis
        if request.instruction:
            analysis = await analyze_with_prompt(
                url=request.url,
                content=content,
                instruction=request.instruction,
            )
        else:
            analysis = await analyze_content(
                url=request.url,
                content=content,
            )

        return AnalyzeResult(url=request.url, analysis=analysis)

    except Exception as exc:
        logger.exception("Analyze failed for %s", request.url)
        return AnalyzeResult(url=request.url, error=str(exc))


# ---------------------------------------------------------------------------
# Deep Scan (unified pipeline)
# ---------------------------------------------------------------------------

@app.post("/v1/scan", response_model=ScanResult)
async def scan_endpoint(request: ScanRequest):
    """
    Run the full NexCrawl pipeline on a single URL:
    scrape → detect site type → smart extract → format → AI analyze.
    """
    try:
        result = await deep_scan(
            url=request.url,
            use_browser=request.use_browser,
            wait_for=request.wait_for,
            timeout=request.timeout,
            instruction=request.instruction,
            include_ai=request.include_ai,
            only_main_content=request.only_main_content,
        )

        if result.get("error") and not result.get("success"):
            return ScanResult(url=request.url, error=result["error"])

        return ScanResult(**result)

    except Exception as exc:
        logger.exception("Deep scan failed for %s", request.url)
        return ScanResult(url=request.url, error=str(exc))
