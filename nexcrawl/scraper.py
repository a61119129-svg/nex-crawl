"""Core single-page scraper — fetches a URL and returns cleaned content."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from bs4 import BeautifulSoup, Comment
from readability import Document
from tenacity import retry, stop_after_attempt, wait_exponential

from nexcrawl.config import config
from nexcrawl.markdown_converter import html_to_markdown
from nexcrawl.models import OutputFormat, ScrapeRequest, ScrapeResult

logger = logging.getLogger(__name__)

# Tags considered "boilerplate" and stripped when only_main_content is enabled
_BOILERPLATE_TAGS = {
    "nav", "footer", "header", "aside", "script", "style", "noscript",
    "iframe", "svg", "form",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": config.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    headers.update(config.default_headers)
    if extra:
        headers.update(extra)
    return headers


def _extract_metadata(soup: BeautifulSoup, url: str) -> dict[str, Any]:
    """Pull common metadata fields from the page."""
    meta: dict[str, Any] = {"url": url}

    title_tag = soup.find("title")
    if title_tag:
        meta["title"] = title_tag.get_text(strip=True)

    desc = soup.find("meta", attrs={"name": "description"})
    if desc:
        meta["description"] = desc.get("content", "")

    og_image = soup.find("meta", attrs={"property": "og:image"})
    if og_image:
        meta["og_image"] = og_image.get("content", "")

    canonical = soup.find("link", attrs={"rel": "canonical"})
    if canonical:
        meta["canonical"] = canonical.get("href", "")

    lang = soup.find("html")
    if lang:
        meta["language"] = lang.get("lang", "")

    return meta


def _clean_html(
    html: str,
    *,
    only_main_content: bool = True,
    include_tags: list[str] | None = None,
    exclude_tags: list[str] | None = None,
) -> str:
    """Return cleaned HTML body content."""

    # Use readability to isolate main content if requested
    if only_main_content:
        try:
            doc = Document(html)
            html = doc.summary(html_partial=True)
        except Exception:
            logger.debug("Readability extraction failed, falling back to full HTML")

    soup = BeautifulSoup(html, "lxml")

    # Remove comments
    for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
        comment.extract()

    # Remove boilerplate tags
    if only_main_content:
        for tag_name in _BOILERPLATE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

    # Exclude specified selectors
    if exclude_tags:
        for selector in exclude_tags:
            for el in soup.select(selector):
                el.decompose()

    # If include_tags specified, keep only those
    if include_tags:
        fragments = []
        for selector in include_tags:
            fragments.extend(soup.select(selector))
        new_soup = BeautifulSoup("<div></div>", "lxml")
        container = new_soup.find("div")
        for frag in fragments:
            container.append(frag)  # type: ignore[union-attr]
        soup = new_soup

    return str(soup)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@retry(
    stop=stop_after_attempt(config.max_retries),
    wait=wait_exponential(multiplier=config.retry_backoff, min=1, max=10),
    reraise=True,
)
async def fetch_url(url: str, *, headers: dict[str, str] | None = None, timeout: int | None = None) -> httpx.Response:
    """Fetch a URL with retries and return the httpx Response."""
    async with httpx.AsyncClient(
        headers=_build_headers(headers),
        timeout=timeout or config.default_timeout,
        follow_redirects=True,
        verify=config.verify_ssl,
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp


async def scrape(request: ScrapeRequest) -> ScrapeResult:
    """Scrape a single URL and return the result in requested formats."""

    # Determine whether we need a browser
    use_browser = request.use_browser or request.wait_for > 0 or request.stealth or request.bypass_captcha or request.accept_cookies

    try:
        if use_browser:
            from nexcrawl.browser import render_page
            raw_html, status_code = await render_page(
                request.url,
                wait_for=request.wait_for,
                timeout=request.timeout,
                stealth=request.stealth,
                bypass_captcha=request.bypass_captcha,
                accept_cookies=request.accept_cookies,
            )
        else:
            resp = await fetch_url(
                request.url,
                headers=request.headers,
                timeout=request.timeout // 1000,
            )
            raw_html = resp.text
            status_code = resp.status_code

        # Clean
        cleaned_html = _clean_html(
            raw_html,
            only_main_content=request.only_main_content,
            include_tags=request.include_tags,
            exclude_tags=request.exclude_tags,
        )

        # Metadata
        full_soup = BeautifulSoup(raw_html, "lxml")
        metadata = _extract_metadata(full_soup, request.url)

        # Build result based on requested formats
        result = ScrapeResult(url=request.url, status_code=status_code, metadata=metadata)

        for fmt in request.formats:
            if fmt == OutputFormat.markdown:
                result.markdown = html_to_markdown(cleaned_html)
            elif fmt == OutputFormat.html:
                result.html = cleaned_html
            elif fmt == OutputFormat.raw_html:
                result.raw_html = raw_html
            elif fmt == OutputFormat.text:
                soup = BeautifulSoup(cleaned_html, "lxml")
                result.text = soup.get_text(separator="\n", strip=True)

        return result

    except Exception as exc:
        logger.exception("Scrape failed for %s", request.url)
        return ScrapeResult(url=request.url, error=str(exc))
