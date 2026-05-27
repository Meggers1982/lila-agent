"""
session.py — session state tracking for a Lila run.

Claude Managed Agents handles the conversation history and tool execution.
This module tracks Lila-specific state that persists across turns in a session:
the current phase, approved direction, asset board, and generation approval flag.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Phase(str, Enum):
    BRIEFING       = "briefing"        # Receiving and clarifying the brief
    DIRECTIONS     = "directions"      # Proposing visual directions
    BOARD_LOCKED   = "board_locked"    # Asset board approved, awaiting generation approval
    GENERATING     = "generating"      # Actively generating images
    COMPLETE       = "complete"        # All assets delivered


@dataclass
class SessionState:
    session_id: str
    phase: Phase = Phase.BRIEFING

    # Brief details (filled in as clarified)
    brand: str = ""
    campaign: str = ""
    product: str = ""
    audience: str = ""
    channel: str = ""
    cta: str = ""

    # Visual direction
    approved_direction: Optional[str] = None
    approved_register: Optional[str] = None
    approved_palette: Optional[dict] = None

    # Asset board
    asset_board: list = field(default_factory=list)
    assets_generated: list = field(default_factory=list)

    # Approval gate (Production Rule #1)
    generation_approved: bool = False

    # Token optimisation flags
    skill_file_loaded: bool = False    # read once per session, not on every direction turn
    brand_site_fetched: bool = False   # track whether we've already fetched the brand URL

    # Cost tracking
    estimated_image_count: int = 0
    images_generated: int = 0
    input_tokens_used: int = 0
    output_tokens_used: int = 0

    def advance_to(self, phase: Phase):
        """Transition to the next phase. Logs the transition."""
        print(f"[session] {self.session_id}: {self.phase} → {phase}")
        self.phase = phase

    def mark_generation_approved(self):
        """Called when ask_question returns affirmative approval for generation."""
        self.generation_approved = True
        self.advance_to(Phase.GENERATING)

    def reset_generation_approval(self):
        """Call if the asset board changes materially after initial approval."""
        self.generation_approved = False
        if self.phase == Phase.GENERATING:
            self.advance_to(Phase.BOARD_LOCKED)

    def record_generated_asset(self, asset: dict):
        """Record a successfully generated asset."""
        self.assets_generated.append(asset)
        self.images_generated += 1

    def record_token_usage(self, input_tokens: int, output_tokens: int):
        """Accumulate token usage across turns for cost tracking."""
        self.input_tokens_used += input_tokens
        self.output_tokens_used += output_tokens

    def estimated_cost_usd(self) -> float:
        """
        Rough cost estimate based on claude-opus-4-6 pricing.
        Input: $15/M tokens. Output: $75/M tokens.
        Cached input reads are ~90% cheaper but counted separately by the platform.
        Use this as an order-of-magnitude guide, not a billing source.
        """
        input_cost  = (self.input_tokens_used  / 1_000_000) * 15.00
        output_cost = (self.output_tokens_used / 1_000_000) * 75.00
        return round(input_cost + output_cost, 4)

    def to_dict(self) -> dict:
        """Serialize state for logging and debugging."""
        return {
            "session_id": self.session_id,
            "phase": self.phase,
            "brand": self.brand,
            "campaign": self.campaign,
            "approved_direction": self.approved_direction,
            "asset_board_count": len(self.asset_board),
            "assets_generated": len(self.assets_generated),
            "generation_approved": self.generation_approved,
            "images_generated": self.images_generated,
            "skill_file_loaded": self.skill_file_loaded,
            "input_tokens_used": self.input_tokens_used,
            "output_tokens_used": self.output_tokens_used,
            "estimated_cost_usd": self.estimated_cost_usd(),
        }
