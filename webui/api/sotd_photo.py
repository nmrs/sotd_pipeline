"""Extract SOTD header photo/link URLs from comment bodies."""

from __future__ import annotations

import re
from typing import Optional

_MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


def extract_sotd_header_link(body: Optional[str]) -> Optional[str]:
    """Return the first markdown link URL on the SOTD header line, or None.

    The header is the first non-empty line of the comment body. Any markdown
    link on that line counts (no image-host inference); only the first URL
    is returned.
    """
    if not body:
        return None

    header = ""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped:
            header = stripped
            break

    if not header:
        return None

    match = _MARKDOWN_LINK.search(header)
    if not match:
        return None

    url = match.group(2).strip()
    return url or None


def prefer_first_photo_url(existing: Optional[str], new: Optional[str]) -> Optional[str]:
    """Keep the first non-null photo URL when merging mismatch items."""
    return existing if existing else new
