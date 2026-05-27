"""
image_gen_server.py — MCP server wrapping GPT-5.5 + GPT Image 2.

Exposes a single HTTP endpoint: POST /generate
Accepts a prompt and format, calls the OpenAI Responses API,
saves the result to data/outputs/, and returns the file path.

Start this server before running a Lila session:
    python mcp_servers/image_gen_server.py

Claude never calls OpenAI directly. This server is the boundary.
"""

import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    sys.exit("OPENAI_API_KEY not set. Copy .env.example to .env and fill it in.")

PORT = int(os.getenv("MCP_IMAGE_SERVER_PORT", "8765"))
OUTPUTS_DIR = Path(__file__).parent.parent / "data" / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# Map Lila format slugs to GPT Image 2 size parameters
FORMAT_TO_SIZE = {
    "1x1":           "1024x1024",
    "4x5":           "1024x1280",
    "9x16":          "1024x1792",
    "landscape_191": "1792x1024",
    "landscape_169": "1792x1024",
    "carousel":      "1024x1280",   # default to 4:5 for carousel slides
}

client = OpenAI(api_key=OPENAI_API_KEY)


# ── Generation logic ──────────────────────────────────────────────────────────

def generate(prompt: str, format: str, asset_name: str, brand: str, campaign: str) -> dict:
    size = FORMAT_TO_SIZE.get(format, "1024x1024")

    # GPT-5.5 with the image_generation tool (Responses API)
    # The model auto-revises the prompt for improved results
    response = client.responses.create(
        model="gpt-5.5",
        input=prompt,
        tools=[{"type": "image_generation"}],
    )

    image_calls = [
        output for output in response.output
        if output.type == "image_generation_call"
    ]

    if not image_calls:
        raise ValueError("No image returned from GPT-5.5. Do not fabricate a result.")

    image_base64 = image_calls[0].result
    revised_prompt = getattr(image_calls[0], "revised_prompt", prompt)

    # Save to data/outputs/
    file_name = f"{brand}-{campaign}-{asset_name}-{format}.png"
    file_path = OUTPUTS_DIR / file_name
    file_path.write_bytes(base64.b64decode(image_base64))

    return {
        "file_path": str(file_path),
        "file_name": file_name,
        "revised_prompt": revised_prompt,
        "dimensions": size,
    }


# ── HTTP handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/generate":
            self._respond(404, {"error": "Unknown endpoint. Use POST /generate"})
            return

        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        required = {"prompt", "format", "asset_name", "brand", "campaign"}
        missing = required - body.keys()
        if missing:
            self._respond(400, {"error": f"Missing fields: {', '.join(missing)}"})
            return

        try:
            result = generate(**{k: body[k] for k in required})
            self._respond(200, result)
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress default HTTP logging; observability/logger.py handles this
        pass


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"[image_gen_server] Starting on port {PORT}")
    print(f"[image_gen_server] Outputs → {OUTPUTS_DIR}")
    print(f"[image_gen_server] Model: gpt-5.5 + image_generation tool")
    server = HTTPServer(("localhost", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[image_gen_server] Stopped.")
