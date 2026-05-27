"""
input_validator.py — validate incoming session requests before Lila acts on them.

Checks that the brief is minimally usable. Does not block vague briefs —
Lila's ask_question flow handles clarification. Blocks only malformed or
clearly invalid inputs that would waste generation budget.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationResult:
    valid: bool
    error: Optional[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


def validate_brief(brief: str) -> ValidationResult:
    """
    Validate a user-submitted product brief.

    Args:
        brief: Raw user input string

    Returns:
        ValidationResult with valid=True if the brief can proceed,
        or valid=False with an error message if it must be rejected.
    """
    warnings = []

    if not brief or not brief.strip():
        return ValidationResult(valid=False, error="Brief is empty. Please describe your product or campaign.")

    if len(brief.strip()) < 10:
        return ValidationResult(valid=False, error="Brief is too short to act on. Add a product name and what you're launching.")

    if len(brief) > 10_000:
        return ValidationResult(valid=False, error="Brief exceeds 10,000 characters. Shorten it — Lila will ask for detail when needed.")

    # Warn about common missing pieces (Lila will ask, but flag early)
    brief_lower = brief.lower()
    if not any(word in brief_lower for word in ["instagram", "linkedin", "tiktok", "twitter", "x.com", "story", "stories", "feed", "social", "channel", "platform"]):
        warnings.append("No channel/platform mentioned — Lila will ask.")

    if not any(word in brief_lower for word in ["audience", "for", "targeting", "users", "customers", "people"]):
        warnings.append("No audience mentioned — Lila will ask.")

    return ValidationResult(valid=True, warnings=warnings)


def validate_asset_name(asset_name: str) -> ValidationResult:
    """Validate an asset file name before saving."""
    if not asset_name:
        return ValidationResult(valid=False, error="asset_name cannot be empty.")

    # Enforce naming convention: <brand>-<campaign>-<asset>-<format>
    parts = asset_name.replace(".png", "").split("-")
    if len(parts) < 3:
        return ValidationResult(
            valid=False,
            error=f"asset_name '{asset_name}' must follow: <brand>-<campaign>-<asset>-<format>"
        )

    # Block path traversal
    if ".." in asset_name or "/" in asset_name or "\\" in asset_name:
        return ValidationResult(valid=False, error="asset_name contains invalid characters.")

    return ValidationResult(valid=True)
