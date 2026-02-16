"""Pydantic models shared across the application."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class OutputFormat(str, Enum):
    markdown = "markdown"
    html = "html"
    raw_html = "raw_html"
    text = "text"


class CrawlStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class ScrapeRequest(BaseModel):
    """Payload accepted by the /scrape endpoint."""
    url: str
    formats: list[OutputFormat] = Field(default=[OutputFormat.markdown])
    wait_for: int = Field(default=0, description="Extra ms to wait after page load (JS rendering)")
    include_tags: list[str] | None = Field(default=None, description="CSS selectors to include")
    exclude_tags: list[str] | None = Field(default=None, description="CSS selectors to exclude")
    only_main_content: bool = Field(default=True, description="Strip navs, footers, etc.")
    timeout: int = Field(default=30_000, description="Request timeout in ms")
    headers: dict[str, str] | None = None
    use_browser: bool = Field(default=False, description="Force headless browser rendering")
    stealth: bool = Field(default=False, description="Enable stealth anti-detection mode")
    bypass_captcha: bool = Field(default=False, description="Attempt to bypass reCAPTCHA/hCaptcha/Cloudflare")


class CrawlRequest(BaseModel):
    """Payload accepted by the /crawl endpoint."""
    url: str
    max_depth: int = Field(default=2, ge=0, le=10)
    max_pages: int = Field(default=50, ge=1, le=10_000)
    formats: list[OutputFormat] = Field(default=[OutputFormat.markdown])
    include_paths: list[str] | None = Field(default=None, description="Glob patterns for allowed URL paths")
    exclude_paths: list[str] | None = Field(default=None, description="Glob patterns to skip")
    only_main_content: bool = True
    use_browser: bool = False
    wait_for: int = 0


class ExtractRequest(BaseModel):
    """Payload accepted by the /extract endpoint."""
    model_config = {"populate_by_name": True}

    url: str
    extract_schema: dict[str, Any] = Field(
        ..., alias="schema",
        description="JSON-like schema describing which fields to extract via CSS/XPath selectors",
    )
    use_browser: bool = False
    wait_for: int = 0


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class ScrapeResult(BaseModel):
    url: str
    status_code: int | None = None
    markdown: str | None = None
    html: str | None = None
    raw_html: str | None = None
    text: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class CrawlResult(BaseModel):
    id: str
    status: CrawlStatus = CrawlStatus.pending
    total: int = 0
    completed: int = 0
    pages: list[ScrapeResult] = Field(default_factory=list)
    error: str | None = None


class ExtractResult(BaseModel):
    url: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


# ---------------------------------------------------------------------------
# Format (structured data) models
# ---------------------------------------------------------------------------

class FormatRequest(BaseModel):
    """Payload accepted by the /v1/format endpoint."""
    url: str
    formats: list[OutputFormat] = Field(default=[OutputFormat.html])
    use_browser: bool = False
    wait_for: int = 0
    only_main_content: bool = True


class FormatResult(BaseModel):
    url: str
    tables: list[dict[str, Any]] = Field(default_factory=list)
    lists: list[dict[str, Any]] = Field(default_factory=list)
    key_value_pairs: list[dict[str, str]] = Field(default_factory=list)
    headings: list[dict[str, Any]] = Field(default_factory=list)
    tables_csv: str = ""
    tables_markdown: str = ""
    summary: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


# ---------------------------------------------------------------------------
# AI Analyze models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    """Payload accepted by the /v1/analyze endpoint."""
    url: str
    instruction: str | None = Field(
        default=None,
        description="Custom prompt / question about the content (optional)",
    )
    use_browser: bool = False
    wait_for: int = 0
    only_main_content: bool = True


class AnalyzeResult(BaseModel):
    url: str
    analysis: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


# ---------------------------------------------------------------------------
# Deep Scan (unified pipeline) models
# ---------------------------------------------------------------------------

class ScanRequest(BaseModel):
    """Payload accepted by the /v1/scan endpoint — runs full pipeline."""
    url: str
    use_browser: bool = Field(default=False, description="Force headless browser rendering")
    wait_for: int = Field(default=0, description="Extra ms to wait (JS rendering)")
    timeout: int = Field(default=30000, description="Request timeout in ms")
    instruction: str | None = Field(
        default=None,
        description="Custom AI instruction for analysis (optional)",
    )
    include_ai: bool = Field(default=True, description="Include AI analysis step")
    only_main_content: bool = Field(default=True, description="Strip navs/footers")
    stealth: bool = Field(default=False, description="Enable stealth anti-detection mode")
    bypass_captcha: bool = Field(default=False, description="Attempt to bypass CAPTCHAs")


class ScanResult(BaseModel):
    url: str
    success: bool = False
    timing: dict[str, float] = Field(default_factory=dict)
    scan_summary: dict[str, Any] = Field(default_factory=dict)
    scrape: dict[str, Any] = Field(default_factory=dict)
    site_detection: dict[str, Any] = Field(default_factory=dict)
    smart_extraction: dict[str, Any] = Field(default_factory=dict)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    ai_analysis: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


# ---------------------------------------------------------------------------
# Plans scraping models
# ---------------------------------------------------------------------------

class PlansRequest(BaseModel):
    """Payload accepted by the /v1/plans endpoint."""
    url: str
    filter_selectors: list[str] | None = Field(
        default=None,
        description="CSS selectors for filter buttons to click (auto-detected if omitted)",
    )
    click_selectors: list[str] | None = Field(
        default=None,
        description="Specific elements to click (e.g. monthly/yearly toggle)",
    )
    wait_for: int = Field(default=2000, description="Wait ms after each interaction")
    timeout: int = Field(default=45000, description="Total timeout in ms")
    load_all_pages: bool = Field(default=False, description="Paginate through results")
    next_button_selector: str | None = Field(
        default=None,
        description="CSS selector for 'next page' button (only if load_all_pages=True)",
    )
    max_pages: int = Field(default=5, ge=1, le=50, description="Max pagination pages to load")
    include_ai: bool = Field(default=True, description="Include AI analysis of plans")


class PlansResult(BaseModel):
    url: str
    success: bool = False
    all_plans: list[dict[str, Any]] = Field(default_factory=list)
    plans_by_filter: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)
    comparison_table: dict[str, Any] | None = None
    billing_options: list[str] = Field(default_factory=list)
    total_plans_found: int = 0
    filter_states_scraped: int = 0
    pages_loaded: int = 1
    markdown: str = ""
    ai_analysis: dict[str, Any] = Field(default_factory=dict)
    timing: float = 0
    error: str | None = None
