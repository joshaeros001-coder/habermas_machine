"""
Voting Package for Sacred Values Architecture

ADAPTED FROM: habermas_machine/social_choice/
KEY CHANGE: Simplified voting that operates on pre-filtered feasible set
WHY: Standard CRM votes on all statements; we vote only on constraint-satisfying ones

This implements constrained voting: citizens vote ONLY on statements that
satisfy all sacred value constraints. This ensures the final consensus
respects non-negotiable commitments.
"""

from .simple_voting import SimpleVoting

__all__ = ['SimpleVoting']
