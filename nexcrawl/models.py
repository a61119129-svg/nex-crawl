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
