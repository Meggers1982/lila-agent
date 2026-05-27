"""
web_search — search the web for brand research, visual references, and product context.

Used by Lila to research brand websites, competitors, visual trends, and product categories
before proposing visual directions.
"""

import httpx
from config.secrets import get_secret


def web_search(query: str) -> dict:
    """
    Search the web. Returns a list of results with title, url, and snippet.

    Args:
        query: Search query string (keep it specific, 1–6 words works best)

    Returns:
        {"results": [{"title": str, "url": str, "snippet": str}]}
        {"error": str} on failure — do not fabricate results on error
    """
    # Claude Managed Agents provides web search as a built-in tool.
    # This module is the standalone fallback for local testing.
    # In production, the platform's native web_search is used.
    raise NotImplementedError(
        "web_search is provided natively by Claude Managed Agents in production. "
        "This stub exists for local unit testing only. "
        "Use scripts/run_agent.py to run a real session."
    )
