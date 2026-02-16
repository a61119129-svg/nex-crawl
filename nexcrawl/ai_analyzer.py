"""AI Analyzer — uses Groq (free Llama 3.3 70B) to analyze scraped content."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import httpx

from nexcrawl.config import config

logger = logging.getLogger(__name__)

# Groq free tier: 30 RPM, 15K tokens/min for llama-3.3-70b
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _get_api_key() -> str | None:
    """Get Groq API key from env or config."""
    return os.environ.get("GROQ_API_KEY") or getattr(config, "groq_api_key", None)


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

ANALYZE_PROMPT = """You are NexCrawl AI — an expert web data analyst.
Analyze the following scraped web content and provide a structured, valuable analysis.

URL: {url}

CONTENT:
{content}

Provide your analysis in this exact JSON format:
{{
  "summary": "A clear 2-3 sentence summary of what this page is about",
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "topics": ["topic1", "topic2"],
  "sentiment": "positive/negative/neutral/mixed",
  "content_type": "article/product/documentation/landing_page/forum/news/other",
  "important_data": [
    {{"label": "name of data point", "value": "the value"}}
  ],
  "entities": {{
    "people": ["names found"],
    "organizations": ["org names"],
    "locations": ["places"],
    "dates": ["dates mentioned"],
    "prices": ["prices/numbers mentioned"]
  }},
  "action_items": ["any actionable items or CTAs found"],
  "quality_score": 8,
  "quality_reasoning": "Why this score"
}}

IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, no extra text."""

COMPARE_PROMPT = """You are NexCrawl AI — an expert web data analyst.
Compare the following scraped pages and provide a structured comparison.

{pages_content}

Provide your analysis in this exact JSON format:
{{
  "comparison_summary": "Overview of how these pages compare",
  "similarities": ["similarity 1", "similarity 2"],
  "differences": ["difference 1", "difference 2"],
  "page_rankings": [
    {{"url": "url", "score": 8, "reason": "why"}}
  ],
  "recommendation": "Which page is best and why"
}}

IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, no extra text."""

CUSTOM_PROMPT_TEMPLATE = """You are NexCrawl AI — an expert web data analyst.
The user wants you to analyze scraped web content with a custom instruction.

URL: {url}

CONTENT:
{content}

USER'S INSTRUCTION: {instruction}

Provide a thorough, structured response. If the user asks for data extraction,
format it as a JSON object. Otherwise, provide clear, well-organized text.
Return your response as JSON with this structure:
{{
  "answer": "your detailed response to the user's instruction",
  "data": {{}},
  "confidence": "high/medium/low"
}}

IMPORTANT: Return ONLY valid JSON. No markdown, no code blocks, no extra text."""


# ---------------------------------------------------------------------------
# Groq API call (OpenAI-compatible)
# ---------------------------------------------------------------------------

async def _call_llm(prompt: str) -> dict[str, Any]:
    """Call the Groq API (OpenAI-compatible) and return parsed JSON response."""
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Get a free key at https://console.groq.com/keys"
        )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise data analysis AI. Always respond with valid JSON only. No markdown formatting, no code blocks.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(verify=config.verify_ssl, timeout=60) as client:
        # Retry up to 3 times on 429 rate limit
        for attempt in range(3):
            resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
            if resp.status_code == 429:
                wait = (attempt + 1) * 5
                logger.warning("Groq 429 rate limit, retrying in %ds (attempt %d/3)", wait, attempt + 1)
                await asyncio.sleep(wait)
                continue
            resp.raise_for_status()
            break
        else:
            resp.raise_for_status()

    data = resp.json()

    # Extract text from OpenAI-compatible response
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        logger.error("Unexpected Groq response: %s", data)
        raise ValueError(f"Failed to parse Groq response: {e}") from e

    # Parse JSON
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw_response": text}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------

def _truncate_content(content: str, max_chars: int = 12000) -> str:
    """Truncate content to fit within token limits."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "\n\n[... content truncated for analysis ...]"


async def analyze_content(
    *,
    url: str,
    content: str,
) -> dict[str, Any]:
    """Analyze scraped content using AI and return structured insights."""
    truncated = _truncate_content(content)
    prompt = ANALYZE_PROMPT.format(url=url, content=truncated)

    try:
        result = await _call_llm(prompt)
        result["url"] = url
        result["ai_model"] = GROQ_MODEL
        return result
    except Exception as exc:
        logger.exception("AI analysis failed for %s", url)
        return {
            "url": url,
            "error": str(exc),
            "summary": "AI analysis failed. Check your GROQ_API_KEY.",
        }


async def analyze_with_prompt(
    *,
    url: str,
    content: str,
    instruction: str,
) -> dict[str, Any]:
    """Analyze content with a custom user-provided instruction."""
    truncated = _truncate_content(content)
    prompt = CUSTOM_PROMPT_TEMPLATE.format(
        url=url, content=truncated, instruction=instruction
    )

    try:
        result = await _call_llm(prompt)
        result["url"] = url
        result["instruction"] = instruction
        result["ai_model"] = GROQ_MODEL
        return result
    except Exception as exc:
        logger.exception("Custom AI analysis failed for %s", url)
        return {
            "url": url,
            "error": str(exc),
            "instruction": instruction,
        }


async def compare_pages(
    pages: list[dict[str, str]],
) -> dict[str, Any]:
    """Compare multiple scraped pages using AI."""
    pages_text = ""
    for i, page in enumerate(pages, 1):
        truncated = _truncate_content(page["content"], max_chars=5000)
        pages_text += f"\n--- PAGE {i}: {page['url']} ---\n{truncated}\n"

    prompt = COMPARE_PROMPT.format(pages_content=pages_text)

    try:
        result = await _call_llm(prompt)
        result["pages_analyzed"] = len(pages)
        result["ai_model"] = GROQ_MODEL
        return result
    except Exception as exc:
        logger.exception("AI comparison failed")
        return {"error": str(exc), "pages_analyzed": len(pages)}
