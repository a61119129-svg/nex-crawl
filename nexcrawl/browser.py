"""Headless browser rendering via Playwright (async)."""

from __future__ import annotations

import logging

from nexcrawl.config import config

logger = logging.getLogger(__name__)

# Module-level singleton for reusing the browser across calls
_browser = None
_playwright = None


async def _get_browser():
    """Lazily launch a Playwright Chromium browser."""
    global _browser, _playwright
    if _browser is None or not _browser.is_connected():
        from playwright.async_api import async_playwright

        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=config.headless)
        logger.info("Playwright browser launched (headless=%s)", config.headless)
    return _browser


async def render_page(
    url: str,
    *,
    wait_for: int = 0,
    timeout: int | None = None,
) -> tuple[str, int]:
    """
    Render a page using a headless browser and return ``(html, status_code)``.

    Parameters
    ----------
    url:
        The page to load.
    wait_for:
        Additional milliseconds to wait after the ``load`` event.
    timeout:
        Navigation timeout in milliseconds.
    """
    browser = await _get_browser()
    context = await browser.new_context(
        user_agent=config.user_agent,
        viewport={"width": 1280, "height": 900},
    )
    page = await context.new_page()

    try:
        response = await page.goto(
            url,
            wait_until="networkidle",
            timeout=timeout or config.browser_timeout,
        )
        status_code = response.status if response else 0

        if wait_for > 0:
            await page.wait_for_timeout(wait_for)

        html = await page.content()
        return html, status_code

    finally:
        await context.close()


async def close_browser() -> None:
    """Shut down the shared browser (call on app shutdown)."""
    global _browser, _playwright
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
