"""
image_search — find real-world visual references before generating assets.

Lila uses this before every generate_image call to ground the visual direction
in real environments, product category cues, wardrobe, materials, or photography style.
Do not skip this step and jump straight to generation.
"""


def image_search(query: str, max_results: int = 5) -> dict:
    """
    Search for images on the web. Returns image URLs and metadata.

    Args:
        query: Descriptive search query (e.g. "editorial linen bedding flat lay natural light")
        max_results: Number of results to return (default 5, max 10)

    Returns:
        {"images": [{"url": str, "title": str, "source": str}]}
        {"error": str} on failure
    """
    # Claude Managed Agents provides image search as a built-in tool.
    # This stub exists for local unit testing only.
    raise NotImplementedError(
        "image_search is provided natively by Claude Managed Agents in production."
    )
