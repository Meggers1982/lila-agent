"""
Unit tests for Lila's tools.
Each tool is tested in isolation — no agent, no session, no Claude API calls.

Run: pytest tests/unit/test_tools.py -v
"""

import base64
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── file_io ────────────────────────────────────────────────────────────────────

class TestFileIO:
    def test_save_file_creates_file(self, tmp_path):
        with patch("tools.file_io.OUTPUTS_DIR", tmp_path):
            from tools.file_io import save_file
            content = b"fake PNG bytes"
            result = save_file("test-brand-test-hero-4x5.png", base64.b64encode(content).decode())
            assert result["file_name"] == "test-brand-test-hero-4x5.png"
            assert result["size_bytes"] == len(content)
            assert Path(result["file_path"]).exists()

    def test_save_file_returns_error_on_bad_base64(self, tmp_path):
        with patch("tools.file_io.OUTPUTS_DIR", tmp_path):
            from tools.file_io import save_file
            result = save_file("test.png", "not-valid-base64!!!")
            assert "error" in result

    def test_fetch_stored_file_found(self, tmp_path):
        with patch("tools.file_io.OUTPUTS_DIR", tmp_path):
            from tools.file_io import save_file, fetch_stored_file
            content = b"fake image"
            save_file("brand-campaign-hero-4x5.png", base64.b64encode(content).decode())
            result = fetch_stored_file("brand-campaign-hero-4x5.png")
            assert result["file_name"] == "brand-campaign-hero-4x5.png"
            assert base64.b64decode(result["content_base64"]) == content

    def test_fetch_stored_file_missing(self, tmp_path):
        with patch("tools.file_io.OUTPUTS_DIR", tmp_path):
            from tools.file_io import fetch_stored_file
            result = fetch_stored_file("nonexistent.png")
            assert "error" in result
            assert "not found" in result["error"]


# ── guardrails/input_validator ─────────────────────────────────────────────────

class TestInputValidator:
    def setup_method(self):
        from guardrails.input_validator import validate_brief, validate_asset_name
        self.validate_brief = validate_brief
        self.validate_asset_name = validate_asset_name

    def test_empty_brief_invalid(self):
        result = self.validate_brief("")
        assert not result.valid

    def test_too_short_brief_invalid(self):
        result = self.validate_brief("candle")
        assert not result.valid

    def test_valid_brief(self):
        result = self.validate_brief("Product: Ember & Oak soy candles. Audience: women 28-45. Channel: Instagram.")
        assert result.valid

    def test_brief_without_channel_warns(self):
        result = self.validate_brief("Product: Ember & Oak soy candles. Great for home decor.")
        assert result.valid  # valid, but with warning
        assert any("channel" in w.lower() or "platform" in w.lower() for w in result.warnings)

    def test_asset_name_valid(self):
        result = self.validate_asset_name("emberoak-spring-launch-hero-4x5.png")
        assert result.valid

    def test_asset_name_path_traversal_blocked(self):
        result = self.validate_asset_name("../../../etc/passwd")
        assert not result.valid

    def test_asset_name_too_few_parts(self):
        result = self.validate_asset_name("hero.png")
        assert not result.valid


# ── guardrails/approval_gate ───────────────────────────────────────────────────

class TestApprovalGate:
    def setup_method(self):
        from guardrails.approval_gate import (
            check_approval, mark_approved, reset_approval, ApprovalNotGrantedError
        )
        self.check_approval = check_approval
        self.mark_approved = mark_approved
        self.reset_approval = reset_approval
        self.ApprovalNotGrantedError = ApprovalNotGrantedError

    def test_blocks_without_approval(self):
        state = {"generation_approved": False}
        with pytest.raises(self.ApprovalNotGrantedError):
            self.check_approval(state)

    def test_passes_with_approval(self):
        state = {"generation_approved": True}
        assert self.check_approval(state) is True

    def test_mark_approved_sets_flag(self):
        state = {}
        self.mark_approved(state)
        assert state["generation_approved"] is True

    def test_reset_clears_flag(self):
        state = {"generation_approved": True}
        self.reset_approval(state)
        assert state["generation_approved"] is False


# ── guardrails/output_validator ────────────────────────────────────────────────

class TestOutputValidator:
    def setup_method(self):
        from guardrails.output_validator import validate_final_output
        self.validate = validate_final_output

    def test_complete_output_valid(self):
        output = {
            "assets": [{"file_name": "brand-c-hero-4x5.png", "file_path": "/tmp/x.png", "alt_text": "Alt text here"}],
            "concept_summary": "Warm editorial. Editorial Restraint register.",
            "asset_board": [{"asset": "hero"}],
            "captions": ["Caption one.", "Caption two."],
            "follow_up_suggestions": ["Resize to 1:1"],
        }
        result = self.validate(output)
        assert result.valid

    def test_missing_alt_text_invalid(self):
        output = {
            "assets": [{"file_name": "brand-c-hero-4x5.png", "file_path": "/tmp/x.png"}],
            "concept_summary": "Summary",
            "asset_board": [],
            "captions": ["One", "Two"],
        }
        result = self.validate(output)
        assert not result.valid
        assert any("alt_text" in m for m in result.missing)

    def test_single_caption_invalid(self):
        output = {
            "assets": [{"file_name": "x.png", "file_path": "/tmp/x.png", "alt_text": "Alt"}],
            "concept_summary": "Summary",
            "asset_board": [],
            "captions": ["Only one caption"],
        }
        result = self.validate(output)
        assert not result.valid
