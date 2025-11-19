"""
Core components for sacred values deliberation.

This package contains the core algorithmic components that implement
constraint-based deliberation:
- Sacred value detection (identify non-negotiable commitments)
- Constraint compilation (convert values to formal constraints)
- Statement generation (create constraint-satisfying candidates)
- Constraint filtering (remove violating statements)
- Transparency logging (audit trail of decisions)
"""

from .sacred_value_detector import detect_sacred_value, SacredValueDetector

__all__ = [
    'detect_sacred_value',
    'SacredValueDetector',
]
