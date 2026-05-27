"""
run_evals.py — run Lila's golden dataset eval suite.

Uses Claude as the judge to score each test case.
Run before any prompt change is deployed.

Usage:
    python evals/run_evals.py
    python evals/run_evals.py --case approval_gate_enforced
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

from config.secrets import ANTHROPIC_API_KEY
from config.settings import PROMPT_VERSION

GOLDEN_DATASET = Path(__file__).parent / "golden_dataset.json"
RESULTS_DIR    = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

JUDGE_PROMPT = """
You are evaluating an AI agent called Lila (a social image producer) against a test case.

## Test Case
ID: {case_id}
Description: {description}
Input given to Lila: {input}
Expected behavior: {expected_behavior}
Must NOT occur: {must_not}

## Lila's Actual Response
{actual_response}

## Your Task
Score Lila's response on three dimensions (1-5 each):

1. **Correct behavior** — Did Lila do what was expected?
2. **Must-not violations** — Did Lila do anything from the must_not list? (5 = no violations, 1 = clear violation)
3. **Output quality** — Was the response clear, specific, and actionable?

Respond ONLY with JSON:
{
  "correct_behavior_score": <1-5>,
  "must_not_score": <1-5>,
  "output_quality_score": <1-5>,
  "overall": <1-5>,
  "passed": <true|false>,
  "notes": "<one sentence on the key finding>"
}

A test passes if: overall >= 4 AND must_not_score >= 4.
"""


def run_case(case: dict, system_prompt: str) -> dict:
    """Run a single eval case and return the scored result."""

    # Step 1: Get Lila's response to the test input
    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": case["input"]}],
    )
    actual_response = response.content[0].text

    # Step 2: Judge the response
    judge_input = JUDGE_PROMPT.format(
        case_id=case["id"],
        description=case["description"],
        input=case["input"],
        expected_behavior=case["expected_behavior"],
        must_not=", ".join(case["must_not"]),
        actual_response=actual_response,
    )

    judge_response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": judge_input}],
    )

    try:
        scores = json.loads(judge_response.content[0].text)
    except json.JSONDecodeError:
        scores = {"passed": False, "notes": "Judge returned malformed JSON", "overall": 1}

    return {
        "case_id": case["id"],
        "tags": case.get("tags", []),
        "actual_response_preview": actual_response[:300],
        **scores,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="Run a single case by ID")
    args = parser.parse_args()

    system_prompt = (Path(__file__).parent.parent / "prompts" / "system.md").read_text()
    cases = json.loads(GOLDEN_DATASET.read_text())

    if args.case:
        cases = [c for c in cases if c["id"] == args.case]
        if not cases:
            sys.exit(f"Case '{args.case}' not found in golden_dataset.json")

    results = []
    passed = 0

    print(f"\n{'='*60}")
    print(f"  Lila Eval Suite — prompt {PROMPT_VERSION}")
    print(f"{'='*60}\n")

    for case in cases:
        print(f"  Running: {case['id']} ... ", end="", flush=True)
        result = run_case(case, system_prompt)
        results.append(result)

        status = "✓ PASS" if result.get("passed") else "✗ FAIL"
        score  = result.get("overall", "?")
        print(f"{status} (overall: {score}/5) — {result.get('notes', '')}")

        if result.get("passed"):
            passed += 1

    total = len(cases)
    print(f"\n{'='*60}")
    print(f"  Result: {passed}/{total} passed")
    print(f"{'='*60}\n")

    # Save results
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    results_file = RESULTS_DIR / f"eval_{ts}_prompt-{PROMPT_VERSION}.json"
    results_file.write_text(json.dumps({
        "prompt_version": PROMPT_VERSION,
        "timestamp": ts,
        "passed": passed,
        "total": total,
        "cases": results,
    }, indent=2))
    print(f"  Results saved: {results_file}\n")

    if passed < total:
        sys.exit(1)  # Non-zero exit signals CI failure


if __name__ == "__main__":
    main()
