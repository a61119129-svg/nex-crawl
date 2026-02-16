"""Deep Scan — unified pipeline: scrape → detect site → smart extract → format → AI."""

from __future__ import annotations

import logging
import time
from typing import Any

from nexcrawl.config import config
from nexcrawl.models import OutputFormat, ScrapeRequest
from nexcrawl.scraper import scrape, fetch_url
from nexcrawl.formatter import format_scraped_data
from nexcrawl.ai_analyzer import analyze_content, analyze_with_prompt
from nexcrawl.site_profiles import detect_site_type, smart_extract, get_ai_context_for_site

logger = logging.getLogger(__name__)


async def deep_scan(
    *,
    url: str,
    use_browser: bool = False,
    wait_for: int = 0,
    timeout: int = 30000,
    instruction: str | None = None,
    include_ai: bool = True,
    only_main_content: bool = True,
    stealth: bool = False,
    bypass_captcha: bool = False,
) -> dict[str, Any]:
    """
    Run the full NexCrawl pipeline on a single URL:

    1. Scrape the page (httpx or Playwright)
    2. Detect site type (Yelp, e-commerce, news, etc.)
    3. Smart-extract fields using site-specific selectors
    4. Format structured data (tables, lists, key-value, headings)
    5. AI analysis (summary, insights, entities, sentiment)

    Returns a unified result dict with all sections.
    """
    started = time.time()
    result: dict[str, Any] = {
        "url": url,
        "success": False,
        "timing": {},
        "scrape": {},
        "site_detection": {},
        "smart_extraction": {},
        "structured_data": {},
        "ai_analysis": {},
        "error": None,
    }

    # -----------------------------------------------------------------------
    # Step 1: Scrape
    # -----------------------------------------------------------------------
    t0 = time.time()
    try:
        scrape_req = ScrapeRequest(
            url=url,
            formats=[OutputFormat.markdown, OutputFormat.html, OutputFormat.raw_html, OutputFormat.text],
            use_browser=use_browser,
            wait_for=wait_for,
            timeout=timeout,
            only_main_content=only_main_content,
            stealth=stealth,
            bypass_captcha=bypass_captcha,
        )
        scrape_result = await scrape(scrape_req)

        if scrape_result.error:
            result["error"] = f"Scrape failed: {scrape_result.error}"
            result["timing"]["total"] = round(time.time() - started, 2)
            return result

        result["scrape"] = {
            "status_code": scrape_result.status_code,
            "metadata": scrape_result.metadata,
            "markdown": scrape_result.markdown or "",
            "text": scrape_result.text or "",
            "html": scrape_result.html or "",
            "word_count": len((scrape_result.text or "").split()),
        }
        result["timing"]["scrape"] = round(time.time() - t0, 2)
        logger.info("Step 1 — Scrape complete: %s (%ds)", url, result["timing"]["scrape"])
    except Exception as exc:
        result["error"] = f"Scrape error: {exc}"
        result["timing"]["total"] = round(time.time() - started, 2)
        return result

    # -----------------------------------------------------------------------
    # Step 2: Detect site type
    # -----------------------------------------------------------------------
    t0 = time.time()
    raw_html = scrape_result.raw_html or scrape_result.html or ""
    site_info = detect_site_type(url, raw_html)
    result["site_detection"] = site_info
    result["timing"]["site_detection"] = round(time.time() - t0, 2)
    logger.info("Step 2 — Site type: %s (confidence: %s)", site_info["type"], site_info["confidence"])

    # -----------------------------------------------------------------------
    # Step 3: Smart extraction using site profile
    # -----------------------------------------------------------------------
    t0 = time.time()
    try:
        smart_data = smart_extract(raw_html, site_info["type"])
        result["smart_extraction"] = smart_data
        result["timing"]["smart_extraction"] = round(time.time() - t0, 2)
        logger.info(
            "Step 3 — Smart extraction: %d fields, %d lists",
            len(smart_data.get("extracted_fields", {})),
            len(smart_data.get("extracted_lists", {})),
        )
    except Exception as exc:
        logger.warning("Smart extraction failed: %s", exc)
        result["smart_extraction"] = {"error": str(exc)}
        result["timing"]["smart_extraction"] = round(time.time() - t0, 2)

    # -----------------------------------------------------------------------
    # Step 4: Structured data formatting
    # -----------------------------------------------------------------------
    t0 = time.time()
    try:
        formatted = format_scraped_data(
            html=raw_html,
            text=scrape_result.text,
            markdown=scrape_result.markdown,
            url=url,
        )
        result["structured_data"] = formatted
        result["timing"]["format"] = round(time.time() - t0, 2)
        logger.info(
            "Step 4 — Formatting: %d tables, %d lists, %d KV pairs",
            formatted["summary"]["tables_found"],
            formatted["summary"]["lists_found"],
            formatted["summary"]["key_value_pairs_found"],
        )
    except Exception as exc:
        logger.warning("Formatting failed: %s", exc)
        result["structured_data"] = {"error": str(exc)}
        result["timing"]["format"] = round(time.time() - t0, 2)

    # -----------------------------------------------------------------------
    # Step 5: AI Analysis
    # -----------------------------------------------------------------------
    if include_ai:
        t0 = time.time()
        try:
            content_for_ai = scrape_result.markdown or scrape_result.text or ""

            # Add site-type context to custom instruction
            site_context = get_ai_context_for_site(site_info["type"])

            if instruction:
                full_instruction = f"{site_context}\n\nUSER REQUEST: {instruction}"
                ai_result = await analyze_with_prompt(
                    url=url,
                    content=content_for_ai,
                    instruction=full_instruction,
                )
            else:
                # Enrich the analysis prompt with smart-extracted data
                enrichment = ""
                fields = result["smart_extraction"].get("extracted_fields", {})
                if fields:
                    enrichment = "\n\nPRE-EXTRACTED DATA:\n"
                    for k, v in fields.items():
                        enrichment += f"- {k}: {v}\n"

                ai_result = await analyze_content(
                    url=url,
                    content=content_for_ai + enrichment,
                )

            result["ai_analysis"] = ai_result
            result["timing"]["ai_analysis"] = round(time.time() - t0, 2)
            logger.info("Step 5 — AI analysis complete (%ds)", result["timing"]["ai_analysis"])
        except Exception as exc:
            logger.warning("AI analysis failed: %s", exc)
            result["ai_analysis"] = {"error": str(exc)}
            result["timing"]["ai_analysis"] = round(time.time() - t0, 2)
    else:
        result["ai_analysis"] = {"skipped": True}

    # -----------------------------------------------------------------------
    # Finalize
    # -----------------------------------------------------------------------
    result["success"] = True
    result["timing"]["total"] = round(time.time() - started, 2)

    # Build a quick summary
    result["scan_summary"] = {
        "site_type": site_info["type"],
        "site_confidence": site_info["confidence"],
        "word_count": result["scrape"].get("word_count", 0),
        "tables_found": result["structured_data"].get("summary", {}).get("tables_found", 0),
        "lists_found": result["structured_data"].get("summary", {}).get("lists_found", 0),
        "fields_extracted": len(result["smart_extraction"].get("extracted_fields", {})),
        "ai_available": "error" not in result["ai_analysis"],
        "total_time": result["timing"]["total"],
    }

    return result
