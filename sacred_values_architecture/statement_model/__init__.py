"""
Statement Generation Package for Sacred Values Architecture

ADAPTED FROM: habermas_machine/statement_model/
KEY CHANGE: Adds constraint-aware generation

Standard CRM: Generates arbitrary consensus statements, hopes they satisfy preferences
Sacred Values Architecture: Injects hard constraints into prompts, generates ONLY feasible statements

This is the CORE INNOVATION for respecting sacred values.
"""

from .constrained_generator import ConstrainedStatementGenerator

__all__ = ['ConstrainedStatementGenerator']
