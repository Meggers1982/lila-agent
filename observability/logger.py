"""
logger.py — structured, PII-safe logging for Lila sessions.

Every session run is logged with: session_id, prompt_version, model,
phase transitions, tool calls, token usage, cost estimate, and errors.

PII policy: briefs may contain brand names and product details — these
are logged as-is (they're business data, not personal data). If future
sessions involve personal customer data, add masking here first.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from config.settings import LOG_LEVEL, PROMPT_VERSION, MODEL_ID

# ── Setup ─────────────────────────────────────────────────────────────────────

LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.DEBUG),
    format="%(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / f"lila-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.log"),
    ],
)

logger = logging.getLogger("lila")


# ── Structured log helpers ────────────────────────────────────────────────────

def _log(level: str, event: str, session_id: str, **kwargs):
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "event": event,
        "session_id": session_id,
        "prompt_version": PROMPT_VERSION,
        "model": MODEL_ID,
        **kwargs,
    }
    getattr(logger, level.lower())(json.dumps(record))


def log_session_start(session_id: str, brief_length: int):
    _log("INFO", "session_start", session_id, brief_length=brief_length)


def log_phase_transition(session_id: str, from_phase: str, to_phase: str):
    _log("INFO", "phase_transition", session_id, from_phase=from_phase, to_phase=to_phase)


def log_tool_call(session_id: str, tool_name: str, input_summary: str):
    _log("DEBUG", "tool_call", session_id, tool=tool_name, input_summary=input_summary[:200])


def log_tool_result(session_id: str, tool_name: str, success: bool, error: str = ""):
    _log("DEBUG", "tool_result", session_id, tool=tool_name, success=success, error=error)


def log_approval_gate(session_id: str, approved: bool, asset_count: int):
    _log("INFO", "approval_gate", session_id, approved=approved, asset_count=asset_count)


def log_image_generated(session_id: str, file_name: str, format: str):
    _log("INFO", "image_generated", session_id, file_name=file_name, format=format)


def log_session_complete(session_id: str, images_generated: int, total_cost_usd: float):
    _log("INFO", "session_complete", session_id,
         images_generated=images_generated,
         total_cost_usd=round(total_cost_usd, 4))


def log_error(session_id: str, error: str, context: str = ""):
    _log("ERROR", "error", session_id, error=error, context=context)
