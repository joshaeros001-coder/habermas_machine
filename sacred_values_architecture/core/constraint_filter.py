"""
Constraint Filter Module

This module filters out consensus statement candidates that violate sacred value
constraints. It serves as a safety net ensuring that no constraint-violating
statement reaches the voting stage.

The filter is applied AFTER statement generation but BEFORE voting. This creates
a "feasible set" of statements that satisfy all constraints.

Key functions:
- filter_violating_statements: Remove statements that violate any constraint
- check_statement_feasibility: Check if a single statement is feasible
- get_feasible_set: Get all constraint-satisfying statements with violation log

This is a critical component for ensuring sacred values are respected.
"""

from typing import List, Tuple, Dict, Optional
from ..models.constraint import Constraint
from ..models.deliberation_result import TransparencyLog


def check_statement_feasibility(statement: str,
                                constraints: List[Constraint]) -> Tuple[bool, Optional[Constraint]]:
    """
    Check if a statement is feasible (satisfies all constraints).

    A statement is feasible if it does NOT violate ANY constraint.
    If it violates even one constraint, it's infeasible and should be filtered out.

    Args:
        statement: The consensus statement candidate to check
        constraints: List of all active constraints to check against

    Returns:
        Tuple of (is_feasible, violated_constraint)
        - is_feasible: True if statement satisfies all constraints
        - violated_constraint: The first constraint violated (None if feasible)

    Example:
        >>> constraint = Constraint(type=PROHIBITION, affected_actions=["medication"], ...)
        >>> statement = "The patient should try SSRIs"
        >>> feasible, violated = check_statement_feasibility(statement, [constraint])
        >>> feasible
        False  # Violates the prohibition on medication
        >>> violated.constraint_text
        "cannot take medication"
    """
    # Check each constraint
    for constraint in constraints:
        # Use the Constraint's built-in violation check
        if constraint.is_violated_by(statement):
            # This statement violates this constraint
            # Return immediately - one violation is enough to be infeasible
            return False, constraint

    # Statement satisfies all constraints
    return True, None


def filter_violating_statements(
    candidates: List[str],
    constraints: List[Constraint],
    verbose: bool = False
) -> Tuple[List[str], List[Tuple[str, Constraint]]]:
    """
    Filter out statements that violate sacred value constraints.

    This is the main filtering function. It takes a list of candidate statements
    and returns:
    1. The feasible set (statements that satisfy all constraints)
    2. The violation log (statements that were filtered out and why)

    Algorithm:
    1. For each candidate statement:
       a. Check if it violates any constraint
       b. If yes: add to violations list with the violated constraint
       c. If no: add to feasible set
    2. Return both lists for transparency

    Args:
        candidates: List of candidate consensus statements (from generation)
        constraints: List of sacred value constraints to enforce
        verbose: If True, print filtering details

    Returns:
        Tuple of (feasible_statements, filtered_out)
        - feasible_statements: Statements that satisfy all constraints
        - filtered_out: List of (statement, violated_constraint) pairs

    Example:
        >>> candidates = [
        ...     "The patient should try SSRIs",  # Violates
        ...     "For those whose faith prohibits medication, therapy is valid"  # OK
        ... ]
        >>> constraints = [medication_prohibition_constraint]
        >>> feasible, filtered = filter_violating_statements(candidates, constraints)
        >>> len(feasible)
        1
        >>> len(filtered)
        1
        >>> filtered[0][0]  # The filtered statement
        "The patient should try SSRIs"
        >>> filtered[0][1]  # The violated constraint
        <Constraint: cannot take medication>
    """
    feasible = []
    filtered_out = []

    if verbose:
        print(f"\n{'='*80}")
        print(f"FILTERING {len(candidates)} CANDIDATES AGAINST {len(constraints)} CONSTRAINTS")
        print(f"{'='*80}\n")

    for i, statement in enumerate(candidates, 1):
        # Check if this statement is feasible
        is_feasible, violated_constraint = check_statement_feasibility(
            statement, constraints
        )

        if is_feasible:
            # Statement satisfies all constraints - add to feasible set
            feasible.append(statement)

            if verbose:
                print(f"✓ Candidate {i}: FEASIBLE")
                print(f"  \"{statement[:80]}...\"")

        else:
            # Statement violates a constraint - filter it out
            filtered_out.append((statement, violated_constraint))

            if verbose:
                print(f"✗ Candidate {i}: FILTERED OUT")
                print(f"  \"{statement[:80]}...\"")
                print(f"  Violated constraint: {violated_constraint.constraint_text}")
                print(f"  From citizen {violated_constraint.citizen_id}")

    if verbose:
        print(f"\n{'-'*80}")
        print(f"FILTERING RESULTS:")
        print(f"  Feasible statements: {len(feasible)}")
        print(f"  Filtered out: {len(filtered_out)}")
        print(f"{'-'*80}\n")

    return feasible, filtered_out


def get_constraint_satisfaction_status(
    statement: str,
    constraints: List[Constraint]
) -> Dict[str, bool]:
    """
    Get detailed satisfaction status for each constraint.

    This checks a single statement against all constraints and returns
    a dictionary showing which constraints are satisfied and which are violated.

    Useful for transparency logging and explaining why a statement was filtered.

    Args:
        statement: The statement to check
        constraints: List of constraints to check against

    Returns:
        Dictionary mapping constraint_text to satisfied (True/False)

    Example:
        >>> status = get_constraint_satisfaction_status(statement, constraints)
        >>> status
        {
            "cannot take medication": True,
            "must include spiritual option": False
        }
    """
    status = {}

    for constraint in constraints:
        # Check if this constraint is violated
        violated = constraint.is_violated_by(statement)

        # Satisfied = not violated
        satisfied = not violated

        # Use constraint text as key
        status[constraint.constraint_text] = satisfied

    return status


def check_infeasibility(constraints: List[Constraint]) -> Tuple[bool, Optional[str]]:
    """
    Check if constraints are mutually incompatible (infeasible).

    This analyzes whether it's possible to satisfy ALL constraints simultaneously.
    If constraints conflict, NO consensus statement can satisfy them all.

    Current implementation: Simplified heuristic check
    Future improvement: Formal constraint satisfaction analysis

    Args:
        constraints: List of constraints to check for conflicts

    Returns:
        Tuple of (is_infeasible, reason)
        - is_infeasible: True if constraints conflict
        - reason: Explanation of why constraints are incompatible

    Example:
        >>> c1 = Constraint(type=PROHIBITION, affected_actions=["medication"], ...)
        >>> c2 = Constraint(type=REQUIREMENT, affected_actions=["medication"], ...)
        >>> infeasible, reason = check_infeasibility([c1, c2])
        >>> infeasible
        True
        >>> reason
        "Conflicting constraints: prohibition and requirement on 'medication'"
    """
    # Simple heuristic: Check for direct conflicts
    # A prohibition and requirement on the same action is infeasible

    prohibitions = [c for c in constraints if c.type.value == "prohibition"]
    requirements = [c for c in constraints if c.type.value == "requirement"]

    # Check for conflicts between prohibitions and requirements
    for prohibition in prohibitions:
        for requirement in requirements:
            # Check if they affect overlapping actions
            overlap = set(prohibition.affected_actions) & set(requirement.affected_actions)

            if overlap:
                # This is a conflict: one citizen prohibits X, another requires X
                conflicting_action = list(overlap)[0]
                reason = (
                    f"Conflicting constraints on '{conflicting_action}': "
                    f"Citizen {prohibition.citizen_id} prohibits it "
                    f"('{prohibition.constraint_text}'), but "
                    f"Citizen {requirement.citizen_id} requires it "
                    f"('{requirement.constraint_text}'). "
                    f"No statement can satisfy both."
                )
                return True, reason

    # No conflicts detected
    return False, None


class ConstraintFilter:
    """
    Stateful constraint filter with violation logging.

    This class wraps the filtering logic in an object that maintains
    a log of all filtering decisions for transparency.

    Attributes:
        constraints: Active constraints to enforce
        verbose: Whether to print filtering details
        filter_log: History of all filtering operations

    Example:
        >>> filter = ConstraintFilter(constraints, verbose=True)
        >>> feasible = filter.filter(candidates)
        >>> print(filter.get_summary())
    """

    def __init__(self, constraints: List[Constraint], verbose: bool = False):
        """
        Initialize the filter with constraints.

        Args:
            constraints: List of constraints to enforce
            verbose: If True, print filtering details
        """
        self.constraints = constraints
        self.verbose = verbose
        self.filter_log: List[Dict] = []  # History of filtering operations

    def filter(self, candidates: List[str]) -> List[str]:
        """
        Filter candidates and return only feasible statements.

        Args:
            candidates: List of candidate statements

        Returns:
            List of feasible statements (satisfying all constraints)

        Example:
            >>> filter = ConstraintFilter(constraints)
            >>> candidates = [statement1, statement2, statement3]
            >>> feasible = filter.filter(candidates)
            >>> len(feasible) <= len(candidates)  # Some may be filtered out
            True
        """
        feasible, filtered_out = filter_violating_statements(
            candidates, self.constraints, self.verbose
        )

        # Log this filtering operation
        self.filter_log.append({
            'candidates_in': len(candidates),
            'feasible_out': len(feasible),
            'filtered_out': len(filtered_out),
            'violations': filtered_out
        })

        return feasible

    def get_filtered_count(self) -> int:
        """
        Get total number of statements filtered across all operations.

        Returns:
            Total count of filtered statements
        """
        return sum(log['filtered_out'] for log in self.filter_log)

    def get_summary(self) -> str:
        """
        Get a summary of all filtering operations.

        Returns:
            Human-readable summary string

        Example:
            >>> print(filter.get_summary())
            Filtering Summary:
              Total operations: 2
              Total candidates: 8
              Total filtered out: 3
              Total feasible: 5
        """
        if not self.filter_log:
            return "No filtering operations performed yet."

        total_in = sum(log['candidates_in'] for log in self.filter_log)
        total_out = sum(log['feasible_out'] for log in self.filter_log)
        total_filtered = sum(log['filtered_out'] for log in self.filter_log)

        summary = "FILTERING SUMMARY\n"
        summary += "=" * 80 + "\n"
        summary += f"Total operations: {len(self.filter_log)}\n"
        summary += f"Total candidates processed: {total_in}\n"
        summary += f"Total filtered out: {total_filtered}\n"
        summary += f"Total feasible statements: {total_out}\n"
        summary += f"Filter rate: {(total_filtered/total_in)*100:.1f}%\n"

        return summary


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    from .constraint_compiler import compile_constraint
    from .sacred_value_detector import detect_sacred_value

    print("="*80)
    print("CONSTRAINT FILTERING EXAMPLE")
    print("="*80)

    # Step 1: Create a constraint (religious objection to medication)
    opinion = """
    As a devout Christian, I believe depression is a spiritual trial.
    I cannot take medication due to my faith.
    """

    sacred_value = detect_sacred_value(opinion, citizen_id=2)
    if not sacred_value:
        print("No sacred value detected")
        exit(1)

    constraint = compile_constraint(sacred_value)

    print("\n" + "-"*80)
    print("Active Constraint:")
    print("-"*80)
    print(f"Type: {constraint.type.value.upper()}")
    print(f"Text: {constraint.constraint_text}")
    print(f"Affected actions: {constraint.affected_actions[:5]}...")

    # Step 2: Test filtering on candidate statements
    candidates = [
        # Candidate 1: Violates (prescribes medication)
        "The patient should try SSRIs as recommended by their doctor.",

        # Candidate 2: Satisfies (acknowledges sacred value)
        "For those whose faith prohibits medication, therapy and spiritual "
        "support are valid alternatives.",

        # Candidate 3: Violates (recommends medication)
        "Start antidepressant medication promptly to reduce symptoms.",

        # Candidate 4: Satisfies (neutral, doesn't prescribe)
        "Multiple treatment approaches exist. The choice should reflect "
        "individual values and circumstances.",
    ]

    print("\n" + "-"*80)
    print(f"Filtering {len(candidates)} candidates:")
    print("-"*80)

    # Filter with verbose output
    feasible, filtered_out = filter_violating_statements(
        candidates, [constraint], verbose=True
    )

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"\nFeasible set ({len(feasible)} statements):")
    for i, stmt in enumerate(feasible, 1):
        print(f"  {i}. {stmt[:70]}...")

    print(f"\nFiltered out ({len(filtered_out)} statements):")
    for i, (stmt, violated_constraint) in enumerate(filtered_out, 1):
        print(f"  {i}. {stmt[:70]}...")
        print(f"     Violated: {violated_constraint.constraint_text}")

    print("\n" + "="*80)
    print("Key Insight:")
    print("="*80)
    print(f"In standard deliberation: All {len(candidates)} statements would be voted on")
    print(f"With sacred values: Only {len(feasible)} constraint-satisfying statements reach voting")
    print(f"This ensures the final consensus respects non-negotiable values.")
    print("="*80)
