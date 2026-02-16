"""Headless browser rendering via Playwright (async) — with stealth anti-detection."""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any

from nexcrawl.config import config

logger = logging.getLogger(__name__)

# Module-level singleton for reusing the browser across calls
_browser = None
_playwright = None

# Realistic user agents (rotated per context)
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]


def _random_ua() -> str:
    return random.choice(_USER_AGENTS)


async def _get_browser(*, stealth_mode: bool = False):
    """Lazily launch a Playwright Chromium browser."""
    global _browser, _playwright
    if _browser is None or not _browser.is_connected():
        from playwright.async_api import async_playwright

        _playwright = await async_playwright().start()

        launch_args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-features=IsolateOrigins,site-per-process",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--no-first-run",
            "--no-zygote",
            "--disable-gpu",
        ]

        _browser = await _playwright.chromium.launch(
            headless=config.headless,
            args=launch_args,
        )
        logger.info("Playwright browser launched (headless=%s, stealth=%s)", config.headless, stealth_mode)
    return _browser


async def _create_stealth_context(browser, *, user_agent: str | None = None):
    """Create a browser context with stealth anti-detection patches applied."""
    ua = user_agent or _random_ua()
    context = await browser.new_context(
        user_agent=ua,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",
        color_scheme="light",
        java_script_enabled=True,
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        },
    )

    # Apply playwright-stealth patches
    try:
        from playwright_stealth import stealth_async
        await stealth_async(context)
        logger.debug("Stealth patches applied to context")
    except ImportError:
        logger.warning("playwright-stealth not installed — running without stealth")
    except Exception as e:
        logger.warning("Stealth patch failed: %s", e)

    return context


async def _human_like_delay(min_ms: int = 500, max_ms: int = 2000):
    """Random delay to mimic human behavior."""
    delay = random.randint(min_ms, max_ms) / 1000.0
    await asyncio.sleep(delay)


async def _accept_cookie_consent(page) -> bool:
    """
    Auto-detect and dismiss cookie consent banners / popups.

    Covers major consent frameworks:
    - OneTrust, CookieBot, TrustArc, Quantcast, Osano
    - GDPR banners, cookie bars, privacy popups
    - Generic "Accept", "Accept All", "I Agree", "Got it" buttons

    Returns True if a consent banner was detected and dismissed.
    """
    handled = False

    # ── Common cookie accept button selectors ──────────────────
    accept_selectors = [
        # OneTrust
        "#onetrust-accept-btn-handler",
        ".onetrust-close-btn-handler",
        # CookieBot
        "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
        "#CybotCookiebotDialogBodyButtonAccept",
        "a#CybotCookiebotDialogBodyLevelButtonAccept",
        # TrustArc / TRUSTe
        ".trustarc-agree-btn",
        "#truste-consent-button",
        ".truste_overlay .truste-consent-button",
        # Quantcast / GDPR
        ".qc-cmp2-summary-buttons button[mode='primary']",
        ".qc-cmp-button",
        "#qc-cmp2-ui button.css-47sehv",
        # Osano
        ".osano-cm-accept-all",
        ".osano-cm-dialog__button--type_accept",
        # Klaro
        ".klaro .cm-btn-accept",
        ".klaro .cm-btn-accept-all",
        # Iubenda
        ".iubenda-cs-accept-btn",
        "#iubenda-cs-banner .iubenda-cs-accept-btn",
        # Didomi
        "#didomi-notice-agree-button",
        # Complianz
        ".cmplz-accept",
        ".cmplz-btn.cmplz-accept",
        # Cookie Notice plugin (WP)
        "#cookie-notice .cn-set-cookie",
        "#cookie-law-info-bar .cli_action_button",
        ".cookie-notice-container .cn-set-cookie",
        # Cookieyes
        ".cky-btn-accept",
        # Generic patterns — text-based
        "button:has-text('Accept All')",
        "button:has-text('Accept all')",
        "button:has-text('Accept Cookies')",
        "button:has-text('Accept cookies')",
        "button:has-text('Allow All')",
        "button:has-text('Allow all')",
        "button:has-text('Allow Cookies')",
        "button:has-text('I Accept')",
        "button:has-text('I Agree')",
        "button:has-text('I agree')",
        "button:has-text('Agree')",
        "button:has-text('Got it')",
        "button:has-text('OK')",
        "button:has-text('Okay')",
        "a:has-text('Accept All')",
        "a:has-text('Accept all')",
        "a:has-text('Accept Cookies')",
        "a:has-text('I Agree')",
        "a:has-text('Got it')",
        # Generic class/id patterns
        "[id*='cookie'] button[class*='accept']",
        "[id*='cookie'] button[class*='agree']",
        "[id*='cookie'] a[class*='accept']",
        "[class*='cookie-banner'] button",
        "[class*='cookie-consent'] button",
        "[class*='cookie-notice'] button",
        "[class*='consent-banner'] button",
        "[class*='gdpr'] button[class*='accept']",
        "[id*='consent'] button[class*='accept']",
        "[data-testid*='cookie'] button",
        "[aria-label*='cookie'] button",
        "[aria-label*='consent'] button",
        ".cc-btn.cc-allow",
        ".cc-accept",
        ".cc-dismiss",
        "#cookie-accept",
        "#accept-cookies",
        "#acceptCookies",
        ".cookie-accept",
        ".accept-cookies",
        ".js-cookie-accept",
        ".js-accept-cookies",
    ]

    for selector in accept_selectors:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=300):
                logger.info("Cookie consent detected — clicking: %s", selector)
                await _human_like_delay(200, 600)
                await btn.click()
                await _human_like_delay(300, 800)
                handled = True
                break  # Only need to click one
        except Exception:
            continue

    # ── Fallback: dismiss by closing overlay-like cookie divs ─
    if not handled:
        close_selectors = [
            "[id*='cookie'] [class*='close']",
            "[id*='cookie'] button[aria-label='Close']",
            "[class*='cookie'] [class*='close']",
            "[class*='consent'] [class*='close']",
            "[class*='cookie'] button[aria-label='Close']",
        ]
        for selector in close_selectors:
            try:
                btn = page.locator(selector).first
                if await btn.is_visible(timeout=300):
                    logger.info("Cookie banner close button — clicking: %s", selector)
                    await btn.click()
                    await _human_like_delay(200, 500)
                    handled = True
                    break
            except Exception:
                continue

    if handled:
        logger.info("Cookie consent banner dismissed")
    return handled


async def _solve_captcha_challenges(page) -> bool:
    """
    Attempt to detect and bypass common CAPTCHA challenges.

    Strategies:
    1. Detect reCAPTCHA iframes and click the checkbox
    2. Detect hCaptcha and click the checkbox
    3. Detect Cloudflare challenge and wait it out
    4. Detect "press and hold" or "verify you are human" buttons

    Returns True if a challenge was detected and handled.
    """
    handled = False

    try:
        # --- Strategy 1: reCAPTCHA v2 checkbox ---
        recaptcha_frame = page.frame_locator("iframe[src*='recaptcha']")
        checkbox = recaptcha_frame.locator(".recaptcha-checkbox-border, #recaptcha-anchor")
        if await checkbox.count() > 0:
            logger.info("reCAPTCHA v2 detected — clicking checkbox")
            await _human_like_delay(800, 2000)
            await checkbox.first.click()
            await _human_like_delay(2000, 5000)
            handled = True
    except Exception:
        pass

    try:
        # --- Strategy 2: hCaptcha checkbox ---
        hcaptcha_frame = page.frame_locator("iframe[src*='hcaptcha']")
        hcheckbox = hcaptcha_frame.locator("#checkbox")
        if await hcheckbox.count() > 0:
            logger.info("hCaptcha detected — clicking checkbox")
            await _human_like_delay(800, 2000)
            await hcheckbox.first.click()
            await _human_like_delay(2000, 5000)
            handled = True
    except Exception:
        pass

    try:
        # --- Strategy 3: Cloudflare challenge (just wait) ---
        cf_challenge = page.locator("#challenge-running, .cf-browser-verification, #cf-challenge-running")
        if await cf_challenge.count() > 0:
            logger.info("Cloudflare challenge detected — waiting")
            await page.wait_for_selector(
                "#challenge-running, .cf-browser-verification",
                state="hidden",
                timeout=15000,
            )
            await _human_like_delay(2000, 4000)
            handled = True
    except Exception:
        pass

    try:
        # --- Strategy 4: Cloudflare Turnstile ---
        turnstile_frame = page.frame_locator("iframe[src*='challenges.cloudflare.com']")
        turnstile_box = turnstile_frame.locator("input[type='checkbox'], .ctp-checkbox-container")
        if await turnstile_box.count() > 0:
            logger.info("Cloudflare Turnstile detected — clicking")
            await _human_like_delay(1000, 2500)
            await turnstile_box.first.click()
            await _human_like_delay(3000, 6000)
            handled = True
    except Exception:
        pass

    try:
        # --- Strategy 5: Generic "verify" / "I'm not a robot" buttons ---
        verify_btns = page.locator(
            "button:has-text('Verify'), button:has-text('I am human'), "
            "button:has-text('Continue'), a:has-text('Verify you are human'), "
            "button:has-text('I\\'m not a robot'), [data-action='verify']"
        )
        if await verify_btns.count() > 0:
            logger.info("Generic verify button detected — clicking")
            await _human_like_delay(500, 1500)
            await verify_btns.first.click()
            await _human_like_delay(2000, 4000)
            handled = True
    except Exception:
        pass

    return handled


async def render_page(
    url: str,
    *,
    wait_for: int = 0,
    timeout: int | None = None,
    stealth: bool = False,
    bypass_captcha: bool = False,
    accept_cookies: bool = True,
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
    stealth:
        Enable anti-detection patches and realistic fingerprints.
    bypass_captcha:
        Attempt to detect and bypass reCAPTCHA/hCaptcha/Cloudflare challenges.
    accept_cookies:
        Auto-detect and dismiss cookie consent banners.
    """
    use_stealth = stealth or bypass_captcha
    browser = await _get_browser(stealth_mode=use_stealth)

    if use_stealth:
        context = await _create_stealth_context(browser)
    else:
        context = await browser.new_context(
            user_agent=config.user_agent,
            viewport={"width": 1280, "height": 900},
        )

    page = await context.new_page()

    # Inject JS to mask automation flags
    if use_stealth:
        await page.add_init_script("""
            // Override navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Override chrome runtime
            window.chrome = { runtime: {} };
            // Override permissions query
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) =>
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters);
            // Override plugins length
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)

    try:
        response = await page.goto(
            url,
            wait_until="networkidle",
            timeout=timeout or config.browser_timeout,
        )
        status_code = response.status if response else 0

        # Accept cookies first
        if accept_cookies:
            await _accept_cookie_consent(page)

        # Attempt CAPTCHA bypass if enabled
        if bypass_captcha:
            for attempt in range(3):
                detected = await _solve_captcha_challenges(page)
                if not detected:
                    break
                logger.info("CAPTCHA bypass attempt %d", attempt + 1)
                await page.wait_for_load_state("networkidle")

        if wait_for > 0:
            await page.wait_for_timeout(wait_for)

        html = await page.content()
        return html, status_code

    finally:
        await context.close()


async def render_page_with_filters(
    url: str,
    *,
    filter_selectors: list[str] | None = None,
    click_selectors: list[str] | None = None,
    wait_for: int = 2000,
    timeout: int | None = None,
    stealth: bool = True,
    bypass_captcha: bool = True,
    scroll_to_bottom: bool = True,
    load_all_pages: bool = False,
    next_button_selector: str | None = None,
    max_pages: int = 10,
) -> dict[str, Any]:
    """
    Render a page and interact with filters to scrape all content.

    Designed for plans/pricing pages and directory listings with filter options.

    Returns a dict:
      - html: the final page HTML
      - status_code: HTTP status
      - filter_states: list of HTML snapshots per filter combination
      - pages_loaded: number of pagination pages loaded
    """
    browser = await _get_browser(stealth_mode=stealth)

    if stealth:
        context = await _create_stealth_context(browser)
    else:
        context = await browser.new_context(
            user_agent=config.user_agent,
            viewport={"width": 1366, "height": 900},
        )

    page = await context.new_page()

    if stealth:
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

    result: dict[str, Any] = {
        "html": "",
        "status_code": 0,
        "filter_states": [],
        "pages_loaded": 1,
    }

    try:
        response = await page.goto(
            url,
            wait_until="networkidle",
            timeout=timeout or config.browser_timeout,
        )
        result["status_code"] = response.status if response else 0

        # Accept cookies first
        await _accept_cookie_consent(page)

        # Handle CAPTCHAs
        if bypass_captcha:
            for _ in range(3):
                detected = await _solve_captcha_challenges(page)
                if not detected:
                    break
                await page.wait_for_load_state("networkidle")

        # Scroll to bottom to trigger lazy-loaded content
        if scroll_to_bottom:
            await _scroll_to_bottom(page)

        await _human_like_delay(500, 1500)

        # Capture initial state
        initial_html = await page.content()
        result["filter_states"].append({
            "filter": "initial",
            "html": initial_html,
        })

        # --- Click specific filter elements ---
        if click_selectors:
            for selector in click_selectors:
                try:
                    elements = page.locator(selector)
                    count = await elements.count()
                    for i in range(count):
                        el = elements.nth(i)
                        if await el.is_visible():
                            label = await el.inner_text()
                            label = label.strip()[:50]
                            logger.info("Clicking filter: %s (%s)", selector, label)
                            await _human_like_delay(300, 800)
                            await el.click()
                            await page.wait_for_load_state("networkidle")
                            await _human_like_delay(500, 1500)

                            if scroll_to_bottom:
                                await _scroll_to_bottom(page)

                            state_html = await page.content()
                            result["filter_states"].append({
                                "filter": label or f"{selector}[{i}]",
                                "html": state_html,
                            })
                except Exception as e:
                    logger.warning("Filter click failed for %s: %s", selector, e)

        # --- Auto-detect and click common filter patterns ---
        if filter_selectors:
            for selector in filter_selectors:
                try:
                    filters = page.locator(selector)
                    count = await filters.count()
                    for i in range(min(count, 20)):
                        el = filters.nth(i)
                        if await el.is_visible():
                            label = await el.inner_text()
                            label = label.strip()[:50]
                            await _human_like_delay(300, 800)
                            await el.click()
                            await page.wait_for_load_state("networkidle")
                            await _human_like_delay(800, 2000)

                            if scroll_to_bottom:
                                await _scroll_to_bottom(page)

                            state_html = await page.content()
                            result["filter_states"].append({
                                "filter": label or f"{selector}[{i}]",
                                "html": state_html,
                            })
                except Exception as e:
                    logger.warning("Filter interaction failed for %s: %s", selector, e)

        # --- Pagination: load multiple pages ---
        if load_all_pages and next_button_selector:
            for page_num in range(2, max_pages + 1):
                try:
                    next_btn = page.locator(next_button_selector)
                    if await next_btn.count() == 0 or not await next_btn.first.is_visible():
                        break
                    logger.info("Loading page %d", page_num)
                    await _human_like_delay(500, 1500)
                    await next_btn.first.click()
                    await page.wait_for_load_state("networkidle")
                    await _human_like_delay(1000, 2500)

                    if scroll_to_bottom:
                        await _scroll_to_bottom(page)

                    page_html = await page.content()
                    result["filter_states"].append({
                        "filter": f"page_{page_num}",
                        "html": page_html,
                    })
                    result["pages_loaded"] = page_num
                except Exception as e:
                    logger.warning("Pagination failed at page %d: %s", page_num, e)
                    break

        # Final combined HTML is the last state
        result["html"] = await page.content()

        if wait_for > 0:
            await page.wait_for_timeout(wait_for)
            result["html"] = await page.content()

        return result

    finally:
        await context.close()


async def _scroll_to_bottom(page, *, max_scrolls: int = 10, delay_ms: int = 500):
    """Scroll page to bottom to trigger lazy loading."""
    for _ in range(max_scrolls):
        previous_height = await page.evaluate("document.body.scrollHeight")
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(delay_ms)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break


async def take_screenshot(
    url: str,
    *,
    full_page: bool = True,
    wait_for: int = 0,
    timeout: int | None = None,
    stealth: bool = False,
    bypass_captcha: bool = False,
    viewport_width: int = 1280,
    viewport_height: int = 800,
) -> dict[str, Any]:
    """
    Take a screenshot of a page and return base64-encoded PNG data.

    Returns dict with:
      - screenshot_base64: the PNG image data as base64
      - content_type: 'image/png'
      - url: the page URL
      - title: the page title
      - status_code: HTTP status
      - viewport: the viewport size used
    """
    import base64

    use_stealth = stealth or bypass_captcha
    browser = await _get_browser(stealth_mode=use_stealth)

    if use_stealth:
        context = await _create_stealth_context(browser, user_agent=_random_ua())
    else:
        context = await browser.new_context(
            user_agent=config.user_agent,
            viewport={"width": viewport_width, "height": viewport_height},
        )

    page = await context.new_page()

    if use_stealth:
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            window.chrome = { runtime: {} };
        """)

    try:
        response = await page.goto(
            url,
            wait_until="networkidle",
            timeout=timeout or config.browser_timeout,
        )
        status_code = response.status if response else 0

        # Accept cookies
        await _accept_cookie_consent(page)

        # Handle CAPTCHAs
        if bypass_captcha:
            for _ in range(3):
                detected = await _solve_captcha_challenges(page)
                if not detected:
                    break
                await page.wait_for_load_state("networkidle")

        if wait_for > 0:
            await page.wait_for_timeout(wait_for)

        # Get page title
        title = await page.title()

        # ── Extract structured layout text from DOM ──────────
        layout_data = await page.evaluate("""() => {
            const sections = [];
            const seen = new Set();

            function addSection(type, content, extra = {}) {
                const key = type + '::' + content;
                if (seen.has(key) || !content.trim()) return;
                seen.add(key);
                sections.push({ type, content: content.trim(), ...extra });
            }

            // Walk the DOM in reading order
            const walker = document.createTreeWalker(
                document.body,
                NodeFilter.SHOW_ELEMENT,
                {
                    acceptNode: (node) => {
                        const tag = node.tagName.toLowerCase();
                        const skip = ['script','style','noscript','svg','path','meta','link','head'];
                        if (skip.includes(tag)) return NodeFilter.FILTER_REJECT;
                        const style = window.getComputedStyle(node);
                        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0')
                            return NodeFilter.FILTER_REJECT;
                        return NodeFilter.FILTER_ACCEPT;
                    }
                }
            );

            let node;
            while (node = walker.nextNode()) {
                const tag = node.tagName.toLowerCase();

                // Headings
                if (/^h[1-6]$/.test(tag)) {
                    const level = parseInt(tag[1]);
                    addSection('heading', node.innerText, { level });
                }
                // Paragraphs
                else if (tag === 'p') {
                    addSection('paragraph', node.innerText);
                }
                // List items
                else if (tag === 'ul' || tag === 'ol') {
                    const items = Array.from(node.querySelectorAll(':scope > li'))
                        .map(li => li.innerText.trim()).filter(Boolean);
                    if (items.length > 0) {
                        addSection('list', items.join('\\n'), { ordered: tag === 'ol', items });
                    }
                }
                // Tables
                else if (tag === 'table') {
                    const rows = [];
                    node.querySelectorAll('tr').forEach(tr => {
                        const cells = Array.from(tr.querySelectorAll('th, td'))
                            .map(c => c.innerText.trim());
                        if (cells.some(c => c)) rows.push(cells);
                    });
                    if (rows.length > 0) {
                        addSection('table', rows.map(r => r.join(' | ')).join('\\n'), { rows });
                    }
                }
                // Images with alt text
                else if (tag === 'img') {
                    const alt = node.getAttribute('alt') || '';
                    const src = node.getAttribute('src') || '';
                    if (alt || src) {
                        addSection('image', alt || src, { alt, src: src.substring(0, 200) });
                    }
                }
                // Links
                else if (tag === 'a') {
                    const text = node.innerText.trim();
                    const href = node.getAttribute('href') || '';
                    if (text && href && !href.startsWith('#') && !href.startsWith('javascript:')) {
                        addSection('link', text, { href: href.substring(0, 300) });
                    }
                }
                // Blockquotes
                else if (tag === 'blockquote') {
                    addSection('quote', node.innerText);
                }
                // Code blocks
                else if (tag === 'pre' || tag === 'code') {
                    if (tag === 'pre' || !node.closest('pre')) {
                        addSection('code', node.innerText);
                    }
                }
                // Form elements
                else if (tag === 'form') {
                    const inputs = Array.from(node.querySelectorAll('input, select, textarea'))
                        .map(el => {
                            const label = el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.getAttribute('name') || el.type;
                            return label;
                        }).filter(Boolean);
                    if (inputs.length > 0) {
                        addSection('form', 'Form fields: ' + inputs.join(', '), { fields: inputs });
                    }
                }
                // Buttons
                else if (tag === 'button' || (tag === 'input' && ['submit','button'].includes(node.type))) {
                    const text = node.innerText || node.value || '';
                    if (text.trim()) addSection('button', text.trim());
                }
                // Navigation
                else if (tag === 'nav') {
                    const links = Array.from(node.querySelectorAll('a'))
                        .map(a => a.innerText.trim()).filter(Boolean);
                    if (links.length > 0) {
                        addSection('navigation', links.join(' | '), { links });
                    }
                }
                // Divs / sections with direct text (fallback)
                else if (['div', 'section', 'article', 'main', 'aside', 'footer', 'header', 'span'].includes(tag)) {
                    // Only capture direct text nodes (not nested elements' text)
                    const directText = Array.from(node.childNodes)
                        .filter(n => n.nodeType === Node.TEXT_NODE)
                        .map(n => n.textContent.trim())
                        .filter(Boolean)
                        .join(' ');
                    if (directText.length > 20) {
                        addSection('text', directText);
                    }
                }
            }

            // Build structured text output
            let structuredText = '';
            for (const s of sections) {
                switch (s.type) {
                    case 'heading':
                        structuredText += '#'.repeat(s.level) + ' ' + s.content + '\\n\\n';
                        break;
                    case 'paragraph':
                    case 'text':
                        structuredText += s.content + '\\n\\n';
                        break;
                    case 'list':
                        (s.items || s.content.split('\\n')).forEach((item, i) => {
                            structuredText += (s.ordered ? (i+1) + '. ' : '- ') + item + '\\n';
                        });
                        structuredText += '\\n';
                        break;
                    case 'table':
                        if (s.rows && s.rows.length > 0) {
                            s.rows.forEach((row, i) => {
                                structuredText += '| ' + row.join(' | ') + ' |\\n';
                                if (i === 0) structuredText += '|' + row.map(() => '---').join('|') + '|\\n';
                            });
                            structuredText += '\\n';
                        }
                        break;
                    case 'image':
                        structuredText += '[Image: ' + s.content + ']\\n\\n';
                        break;
                    case 'link':
                        structuredText += '[' + s.content + '](' + (s.href || '') + ')\\n';
                        break;
                    case 'quote':
                        structuredText += '> ' + s.content.replace(/\\n/g, '\\n> ') + '\\n\\n';
                        break;
                    case 'code':
                        structuredText += '```\\n' + s.content + '\\n```\\n\\n';
                        break;
                    case 'form':
                        structuredText += '[Form: ' + s.content + ']\\n\\n';
                        break;
                    case 'button':
                        structuredText += '[Button: ' + s.content + ']\\n';
                        break;
                    case 'navigation':
                        structuredText += 'Nav: ' + s.content + '\\n\\n';
                        break;
                }
            }

            // Page metadata
            const meta = {};
            const desc = document.querySelector('meta[name="description"]');
            if (desc) meta.description = desc.content;
            const keywords = document.querySelector('meta[name="keywords"]');
            if (keywords) meta.keywords = keywords.content;
            const ogTitle = document.querySelector('meta[property="og:title"]');
            if (ogTitle) meta.og_title = ogTitle.content;
            const ogDesc = document.querySelector('meta[property="og:description"]');
            if (ogDesc) meta.og_description = ogDesc.content;
            const canonical = document.querySelector('link[rel="canonical"]');
            if (canonical) meta.canonical = canonical.href;

            return {
                structured_text: structuredText,
                layout_sections: sections.slice(0, 500),
                page_info: {
                    title: document.title,
                    meta: meta,
                    word_count: document.body.innerText.split(/\\s+/).filter(Boolean).length,
                    link_count: document.querySelectorAll('a[href]').length,
                    image_count: document.querySelectorAll('img').length,
                    heading_count: document.querySelectorAll('h1,h2,h3,h4,h5,h6').length,
                    form_count: document.querySelectorAll('form').length,
                    section_count: sections.length,
                }
            };
        }""")

        # Take screenshot
        screenshot_bytes = await page.screenshot(
            full_page=full_page,
            type="png",
        )
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode("utf-8")

        return {
            "screenshot_base64": screenshot_b64,
            "content_type": "image/png",
            "url": url,
            "title": title,
            "status_code": status_code,
            "viewport": {"width": viewport_width, "height": viewport_height},
            "full_page": full_page,
            "structured_text": layout_data.get("structured_text", ""),
            "layout_sections": layout_data.get("layout_sections", []),
            "page_info": layout_data.get("page_info", {}),
        }

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
