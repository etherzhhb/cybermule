import json
import re
from typing import List, Optional, Any

from markdown_it import MarkdownIt


def extract_json_blocks(text: str) -> List[dict]:
    """
    Extract all valid JSON code blocks from the given Markdown text.

    Args:
        text: Full LLM response or markdown content.

    Returns:
        A list of successfully parsed JSON objects.
    """
    md = MarkdownIt()
    tokens = md.parse(text)
    results = []

    for t in tokens:
        if t.type == "fence" and t.info.strip() in ("json", ""):
            try:
                parsed = json.loads(t.content)
                results.append(parsed)
            except json.JSONDecodeError:
                continue

    return results


def extract_first_json_block(text: str) -> Optional[dict]:
    """
    Extract only the first valid JSON code block (```json) from the text.

    Args:
        text: Full LLM response.

    Returns:
        Parsed JSON dict or None if not found.
    """
    blocks = extract_json_blocks(text)
    return blocks[0] if blocks else None


def extract_code_blocks(text: str) -> List[str]:
    md = MarkdownIt()
    tokens = md.parse(text)
    return [
        t.content for t in tokens
        if t.type == "fence" and t.info.strip() in ("python", "")
    ]
