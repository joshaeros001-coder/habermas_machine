"""
Transparency Logger Module

This module creates complete audit trails (transparency logs) for constraint-based
deliberation. Every decision - from detection to filtering to final consensus - is
logged with explanations.

The transparency log answers:
- What sacred values were detected and why?
- What constraints were compiled from them?
- What candidate statements were generated?
- Which candidates were filtered out and why?
- Does the final consensus satisfy all constraints?
- If infeasible, why couldn't consensus be reached?

This makes the entire process auditable, explainable, and verifiable.
"""

from typing import List, Tuple, Optional, Dict
from ..models.sacred_value import SacredValue
from ..models.constraint import Constraint
from ..models.deliberation_result import TransparencyLog, DeliberationResult


def create_transparency_log(
    detected_sacred_values: List[SacredValue],
    compiled_constraints: List[Constraint],
    generated_candidates: List[str],
    filtered_out: List[Tuple[str, Constraint]],
    final_feasible_set: List[str],
    final_consensus: Optional[str],
    is_infeasible: bool = False,
    infeasibility_reason: Optional[str] = None
) -> TransparencyLog:
    """
    Create a complete transparency log for a deliberation.

    This assembles all information about the deliberation process into a
    structured log that can be inspected, printed, or saved.

    Args:
        detected_sacred_values: All sacred values detected across citizens
        compiled_constraints: Constraints compiled from sacred values
        generated_candidates: ALL candidates before filtering
        filtered_out: Statements filtered for violating constraints
        final_feasible_set: Candidates that satisfied all constraints
        final_consensus: The final consensus statement (if found)
        is_infeasible: Whether consensus was impossible
        infeasibility_reason: Why consensus was impossible (if infeasible)

    Returns:
        TransparencyLog object with complete audit trail

    Example:
        >>> log = create_transparency_log(
        ...     detected_sacred_values=[sv1, sv2],
        ...     compiled_constraints=[c1],
        ...     generated_candidates=[stmt1, stmt2, stmt3, stmt4],
        ...     filtered_out=[(stmt1, c1), (stmt3, c1)],
        ...     final_feasible_set=[stmt2, stmt4],
        ...     final_consensus=stmt2,
        ...     is_infeasible=False
        ... )
        >>> print(log.generate_summary())
    """
    # Calculate constraint satisfaction for final consensus
    constraint_satisfaction = {}

    if final_consensus and not is_infeasible:
        # Check if final consensus satisfies each constraint
        for constraint in compiled_constraints:
            violated = constraint.is_violated_by(final_consensus)
            constraint_satisfaction[constraint.constraint_text] = not violated

    # Generate natural language explanation
    explanation = generate_explanation(
        detected_sacred_values=detected_sacred_values,
        compiled_constraints=compiled_constraints,
        generated_count=len(generated_candidates),
        filtered_count=len(filtered_out),
        final_consensus=final_consensus,
        is_infeasible=is_infeasible,
        infeasibility_reason=infeasibility_reason
    )

    # Create and return transparency log
    return TransparencyLog(
        detected_sacred_values=detected_sacred_values,
        compiled_constraints=compiled_constraints,
        generated_candidates=generated_candidates,
        filtered_out=filtered_out,
        final_feasible_set=final_feasible_set,
        constraint_satisfaction=constraint_satisfaction,
        infeasible=is_infeasible,
        infeasibility_reason=infeasibility_reason,
        explanation=explanation
    )


def generate_explanation(
    detected_sacred_values: List[SacredValue],
    compiled_constraints: List[Constraint],
    generated_count: int,
    filtered_count: int,
    final_consensus: Optional[str],
    is_infeasible: bool,
    infeasibility_reason: Optional[str]
) -> str:
    """
    Generate a natural language explanation of the deliberation process.

    This creates a human-readable narrative explaining what happened,
    suitable for showing to end users or including in reports.

    Args:
        detected_sacred_values: Sacred values that were detected
        compiled_constraints: Constraints that were compiled
        generated_count: Number of candidates generated
        filtered_count: Number of candidates filtered out
        final_consensus: The final consensus (if found)
        is_infeasible: Whether consensus was impossible
        infeasibility_reason: Why it was infeasible (if applicable)

    Returns:
        Multi-paragraph natural language explanation

    Example output:
        "The deliberation detected 1 sacred value from Citizen 2, who expressed
         a religious objection to medication with high confidence (0.95). This
         was compiled into a prohibition constraint affecting medication-related
         actions.

         During statement generation, 4 candidate consensus statements were created.
         Of these, 2 were filtered out for violating the medication prohibition.
         This left 2 feasible statements that respected the sacred value constraint.

         The final consensus was selected from the feasible set and satisfies
         all constraints. The sacred value was successfully respected in the
         deliberation outcome."
    """
    # Start with sacred value detection
    explanation = ""

    if not detected_sacred_values:
        explanation += (
            "No sacred values were detected in the citizen opinions. "
            "All perspectives were treated as negotiable preferences in the "
            "standard deliberation process.\n\n"
        )
    else:
        explanation += (
            f"SACRED VALUE DETECTION:\n"
            f"The deliberation detected {len(detected_sacred_values)} sacred value(s) "
            f"across the citizen opinions:\n\n"
        )

        for sv in detected_sacred_values:
            explanation += (
                f"- Citizen {sv.citizen_id}: Confidence {sv.confidence:.2f}\n"
                f"  Justification: {sv.justification}\n"
                f"  Markers: {', '.join(sv.markers[:5])}\n"
            )
            if len(sv.markers) > 5:
                explanation += f"  ... and {len(sv.markers) - 5} more\n"
            explanation += "\n"

    # Constraint compilation
    if not compiled_constraints:
        explanation += (
            "CONSTRAINT COMPILATION:\n"
            "No constraints were compiled (no sacred values detected).\n\n"
        )
    else:
        explanation += (
            f"CONSTRAINT COMPILATION:\n"
            f"The sacred value(s) were compiled into {len(compiled_constraints)} "
            f"formal constraint(s):\n\n"
        )

        for c in compiled_constraints:
            explanation += (
                f"- {c.type.value.upper()}: {c.constraint_text}\n"
                f"  Affected actions: {', '.join(c.affected_actions[:5])}\n"
            )
            if len(c.affected_actions) > 5:
                explanation += f"  ... and {len(c.affected_actions) - 5} more\n"
            explanation += "\n"

    # Statement generation and filtering
    explanation += (
        f"STATEMENT GENERATION & FILTERING:\n"
        f"Generated {generated_count} candidate consensus statements. "
    )

    if filtered_count == 0:
        explanation += (
            "All candidates satisfied the constraints and were included in the "
            "feasible set for voting.\n\n"
        )
    else:
        feasible_count = generated_count - filtered_count
        explanation += (
            f"Of these, {filtered_count} were filtered out for violating "
            f"sacred value constraints, leaving {feasible_count} feasible "
            f"statements for voting.\n\n"
        )

    # Final consensus
    if is_infeasible:
        explanation += (
            f"INFEASIBILITY:\n"
            f"The deliberation could not reach consensus because the constraints "
            f"are mutually incompatible:\n"
            f"{infeasibility_reason}\n\n"
            f"This represents a genuine moral disagreement that cannot be resolved "
            f"through compromise. The system correctly acknowledges this rather than "
            f"forcing an artificial consensus.\n"
        )
    elif final_consensus:
        explanation += (
            f"FINAL CONSENSUS:\n"
            f"The final consensus statement was selected from the feasible set "
            f"through democratic voting. "
        )

        if compiled_constraints:
            all_satisfied = all(
                not c.is_violated_by(final_consensus)
                for c in compiled_constraints
            )

            if all_satisfied:
                explanation += (
                    f"This statement satisfies all {len(compiled_constraints)} "
                    f"sacred value constraint(s), successfully respecting the "
                    f"non-negotiable commitments expressed by citizens.\n"
                )
            else:
                explanation += (
                    f"⚠️ WARNING: This statement violates one or more constraints. "
                    f"This should not happen and indicates a filtering failure.\n"
                )
        else:
            explanation += "No constraints were present.\n"
    else:
        explanation += (
            "No consensus was reached in this deliberation.\n"
        )

    return explanation


class TransparencyLogger:
    """
    Stateful transparency logger that accumulates information during deliberation.

    This class is designed to be used throughout the deliberation process,
    recording each step as it happens, then producing a final transparency log.

    Usage pattern:
        logger = TransparencyLogger()
        logger.log_detection(sacred_values)
        logger.log_compilation(constraints)
        logger.log_generation(candidates)
        logger.log_filtering(filtered_out, feasible_set)
        logger.log_consensus(final_consensus)
        transparency_log = logger.create_log()

    Attributes:
        sacred_values: Detected sacred values
        constraints: Compiled constraints
        candidates: Generated candidates
        filtered_out: Filtered statements with violated constraints
        feasible_set: Final feasible set
        consensus: Final consensus
        infeasible: Whether deliberation was infeasible
        infeasibility_reason: Reason for infeasibility

    Example:
        >>> logger = TransparencyLogger()
        >>> logger.log_detection([sv1, sv2])
        >>> logger.log_compilation([c1])
        >>> logger.log_generation([stmt1, stmt2, stmt3])
        >>> logger.log_filtering([(stmt1, c1)], [stmt2, stmt3])
        >>> logger.log_consensus(stmt2)
        >>> log = logger.create_log()
        >>> print(log)
    """

    def __init__(self):
        """Initialize an empty transparency logger."""
        self.sacred_values: List[SacredValue] = []
        self.constraints: List[Constraint] = []
        self.candidates: List[str] = []
        self.filtered_out: List[Tuple[str, Constraint]] = []
        self.feasible_set: List[str] = []
        self.consensus: Optional[str] = None
        self.infeasible: bool = False
        self.infeasibility_reason: Optional[str] = None

    def log_detection(self, sacred_values: List[SacredValue]) -> None:
        """
        Log sacred value detection results.

        Args:
            sacred_values: List of detected sacred values
        """
        self.sacred_values = sacred_values

    def log_compilation(self, constraints: List[Constraint]) -> None:
        """
        Log constraint compilation results.

        Args:
            constraints: List of compiled constraints
        """
        self.constraints = constraints

    def log_generation(self, candidates: List[str]) -> None:
        """
        Log statement generation results.

        Args:
            candidates: List of generated candidate statements
        """
        self.candidates = candidates

    def log_filtering(self,
                     filtered_out: List[Tuple[str, Constraint]],
                     feasible_set: List[str]) -> None:
        """
        Log filtering results.

        Args:
            filtered_out: Statements that were filtered with violated constraints
            feasible_set: Statements that satisfied all constraints
        """
        self.filtered_out = filtered_out
        self.feasible_set = feasible_set

    def log_consensus(self, consensus: Optional[str]) -> None:
        """
        Log final consensus statement.

        Args:
            consensus: The final consensus statement (None if none found)
        """
        self.consensus = consensus

    def log_infeasibility(self, reason: str) -> None:
        """
        Log that deliberation was infeasible.

        Args:
            reason: Explanation of why consensus is impossible
        """
        self.infeasible = True
        self.infeasibility_reason = reason

    def create_log(self) -> TransparencyLog:
        """
        Create the final transparency log from accumulated information.

        Returns:
            Complete TransparencyLog object

        Example:
            >>> logger = TransparencyLogger()
            >>> # ... log various steps ...
            >>> transparency_log = logger.create_log()
            >>> print(transparency_log.generate_summary())
        """
        return create_transparency_log(
            detected_sacred_values=self.sacred_values,
            compiled_constraints=self.constraints,
            generated_candidates=self.candidates,
            filtered_out=self.filtered_out,
            final_feasible_set=self.feasible_set,
            final_consensus=self.consensus,
            is_infeasible=self.infeasible,
            infeasibility_reason=self.infeasibility_reason
        )

    def get_summary(self) -> str:
        """
        Get a summary of current state (before final log creation).

        Returns:
            Human-readable summary of what has been logged so far
        """
        summary = "TRANSPARENCY LOGGER STATUS\n"
        summary += "=" * 80 + "\n"
        summary += f"Sacred values logged: {len(self.sacred_values)}\n"
        summary += f"Constraints logged: {len(self.constraints)}\n"
        summary += f"Candidates logged: {len(self.candidates)}\n"
        summary += f"Filtered out: {len(self.filtered_out)}\n"
        summary += f"Feasible set: {len(self.feasible_set)}\n"
        summary += f"Consensus: {'Yes' if self.consensus else 'No'}\n"
        summary += f"Infeasible: {'Yes' if self.infeasible else 'No'}\n"

        return summary


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    from .sacred_value_detector import detect_sacred_value
    from .constraint_compiler import compile_constraint

    print("="*80)
    print("TRANSPARENCY LOGGING EXAMPLE")
    print("="*80)

    # Simulate a deliberation
    print("\nSimulating a deliberation with sacred values...\n")

    # Step 1: Detection
    opinion = """
    I cannot take medication due to my religious faith.
    This is a matter of spiritual integrity.
    """
    sacred_value = detect_sacred_value(opinion, citizen_id=2)

    # Step 2: Compilation
    constraint = compile_constraint(sacred_value)

    # Step 3: Generation (simulated)
    candidates = [
        "The patient should try SSRIs as recommended.",
        "For those whose faith prohibits medication, therapy is a valid path.",
        "Start medication promptly to reduce symptoms.",
        "Treatment choices should respect individual values and beliefs."
    ]

    # Step 4: Filtering (simulated)
    filtered_out = [
        (candidates[0], constraint),  # Filtered: prescribes medication
        (candidates[2], constraint),  # Filtered: prescribes medication
    ]
    feasible_set = [candidates[1], candidates[3]]

    # Step 5: Consensus (simulated)
    final_consensus = candidates[1]  # Selected from feasible set

    # Create transparency log
    print("-"*80)
    print("Creating transparency log...")
    print("-"*80)

    logger = TransparencyLogger()
    logger.log_detection([sacred_value])
    logger.log_compilation([constraint])
    logger.log_generation(candidates)
    logger.log_filtering(filtered_out, feasible_set)
    logger.log_consensus(final_consensus)

    transparency_log = logger.create_log()

    # Print the log
    print("\n" + "="*80)
    print("TRANSPARENCY LOG")
    print("="*80)
    print(transparency_log.generate_summary())

    # Also print the natural language explanation
    print("\n" + "="*80)
    print("NATURAL LANGUAGE EXPLANATION")
    print("="*80)
    print(transparency_log.explanation)

    print("\n" + "="*80)
    print("This transparency log makes the deliberation process:")
    print("  - Auditable: Every decision is recorded")
    print("  - Explainable: Natural language summaries provided")
    print("  - Verifiable: Can check that constraints were respected")
    print("="*80)
