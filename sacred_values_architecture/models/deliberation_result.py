"""
Data classes for deliberation results with constraint tracking.

These classes extend the standard deliberation result to include:
- Sacred values detected
- Constraints compiled
- Constraint satisfaction status
- Complete transparency log (why-log)

This makes the deliberation process auditable and explainable.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from .sacred_value import SacredValue
from .constraint import Constraint


@dataclass
class TransparencyLog:
    """
    Complete audit trail of constraint handling decisions.

    This log answers the question: "How did the system handle sacred values?"
    It shows every step from detection to final consensus, making the process
    transparent and verifiable.

    Attributes:
        detected_sacred_values: All sacred values detected across all citizens
        compiled_constraints: Constraints compiled from sacred values
        generated_candidates: ALL candidate statements before filtering
        filtered_out: Statements removed for violating constraints
            Format: List[(statement, constraint_that_was_violated)]
        final_feasible_set: Candidates that satisfied all constraints
        constraint_satisfaction: Did final consensus satisfy each constraint?
            Format: {constraint_text: True/False}
        infeasible: Whether consensus was impossible (conflicting constraints)
        infeasibility_reason: Why consensus was impossible (if infeasible)
        explanation: Natural language summary of the entire process

    Example:
        >>> log = TransparencyLog(
        ...     detected_sacred_values=[sv1, sv2],
        ...     compiled_constraints=[c1],
        ...     generated_candidates=["stmt1", "stmt2", "stmt3", "stmt4"],
        ...     filtered_out=[("stmt1", c1), ("stmt3", c1)],
        ...     final_feasible_set=["stmt2", "stmt4"],
        ...     constraint_satisfaction={"no medication": True},
        ...     infeasible=False,
        ...     explanation="Detected 1 sacred value (religious objection)..."
        ... )
    """

    detected_sacred_values: List[SacredValue] = field(default_factory=list)
    compiled_constraints: List[Constraint] = field(default_factory=list)
    generated_candidates: List[str] = field(default_factory=list)
    filtered_out: List[Tuple[str, Constraint]] = field(default_factory=list)
    final_feasible_set: List[str] = field(default_factory=list)
    constraint_satisfaction: Dict[str, bool] = field(default_factory=dict)
    infeasible: bool = False
    infeasibility_reason: Optional[str] = None
    explanation: str = ""

    def generate_summary(self) -> str:
        """
        Generate a human-readable summary of constraint handling.

        This creates a natural language explanation of what happened,
        suitable for showing to end users or including in research papers.

        Returns:
            Multi-paragraph summary explaining the entire process

        Example output:
            "Sacred Value Detection:
             - Detected 1 sacred value from Citizen 2 (confidence: 0.95)
             - Justification: Religious faith prohibits medication

             Constraint Compilation:
             - Compiled 1 prohibition constraint: cannot take medication
             - Affected actions: medication, SSRI, pharmaceutical, drug

             Statement Generation:
             - Generated 4 candidate consensus statements
             - Filtered out 2 statements that violated constraints
             - Remaining feasible set: 2 statements

             Final Consensus:
             - Selected statement satisfies all constraints
             - Constraint 'no medication' satisfied: TRUE

             Conclusion:
             The deliberation successfully found consensus while respecting
             the sacred value constraint."
        """
        summary = "=== TRANSPARENCY LOG: Constraint Handling ===\n\n"

        # Section 1: Sacred Value Detection
        summary += "1. SACRED VALUE DETECTION\n"
        summary += "-" * 40 + "\n"
        if not self.detected_sacred_values:
            summary += "No sacred values detected.\n"
        else:
            for sv in self.detected_sacred_values:
                summary += f"- Citizen {sv.citizen_id}: "
                summary += f"Confidence {sv.confidence:.2f}\n"
                summary += f"  Justification: {sv.justification}\n"
                summary += f"  Markers: {', '.join(sv.markers)}\n"
        summary += "\n"

        # Section 2: Constraint Compilation
        summary += "2. CONSTRAINT COMPILATION\n"
        summary += "-" * 40 + "\n"
        if not self.compiled_constraints:
            summary += "No constraints compiled.\n"
        else:
            for c in self.compiled_constraints:
                summary += f"- {c.type.value.upper()}: {c.constraint_text}\n"
                summary += f"  Affected actions: {', '.join(c.affected_actions)}\n"
        summary += "\n"

        # Section 3: Statement Filtering
        summary += "3. STATEMENT GENERATION & FILTERING\n"
        summary += "-" * 40 + "\n"
        summary += f"Generated {len(self.generated_candidates)} candidates\n"
        if self.filtered_out:
            summary += f"Filtered out {len(self.filtered_out)} "
            summary += "constraint-violating statements:\n"
            for stmt, constraint in self.filtered_out:
                summary += f"  - '{stmt[:60]}...'\n"
                summary += f"    Violated: {constraint.constraint_text}\n"
        else:
            summary += "All candidates satisfied constraints.\n"
        summary += f"Final feasible set: {len(self.final_feasible_set)} statements\n"
        summary += "\n"

        # Section 4: Constraint Satisfaction
        summary += "4. FINAL CONSENSUS CONSTRAINT CHECK\n"
        summary += "-" * 40 + "\n"
        if self.infeasible:
            summary += f"❌ INFEASIBLE: {self.infeasibility_reason}\n"
        else:
            for constraint_text, satisfied in self.constraint_satisfaction.items():
                status = "✓ SATISFIED" if satisfied else "✗ VIOLATED"
                summary += f"{status}: {constraint_text}\n"
        summary += "\n"

        # Section 5: Explanation
        if self.explanation:
            summary += "5. EXPLANATION\n"
            summary += "-" * 40 + "\n"
            summary += self.explanation + "\n"

        return summary

    def __str__(self) -> str:
        """Human-readable representation."""
        return self.generate_summary()


@dataclass
class DeliberationResult:
    """
    Enhanced deliberation result with sacred value tracking.

    This extends the standard result (question, opinions, consensus) with
    information about sacred values, constraints, and satisfaction status.

    Attributes:
        question: The deliberation question
        opinions: All citizen opinions
        consensus_statement: The final consensus (if found)
        ranked_candidates: All candidates ranked by preference
        sacred_values: Detected sacred values
        constraints: Compiled constraints
        all_constraints_satisfied: Whether final consensus satisfies all
        is_infeasible: Whether consensus was impossible
        infeasibility_reason: Why consensus was impossible (if applicable)
        conflicting_constraints: Constraints that are mutually incompatible
        transparency_log: Complete audit trail

    Example:
        >>> result = DeliberationResult(
        ...     question="Should patient accept SSRIs?",
        ...     opinions=[...],
        ...     consensus_statement="For those whose faith prohibits...",
        ...     sacred_values=[sv1],
        ...     constraints=[c1],
        ...     all_constraints_satisfied=True,
        ...     transparency_log=log
        ... )
        >>> print(result.all_constraints_satisfied)
        True
    """

    question: str
    opinions: List[str]
    consensus_statement: Optional[str]
    ranked_candidates: List[str] = field(default_factory=list)

    # Sacred value tracking
    sacred_values: List[SacredValue] = field(default_factory=list)
    constraints: List[Constraint] = field(default_factory=list)
    all_constraints_satisfied: bool = True

    # Infeasibility tracking
    is_infeasible: bool = False
    infeasibility_reason: Optional[str] = None
    conflicting_constraints: List[Tuple[Constraint, Constraint]] = field(
        default_factory=list
    )

    # Complete transparency
    transparency_log: Optional[TransparencyLog] = None

    def summary(self) -> str:
        """
        Generate a concise summary of the deliberation.

        Returns:
            Multi-line summary string
        """
        summary = "=== DELIBERATION RESULT SUMMARY ===\n\n"
        summary += f"Question: {self.question}\n"
        summary += f"Number of citizens: {len(self.opinions)}\n\n"

        summary += f"Sacred values detected: {len(self.sacred_values)}\n"
        summary += f"Constraints compiled: {len(self.constraints)}\n\n"

        if self.is_infeasible:
            summary += f"❌ INFEASIBLE: {self.infeasibility_reason}\n"
        else:
            summary += f"✓ Consensus found\n"
            summary += f"✓ All constraints satisfied: {self.all_constraints_satisfied}\n"
            summary += f"\nConsensus: {self.consensus_statement[:200]}...\n"

        return summary

    def __str__(self) -> str:
        """Human-readable representation."""
        return self.summary()
