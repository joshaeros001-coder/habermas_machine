# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Core types for Sacred Values Architecture.

This module defines the fundamental data structures for the constraint-based
Habermas Machine. These types extend the standard CRM types with sacred value
and constraint tracking capabilities.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set
import enum


# ==============================================================================
# SACRED VALUE TYPES (NEW - Core Innovation)
# ==============================================================================

@dataclass
class SacredValue:
    """Represents a detected sacred value (non-negotiable belief).

    Sacred values are identified by absolute language ("cannot", "must not"),
    religious/moral justifications, and explicit rejection of trade-offs.

    Unlike preferences (which have weights), sacred values are CONSTRAINTS
    that must be satisfied before any optimization occurs.

    Attributes:
        citizen_id: The index of the citizen who holds this sacred value (0-indexed)
        constraint_text: The extracted text expressing the constraint
        confidence: Float 0-1 indicating detection confidence
        markers_found: List of linguistic markers that triggered detection
        original_opinion: The full original opinion text containing the sacred value

    Example:
        SacredValue(
            citizen_id=1,
            constraint_text="cannot take medication due to my faith",
            confidence=0.95,
            markers_found=["cannot", "faith"],
            original_opinion="As a Christian, I believe depression is spiritual..."
        )
    """
    citizen_id: int
    constraint_text: str
    confidence: float
    markers_found: List[str]
    original_opinion: str

    def __post_init__(self):
        """Validate sacred value fields."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be in [0,1], got {self.confidence}")
        if self.citizen_id < 0:
            raise ValueError(f"Citizen ID must be non-negative, got {self.citizen_id}")


@dataclass
class Constraint:
    """Represents a compiled constraint derived from a sacred value.

    After detecting a sacred value, we compile it into a structured constraint
    that can be checked against candidate statements.

    This is the CORE INNOVATION: converting natural language sacred values
    into enforceable constraints on the deliberation process.

    Attributes:
        sacred_value: The original sacred value this was derived from
        prohibited_actions: List of actions/recommendations that violate this constraint
        required_elements: List of elements that MUST be in any valid statement
        constraint_type: Type of constraint (prohibition, requirement, etc.)

    Example:
        Constraint(
            sacred_value=SacredValue(...),
            prohibited_actions=["SSRI", "medication", "pharmaceutical treatment"],
            required_elements=["spiritual", "prayer", "faith-based"],
            constraint_type=ConstraintType.PROHIBITION
        )
    """
    sacred_value: SacredValue
    prohibited_actions: List[str] = field(default_factory=list)
    required_elements: List[str] = field(default_factory=list)
    constraint_type: 'ConstraintType' = field(default='ConstraintType.PROHIBITION')

    @property
    def citizen_id(self) -> int:
        """Convenience accessor for the citizen who holds this constraint."""
        return self.sacred_value.citizen_id


@enum.unique
class ConstraintType(enum.Enum):
    """Types of constraints that can be enforced.

    PROHIBITION: Statement must NOT contain certain actions/recommendations
    REQUIREMENT: Statement MUST contain certain elements
    CONDITIONAL: If X, then must/must not Y
    """
    PROHIBITION = "prohibition"
    REQUIREMENT = "requirement"
    CONDITIONAL = "conditional"


# ==============================================================================
# TRANSPARENCY LOGGING (NEW - For Explainability)
# ==============================================================================

@dataclass
class TransparencyLog:
    """Tracks all constraint-related decisions during deliberation.

    This provides full transparency into how sacred values were detected,
    compiled into constraints, and respected throughout the process.

    CRITICAL for real-world deployment: users must understand WHY certain
    statements were filtered out and HOW their constraints were handled.

    Attributes:
        constraints_detected: Number of sacred values detected
        constraints_satisfied: Number of constraints successfully satisfied
        statements_generated: Total number of statements generated
        statements_filtered: Number of statements filtered for constraint violations
        filtering_reasons: Detailed reasons for each filtered statement
        constraint_violations: List of (statement, constraint, reason) tuples
        final_check_passed: Whether the winning statement satisfies all constraints
    """
    constraints_detected: int = 0
    constraints_satisfied: int = 0
    statements_generated: int = 0
    statements_filtered: int = 0
    filtering_reasons: List[str] = field(default_factory=list)
    constraint_violations: List[tuple] = field(default_factory=list)
    final_check_passed: bool = False
    detected_sacred_values: List[SacredValue] = field(default_factory=list)
    compiled_constraints: List[Constraint] = field(default_factory=list)

    def add_violation(self, statement: str, constraint: Constraint, reason: str):
        """Record a constraint violation."""
        self.constraint_violations.append((statement, constraint, reason))
        self.filtering_reasons.append(
            f"Statement violates constraint from Citizen {constraint.citizen_id}: {reason}"
        )

    def summary(self) -> str:
        """Generate a human-readable summary of constraint handling."""
        summary = f"""
=== CONSTRAINT TRANSPARENCY LOG ===
Sacred Values Detected: {self.constraints_detected}
Constraints Compiled: {len(self.compiled_constraints)}
Statements Generated: {self.statements_generated}
Statements Filtered: {self.statements_filtered}
Final Check: {'PASSED' if self.final_check_passed else 'FAILED'}

Detected Sacred Values:
"""
        for sv in self.detected_sacred_values:
            summary += f"  - Citizen {sv.citizen_id}: \"{sv.constraint_text}\" (confidence: {sv.confidence:.2f})\n"

        if self.constraint_violations:
            summary += f"\nConstraint Violations ({len(self.constraint_violations)}):\n"
            for stmt_preview, constraint, reason in self.constraint_violations[:5]:  # Show first 5
                summary += f"  - {stmt_preview[:60]}... violates Citizen {constraint.citizen_id}'s constraint\n"
                summary += f"    Reason: {reason}\n"

        return summary


# ==============================================================================
# DELIBERATION RESULT (ENHANCED - Includes Constraint Info)
# ==============================================================================

@dataclass
class DeliberationResult:
    """Enhanced deliberation result that includes sacred value tracking.

    ADAPTED FROM: Standard CRM result
    CHANGES: Added sacred value detection, constraints, and transparency log
    WHY: Users need to see that their sacred values were respected

    Attributes:
        winning_statement: The final consensus statement
        all_statements: All candidate statements (sorted by rank)
        detected_sacred_values: List of all detected sacred values
        compiled_constraints: List of all compiled constraints
        transparency_log: Detailed log of constraint handling
        is_feasible: Whether a constraint-satisfying solution was found
        infeasibility_reason: If infeasible, explanation of why
    """
    winning_statement: str
    all_statements: List[str]
    detected_sacred_values: List[SacredValue]
    compiled_constraints: List[Constraint]
    transparency_log: TransparencyLog
    is_feasible: bool = True
    infeasibility_reason: Optional[str] = None

    # Additional metadata from standard CRM
    rankings: Optional[List[List[int]]] = None
    social_ranking: Optional[List[int]] = None


@dataclass
class InfeasibleResult(DeliberationResult):
    """Result when no statement can satisfy all constraints.

    This can happen when constraints are contradictory or too restrictive.
    Important to communicate this clearly rather than forcing a compromise.

    Example:
        If Citizen A requires "medication" and Citizen B prohibits "medication",
        no statement can satisfy both constraints. Better to return InfeasibleResult
        than to ignore one person's sacred value.
    """
    is_feasible: bool = False

    def __init__(self, reason: str, detected_sacred_values: List[SacredValue],
                 compiled_constraints: List[Constraint], transparency_log: TransparencyLog):
        super().__init__(
            winning_statement="",
            all_statements=[],
            detected_sacred_values=detected_sacred_values,
            compiled_constraints=compiled_constraints,
            transparency_log=transparency_log,
            is_feasible=False,
            infeasibility_reason=reason
        )


# ==============================================================================
# STATEMENT AND RANKING TYPES (Adapted from standard CRM)
# ==============================================================================

@dataclass
class Statement:
    """A candidate consensus statement.

    ADAPTED FROM: Standard CRM
    CHANGES: Added constraint_check field
    WHY: Need to track whether statement passes constraint validation
    """
    text: str
    explanation: str
    passes_constraints: bool = True
    violated_constraints: List[Constraint] = field(default_factory=list)


@dataclass
class StatementResult:
    """Result from statement generation.

    COPIED FROM: habermas_machine.statement_model.base_model
    This is the return type for statement generation models.
    """
    statement: str
    explanation: str

    def __iter__(self):
        """Allow tuple unpacking: statement, explanation = result"""
        return iter((self.statement, self.explanation))


# ==============================================================================
# RANKING CONSTANTS (From standard CRM)
# ==============================================================================

# Mock ranking value indicating "no preference" or "invalid"
RANKING_MOCK = -1
