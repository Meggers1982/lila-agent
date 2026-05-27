# Secrets Registry

This file is committed to version control. **Values are never committed.**
Actual values live in `.env` (local) or your secrets manager (production).

---

## Credential Index

| Key Name | Service | Used By | Rotation Policy | Where to Get It |
|---|---|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic | `config/secrets.py`, `scripts/deploy.py` | Every 90 days | console.anthropic.com → API Keys |
| `OPENAI_API_KEY` | OpenAI | `mcp_servers/image_gen_server.py` | Every 90 days | platform.openai.com → API Keys |
| `CLAUDE_AGENT_ID` | Claude Platform | `scripts/run_agent.py` | On redeploy | Output of `scripts/deploy.py` |
| `CLAUDE_ENVIRONMENT_ID` | Claude Platform | `scripts/run_agent.py` | On redeploy | Output of `scripts/deploy.py` |

---

## Notes

**OPENAI_API_KEY:** OpenAI requires Organization Verification before GPT Image 2 (`gpt-image-2`) API access is granted. Complete verification at platform.openai.com → Settings → Organization before running `scripts/deploy.py`.

**CLAUDE_AGENT_ID / CLAUDE_ENVIRONMENT_ID:** These are generated the first time you run `scripts/deploy.py`. They are not secrets in the traditional sense (no security risk if exposed), but they are environment-specific — keep them out of version control so dev and prod don't collide.

---

## Rotation Procedure

1. Generate new key at the provider
2. Update value in `.env` (local) or secrets manager (production)
3. Redeploy: `python scripts/deploy.py`
4. Revoke the old key at the provider
5. Update the "Last Rotated" date in this table

## Emergency Revocation

Revoke at the provider **first**. Do not wait to generate a replacement. Then rotate and redeploy.
