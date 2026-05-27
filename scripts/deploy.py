"""
deploy.py — deploy (or update) Lila on Claude Managed Agents.

Creates the agent definition and cloud environment on the Claude Platform,
then writes the resulting IDs to .env so run_agent.py can reference them.

Usage:
    python scripts/deploy.py              # First deploy or update
    python scripts/deploy.py --env-only   # Create environment without touching the agent

Requires: ANTHROPIC_API_KEY in .env, `ant` CLI installed (npm i -g @anthropic-ai/claude-code)
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
SYSTEM_PROMPT_PATH = ROOT / "prompts" / "system.md"
ENV_PATH = ROOT / ".env"

# ── Helpers ────────────────────────────────────────────────────────────────────

def run(cmd: list[str]) -> dict:
    """Run an `ant` CLI command and return parsed JSON output."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n[deploy] Error running: {' '.join(cmd)}")
        print(result.stderr)
        sys.exit(1)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(result.stdout)
        return {}


def update_env(key: str, value: str):
    """Write or update a key in .env."""
    lines = ENV_PATH.read_text().splitlines() if ENV_PATH.exists() else []
    updated = False
    new_lines = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)
    if not updated:
        new_lines.append(f"{key}={value}")
    ENV_PATH.write_text("\n".join(new_lines) + "\n")
    print(f"[deploy] .env updated: {key}={value[:20]}...")


# ── Deploy steps ───────────────────────────────────────────────────────────────

def create_or_update_agent() -> str:
    """Create the Lila agent definition on Claude Platform. Returns agent ID."""
    system_prompt = SYSTEM_PROMPT_PATH.read_text()

    existing_id = os.getenv("CLAUDE_AGENT_ID", "")
    if existing_id:
        print(f"[deploy] Updating existing agent: {existing_id}")
        result = run([
            "ant", "beta:agents", "update", existing_id,
            "--system", system_prompt,
            "--model", json.dumps({"id": "claude-opus-4-6"}),
        ])
    else:
        print("[deploy] Creating new agent: Lila: Social Image Producer")
        result = run([
            "ant", "beta:agents", "create",
            "--name", "Lila: Social Image Producer",
            "--model", json.dumps({"id": "claude-opus-4-6"}),
            "--system", system_prompt,
            "--tool", json.dumps({"type": "agent_toolset_20260401"}),
        ])

    agent_id = result.get("id", "")
    if not agent_id:
        print("[deploy] No agent ID returned. Check Claude Platform access.")
        sys.exit(1)

    update_env("CLAUDE_AGENT_ID", agent_id)
    print(f"[deploy] Agent ID: {agent_id}")
    return agent_id


def create_environment() -> str:
    """Create a cloud execution environment. Returns environment ID."""
    existing_id = os.getenv("CLAUDE_ENVIRONMENT_ID", "")
    if existing_id:
        print(f"[deploy] Reusing existing environment: {existing_id}")
        return existing_id

    print("[deploy] Creating cloud environment...")
    result = run([
        "ant", "beta:environments", "create",
        "--name", "lila-production",
        "--config", json.dumps({"type": "cloud", "networking": {"type": "unrestricted"}}),
    ])

    env_id = result.get("id", "")
    if not env_id:
        print("[deploy] No environment ID returned.")
        sys.exit(1)

    update_env("CLAUDE_ENVIRONMENT_ID", env_id)
    print(f"[deploy] Environment ID: {env_id}")
    return env_id


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Deploy Lila to Claude Managed Agents")
    parser.add_argument("--env-only", action="store_true", help="Only create/verify the environment")
    args = parser.parse_args()

    # Load .env
    from dotenv import load_dotenv
    load_dotenv()

    # Check CLI is available
    check = subprocess.run(["ant", "--version"], capture_output=True, text=True)
    if check.returncode != 0:
        sys.exit(
            "[deploy] `ant` CLI not found. Install it:\n"
            "  npm install -g @anthropic-ai/claude-code\n"
        )

    if not args.env_only:
        create_or_update_agent()

    create_environment()

    print("\n[deploy] ✓ Lila is deployed. Run a session with:")
    print("         python scripts/run_agent.py\n")


if __name__ == "__main__":
    main()
