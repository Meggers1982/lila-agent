"""
output_validator.py — validate Lila's outputs before returning them to the user.

Checks that the final delivery includes required components.
Does not validate image quality (that's a human judgment call).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OutputValidationResult:
    valid: bool
    missing: list[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.missing is None:
            self.missing = []


def validate_final_output(output: dict) -> OutputValidationResult:
    """
    Validate Lila's final session output before presenting to the user.

    Expected output structure:
    {
        "assets": [{"file_name": str, "file_path": str, "alt_text": str}],
        "concept_summary": str,
        "asset_board": list,
        "captions": list,          — at least 2 options
        "follow_up_suggestions": list,
    }

    Args:
        output: Lila's final output dict

    Returns:
        OutputValidationResult
    """
    missing = []

    if not output.get("assets"):
        missing.append("assets (no files generated or referenced)")

    assets = output.get("assets", [])
    for i, asset in enumerate(assets):
        if not asset.get("alt_text"):
            missing.append(f"assets[{i}].alt_text (required for accessibility)")
        if not asset.get("file_path"):
            missing.append(f"assets[{i}].file_path (where is the file?)")

    if not output.get("concept_summary"):
        missing.append("concept_summary (two-line name + register + rationale)")

    captions = output.get("captions", [])
    if len(captions) < 2:
        missing.append("captions (need at least 2 options: launch and conversion-focused)")

    if missing:
        return OutputValidationResult(
            valid=False,
            missing=missing,
            error=f"Output is incomplete. Missing: {'; '.join(missing)}"
        )

    return OutputValidationResult(valid=True)


def validate_file_exists(file_path: str) -> OutputValidationResult:
    """Confirm a generated file actually exists on disk before reporting it to the user."""
    import os
    if not os.path.isfile(file_path):
        return OutputValidationResult(
            valid=False,
            error=f"File not found: {file_path}. Do not report it as generated."
        )
    return OutputValidationResult(valid=True)
