from __future__ import annotations

import re


_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.IGNORECASE)
_XML_TAG_RE = re.compile(r"</?\w+[^>]*>")


def sanitize_output(text: str) -> str:
    if not text:
        return ""
    cleaned = _THINK_RE.sub("", text)
    # strip generic xml-like tags, including stray <think>
    cleaned = _XML_TAG_RE.sub("", cleaned)
    # collapse excessive blank lines
    cleaned = re.sub(r"\n\n\n+", "\n\n", cleaned).strip()
    return cleaned
