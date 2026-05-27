"""
web_fetch — fetch the contents of a specific URL.

Used by Lila to inspect brand websites, read visual references, and pull
product pages before proposing directions. Always fetch the brand site first
if a URL is provided in the brief.
"""


def web_fetch(url: str) -> dict:
    """
    Fetch the text content of a URL.

    Args:
        url: Full URL including scheme (https://...)

    Returns:
        {"content": str, "url": str}
        {"error": str} on failure — say what failed, do not invent content
    """
    # Claude Managed Agents provides web fetch as a built-in tool.
    # This stub exists for local unit testing only.
    raise NotImplementedError(
        "web_fetch is provided natively by Claude Managed Agents in production."
    )
