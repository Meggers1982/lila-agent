"""
ask_question — human-in-the-loop tool for clarifications and approval gates.

Lila uses this in two contexts:
  1. CLARIFICATION: when the brief is missing required information (≤3 questions per round)
  2. APPROVAL GATE: required before any generate_image call (Production Rule #1)

The approval gate call must include the full asset board and image count.
Never call generate_image without first calling ask_question for approval and
receiving an affirmative response.
"""


def ask_question(
    question: str,
    context: str = "",
    is_approval_gate: bool = False,
    asset_board: list | None = None,
    image_count: int = 0,
) -> dict:
    """
    Pause and surface a question or approval request to the user.

    For APPROVAL GATE calls (is_approval_gate=True), include:
        - asset_board: list of asset dicts from the locked board
        - image_count: total number of images to be generated

    Claude Managed Agents handles the actual user interaction.
    This module documents the interface contract.

    Args:
        question:         The question or approval prompt to show the user
        context:          Optional supporting context (e.g. asset board summary)
        is_approval_gate: True if this is a pre-generation approval request
        asset_board:      List of asset dicts (required when is_approval_gate=True)
        image_count:      Number of images to be generated (required when is_approval_gate=True)

    Returns:
        {"response": str}   — the user's answer
        {"approved": bool}  — for approval gates, also includes this field

    Raises:
        ValueError if is_approval_gate=True but asset_board or image_count not provided
    """
    if is_approval_gate:
        if not asset_board or image_count == 0:
            raise ValueError(
                "Approval gate calls require asset_board and image_count. "
                "Show the full board before requesting approval."
            )

    # Claude Managed Agents handles user interaction natively.
    # This stub documents the expected interface for testing.
    raise NotImplementedError(
        "ask_question is handled natively by Claude Managed Agents in production. "
        "For local testing, see tests/unit/test_tools.py for mock patterns."
    )
