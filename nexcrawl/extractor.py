"""Structured data extraction from web pages using CSS / XPath selectors."""

from __future__ import annotations

import logging
from typing import Any

from bs4 import BeautifulSoup

from nexcrawl.models import ExtractRequest, ExtractResult
from nexcrawl.scraper import fetch_url

logger = logging.getLogger(__name__)


def _resolve_selector(soup: BeautifulSoup, selector: str) -> list[str]:
    """
    Resolve a CSS selector and return a list of text values.

    Selector syntax extensions:
    -  ``css::<selector>``  → CSS selector (default)
    -  ``xpath::<expr>``    → lxml XPath  (requires lxml)
    -  ``attr::<selector>::<attribute>``  → return attribute value
    """
    if selector.startswith("xpath::"):
        from lxml import etree

        tree = etree.HTML(str(soup))
        xpath_expr = selector[len("xpath::"):]
        results = tree.xpath(xpath_expr)
        return [str(r).strip() if not isinstance(r, str) else r.strip() for r in results]

    if selector.startswith("attr::"):
        parts = selector[len("attr::"):].split("::", 1)
        if len(parts) != 2:
            return []
        css_sel, attr_name = parts
        return [el.get(attr_name, "") for el in soup.select(css_sel)]

    # Default: CSS selector → text
    css = selector
    if css.startswith("css::"):
        css = css[len("css::"):]

    return [el.get_text(strip=True) for el in soup.select(css)]


def _walk_schema(soup: BeautifulSoup, schema: dict[str, Any]) -> dict[str, Any]:
    """
    Walk a user-defined schema and resolve each leaf selector.

    Schema format::

        {
            "title": "h1",
            "prices": {
                "_list": true,
                "selector": ".product-card .price"
            },
            "author": "attr::.author::data-name"
        }

    - Scalar string value → CSS selector, returns first match text
    - Dict with ``_list: true`` → returns all matches as a list
    - Nested dict (no ``selector``) → recurse
    """
    result: dict[str, Any] = {}

    for key, value in schema.items():
        if isinstance(value, str):
            matches = _resolve_selector(soup, value)
            result[key] = matches[0] if matches else None

        elif isinstance(value, dict):
            if "selector" in value:
                matches = _resolve_selector(soup, value["selector"])
                if value.get("_list"):
                    result[key] = matches
                else:
                    result[key] = matches[0] if matches else None
            else:
                # Nested schema
                result[key] = _walk_schema(soup, value)
        else:
            result[key] = None

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def extract(request: ExtractRequest) -> ExtractResult:
    """Fetch a URL and extract structured data according to the given schema."""
    try:
        if request.use_browser or request.wait_for > 0:
            from nexcrawl.browser import render_page
            html, _ = await render_page(request.url, wait_for=request.wait_for)
        else:
            resp = await fetch_url(request.url)
            html = resp.text

        soup = BeautifulSoup(html, "lxml")
        data = _walk_schema(soup, request.extract_schema)
        return ExtractResult(url=request.url, data=data)

    except Exception as exc:
        logger.exception("Extraction failed for %s", request.url)
        return ExtractResult(url=request.url, error=str(exc))
