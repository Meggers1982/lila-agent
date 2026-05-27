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

Token optimisations active:
  - System prompt cached via deploy.py (--system-cache-control ephemeral)
  - Reference images compressed to 1024px max before base64 encoding
  - Per-session token budget enforced (see config/settings.py)
  - Token usage logged per turn for cost visibility
"""

import argparse
import base64
import io
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
from config.settings import (
    MAX_BUDGET_USD, PROMPT_VERSION,
    REFERENCE_IMAGE_MAX_PX, REFERENCE_IMAGE_JPEG_QUALITY,
    MAX_INPUT_TOKENS_PER_SESSION, MAX_OUTPUT_TOKENS_PER_SESSION,
    BUDGET_WARNING_USD,
)
from agent.session import SessionState, Phase
from guardrails.input_validator import validate_brief
from memory.brand_memory import format_for_prompt
from memory.cache import session_cache
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


# ── Brief input ───────────────────────────────────────────────────────────────

def get_brief(cli_brief: str | None) -> str:
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


# ── Reference image handling ──────────────────────────────────────────────────

def compress_reference_image(path: Path) -> bytes:
    """
    Resize image so longest edge is REFERENCE_IMAGE_MAX_PX and encode as JPEG.
    Reduces token cost for large source files with negligible quality impact
    for palette/composition reading.
    """
    try:
        from PIL import Image
    except ImportError:
        console.print("[yellow]Warning:[/yellow] pillow not installed — skipping compression. Run: pip install pillow")
        return path.read_bytes()

    with Image.open(path) as img:
        img = img.convert("RGB")
        w, h = img.size
        original_size = path.stat().st_size

        if max(w, h) > REFERENCE_IMAGE_MAX_PX:
            ratio = REFERENCE_IMAGE_MAX_PX / max(w, h)
            new_w, new_h = int(w * ratio), int(h * ratio)
            img = img.resize((new_w, new_h), Image.LANCZOS)
            console.print(f"[dim]  Resized {path.name}: {w}×{h} → {new_w}×{new_h}[/dim]")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=REFERENCE_IMAGE_JPEG_QUALITY)
        compressed = buf.getvalue()

        saving_pct = round((1 - len(compressed) / original_size) * 100)
        if saving_pct > 0:
            console.print(f"[dim]  Compressed {path.name}: {original_size//1024}KB → {len(compressed)//1024}KB ({saving_pct}% smaller)[/dim]")

        return compressed


def load_reference_images(paths: list[str]) -> list[dict]:
    """
    Load, compress, and base64-encode reference images as API content blocks.
    Images are compressed to REFERENCE_IMAGE_MAX_PX before encoding.
    """
    blocks = []
    if not paths:
        return blocks

    blocks.append({
        "type": "text",
        "text": (
            "The following images are visual references provided by the user. "
            "Read each one for aesthetic signals only: colour palette, composition style, "
            "typography treatment, density vs. negative space, photography mood, and register. "
            "Do NOT reproduce their layouts, subjects, or copy. "
            "Use them to inform your direction proposals — cite specific observations "
            "('the references use warm cream tones and strong negative space') "
            "rather than generic descriptions ('the references are minimal'). "
            "Read these once. Do not re-describe them on subsequent turns."
        )
    })

    loaded = 0
    for i, path_str in enumerate(paths):
        path = Path(path_str)
        if not path.exists():
            console.print(f"[yellow]Warning:[/yellow] Reference not found: {path_str} — skipping")
            continue

        suffix = path.suffix.lower()
        if suffix not in SUPPORTED_IMAGE_TYPES:
            console.print(f"[yellow]Warning:[/yellow] Unsupported type '{suffix}': {path_str} — skipping")
            continue

        try:
            image_bytes = compress_reference_image(path)
            image_data  = base64.standard_b64encode(image_bytes).decode("utf-8")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not load {path_str}: {e} — skipping")
            continue

        blocks.append({"type": "text", "text": f"Reference {i + 1} of {len(paths)} ({path.name}):"})
        blocks.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data},
        })
        loaded += 1

    if loaded > 0:
        blocks.append({"type": "text", "text": "End of reference images. Now read the brief below."})

    return blocks


def build_first_message(brief: str, reference_blocks: list[dict]) -> list[dict] | str:
    if not reference_blocks:
        return brief
    return reference_blocks + [{"type": "text", "text": brief}]


# ── Budget enforcement ────────────────────────────────────────────────────────

def check_session_budget(state: SessionState) -> bool:
    """
    Returns False and prints a warning if the session is approaching or over budget.
    Logs a warning at 75% of the token limit; hard-stops at 100%.
    """
    input_pct  = state.input_tokens_used  / MAX_INPUT_TOKENS_PER_SESSION
    output_pct = state.output_tokens_used / MAX_OUTPUT_TOKENS_PER_SESSION

    if input_pct >= 1.0 or output_pct >= 1.0:
        console.print(
            f"\n[red]Session token budget reached[/red] "
            f"({state.input_tokens_used:,} input / {state.output_tokens_used:,} output). "
            f"Stopping to avoid runaway costs. Estimated cost: ${state.estimated_cost_usd():.4f}"
        )
        return False

    if input_pct >= 0.75 or output_pct >= 0.75:
        console.print(
            f"[yellow]Token budget at {max(input_pct, output_pct):.0%}[/yellow] — "
            f"~{state.input_tokens_used:,} input tokens used. "
            f"Wrap up this session soon."
        )

    return True


# ── Session runner ────────────────────────────────────────────────────────────

def run_session(brief: str, reference_paths: list[str] | None = None):
    session_id = str(uuid.uuid4())[:8]
    state = SessionState(session_id=session_id)
    session_cache.clear()  # fresh cache for each session

    validation = validate_brief(brief)
    if not validation.valid:
        console.print(f"\n[red]Brief issue:[/red] {validation.error}")
        sys.exit(1)
    for warning in validation.warnings:
        console.print(f"[yellow]Note:[/yellow] {warning}")

    log_session_start(session_id, len(brief))

    # Compress and load reference images
    reference_blocks = load_reference_images(reference_paths or [])
    if reference_blocks:
        count = sum(1 for b in reference_blocks if b.get("type") == "image")
        console.print(f"[dim]{count} reference image(s) attached and compressed.[/dim]")

    # Inject brand memory
    brand_slug = state.brand or brief.split()[0].lower().strip(".,!?")
    brand_context = format_for_prompt(brand_slug)
    if brand_context:
        console.print(f"[dim]Brand memory found for '{brand_slug}' — injecting.[/dim]")
        brief = brand_context + "\n\n---\n\n" + brief

    agent_id = get_secret("CLAUDE_AGENT_ID")
    environment_id = get_secret("CLAUDE_ENVIRONMENT_ID")
    if not agent_id or not environment_id:
        console.print("\n[red]CLAUDE_AGENT_ID or CLAUDE_ENVIRONMENT_ID not set.[/red]")
        console.print("Run: python scripts/deploy.py")
        sys.exit(1)

    console.print(
        f"\n[dim]Session {session_id} | Prompt {PROMPT_VERSION} | "
        f"Budget ${MAX_BUDGET_USD} | Cache: {session_cache.size} entries[/dim]\n"
    )

    try:
        session = client.beta.agents.sessions.create(
            agent_id=agent_id,
            environment_id=environment_id,
        )

        first_content = build_first_message(brief, reference_blocks)
        messages = [{"role": "user", "content": first_content}]

        while True:
            # Hard budget check before each turn
            if not check_session_budget(state):
                break

            response = client.beta.agents.sessions.send(
                session_id=session.id,
                messages=messages,
            )

            # Track token usage if the platform returns it
            if hasattr(response, "usage") and response.usage:
                state.record_token_usage(
                    input_tokens=getattr(response.usage, "input_tokens", 0),
                    output_tokens=getattr(response.usage, "output_tokens", 0),
                )

            console.print(Markdown(response.content))

            if response.stop_reason == "end_turn":
                cost = state.estimated_cost_usd()
                console.print(
                    f"\n[dim]Session complete — "
                    f"{state.input_tokens_used:,} input / {state.output_tokens_used:,} output tokens | "
                    f"~${cost:.4f} estimated[/dim]"
                )
                log_session_complete(session_id, state.images_generated, cost)
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


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run a Lila session")
    parser.add_argument("--brief", help="Brief text (skips interactive prompt)")
    parser.add_argument(
        "--references", nargs="+", metavar="IMAGE",
        help="Path(s) to reference images. Compressed to 1024px before sending. "
             "Lila reads for palette/mood — does not copy them."
    )
    args = parser.parse_args()

    brief = get_brief(args.brief)
    if not brief:
        console.print("[red]No brief provided.[/red]")
        sys.exit(1)

    run_session(brief, reference_paths=args.references)


if __name__ == "__main__":
    main()
