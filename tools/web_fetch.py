"""
web_fetch — fetch the contents of a specific URL.

Used by Lila to inspect brand websites, read visual references, and pull
product pages before proposing directions. Always fetch the brand site first
if a URL is provided in the brief.

Token optimisations applied:
  1. Results are truncated to MAX_FETCH_CHARS (~1,000 tokens) — brand voice
     and palette cues are in the first section; nav/footer boilerplate is not.
  2. Results are cached in session_cache for the session lifetime — Lila may
     reference the same URL during directions and again during image prompts.
     No need to re-fetch identical content.
"""

from memory.cache import session_cache

MAX_FETCH_CHARS = 4_000   # ~1,000 tokens — more than enough for brand voice cues


def web_fetch(url: str) -> dict:
    """
    Fetch the text content of a URL, with truncation and session caching.

    Args:
        url: Full URL including scheme (https://...)

    Returns:
        {"content": str, "url": str, "cached": bool}
        {"error": str} on failure — say what failed, do not invent content
    """
    # Check cache first
    cached = session_cache.get("web_fetch", url=url)
    if cached is not None:
        return {**cached, "cached": True}

    # Claude Managed Agents provides web fetch as a built-in tool in production.
    # This module documents the interface and applies post-processing.
    # In production, the platform's native result flows through this truncation logic.
    raise NotImplementedError(
        "web_fetch is provided natively by Claude Managed Agents in production. "
        "Post-processing (truncation + caching) is applied via the wrapper below."
    )


def process_fetch_result(raw_content: str, url: str) -> dict:
    """
    Post-process a raw web fetch result from Claude Managed Agents.

    Truncates to MAX_FETCH_CHARS and writes to session cache.
    Call this after receiving a native web_fetch result to apply
    token optimisation before passing content back into context.

    Args:
        raw_content: Full text content returned by the platform tool
        url:         The URL that was fetched

    Returns:
        {"content": str, "url": str, "cached": bool, "truncated": bool}
    """
    truncated = len(raw_content) > MAX_FETCH_CHARS
    content = raw_content[:MAX_FETCH_CHARS]
    if truncated:
        content += "\n\n[Content truncated to first 4,000 characters for token efficiency]"

    result = {
        "content": content,
        "url": url,
        "cached": False,
        "truncated": truncated,
    }

    session_cache.set(result, "web_fetch", url=url)
    return result
