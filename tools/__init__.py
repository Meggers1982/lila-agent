"""
Tool registry — every tool Lila can call.

Each tool is a plain function that does one thing and returns a result.
No tool imports from agent/. Tools have no knowledge of the agent that uses them.

The TOOL_REGISTRY list is what gets passed to the Claude Platform agent config
in scripts/deploy.py. Add a new tool here after creating its module.
"""

from tools.web_search import web_search
from tools.web_fetch import web_fetch
from tools.image_search import image_search
from tools.image_generate import generate_image
from tools.file_io import save_file, fetch_stored_file
from tools.ask_question import ask_question

TOOL_REGISTRY = [
    web_search,
    web_fetch,
    image_search,
    generate_image,
    save_file,
    fetch_stored_file,
    ask_question,
]

__all__ = [
    "web_search",
    "web_fetch",
    "image_search",
    "generate_image",
    "save_file",
    "fetch_stored_file",
    "ask_question",
    "TOOL_REGISTRY",
]
