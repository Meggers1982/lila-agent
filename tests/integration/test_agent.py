"""
Integration tests — test the full session flow end-to-end with mocked tools.

These verify that Lila's session logic, guardrails, and tool call ordering
work correctly together without making real API calls.

Run: pytest tests/integration/ -v
"""

import pytest
from unittest.mock import patch, MagicMock, call
from agent.session import SessionState, Phase


class TestSessionStateTransitions:
    """Test that session phases advance correctly."""

    def test_initial_phase_is_briefing(self):
        state = SessionState(session_id="test-001")
        assert state.phase == Phase.BRIEFING

    def test_advance_to_directions(self):
        state = SessionState(session_id="test-001")
        state.advance_to(Phase.DIRECTIONS)
        assert state.phase == Phase.DIRECTIONS

    def test_mark_generation_approved_sets_generating(self):
        state = SessionState(session_id="test-001")
        state.advance_to(Phase.BOARD_LOCKED)
        state.mark_generation_approved()
        assert state.generation_approved is True
        assert state.phase == Phase.GENERATING

    def test_reset_approval_returns_to_board_locked(self):
        state = SessionState(session_id="test-001")
        state.mark_generation_approved()
        state.reset_generation_approval()
        assert state.generation_approved is False
        assert state.phase == Phase.BOARD_LOCKED

    def test_record_generated_asset_increments_count(self):
        state = SessionState(session_id="test-001")
        state.record_generated_asset({"file_name": "brand-c-hero-4x5.png"})
        state.record_generated_asset({"file_name": "brand-c-feature-4x5.png"})
        assert state.images_generated == 2
        assert len(state.assets_generated) == 2

    def test_to_dict_includes_key_fields(self):
        state = SessionState(session_id="test-001", brand="emberoak", campaign="spring")
        d = state.to_dict()
        assert d["session_id"] == "test-001"
        assert d["brand"] == "emberoak"
        assert "generation_approved" in d


class TestApprovalGateIntegration:
    """Verify the approval gate integrates correctly with session state."""

    def test_full_approval_flow(self):
        from guardrails.approval_gate import check_approval, mark_approved, ApprovalNotGrantedError
        state = SessionState(session_id="test-002")

        # Before approval: blocked
        with pytest.raises(ApprovalNotGrantedError):
            check_approval(state.__dict__)

        # After approval: passes
        mark_approved(state.__dict__)
        assert check_approval(state.__dict__) is True

    def test_reset_and_re_approve(self):
        from guardrails.approval_gate import (
            check_approval, mark_approved, reset_approval, ApprovalNotGrantedError
        )
        state = {"generation_approved": True}

        # Approved
        assert check_approval(state) is True

        # Board changed — reset required
        reset_approval(state)
        with pytest.raises(ApprovalNotGrantedError):
            check_approval(state)

        # Re-approve
        mark_approved(state)
        assert check_approval(state) is True
