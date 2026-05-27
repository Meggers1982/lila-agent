"""
Global settings. All values come from environment variables — never hardcoded.
Import from here, never from os.getenv() directly in other modules.
"""

import os
from dotenv import load_dotenv

load_dotenv()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# ── Model ─────────────────────────────────────────────────────────────────────
MODEL_ID = "claude-opus-4-6"
EFFORT = "high"

# ── Budget ────────────────────────────────────────────────────────────────────
MAX_BUDGET_USD = float(os.getenv("MAX_BUDGET_USD", "25"))

# ── Production rules ──────────────────────────────────────────────────────────
REQUIRE_APPROVAL_BEFORE_GENERATION = True   # Production Rule #1 — never disable
AUTO_SAVE_MEMORIES = False
MAX_CLARIFYING_QUESTIONS_PER_ROUND = 3

# ── MCP server ────────────────────────────────────────────────────────────────
MCP_IMAGE_SERVER_PORT = int(os.getenv("MCP_IMAGE_SERVER_PORT", "8765"))
MCP_IMAGE_SERVER_URL = f"http://localhost:{MCP_IMAGE_SERVER_PORT}"

# ── Paths ─────────────────────────────────────────────────────────────────────
from pathlib import Path
ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = ROOT / "data" / "outputs"
INPUTS_DIR  = ROOT / "data" / "inputs"
PROMPTS_DIR = ROOT / "prompts"
SKILLS_DIR  = ROOT / "skills"

# ── Prompt versioning ─────────────────────────────────────────────────────────
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1.0.0")

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = "WARNING" if IS_PRODUCTION else "DEBUG"
