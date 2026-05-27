# Prompt Improvement Log

Every change to `prompts/system.md` or `skills/image-assets/SKILL.md` goes here.
One entry per version. Always run `python evals/run_evals.py` before and after.

---

## How to Add an Entry

1. Find a failure pattern in the session logs (`logs/lila-YYYY-MM-DD.log`)
2. Identify the root cause in the prompt
3. Fix **one thing** — don't rewrite multiple sections at once
4. Run evals: `python evals/run_evals.py`
5. If evals pass, commit and tag: `git tag prompt-vX.X.X`
6. Log the change below, newest at the top

---

## Template

```
## YYYY-MM-DD — vX.X.X → vX.X.X
**Failure pattern observed:** [what Lila was doing wrong, with a session_id if available]
**Root cause:** [why the prompt allowed or caused it]
**Fix:** [exact change — what section, what was added/removed/reworded]
**Eval result before:** X/8 passed
**Eval result after:**  X/8 passed
**Commit:** [git commit hash or tag]
```

---

## v1.0.0 — 2026-05-27 — Initial release

Lila deployed to Claude Managed Agents. Baseline eval score: run `python evals/run_evals.py` to establish.

Prompt source: `prompts/versions/system_v1.0.md`
Skills source: `skills/image-assets/SKILL.md` (v1)

Known gaps to watch for:
- Does Lila consistently read the skill file before proposing directions, or does she sometimes skip it?
- Does the reflection step after each image generation actually carry forward improvements?
- Does brand memory get proposed at session end without prompting?

Add an entry here the first time you catch any of these failing in production.

---

<!-- Add new entries above this line, newest first -->

## 2026-05-27 — v1.1.0 → v1.2.0
**Change:** Expanded Lila from product-only to any social graphic brief type.

**Problem:** Prompt assumed a physical product existed. "Product name and one-sentence description" appeared in When To Ask. Asset types were product-launch-flavored. Non-product briefs (quote cards, events, thought leadership, personal brand) would cause Lila to ask irrelevant questions.

**Fix 1 — `prompts/system.md`:**
- Added `## Brief Types` table mapping 8 brief types to their subjects and key questions
- Replaced "Product name" in When To Ask with "What is the subject of this image?" plus brief-type-specific sub-questions
- Updated asset types list to include quote card, educational carousel, event announcement, personal brand post, newsletter cover
- Updated Production Rule 8 (captions) — removed "direct launch, founder, conversion" framing; now says "match the tone of what was made"

**Fix 2 — `skills/image-assets/SKILL.md`:**
- Added `## Extended Asset Types` section with 8 non-product asset types and register guidance for each

**Evals added:** non_product_quote_card, non_product_event_announcement, non_product_thought_leadership (14 total)

**Eval result before:** not run (pre-release change)
**Eval result after:** run `python evals/run_evals.py` to establish baseline
**Prompt snapshot:** `prompts/versions/system_v1.2.md`

## 2026-05-27 — v1.2.0 → v1.3.0
**Change:** Added reference image support — visual inspiration without copying.

**What was added:**
- `prompts/system.md`: new `## Reference Images` section with 6 explicit rules: what to extract (palette, density, composition, photography style, typography, register), how to cite observations (specific, not vague), what is allowed (borrow palette/mood/density), what is not allowed (reproduce layout, copy subject, narrate back), and how to handle conflicts between references and brief
- `scripts/run_agent.py`: `--references` flag accepting one or more image paths; images are base64-encoded and passed as vision content blocks in the first message with labelling context so Lila knows they're references
- `evals/golden_dataset.json`: two new cases — `reference_images_cited_specifically` and `reference_conflict_flagged` (16 total)

**Prompt snapshot:** `prompts/versions/system_v1.3.md`
**Eval result after:** run `python evals/run_evals.py` to establish baseline
