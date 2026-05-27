# Lila — Social Image Producer

Lila is a social image producer agent for product launches, campaigns, drops, and brand moments. She takes a product brief and ships export-ready still assets for Instagram, LinkedIn, Stories, carousels, paid social, and launch covers.

She runs on **Claude Managed Agents** (Claude Platform) and uses **GPT Image 2** (via GPT-5.5) for final image generation.

---

## Requirements

- Python 3.11+
- Anthropic API key (Claude Platform access with Managed Agents beta)
- OpenAI API key (GPT-5.5 / GPT Image 2, org verification required)
- `ant` CLI: `npm install -g @anthropic-ai/claude-code`

---

## Setup

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd lila-agent

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Copy and fill in secrets
cp .env.example .env
# Edit .env with your API keys — see SECRETS_REGISTRY.md for where to get each

# 4. Deploy Lila to Claude Platform
python scripts/deploy.py

# 5. Run a session
python scripts/run_agent.py
```

---

## How Lila Works

1. You provide a product brief (product name, audience, channel, CTA, brand colors)
2. Lila proposes 2–3 visual directions with palette and asset logic
3. You approve a direction
4. Lila presents a full asset board for your review
5. You explicitly approve before any image is generated
6. Lila generates assets via GPT Image 2 and saves them to `data/outputs/`
7. You receive final assets with captions, alt text, and follow-up suggestions

---

## Project Structure

```
lila-agent/
├── agent/          Core session logic and state tracking
├── tools/          Every tool Lila can call (each works in isolation)
├── skills/         Task-specific knowledge modules (read before acting)
├── memory/         Context window management
├── prompts/        System prompt and versions (never hardcoded in Python)
├── evals/          Golden dataset and eval runner
├── guardrails/     Approval gate, input/output validation
├── observability/  Structured logging and cost tracking
├── tests/          Unit, integration, and adversarial tests
├── mcp_servers/    MCP server for GPT Image 2 tool
├── config/         Settings and secret loading
├── scripts/        Entry points: deploy, run, test a tool
└── data/           inputs/ and outputs/ (gitignored)
```

---

## Environment Variables

See `.env.example` for the full list. See `SECRETS_REGISTRY.md` for where to get each key.

---

## Deploying a Prompt Change

```bash
# Edit prompts/system.md
# Tag the change
git add prompts/system.md
git commit -m "fix(prompt): <what changed and why>"
git tag prompt-v1.1.0
git push origin prompt-v1.1.0

# Redeploy
python scripts/deploy.py
```

## Running Evals

```bash
python evals/run_evals.py
```

Evals must pass before any prompt change is deployed to production.
