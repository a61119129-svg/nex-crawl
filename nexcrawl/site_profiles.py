"""Site profiles — smart extraction presets for common site types."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Site type detection
# ---------------------------------------------------------------------------

SITE_PATTERNS: list[tuple[str, list[str], list[str]]] = [
    # (site_type, url_patterns, html_signals)
    ("yelp", [r"yelp\.com"], [".biz-rating", ".business-name"]),
    ("google_maps", [r"google\.com/maps", r"maps\.google"], [".section-hero-header"]),
    ("tripadvisor", [r"tripadvisor\.com"], [".rating", ".reviewSelector"]),
    ("yellowpages", [r"yellowpages\.com"], [".business-name", ".street-address"]),
    ("indeed", [r"indeed\.com"], [".jobTitle", ".company"]),
    ("linkedin", [r"linkedin\.com"], [".profile-section", ".experience-section"]),
    ("amazon", [r"amazon\.com", r"amazon\.co"], ["#productTitle", "#priceblock"]),
    ("ebay", [r"ebay\.com"], [".s-item", "#mainContent"]),
    ("shopify", [], ["shopify", ".product-single", "cdn.shopify.com"]),
    ("ecommerce", [], [".product-price", ".add-to-cart", ".product-title", "[data-product]"]),
    ("news", [r"bbc\.com", r"cnn\.com", r"reuters\.com", r"nytimes\.com"], ["article", ".article-body", ".story-body"]),
    ("blog", [], [".post-content", ".blog-post", ".entry-content", ".article-content"]),
    ("directory", [r"foursquare\.com", r"justdial\.com", r"manta\.com"], [".listing", ".business-card", ".search-result"]),
    ("realestate", [r"zillow\.com", r"realtor\.com", r"redfin\.com"], [".price", ".property-card", ".listing-card"]),
    ("recipe", [r"allrecipes\.com", r"food\.com"], [".recipe-", "[itemtype*=Recipe]", ".ingredients"]),
    ("generic", [], []),
]


def detect_site_type(url: str, html: str = "") -> dict[str, Any]:
    """Detect the site type from URL patterns and HTML structure."""
    domain = urlparse(url).netloc.lower()
    soup = BeautifulSoup(html, "lxml") if html else None

    for site_type, url_patterns, html_signals in SITE_PATTERNS:
        # Check URL patterns
        for pattern in url_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                return {"type": site_type, "confidence": "high", "method": "url_match"}

        # Check HTML signals
        if soup and html_signals:
            matches = 0
            for signal in html_signals:
                if signal.startswith(".") or signal.startswith("#") or signal.startswith("["):
                    if soup.select_one(signal):
                        matches += 1
                elif signal in html.lower():
                    matches += 1

            if matches >= 2:
                return {"type": site_type, "confidence": "medium", "method": "html_signals"}

    return {"type": "generic", "confidence": "low", "method": "default"}


# ---------------------------------------------------------------------------
# Extraction schemas per site type
# ---------------------------------------------------------------------------

EXTRACTION_SCHEMAS: dict[str, dict[str, Any]] = {
    "yelp": {
        "fields": {
            "business_name": {"selectors": ["h1", ".biz-name", "[data-testid='biz-name']"], "type": "text"},
            "rating": {"selectors": [".i-stars", "[aria-label*='rating']", ".rating-large"], "type": "attr", "attr": "aria-label"},
            "review_count": {"selectors": [".review-count", "[data-testid='review-count']"], "type": "text"},
            "address": {"selectors": [".street-address", "address", "[data-testid='address']"], "type": "text"},
            "phone": {"selectors": [".biz-phone", "[href^='tel:']", "a[href*='tel']"], "type": "text"},
            "categories": {"selectors": [".category-str-list a", "[data-testid='category']"], "type": "text_list"},
            "hours": {"selectors": [".hours-table", ".operating-hours"], "type": "text"},
            "price_range": {"selectors": [".price-range", ".businessAttribute--priceRange"], "type": "text"},
            "photos_count": {"selectors": [".photo-count", "[data-testid='photo-count']"], "type": "text"},
        },
        "list_items": {
            "reviews": {
                "container": ".review, [data-testid='review'], .comment",
                "fields": {
                    "author": ".user-name, .reviewer-name",
                    "rating": ".i-stars, [aria-label*='rating']",
                    "text": ".review-content p, .comment-text",
                    "date": ".rating-qualifier, .review-date",
                }
            }
        }
    },
    "directory": {
        "fields": {
            "business_name": {"selectors": ["h1", ".business-name", ".listing-title"], "type": "text"},
            "address": {"selectors": ["address", ".address", ".street-address", ".location"], "type": "text"},
            "phone": {"selectors": [".phone", "[href^='tel:']", ".contact-phone"], "type": "text"},
            "website": {"selectors": [".website a", "a[rel='nofollow']", ".business-website a"], "type": "attr", "attr": "href"},
            "rating": {"selectors": [".rating", ".stars", "[class*='rating']"], "type": "text"},
            "description": {"selectors": [".description", ".business-description", ".about"], "type": "text"},
        },
        "list_items": {
            "listings": {
                "container": ".listing, .search-result, .result-item, .business-card",
                "fields": {
                    "name": "h2, h3, .name, .title",
                    "address": ".address, .location",
                    "phone": ".phone, [href^='tel:']",
                    "rating": ".rating, .stars",
                }
            }
        }
    },
    "ecommerce": {
        "fields": {
            "product_name": {"selectors": ["h1", "#productTitle", ".product-title", ".product-name"], "type": "text"},
            "price": {"selectors": [".price", "#priceblock_ourprice", ".product-price", "[data-price]", ".current-price"], "type": "text"},
            "original_price": {"selectors": [".original-price", ".was-price", ".list-price", "s .price"], "type": "text"},
            "rating": {"selectors": [".rating", ".stars", "[class*='rating']", "#averageCustomerReviews"], "type": "text"},
            "review_count": {"selectors": [".review-count", "#acrCustomerReviewText"], "type": "text"},
            "availability": {"selectors": [".availability", "#availability", ".stock-status"], "type": "text"},
            "description": {"selectors": [".product-description", "#productDescription", ".description"], "type": "text"},
            "brand": {"selectors": [".brand", "#bylineInfo", "[itemprop='brand']"], "type": "text"},
            "sku": {"selectors": [".sku", "[itemprop='sku']", ".product-id"], "type": "text"},
            "images": {"selectors": [".product-image img", "#main-image", ".gallery img"], "type": "attr_list", "attr": "src"},
        },
        "list_items": {
            "reviews": {
                "container": ".review, .review-item, [data-hook='review']",
                "fields": {
                    "author": ".reviewer-name, .review-author, [data-hook='review-author']",
                    "rating": ".review-rating, [data-hook='review-star-rating']",
                    "title": ".review-title, [data-hook='review-title']",
                    "text": ".review-text, .review-body, [data-hook='review-body']",
                    "date": ".review-date, [data-hook='review-date']",
                }
            }
        }
    },
    "news": {
        "fields": {
            "headline": {"selectors": ["h1", ".headline", ".article-title", ".story-title"], "type": "text"},
            "author": {"selectors": [".author", ".byline", "[rel='author']", ".article-author"], "type": "text"},
            "published_date": {"selectors": ["time", ".date", ".published-date", "[datetime]"], "type": "text"},
            "category": {"selectors": [".category", ".section-label", ".topic"], "type": "text"},
            "summary": {"selectors": [".summary", ".article-summary", ".standfirst", "meta[name='description']"], "type": "text"},
        },
        "list_items": {}
    },
    "realestate": {
        "fields": {
            "price": {"selectors": [".price", ".listing-price", "[data-testid='price']"], "type": "text"},
            "address": {"selectors": [".address", ".property-address", "h1"], "type": "text"},
            "bedrooms": {"selectors": [".beds", ".bedrooms", "[data-testid='beds']"], "type": "text"},
            "bathrooms": {"selectors": [".baths", ".bathrooms", "[data-testid='baths']"], "type": "text"},
            "sqft": {"selectors": [".sqft", ".area", "[data-testid='sqft']"], "type": "text"},
            "description": {"selectors": [".description", ".property-description"], "type": "text"},
            "agent": {"selectors": [".agent-name", ".realtor-name"], "type": "text"},
        },
        "list_items": {}
    },
    "recipe": {
        "fields": {
            "title": {"selectors": ["h1", ".recipe-title", "[itemprop='name']"], "type": "text"},
            "prep_time": {"selectors": [".prep-time", "[itemprop='prepTime']"], "type": "text"},
            "cook_time": {"selectors": [".cook-time", "[itemprop='cookTime']"], "type": "text"},
            "servings": {"selectors": [".servings", "[itemprop='recipeYield']"], "type": "text"},
            "rating": {"selectors": [".rating", "[itemprop='ratingValue']"], "type": "text"},
            "calories": {"selectors": [".calories", "[itemprop='calories']"], "type": "text"},
        },
        "list_items": {
            "ingredients": {
                "container": ".ingredient, [itemprop='recipeIngredient'], .ingredients li",
                "fields": {"text": ""}
            },
            "steps": {
                "container": ".step, [itemprop='recipeInstructions'] li, .instructions li",
                "fields": {"text": ""}
            }
        }
    },
    "blog": {
        "fields": {
            "title": {"selectors": ["h1", ".post-title", ".entry-title"], "type": "text"},
            "author": {"selectors": [".author", ".byline", "[rel='author']"], "type": "text"},
            "date": {"selectors": ["time", ".date", ".published", ".post-date"], "type": "text"},
            "categories": {"selectors": [".category a", ".tag a", ".post-categories a"], "type": "text_list"},
        },
        "list_items": {}
    },
    "generic": {
        "fields": {
            "title": {"selectors": ["h1", "title"], "type": "text"},
            "description": {"selectors": ["meta[name='description']"], "type": "attr", "attr": "content"},
        },
        "list_items": {}
    },
}


# ---------------------------------------------------------------------------
# Smart extraction using site profiles
# ---------------------------------------------------------------------------

def smart_extract(html: str, site_type: str) -> dict[str, Any]:
    """Extract structured data using site-specific profiles."""
    schema = EXTRACTION_SCHEMAS.get(site_type, EXTRACTION_SCHEMAS["generic"])
    soup = BeautifulSoup(html, "lxml")
    result: dict[str, Any] = {"extracted_fields": {}, "extracted_lists": {}}

    # Extract single fields
    for field_name, field_config in schema.get("fields", {}).items():
        value = None
        for selector in field_config["selectors"]:
            try:
                el = soup.select_one(selector)
                if el:
                    ftype = field_config.get("type", "text")
                    if ftype == "text":
                        value = el.get_text(strip=True)
                    elif ftype == "attr":
                        value = el.get(field_config.get("attr", ""), "")
                    elif ftype == "text_list":
                        elements = soup.select(selector)
                        value = [e.get_text(strip=True) for e in elements if e.get_text(strip=True)]
                    elif ftype == "attr_list":
                        elements = soup.select(selector)
                        value = [e.get(field_config.get("attr", ""), "") for e in elements]

                    if value:
                        break
            except Exception:
                continue

        if value:
            result["extracted_fields"][field_name] = value

    # Extract list items (reviews, listings, etc.)
    for list_name, list_config in schema.get("list_items", {}).items():
        items = []
        containers = soup.select(list_config["container"])

        for container in containers[:20]:  # Limit to 20 items
            item = {}
            for field_name, selector in list_config["fields"].items():
                if not selector:
                    item[field_name] = container.get_text(strip=True)
                else:
                    el = None
                    for sel in selector.split(", "):
                        el = container.select_one(sel.strip())
                        if el:
                            break
                    if el:
                        item[field_name] = el.get_text(strip=True)
            if item:
                items.append(item)

        if items:
            result["extracted_lists"][list_name] = items

    return result


def get_ai_context_for_site(site_type: str) -> str:
    """Return additional AI prompt context based on site type."""
    contexts = {
        "yelp": "This is a Yelp business listing. Focus on: business reputation, review sentiment trends, and key complaints/praises.",
        "directory": "This is a business directory listing. Focus on: business details, contact info accuracy, and competitive positioning.",
        "ecommerce": "This is a product page. Focus on: pricing analysis, product features, customer satisfaction from reviews, and purchase recommendations.",
        "news": "This is a news article. Focus on: factual summary, key claims, sources cited, and potential bias.",
        "realestate": "This is a real estate listing. Focus on: property value analysis, location benefits, and comparison with market rates.",
        "recipe": "This is a recipe page. Focus on: nutritional info, difficulty level, ingredient substitutions, and tips.",
        "blog": "This is a blog post. Focus on: key takeaways, credibility of claims, and actionable advice.",
    }
    return contexts.get(site_type, "Analyze this page comprehensively.")
