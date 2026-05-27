"""
Global settings. All values come from environment variables — never hardcoded.
Import from here, never from os.getenv() directly in other modules.
"""

import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# ── Models ────────────────────────────────────────────────────────────────────
# Creative tasks: direction proposals, image prompt writing, aesthetic judgement
CREATIVE_MODEL = "claude-opus-4-6"

# Utility tasks: brief validation classification, memory proposal formatting.
# ~20x cheaper than Opus. Switch session to this model for non-creative turns
# once Claude Managed Agents supports per-turn model selection.
# For now both resolve to Opus via the platform agent definition.
UTILITY_MODEL = "claude-haiku-4-5-20251001"

# The model registered with the Claude Platform agent (used by deploy.py)
# Change to UTILITY_MODEL for non-creative turns when the platform supports it.
MODEL_ID = CREATIVE_MODEL

# ── Budget ────────────────────────────────────────────────────────────────────
MAX_BUDGET_USD = float(os.getenv("MAX_BUDGET_USD", "25"))

# Soft warning threshold — log a warning when a session exceeds this
# before hitting the hard cap. Gives you visibility before cutoff.
BUDGET_WARNING_USD = MAX_BUDGET_USD * 0.75

# Per-session token budget (hard cap enforced in run_agent.py)
# Rough estimate: 8-turn Opus session ≈ 12,000 input + 500 output per turn
# = ~100,000 input tokens + ~4,000 output tokens total
MAX_INPUT_TOKENS_PER_SESSION  = 120_000
MAX_OUTPUT_TOKENS_PER_SESSION =   8_000

# ── Token optimisation ────────────────────────────────────────────────────────
# Max characters returned from web_fetch before truncation (~1,000 tokens)
WEB_FETCH_MAX_CHARS = 4_000

# Max longest-edge pixels for reference images before base64 encoding
# 1024px is enough for palette/composition reading; larger adds cost, not quality
REFERENCE_IMAGE_MAX_PX = 1_024

# JPEG quality for compressed reference images (85 = good quality, ~60% size reduction)
REFERENCE_IMAGE_JPEG_QUALITY = 85

# ── Production rules ──────────────────────────────────────────────────────────
REQUIRE_APPROVAL_BEFORE_GENERATION = True   # Production Rule #1 — never disable
AUTO_SAVE_MEMORIES = False
MAX_CLARIFYING_QUESTIONS_PER_ROUND = 3

# ── MCP server ────────────────────────────────────────────────────────────────
MCP_IMAGE_SERVER_PORT = int(os.getenv("MCP_IMAGE_SERVER_PORT", "8765"))
MCP_IMAGE_SERVER_URL = f"http://localhost:{MCP_IMAGE_SERVER_PORT}"

# ── Paths ─────────────────────────────────────────────────────────────────────
from pathlib import Path
ROOT        = Path(__file__).parent.parent
OUTPUTS_DIR = ROOT / "data" / "outputs"
INPUTS_DIR  = ROOT / "data" / "inputs"
MEMORY_DIR  = ROOT / "data" / "memory"
PROMPTS_DIR = ROOT / "prompts"
SKILLS_DIR  = ROOT / "skills"

# ── Prompt versioning ─────────────────────────────────────────────────────────
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1.4.0")

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = "WARNING" if IS_PRODUCTION else "DEBUG"
