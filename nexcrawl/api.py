"""FastAPI REST API — the main HTTP interface for nexcrawl."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from nexcrawl.browser import close_browser, take_screenshot
from nexcrawl.crawler import crawl_sync, get_crawl_job, start_crawl
from nexcrawl.extractor import extract
from nexcrawl.formatter import format_scraped_data
from nexcrawl.ai_analyzer import analyze_content, analyze_with_prompt, chat_with_context
from nexcrawl.deep_scan import deep_scan
from nexcrawl.plans_scraper import scrape_plans_page
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
    PlansRequest,
    PlansResult,
    ScanRequest,
    ScanResult,
    ScreenshotRequest,
    ScreenshotResult,
    ScrapeRequest,
    ScrapeResult,
    ChatRequest,
    ChatResult,
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
            stealth=request.stealth,
            bypass_captcha=request.bypass_captcha,
            accept_cookies=request.accept_cookies,
        )

        if result.get("error") and not result.get("success"):
            return ScanResult(url=request.url, error=result["error"])

        return ScanResult(**result)

    except Exception as exc:
        logger.exception("Deep scan failed for %s", request.url)
        return ScanResult(url=request.url, error=str(exc))


# ---------------------------------------------------------------------------
# Plans (pricing page scraper)
# ---------------------------------------------------------------------------

@app.post("/v1/plans", response_model=PlansResult)
async def plans_endpoint(request: PlansRequest):
    """
    Scrape a pricing/plans page with stealth browser, CAPTCHA bypass,
    and automatic filter interaction (monthly/yearly toggles, etc.).
    """
    try:
        result = await scrape_plans_page(
            request.url,
            filter_selectors=request.filter_selectors,
            click_selectors=request.click_selectors,
            wait_for=request.wait_for,
            timeout=request.timeout,
            load_all_pages=request.load_all_pages,
            next_button_selector=request.next_button_selector,
            max_pages=request.max_pages,
        )

        # Optional AI analysis of the plans
        ai_result = {}
        if request.include_ai and result.get("success") and result.get("markdown"):
            try:
                ai_result = await analyze_with_prompt(
                    url=request.url,
                    content=result["markdown"],
                    instruction=(
                        "Analyze these pricing plans. Compare value propositions, "
                        "identify the best plan for different use cases (startup, "
                        "mid-size, enterprise), highlight hidden costs or limitations, "
                        "and give a recommendation."
                    ),
                )
            except Exception as e:
                logger.warning("AI analysis of plans failed: %s", e)
                ai_result = {"error": str(e)}

        return PlansResult(
            url=request.url,
            success=result.get("success", False),
            all_plans=result.get("all_plans", []),
            plans_by_filter=result.get("plans_by_filter", {}),
            comparison_table=result.get("comparison_table"),
            billing_options=result.get("billing_options", []),
            total_plans_found=result.get("total_plans_found", 0),
            filter_states_scraped=result.get("filter_states_scraped", 0),
            pages_loaded=result.get("pages_loaded", 1),
            markdown=result.get("markdown", ""),
            ai_analysis=ai_result,
            timing=result.get("timing", 0),
            error=result.get("error"),
        )

    except Exception as exc:
        logger.exception("Plans scraping failed for %s", request.url)
        return PlansResult(url=request.url, error=str(exc))


# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------

@app.post("/v1/screenshot", response_model=ScreenshotResult)
async def screenshot_endpoint(request: ScreenshotRequest):
    """
    Take a full-page or viewport screenshot of any URL.
    Returns base64-encoded PNG image data.
    """
    try:
        result = await take_screenshot(
            request.url,
            full_page=request.full_page,
            wait_for=request.wait_for,
            timeout=request.timeout,
            stealth=request.stealth,
            bypass_captcha=request.bypass_captcha,
            viewport_width=request.viewport_width,
            viewport_height=request.viewport_height,
        )
        return ScreenshotResult(
            url=request.url,
            success=True,
            screenshot_base64=result["screenshot_base64"],
            content_type=result["content_type"],
            title=result.get("title", ""),
            status_code=result.get("status_code"),
            viewport=result.get("viewport", {}),
            full_page=result.get("full_page", True),
            structured_text=result.get("structured_text", ""),
            layout_sections=result.get("layout_sections", []),
            page_info=result.get("page_info", {}),
        )
    except Exception as exc:
        logger.exception("Screenshot failed for %s", request.url)
        return ScreenshotResult(url=request.url, error=str(exc))


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@app.post("/v1/chat", response_model=ChatResult)
async def chat_endpoint(request: ChatRequest):
    """
    Conversational AI chat grounded in scraped page data.
    Send messages and context to get AI responses about your scraped content.
    """
    try:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        result = await chat_with_context(
            messages=messages,
            context=request.context,
            url=request.url,
        )
        return ChatResult(
            reply=result.get("reply", ""),
            messages=result.get("messages", messages),
            success=True,
        )
    except Exception as exc:
        logger.exception("Chat failed")
        return ChatResult(error=str(exc))
