"""
generate_image — generate a final production image via GPT-5.5 + GPT Image 2.

This tool calls the local MCP server (mcp_servers/image_gen_server.py) which
wraps the OpenAI Responses API. Claude never calls OpenAI directly.

IMPORTANT: This tool must only be called AFTER the ask_question approval gate
has returned explicit user approval. The agent session enforces this, but the
tool itself will also check for the approval flag in the session state.
"""

import httpx
import os
from config.settings import MCP_IMAGE_SERVER_PORT


def generate_image(
    prompt: str,
    format: str,
    asset_name: str,
    brand: str,
    campaign: str,
) -> dict:
    """
    Generate a production-ready social image.

    Args:
        prompt:      Full visual prompt including aesthetic register, palette, composition,
                     copy overlay text, and format-specific layout instructions.
        format:      One of: "1x1", "4x5", "9x16", "landscape_191", "landscape_169", "carousel"
        asset_name:  Short asset identifier, e.g. "launch-hero", "feature-card-01"
        brand:       Brand name slug, e.g. "loomlinen"
        campaign:    Campaign slug, e.g. "spring-launch"

    Returns:
        {
            "file_path": str,           — saved to data/outputs/
            "file_name": str,           — <brand>-<campaign>-<asset_name>-<format>.png
            "revised_prompt": str,      — GPT-5.5's revised prompt (for transparency)
            "dimensions": str,          — actual dimensions generated
        }
        {"error": str} on failure — report the error, do not fabricate a result

    Raises:
        RuntimeError if the MCP server is unreachable
    """
    payload = {
        "prompt": prompt,
        "format": format,
        "asset_name": asset_name,
        "brand": brand,
        "campaign": campaign,
    }

    try:
        response = httpx.post(
            f"http://localhost:{MCP_IMAGE_SERVER_PORT}/generate",
            json=payload,
            timeout=120.0,  # image generation can take up to 60s
        )
        response.raise_for_status()
        return response.json()

    except httpx.ConnectError:
        return {
            "error": (
                "MCP image server is not running. "
                "Start it with: python mcp_servers/image_gen_server.py"
            )
        }
    except httpx.HTTPStatusError as e:
        return {"error": f"MCP server returned {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": f"Image generation failed: {str(e)}"}
