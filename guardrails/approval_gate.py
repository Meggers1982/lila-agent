"""
approval_gate.py — enforce explicit user approval before image generation.

This is Production Rule #1. It is enforced in two places:
  1. The system prompt instructs Lila to use ask_question before generate_image
  2. agent/session.py calls check_approval() before executing any generate_image tool call

If both layers agree, generation proceeds. If either blocks, generation stops.
"""

from config.settings import REQUIRE_APPROVAL_BEFORE_GENERATION


class ApprovalNotGrantedError(Exception):
    """Raised when generation is attempted without explicit approval."""
    pass


def check_approval(session_state: dict) -> bool:
    """
    Verify that the user has explicitly approved image generation in this session.

    The session state must contain:
        session_state["generation_approved"] = True

    This flag is set by agent/session.py when ask_question returns an
    affirmative response in an is_approval_gate=True call.

    Args:
        session_state: The current session state dict

    Returns:
        True if approved

    Raises:
        ApprovalNotGrantedError if not approved and REQUIRE_APPROVAL_BEFORE_GENERATION is True
    """
    if not REQUIRE_APPROVAL_BEFORE_GENERATION:
        return True  # Only disable in development for testing

    approved = session_state.get("generation_approved", False)
    if not approved:
        raise ApprovalNotGrantedError(
            "Image generation blocked: no explicit user approval on record for this session. "
            "Call ask_question with is_approval_gate=True and present the full asset board first."
        )
    return True


def mark_approved(session_state: dict) -> dict:
    """Mark the session as approved for generation. Called by session.py."""
    session_state["generation_approved"] = True
    return session_state


def reset_approval(session_state: dict) -> dict:
    """
    Reset the approval flag. Call this if the asset board changes materially
    after initial approval — the user must re-approve the new board.
    """
    session_state["generation_approved"] = False
    return session_state
