"""Global configuration & defaults."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class nexcrawlConfig:
    """Runtime configuration – tweak via env vars or pass directly."""

    # Networking
    user_agent: str = (
        "Mozilla/5.0 (compatible; nexcrawlBot/0.1; +https://github.com/nexcrawl)"
    )
    default_timeout: int = 30  # seconds
    verify_ssl: bool = False  # Set True in production with proper certs
    max_retries: int = 3
    retry_backoff: float = 1.0  # seconds (exponential base)

    # Rate-limiting (requests per second per domain)
    rate_limit: float = 2.0

    # Crawl
    max_depth: int = 2
    max_pages: int = 50

    # Browser / JS rendering
    headless: bool = True
    browser_timeout: int = 30_000  # ms

    # Content
    only_main_content: bool = True

    # Extra default headers
    default_headers: dict[str, str] = field(default_factory=dict)


# Singleton-ish default config
config = nexcrawlConfig()
