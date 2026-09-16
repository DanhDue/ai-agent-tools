#!/usr/bin/env python3
"""Shared utilities for normalizing epic slugs and parsing YAML frontmatter.

Used by sync_task_status.py and compute_execution_order.py to ensure consistent
behavior across all epic lifecycle tooling scripts.
"""
import re

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def sanitize_slug(raw: str | None) -> str | None:
    """Normalize and strip delimiters, quotes, and markdown formatting from an epic slug.

    Handles:
    - Markdown links: [slug](url) or [`slug`](url)
    - HTML tags / comments: <code>slug</code> or slug <!-- note -->
    - Quotes: "slug", 'slug', “slug”, ‘slug’
    - Markdown formatting: `slug`, **slug**, *slug*, ~~slug~~
    - Trailing annotations: slug (description) or slug - description
    - Trailing punctuation: slug:, slug, slug.
    """
    if not raw:
        return None
    cleaned = raw.strip()
    link_match = re.match(r"^\[([^\]]+)\](?:\([^)]*\))?", cleaned)
    if link_match:
        cleaned = link_match.group(1).strip()
    cleaned = re.sub(r"<!--.*?-->", "", cleaned).strip()
    cleaned = re.sub(r"<[^>]+>", "", cleaned).strip()
    if " " in cleaned or "(" in cleaned:
        cleaned = re.split(r"[\s(]", cleaned, maxsplit=1)[0]
    cleaned = cleaned.strip("`'\"“”‘’*~:,.;[]() \t\r\n")
    return cleaned or None


def parse_frontmatter(text: str) -> dict:
    """Parse YAML frontmatter delimited by leading '---' blocks.

    Strips double quotes, single quotes, and backticks around values.
    """
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip('"\'`')
    return fields
