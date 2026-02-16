"""Data formatter — converts scraped content into structured tables & formats."""

from __future__ import annotations

import csv
import io
import json
import logging
import re
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Table extraction from HTML
# ---------------------------------------------------------------------------

def _extract_tables_from_html(html: str) -> list[dict[str, Any]]:
    """Find all <table> elements and convert them to structured dicts."""
    soup = BeautifulSoup(html, "lxml")
    tables = []

    for idx, table in enumerate(soup.find_all("table")):
        # Extract caption
        caption_tag = table.find("caption")
        caption = caption_tag.get_text(strip=True) if caption_tag else f"Table {idx + 1}"

        # Extract headers
        headers = []
        thead = table.find("thead")
        if thead:
            header_row = thead.find("tr")
            if header_row:
                headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

        # If no <thead>, check first row for <th>
        if not headers:
            first_row = table.find("tr")
            if first_row and first_row.find("th"):
                headers = [th.get_text(strip=True) for th in first_row.find_all("th")]

        # Extract body rows
        rows = []
        tbody = table.find("tbody") or table
        for tr in tbody.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if cells and cells != headers:
                rows.append(cells)

        tables.append({
            "caption": caption,
            "headers": headers,
            "rows": rows,
            "row_count": len(rows),
            "col_count": len(headers) if headers else (len(rows[0]) if rows else 0),
        })

    return tables


# ---------------------------------------------------------------------------
# Auto-detect structured data (lists, key-value patterns, etc.)
# ---------------------------------------------------------------------------

def _extract_lists(html: str) -> list[dict[str, Any]]:
    """Extract ordered and unordered lists as structured data."""
    soup = BeautifulSoup(html, "lxml")
    lists = []

    for idx, ul_or_ol in enumerate(soup.find_all(["ul", "ol"])):
        items = [li.get_text(strip=True) for li in ul_or_ol.find_all("li", recursive=False)]
        if items:
            lists.append({
                "type": ul_or_ol.name,
                "items": items,
                "count": len(items),
            })

    return lists


def _extract_key_value_pairs(text: str) -> list[dict[str, str]]:
    """Detect common key: value patterns in text content."""
    pairs = []
    # Match lines like "Key: Value" or "Key - Value"
    pattern = re.compile(r'^([A-Z][A-Za-z\s]{1,40})[\s]*[:–—-]\s+(.+)$', re.MULTILINE)
    for match in pattern.finditer(text):
        key = match.group(1).strip()
        value = match.group(2).strip()
        if len(key) > 1 and len(value) > 1:
            pairs.append({"key": key, "value": value})
    return pairs


def _extract_headings_structure(html: str) -> list[dict[str, Any]]:
    """Extract heading hierarchy to show content outline."""
    soup = BeautifulSoup(html, "lxml")
    headings = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(tag.name[1])
        text = tag.get_text(strip=True)
        if text:
            headings.append({"level": level, "text": text})
    return headings


# ---------------------------------------------------------------------------
# Format converters
# ---------------------------------------------------------------------------

def tables_to_csv(tables: list[dict[str, Any]]) -> str:
    """Convert extracted tables to CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)

    for i, table in enumerate(tables):
        if i > 0:
            writer.writerow([])  # blank row separator
        writer.writerow([f"--- {table['caption']} ---"])
        if table["headers"]:
            writer.writerow(table["headers"])
        for row in table["rows"]:
            writer.writerow(row)

    return output.getvalue()


def tables_to_markdown(tables: list[dict[str, Any]]) -> str:
    """Convert extracted tables to Markdown table format."""
    parts = []

    for table in tables:
        lines = []
        lines.append(f"### {table['caption']}")
        lines.append("")

        headers = table["headers"]
        if not headers and table["rows"]:
            headers = [f"Col {j+1}" for j in range(len(table["rows"][0]))]

        if headers:
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

        for row in table["rows"]:
            # Pad row to match headers length
            padded = row + [""] * (len(headers) - len(row)) if len(row) < len(headers) else row
            lines.append("| " + " | ".join(padded[:len(headers)]) + " |")

        parts.append("\n".join(lines))

    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Main formatting function
# ---------------------------------------------------------------------------

def format_scraped_data(
    *,
    html: str | None = None,
    text: str | None = None,
    markdown: str | None = None,
    url: str = "",
) -> dict[str, Any]:
    """
    Analyze scraped content and extract all structured data.

    Returns a dict with:
    - tables: extracted HTML tables as structured data
    - lists: extracted lists
    - key_value_pairs: detected key-value patterns
    - headings: content outline
    - tables_csv: CSV representation of tables
    - tables_markdown: Markdown representation of tables
    - summary: quick stats about what was found
    """
    result: dict[str, Any] = {
        "url": url,
        "tables": [],
        "lists": [],
        "key_value_pairs": [],
        "headings": [],
        "tables_csv": "",
        "tables_markdown": "",
        "summary": {},
    }

    # Extract from HTML if available
    if html:
        result["tables"] = _extract_tables_from_html(html)
        result["lists"] = _extract_lists(html)
        result["headings"] = _extract_headings_structure(html)

        if result["tables"]:
            result["tables_csv"] = tables_to_csv(result["tables"])
            result["tables_markdown"] = tables_to_markdown(result["tables"])

    # Extract key-value pairs from text
    if text:
        result["key_value_pairs"] = _extract_key_value_pairs(text)
    elif markdown:
        result["key_value_pairs"] = _extract_key_value_pairs(markdown)

    # Summary stats
    result["summary"] = {
        "tables_found": len(result["tables"]),
        "total_rows": sum(t["row_count"] for t in result["tables"]),
        "lists_found": len(result["lists"]),
        "total_list_items": sum(lst["count"] for lst in result["lists"]),
        "key_value_pairs_found": len(result["key_value_pairs"]),
        "headings_found": len(result["headings"]),
    }

    return result
