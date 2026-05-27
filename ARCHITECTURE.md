# Architecture

## System Overview

Lila is a single-agent system deployed on Claude Managed Agents (Claude Platform). Claude (Opus 4.6) acts as the brain and orchestrator. GPT Image 2 handles final image generation via a local MCP server.

```
User
  │
  ▼
scripts/run_agent.py          — starts a session via Claude Platform API
  │
  ▼
Claude Managed Agents         — hosts the agent loop, state, and tool execution
  │
  ├── prompts/system.md       — Lila's identity, session flow, production rules
  ├── skills/image-assets/    — format catalog + aesthetic registers (loaded on demand)
  │
  ├── tools/web_search.py     — web search for brand/product research
  ├── tools/web_fetch.py      — fetch brand websites, reference pages
  ├── tools/image_search.py   — find real-world visual references
  ├── tools/ask_question.py   — human-in-the-loop: approval gate + clarification
  ├── tools/file_io.py        — save final assets to data/outputs/
  │
  └── mcp_servers/image_gen_server.py  — MCP server wrapping GPT Image 2
        │
        ▼
      OpenAI API (GPT-5.5 + image_generation tool)
        │
        ▼
      data/outputs/<brand>-<campaign>-<asset>-<format>.png
```

---

## Key Design Decisions

### Why Claude Managed Agents?
The platform provides stateful sessions, built-in tool execution, prompt caching, and context compaction — all the infrastructure described in the guide without needing to build it ourselves.

### Why GPT Image 2 via MCP?
GPT Image 2 produces production-quality social assets with strong text rendering and layout control. Running it as an MCP server keeps the tool self-contained and swappable. Claude never calls the OpenAI API directly — the MCP server is the boundary.

### Why is the approval gate a tool (not a guardrail)?
Lila's Production Rule #1 requires explicit user approval *before* image generation. Making `ask_question` a callable tool means Claude must invoke it as part of the session flow — it's enforced by the session logic in `agent/session.py`, not just the prompt.

### Prompt vs. Skill split
The system prompt holds Lila's identity, session flow, asset types, and production rules. The Format Catalog and Aesthetic Registers live in `skills/image-assets/SKILL.md` — they're only loaded when Lila is about to propose directions or generate assets, keeping context lean on short sessions.

---

## Data Flow

1. User sends brief → `run_agent.py` opens a session
2. Claude reads system prompt + session history
3. If brief is vague → `ask_question` tool → user responds → back to Claude
4. Claude proposes directions (loads `skills/image-assets/SKILL.md`)
5. User approves direction → Claude builds asset board
6. Claude calls `ask_question` for generation approval (approval gate)
7. User approves → Claude calls MCP `generate_image` for each asset
8. MCP server calls OpenAI, returns base64 PNG
9. Claude calls `save_file` → written to `data/outputs/`
10. Claude returns final summary with captions and alt text

---

## Adding a New Tool

1. Create `tools/<tool_name>.py` with a single function, clear docstring, explicit error handling
2. Register it in `tools/__init__.py`
3. Add it to the Claude Platform agent config in `scripts/deploy.py`
4. Add unit tests in `tests/unit/test_tools.py`
5. Add at least one golden eval case in `evals/golden_dataset.json`

## Swapping the Image Model

Replace `mcp_servers/image_gen_server.py` with any model that returns base64 PNG. The MCP interface contract is: input `prompt: str, format: str` → output `image_base64: str, revised_prompt: str`. Nothing else in the codebase changes.
