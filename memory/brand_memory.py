"""
brand_memory.py — store and retrieve what Lila learns about each brand across sessions.

Memory is NEVER saved automatically. Lila must:
  1. Propose the exact memory entry for user review (Production Rule #2)
  2. Wait for explicit confirmation
  3. Only then call save_brand_memory()

Memory is loaded at the start of each session and injected into the brief
by scripts/run_agent.py so Lila has brand history from the first message.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

MEMORY_DIR = Path(__file__).parent.parent / "data" / "memory"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


# ── Schema ────────────────────────────────────────────────────────────────────

MEMORY_SCHEMA = {
    "approved_register":  str,   # e.g. "Editorial Restraint"
    "palette": dict,             # e.g. {"primary": "#F5F0E8", "accent": "#8B4513", "text": "#1A1A1A"}
    "copy_voice": str,           # e.g. "quiet, specific, no hype — short declarative sentences"
    "formats_used": list,        # e.g. ["4x5", "9x16"]
    "what_worked": str,          # e.g. "Tactile close-ups outperformed lifestyle shots 3:1"
    "what_to_avoid": str,        # e.g. "Centered layouts, pastel overlays, generic lifestyle"
    "campaign": str,             # The campaign this learning came from
    "session_id": str,
    "saved_at": str,             # ISO timestamp
}


# ── Write ─────────────────────────────────────────────────────────────────────

def save_brand_memory(brand: str, learnings: dict) -> dict:
    """
    Append a new memory entry for a brand.

    Only call this after the user has explicitly approved the memory block.
    Never call this automatically at session end.

    Args:
        brand:     Brand slug, e.g. "emberoak" (must match the brand used in file naming)
        learnings: Dict matching MEMORY_SCHEMA. Missing keys are allowed — partial memory
                   is better than no memory.

    Returns:
        {"saved": True, "entry_count": int, "file": str}
        {"error": str} on failure
    """
    try:
        learnings["saved_at"] = datetime.now(timezone.utc).isoformat()
        path = _brand_path(brand)
        entries = _load_raw(brand)
        entries.append(learnings)
        path.write_text(json.dumps(entries, indent=2))
        return {
            "saved": True,
            "entry_count": len(entries),
            "file": str(path),
        }
    except Exception as e:
        return {"error": f"save_brand_memory failed: {str(e)}"}


# ── Read ──────────────────────────────────────────────────────────────────────

def load_brand_memory(brand: str) -> list[dict]:
    """
    Return all stored memory entries for a brand, newest first.

    Returns empty list if no memory exists — not an error.
    """
    entries = _load_raw(brand)
    return list(reversed(entries))  # Most recent first


def get_latest_memory(brand: str) -> dict | None:
    """Return only the most recent memory entry, or None."""
    entries = load_brand_memory(brand)
    return entries[0] if entries else None


def format_for_prompt(brand: str) -> str:
    """
    Format brand memory as a context block for injection into the session brief.

    Called by scripts/run_agent.py before the session starts.
    Returns empty string if no memory exists (first session for this brand).
    """
    memory = get_latest_memory(brand)
    if not memory:
        return ""

    lines = [f"## Brand Memory: {brand}"]
    lines.append(f"From the **{memory.get('campaign', 'previous')}** campaign:\n")

    if memory.get("approved_register"):
        lines.append(f"- **Register:** {memory['approved_register']}")
    if memory.get("palette"):
        palette_str = ", ".join(f"{k}: {v}" for k, v in memory["palette"].items())
        lines.append(f"- **Palette:** {palette_str}")
    if memory.get("copy_voice"):
        lines.append(f"- **Copy voice:** {memory['copy_voice']}")
    if memory.get("formats_used"):
        lines.append(f"- **Formats:** {', '.join(memory['formats_used'])}")
    if memory.get("what_worked"):
        lines.append(f"- **What worked:** {memory['what_worked']}")
    if memory.get("what_to_avoid"):
        lines.append(f"- **What to avoid:** {memory['what_to_avoid']}")

    lines.append(
        "\nUse these as defaults in your direction proposals. "
        "Present them as *based on your last campaign* and let the user override."
    )

    return "\n".join(lines)


def list_brands() -> list[str]:
    """Return all brand slugs that have stored memory."""
    return [p.stem for p in MEMORY_DIR.glob("*.json")]


def delete_brand_memory(brand: str) -> dict:
    """
    Delete all memory for a brand. Requires explicit user intent — do not
    call this automatically. Used for GDPR-style erasure or brand offboarding.
    """
    path = _brand_path(brand)
    if not path.exists():
        return {"error": f"No memory found for brand: {brand}"}
    path.unlink()
    return {"deleted": True, "brand": brand}


# ── Internal ──────────────────────────────────────────────────────────────────

def _brand_path(brand: str) -> Path:
    # Sanitise brand slug — no path traversal
    safe = "".join(c for c in brand if c.isalnum() or c in "-_")
    if not safe:
        raise ValueError(f"Invalid brand slug: {brand!r}")
    return MEMORY_DIR / f"{safe}.json"


def _load_raw(brand: str) -> list[dict]:
    try:
        path = _brand_path(brand)
        return json.loads(path.read_text()) if path.exists() else []
    except Exception:
        return []
