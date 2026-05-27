# Skills

Skills are instruction sets the agent reads *before* performing a specific type of task. They encode environment-specific constraints, correct patterns, and common mistakes to avoid.

**Write skills as commands, not descriptions.** Second person, present tense. "Use X. Never use Y. Validate with Z."

---

## Current Skills

| Skill | Path | When Lila Reads It |
|---|---|---|
| Image Assets | `image-assets/SKILL.md` | Before proposing visual directions or generating any image |

---

## Adding a New Skill

1. Create a new subdirectory: `skills/<task-type>/`
2. Create `SKILL.md` inside it
3. Structure it with: When to Use / Constraints / Correct Approach / Common Mistakes / Validation
4. Reference it in `prompts/system.md` under the Skills section
5. Add a test case to `evals/golden_dataset.json` confirming the agent reads it before acting
