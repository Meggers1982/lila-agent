"""
Secret loading and validation.

All secrets are loaded through this module — never via raw os.getenv() elsewhere.
If a required secret is missing, fail loudly at import time, not mid-session.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Load a required secret. Exit with a clear message if missing."""
    value = os.getenv(key)
    if not value:
        sys.exit(
            f"\n[secrets] Missing required environment variable: {key}\n"
            f"Copy .env.example to .env and fill in the value.\n"
            f"See SECRETS_REGISTRY.md for where to get it.\n"
        )
    return value


def _optional(key: str, default: str = "") -> str:
    return os.getenv(key, default)


# ── Secrets ───────────────────────────────────────────────────────────────────

def get_secret(name: str) -> str:
    """Public interface for retrieving any secret by key name."""
    secrets = {
        "ANTHROPIC_API_KEY":     _require("ANTHROPIC_API_KEY"),
        "OPENAI_API_KEY":        _require("OPENAI_API_KEY"),
        "CLAUDE_AGENT_ID":       _optional("CLAUDE_AGENT_ID"),
        "CLAUDE_ENVIRONMENT_ID": _optional("CLAUDE_ENVIRONMENT_ID"),
    }
    if name not in secrets:
        raise KeyError(f"Unknown secret: {name}. Add it to SECRETS_REGISTRY.md first.")
    return secrets[name]


# Eagerly validate required secrets on import so failures surface at startup
ANTHROPIC_API_KEY = _require("ANTHROPIC_API_KEY")
OPENAI_API_KEY    = _require("OPENAI_API_KEY")
