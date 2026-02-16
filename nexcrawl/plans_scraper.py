"""Plans page scraper — scrapes pricing/plans pages with filter interactions."""

from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from nexcrawl.config import config
from nexcrawl.markdown_converter import html_to_markdown

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Common filter selectors for plans/pricing pages
# ---------------------------------------------------------------------------

# These are CSS selectors commonly used on pricing/plans pages
PLAN_FILTER_SELECTORS = [
    # Toggle switches (monthly/yearly)
    ".pricing-toggle, .billing-toggle, .plan-toggle",
    "[data-toggle='pricing'], [data-toggle='billing']",
    ".toggle-switch, .switch-container",
    # Tab-style filters
    ".pricing-tabs button, .pricing-tabs a, .pricing-tabs li",
    ".plan-tabs button, .plan-tabs a, .plan-tabs li",
    ".billing-period button, .billing-period a",
    "[role='tablist'] button, [role='tablist'] a",
    # Radio / pill selectors
    ".pricing-selector button, .pricing-selector input + label",
    ".billing-selector button, .billing-selector label",
    ".plan-selector button, .plan-selector label",
    # Common SaaS patterns
    "button[data-period], button[data-billing]",
    "[data-annual], [data-monthly], [data-yearly]",
    # Dropdown filters
    "select.pricing-filter, select.plan-filter",
]

PLAN_CONTAINER_SELECTORS = [
    # Common pricing card containers
    ".pricing-card, .plan-card, .price-card",
    ".pricing-column, .plan-column",
    ".pricing-tier, .plan-tier",
    ".pricing-box, .plan-box",
    ".pricing-table-row, .pricing-plan",
    "[class*='pricing'], [class*='plan-card']",
    "[data-plan], [data-tier], [data-pricing]",
    # Table-based pricing
    ".comparison-table tr, .feature-table tr",
]


# ---------------------------------------------------------------------------
# Plans data extraction
# ---------------------------------------------------------------------------

def extract_plans_from_html(html: str) -> dict[str, Any]:
    """
    Extract pricing plans and features from HTML.

    Looks for:
    - Plan names, prices, billing periods
    - Feature lists per plan
    - CTAs / signup buttons
    - Comparison tables
    """
    soup = BeautifulSoup(html, "lxml")
    result: dict[str, Any] = {
        "plans": [],
        "comparison_table": None,
        "billing_options": [],
        "features_list": [],
    }

    # --- Detect billing toggle options ---
    for sel in [
        ".pricing-toggle, .billing-toggle, .plan-toggle",
        "[role='tablist'] button, [role='tablist'] a",
        ".billing-period button, .billing-period a",
    ]:
        elements = soup.select(sel)
        for el in elements:
            text = el.get_text(strip=True)
            if text and len(text) < 50:
                result["billing_options"].append(text)

    # --- Extract plan cards ---
    for sel in PLAN_CONTAINER_SELECTORS:
        cards = soup.select(sel)
        if len(cards) >= 2:  # Pricing pages usually have 2+ plans
            for card in cards:
                plan = _extract_plan_card(card, soup)
                if plan and plan.get("name"):
                    result["plans"].append(plan)
            if result["plans"]:
                break

    # If no cards found, try a more aggressive search
    if not result["plans"]:
        result["plans"] = _extract_plans_heuristic(soup)

    # --- Extract comparison tables ---
    tables = soup.find_all("table")
    for table in tables:
        text = table.get_text(strip=True).lower()
        if any(kw in text for kw in ["feature", "plan", "price", "basic", "pro", "enterprise", "free", "starter"]):
            result["comparison_table"] = _extract_comparison_table(table)
            break

    # --- Extract global feature lists ---
    for sel in [".features-list, .feature-list, .plan-features"]:
        features_el = soup.select(sel)
        for fl in features_el:
            items = fl.find_all("li")
            for item in items:
                text = item.get_text(strip=True)
                if text:
                    # Check for check/cross marks
                    has_check = bool(item.select(".check, .included, .yes, svg.check"))
                    has_cross = bool(item.select(".cross, .excluded, .no, svg.cross"))
                    result["features_list"].append({
                        "feature": text,
                        "included": has_check or not has_cross,
                    })

    return result


def _extract_plan_card(card, soup) -> dict[str, Any]:
    """Extract data from a single plan card element."""
    plan: dict[str, Any] = {
        "name": "",
        "price": "",
        "period": "",
        "description": "",
        "features": [],
        "cta_text": "",
        "highlighted": False,
    }

    # Plan name (usually h2, h3, or prominent text)
    for sel in ["h2", "h3", "h4", ".plan-name", ".tier-name", ".card-title", "[class*='name']", "[class*='title']"]:
        el = card.select_one(sel)
        if el:
            plan["name"] = el.get_text(strip=True)
            break

    # Price
    for sel in [".price, .plan-price, .pricing-amount, [class*='price']", "span.amount, .currency + span"]:
        for s in sel.split(", "):
            el = card.select_one(s.strip())
            if el:
                price_text = el.get_text(strip=True)
                if re.search(r'[\$€£¥₹]|\d', price_text):
                    plan["price"] = price_text
                    break
        if plan["price"]:
            break

    # If still no price, look for dollar patterns in text
    if not plan["price"]:
        card_text = card.get_text()
        price_match = re.search(r'[\$€£¥₹]\s*[\d,]+(?:\.\d{2})?(?:\s*/\s*\w+)?', card_text)
        if price_match:
            plan["price"] = price_match.group().strip()

    # Billing period
    for sel in [".period, .billing-period, .plan-period, [class*='period']", "[class*='billing']"]:
        for s in sel.split(", "):
            el = card.select_one(s.strip())
            if el:
                plan["period"] = el.get_text(strip=True)
                break
        if plan["period"]:
            break

    if not plan["period"]:
        card_text = card.get_text().lower()
        if "/month" in card_text or "per month" in card_text or "/mo" in card_text:
            plan["period"] = "monthly"
        elif "/year" in card_text or "per year" in card_text or "/yr" in card_text:
            plan["period"] = "yearly"

    # Description
    for sel in [".description, .plan-description, .plan-subtitle, p"]:
        el = card.select_one(sel)
        if el:
            desc = el.get_text(strip=True)
            if desc and desc != plan["name"] and len(desc) > 10:
                plan["description"] = desc
                break

    # Features list
    features = card.find_all("li")
    for li in features:
        text = li.get_text(strip=True)
        if text and len(text) < 200:
            plan["features"].append(text)

    # CTA button
    for sel in ["button, a.btn, a.button, [class*='cta'], [class*='signup'], [class*='start']"]:
        for s in sel.split(", "):
            el = card.select_one(s.strip())
            if el:
                cta = el.get_text(strip=True)
                if cta and len(cta) < 50:
                    plan["cta_text"] = cta
                    break
        if plan["cta_text"]:
            break

    # Is this plan highlighted/recommended?
    classes = " ".join(card.get("class", []))
    plan["highlighted"] = any(
        kw in classes.lower()
        for kw in ["popular", "recommended", "featured", "highlight", "best", "selected"]
    )

    return plan


def _extract_plans_heuristic(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """
    Fallback: scan the page for pricing patterns when no standard card structure found.
    """
    plans = []

    # Look for elements containing price patterns
    price_pattern = re.compile(r'[\$€£¥₹]\s*[\d,]+(?:\.\d{2})?')

    # Find all elements that look like plans
    for heading in soup.find_all(["h2", "h3", "h4"]):
        heading_text = heading.get_text(strip=True)

        # Skip if heading text is too long or too short
        if not heading_text or len(heading_text) > 50 or len(heading_text) < 2:
            continue

        # Check if there's a price near this heading
        parent = heading.parent
        if parent:
            parent_text = parent.get_text()
            price_match = price_pattern.search(parent_text)
            if price_match:
                plan = {
                    "name": heading_text,
                    "price": price_match.group().strip(),
                    "period": "",
                    "description": "",
                    "features": [],
                    "cta_text": "",
                    "highlighted": False,
                }

                # Extract features from nearby lists
                nearby_list = parent.find("ul") or parent.find("ol")
                if nearby_list:
                    for li in nearby_list.find_all("li"):
                        text = li.get_text(strip=True)
                        if text:
                            plan["features"].append(text)

                plans.append(plan)

    return plans


def _extract_comparison_table(table) -> dict[str, Any]:
    """Extract a feature comparison table."""
    result: dict[str, Any] = {
        "headers": [],
        "rows": [],
    }

    # Headers (plan names)
    thead = table.find("thead")
    if thead:
        ths = thead.find_all(["th", "td"])
        result["headers"] = [th.get_text(strip=True) for th in ths]

    if not result["headers"]:
        first_row = table.find("tr")
        if first_row:
            ths = first_row.find_all(["th", "td"])
            result["headers"] = [th.get_text(strip=True) for th in ths]

    # Feature rows
    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all(["td", "th"])
        row = []
        for cell in cells:
            # Check for checkmark/cross icons
            if cell.find(["svg", "img", "i"]):
                check = cell.find(class_=lambda c: c and any(
                    kw in str(c).lower() for kw in ["check", "yes", "included", "tick"]
                ))
                cross = cell.find(class_=lambda c: c and any(
                    kw in str(c).lower() for kw in ["cross", "no", "excluded", "times"]
                ))
                if check:
                    row.append("✓")
                elif cross:
                    row.append("✗")
                else:
                    row.append(cell.get_text(strip=True) or "✓")
            else:
                row.append(cell.get_text(strip=True))

        if row and any(r for r in row):
            result["rows"].append(row)

    return result


# ---------------------------------------------------------------------------
# Main plans scraping pipeline
# ---------------------------------------------------------------------------

async def scrape_plans_page(
    url: str,
    *,
    filter_selectors: list[str] | None = None,
    click_selectors: list[str] | None = None,
    wait_for: int = 2000,
    timeout: int = 45000,
    load_all_pages: bool = False,
    next_button_selector: str | None = None,
    max_pages: int = 5,
) -> dict[str, Any]:
    """
    Scrape a plans/pricing page by:
    1. Loading with stealth browser + captcha bypass
    2. Scrolling to trigger lazy content
    3. Clicking filter/toggle options
    4. Extracting plans from each filter state
    5. Combining all data

    Returns a comprehensive plans result.
    """
    from nexcrawl.browser import render_page_with_filters

    started = time.time()

    result: dict[str, Any] = {
        "url": url,
        "success": False,
        "plans_by_filter": {},
        "all_plans": [],
        "comparison_table": None,
        "billing_options": [],
        "total_plans_found": 0,
        "filter_states_scraped": 0,
        "pages_loaded": 1,
        "timing": 0,
        "markdown": "",
        "error": None,
    }

    try:
        # Use auto-detected filter selectors if none provided
        all_filter_selectors = filter_selectors or PLAN_FILTER_SELECTORS
        all_click_selectors = click_selectors or []

        browser_result = await render_page_with_filters(
            url,
            filter_selectors=all_filter_selectors,
            click_selectors=all_click_selectors,
            wait_for=wait_for,
            timeout=timeout,
            stealth=True,
            bypass_captcha=True,
            scroll_to_bottom=True,
            load_all_pages=load_all_pages,
            next_button_selector=next_button_selector,
            max_pages=max_pages,
        )

        result["pages_loaded"] = browser_result.get("pages_loaded", 1)
        result["filter_states_scraped"] = len(browser_result.get("filter_states", []))

        # Extract plans from each filter state
        seen_plans = set()
        for state in browser_result.get("filter_states", []):
            filter_name = state["filter"]
            plans_data = extract_plans_from_html(state["html"])

            result["plans_by_filter"][filter_name] = plans_data["plans"]

            # Merge into all_plans (deduplicate by name)
            for plan in plans_data["plans"]:
                plan_key = f"{plan.get('name', '')}-{plan.get('price', '')}"
                if plan_key not in seen_plans and plan.get("name"):
                    seen_plans.add(plan_key)
                    plan["filter_source"] = filter_name
                    result["all_plans"].append(plan)

            # Keep the best comparison table
            if plans_data.get("comparison_table") and not result["comparison_table"]:
                result["comparison_table"] = plans_data["comparison_table"]

            # Merge billing options
            for opt in plans_data.get("billing_options", []):
                if opt not in result["billing_options"]:
                    result["billing_options"].append(opt)

        # Also extract from the final HTML state
        final_plans = extract_plans_from_html(browser_result["html"])
        for plan in final_plans["plans"]:
            plan_key = f"{plan.get('name', '')}-{plan.get('price', '')}"
            if plan_key not in seen_plans and plan.get("name"):
                seen_plans.add(plan_key)
                plan["filter_source"] = "final"
                result["all_plans"].append(plan)

        if not result["comparison_table"] and final_plans.get("comparison_table"):
            result["comparison_table"] = final_plans["comparison_table"]

        result["total_plans_found"] = len(result["all_plans"])

        # Generate markdown summary
        result["markdown"] = _plans_to_markdown(result)

        result["success"] = True
        result["timing"] = round(time.time() - started, 2)

    except Exception as exc:
        logger.exception("Plans scraping failed for %s", url)
        result["error"] = str(exc)
        result["timing"] = round(time.time() - started, 2)

    return result


def _plans_to_markdown(data: dict[str, Any]) -> str:
    """Convert extracted plans to a readable markdown summary."""
    lines = []
    lines.append(f"# Plans & Pricing — {data['url']}\n")

    if data["billing_options"]:
        lines.append(f"**Billing options:** {', '.join(data['billing_options'])}\n")

    lines.append(f"**Total plans found:** {data['total_plans_found']}\n")

    for plan in data["all_plans"]:
        highlighted = " ⭐ RECOMMENDED" if plan.get("highlighted") else ""
        lines.append(f"## {plan['name']}{highlighted}")

        if plan.get("price"):
            price_line = f"**Price:** {plan['price']}"
            if plan.get("period"):
                price_line += f" ({plan['period']})"
            lines.append(price_line)

        if plan.get("description"):
            lines.append(f"\n{plan['description']}")

        if plan.get("features"):
            lines.append("\n**Features:**")
            for f in plan["features"]:
                lines.append(f"- {f}")

        if plan.get("cta_text"):
            lines.append(f"\n*CTA:* {plan['cta_text']}")

        if plan.get("filter_source") and plan["filter_source"] != "initial":
            lines.append(f"\n*Billing:* {plan['filter_source']}")

        lines.append("")

    # Comparison table
    if data.get("comparison_table"):
        ct = data["comparison_table"]
        lines.append("## Feature Comparison\n")
        if ct.get("headers"):
            lines.append("| " + " | ".join(ct["headers"]) + " |")
            lines.append("| " + " | ".join(["---"] * len(ct["headers"])) + " |")
        for row in ct.get("rows", []):
            lines.append("| " + " | ".join(row) + " |")
        lines.append("")

    return "\n".join(lines)
