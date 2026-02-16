"""HTML → Markdown converter using markdownify with sensible defaults."""

from __future__ import annotations

from markdownify import MarkdownConverter, markdownify


class _nexcrawlConverter(MarkdownConverter):
    """Customised converter that produces cleaner markdown."""

    def convert_a(self, el, text, parent_tags=None):
        """Keep links but skip empty ones."""
        href = el.get("href", "")
        if not href or not text.strip():
            return text
        return super().convert_a(el, text, parent_tags=parent_tags)

    def convert_img(self, el, text, parent_tags=None):
        alt = el.get("alt", "")
        src = el.get("src", "")
        if not src:
            return ""
        return f"![{alt}]({src})"


def html_to_markdown(html: str) -> str:
    """Convert an HTML string to clean Markdown."""
    md: str = _nexcrawlConverter(
        heading_style="ATX",
        bullets="-",
        strip=["script", "style", "noscript"],
        newline_style="backslash",
    ).convert(html)

    # Collapse excessive blank lines
    lines = md.splitlines()
    cleaned: list[str] = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                cleaned.append("")
        else:
            blank_count = 0
            cleaned.append(line)

    return "\n".join(cleaned).strip() + "\n"
