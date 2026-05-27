"""
run_agent.py — start a Lila session on Claude Managed Agents.

Prompts for a product brief, opens a session, and streams Lila's responses.
The MCP image generation server must be running before you start.

Usage:
    # Terminal 1 — start the image generation server
    python mcp_servers/image_gen_server.py

    # Terminal 2 — run a session
    python scripts/run_agent.py
    python scripts/run_agent.py --brief "Product: Ember & Oak candles..."

    # With visual references (JPG, PNG, or WEBP)
    python scripts/run_agent.py --references img1.jpg img2.png
    python scripts/run_agent.py --brief "Candle launch" --references ref1.jpg ref2.jpg

References are passed as vision inputs alongside the brief. Lila reads them
for aesthetic signals — palette, composition, density, mood — and uses them
to inform direction proposals. She does not copy them.
"""

import argparse
import base64
import mimetypes
import sys
import uuid
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from config.secrets import ANTHROPIC_API_KEY, get_secret
from config.settings import MODEL_ID, MAX_BUDGET_USD, PROMPT_VERSION
from agent.session import SessionState, Phase
from guardrails.input_validator import validate_brief
from memory.brand_memory import format_for_prompt
from observability.logger import log_session_start, log_session_complete, log_error

console = Console()
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SUPPORTED_IMAGE_TYPES = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".webp": "image/webp",
    ".gif":  "image/gif",
}


def get_brief(cli_brief: str | None) -> str:
    """Get the brief from CLI arg or interactive prompt."""
    if cli_brief:
        return cli_brief

    console.print("\n[bold]Lila — Social Image Producer[/bold]")
    console.print("Describe your product, campaign, and what you need.\n")
    lines = []
    console.print("Brief (press Enter twice when done):")
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def load_reference_images(paths: list[str]) -> list[dict]:
    """
    Load reference images from disk and encode as base64 content blocks.

    Each image becomes a vision content block in the first message,
    preceded by a label so Lila knows it's a reference, not an asset to edit.

    Args:
        paths: List of file paths to images

    Returns:
        List of Anthropic API content blocks (image + text label pairs)
    """
    blocks = []

    if not paths:
        return blocks

    # Opening label — tells Lila what these images are for
    blocks.append({
        "type": "text",
        "text": (
            "The following images are visual references provided by the user. "
            "Read each one for aesthetic signals only: colour palette, composition style, "
            "typography treatment, density vs. negative space, photography mood, and register. "
            "Do NOT reproduce their layouts, subjects, or copy. "
            "Use them to inform your direction proposals — cite specific observations "
            "('the references use warm cream tones and strong negative space') "
            "rather than generic descriptions ('the references are minimal')."
        )
    })

    for i, path_str in enumerate(paths):
        path = Path(path_str)

        if not path.exists():
            console.print(f"[yellow]Warning:[/yellow] Reference image not found: {path_str} — skipping")
            continue

        suffix = path.suffix.lower()
        media_type = SUPPORTED_IMAGE_TYPES.get(suffix)
        if not media_type:
            console.print(f"[yellow]Warning:[/yellow] Unsupported image type '{suffix}': {path_str} — skipping. Use JPG, PNG, WEBP, or GIF.")
            continue

        try:
            image_data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not read {path_str}: {e} — skipping")
            continue

        # Label each image
        blocks.append({
            "type": "text",
            "text": f"Reference image {i + 1} of {len(paths)} ({path.name}):"
        })

        # The image itself
        blocks.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": image_data,
            }
        })

        console.print(f"[dim]Reference loaded: {path.name}[/dim]")

    # Closing instruction
    if len(blocks) > 1:
        blocks.append({
            "type": "text",
            "text": "End of reference images. Now read the brief below."
        })

    return blocks


def build_first_message(brief: str, reference_blocks: list[dict]) -> list[dict] | str:
    """
    Build the first user message content.

    If references are provided, returns a multipart content list (images + text).
    If no references, returns a plain string for cleaner API calls.
    """
    if not reference_blocks:
        return brief

    return reference_blocks + [{"type": "text", "text": brief}]


def run_session(brief: str, reference_paths: list[str] | None = None):
    session_id = str(uuid.uuid4())[:8]
    state = SessionState(session_id=session_id)

    # Validate brief
    validation = validate_brief(brief)
    if not validation.valid:
        console.print(f"\n[red]Brief issue:[/red] {validation.error}")
        sys.exit(1)

    for warning in validation.warnings:
        console.print(f"[yellow]Note:[/yellow] {warning}")

    log_session_start(session_id, len(brief))

    # Load reference images if provided
    reference_blocks = load_reference_images(reference_paths or [])
    if reference_blocks:
        count = sum(1 for b in reference_blocks if b.get("type") == "image")
        console.print(f"[dim]{count} reference image(s) attached.[/dim]")

    # Inject brand memory
    brand_slug = state.brand or brief.split()[0].lower().strip(".,!?")
    brand_context = format_for_prompt(brand_slug)
    if brand_context:
        console.print(f"[dim]Brand memory found for '{brand_slug}' — injecting into session.[/dim]")
        brief = brand_context + "\n\n---\n\n" + brief

    agent_id = get_secret("CLAUDE_AGENT_ID")
    environment_id = get_secret("CLAUDE_ENVIRONMENT_ID")

    if not agent_id or not environment_id:
        console.print("\n[red]CLAUDE_AGENT_ID or CLAUDE_ENVIRONMENT_ID not set.[/red]")
        console.print("Run: python scripts/deploy.py")
        sys.exit(1)

    console.print(f"\n[dim]Session {session_id} | Prompt {PROMPT_VERSION} | Budget ${MAX_BUDGET_USD}[/dim]\n")

    try:
        session = client.beta.agents.sessions.create(
            agent_id=agent_id,
            environment_id=environment_id,
        )

        first_content = build_first_message(brief, reference_blocks)
        messages = [{"role": "user", "content": first_content}]

        while True:
            response = client.beta.agents.sessions.send(
                session_id=session.id,
                messages=messages,
            )

            console.print(Markdown(response.content))

            if response.stop_reason == "end_turn":
                log_session_complete(session_id, state.images_generated, 0.0)
                break

            console.print("\n[dim]You:[/dim] ", end="")
            user_input = input().strip()
            if user_input.lower() in ("exit", "quit", "done"):
                break

            messages = [{"role": "user", "content": user_input}]

    except Exception as e:
        log_error(session_id, str(e))
        console.print(f"\n[red]Session error:[/red] {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run a Lila session")
    parser.add_argument("--brief", help="Brief text (skips interactive prompt)")
    parser.add_argument(
        "--references",
        nargs="+",
        metavar="IMAGE",
        help="Path(s) to reference images for aesthetic inspiration (JPG, PNG, WEBP). "
             "Lila reads these for palette, composition, and mood — she does not copy them."
    )
    args = parser.parse_args()

    brief = get_brief(args.brief)
    if not brief:
        console.print("[red]No brief provided.[/red]")
        sys.exit(1)

    run_session(brief, reference_paths=args.references)


if __name__ == "__main__":
    main()
