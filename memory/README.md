# Memory

Two systems live here:

---

## 1. Brand Memory (`brand_memory.py`)

Stores what Lila learns about each brand across sessions. Lives in `data/memory/<brand>.json`.

**How it works:**
- At the end of a session, Lila proposes a memory block for user review
- The user approves or edits it
- `save_brand_memory()` is called — only then
- On the next session for the same brand, `scripts/run_agent.py` loads it via `format_for_prompt()` and injects it into the brief before the session starts
- Lila presents it as *based on your last campaign* and lets the user override

**What gets stored:**
```json
{
  "approved_register": "Editorial Restraint",
  "palette": {"primary": "#F5F0E8", "accent": "#8B4513", "text": "#1A1A1A"},
  "copy_voice": "quiet, specific, no hype",
  "formats_used": ["4x5", "9x16"],
  "what_worked": "Tactile close-ups outperformed lifestyle shots",
  "what_to_avoid": "Centered layouts, pastel overlays",
  "campaign": "spring-launch-2026",
  "session_id": "abc123",
  "saved_at": "2026-05-27T14:00:00Z"
}
```

**Rules:**
- Never saved automatically — always proposed and approved first (Production Rule #2)
- One file per brand slug: `data/memory/emberoak.json`
- Multiple entries per file — history is preserved, newest entry is used
- Brand slugs are sanitised — no path traversal possible

---

## 2. Prompt Improvement Log (`prompt_improvement_log.md`)

A running developer changelog. Every time you find a failure pattern in the logs and fix it in `prompts/system.md` or `skills/image-assets/SKILL.md`, log it here.

**Format per entry:**
```
## YYYY-MM-DD — vX.X.X → vX.X.X
**Failure pattern:** what Lila was doing wrong
**Root cause:** why the prompt allowed it
**Fix:** what you changed and where
**Eval before:** X/8 passed
**Eval after:**  X/8 passed
```

**Why this matters:** without this log, you'll fix the same failure twice, revert working changes by accident, and have no way to explain why the prompt is structured the way it is.

---

## Adding a New Memory Type

If you want Lila to remember something beyond brand aesthetics (e.g. client communication preferences, approved copy tone, recurring formats), add a function to `brand_memory.py` following the existing pattern and update the schema comment at the top of the file.
