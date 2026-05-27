"""
test_tool.py — quickly test a single tool in isolation without running a full session.

Usage:
    python scripts/test_tool.py image_generate
    python scripts/test_tool.py file_io
"""

import sys
import base64
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()


def test_image_generate():
    """Test the MCP image generation server with a simple prompt."""
    print("Testing generate_image → MCP server → GPT Image 2\n")
    print("(Make sure mcp_servers/image_gen_server.py is running)\n")

    from tools.image_generate import generate_image
    result = generate_image(
        prompt=(
            "Editorial product photo of a soy candle in a warm amber jar. "
            "Natural linen surface, soft morning light from the left. "
            "Minimal props: dried lavender sprig, cream card stock. "
            "4:5 portrait, warm neutrals, Editorial Restraint register."
        ),
        format="4x5",
        asset_name="test-launch-hero",
        brand="testbrand",
        campaign="tooltest",
    )

    if "error" in result:
        print(f"✗ FAILED: {result['error']}")
        sys.exit(1)

    print(f"✓ Generated: {result['file_name']}")
    print(f"  Path:     {result['file_path']}")
    print(f"  Size:     {result.get('dimensions', 'unknown')}")
    print(f"  Revised:  {result.get('revised_prompt', '')[:100]}...")


def test_file_io():
    """Test save and fetch round-trip."""
    print("Testing file_io save → fetch round-trip\n")

    from tools.file_io import save_file, fetch_stored_file

    content = b"fake PNG content for test"
    encoded = base64.b64encode(content).decode()
    name = "testbrand-tooltest-hero-4x5.png"

    save_result = save_file(name, encoded)
    if "error" in save_result:
        print(f"✗ save_file FAILED: {save_result['error']}")
        sys.exit(1)
    print(f"✓ Saved: {save_result['file_path']} ({save_result['size_bytes']} bytes)")

    fetch_result = fetch_stored_file(name)
    if "error" in fetch_result:
        print(f"✗ fetch_stored_file FAILED: {fetch_result['error']}")
        sys.exit(1)

    recovered = base64.b64decode(fetch_result["content_base64"])
    assert recovered == content, "Content mismatch!"
    print(f"✓ Fetched and content matches")


TOOLS = {
    "image_generate": test_image_generate,
    "file_io": test_file_io,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in TOOLS:
        print(f"Usage: python scripts/test_tool.py <tool>")
        print(f"Available: {', '.join(TOOLS.keys())}")
        sys.exit(1)

    TOOLS[sys.argv[1]]()
