"""
Data class for representing compiled constraints from sacred values.

A constraint is a hard restriction on what consensus statements can recommend.
Unlike preferences (which can be traded off), constraints must be satisfied
for a statement to be in the feasible set.

Example:
    If Citizen 2 says "I cannot take medication due to my faith", this becomes:
    Constraint(
        citizen_id=2,
        type="prohibition",
        constraint_text="cannot take medication",
        affected_actions=["medication", "SSRI", "pharmaceutical", "drug"],
        justification="religious faith"
    )

    Any consensus statement that recommends medication violates this constraint
    and must be filtered out.
"""

from dataclasses import dataclass
from typing import List
from enum import Enum


class ConstraintType(Enum):
    """
    Type of constraint imposed by a sacred value.

    PROHIBITION: Something that must NOT be recommended/done
        e.g., "cannot take medication", "must not violate confidentiality"

    REQUIREMENT: Something that MUST be recommended/done
        e.g., "must respect life", "must obtain consent"

    Note: Most sacred values create prohibitions. Requirements are rarer
    but important (e.g., "must protect vulnerable populations").
    """
    PROHIBITION = "prohibition"  # Must NOT do X
    REQUIREMENT = "requirement"  # MUST do X


@dataclass
class Constraint:
    """
    Represents a hard constraint compiled from a sacred value.

    This constraint defines what is NOT in the feasible set. Any consensus
    statement that violates this constraint cannot be selected, regardless
    of how many other citizens prefer it.

    Attributes:
        citizen_id: Who imposed this constraint (0-indexed)
        type: Whether this prohibits or requires something
        constraint_text: Human-readable description of the constraint
            e.g., "cannot take medication due to religious faith"
        affected_actions: Keywords that trigger this constraint
            e.g., ["medication", "SSRI", "pharmaceutical", "drug", "pills"]
            Any statement containing these in a prescriptive context violates
        justification: Why this constraint exists
            e.g., "religious faith", "moral principle", "protected value"

    Example:
        >>> constraint = Constraint(
        ...     citizen_id=2,
        ...     type=ConstraintType.PROHIBITION,
        ...     constraint_text="cannot take medication",
        ...     affected_actions=["medication", "SSRI", "drug"],
        ...     justification="Christian faith - healing through prayer"
        ... )
        >>> constraint.is_violated_by("Patient should try SSRI medication")
        True
        >>> constraint.is_violated_by("Patient may explore therapy")
        False
    """

    citizen_id: int
    type: ConstraintType
    constraint_text: str
    affected_actions: List[str]
    justification: str

    def is_violated_by(self, statement: str) -> bool:
        """
        Check if a consensus statement violates this constraint.

        For PROHIBITION constraints:
            Violated if statement recommends any affected_actions

        For REQUIREMENT constraints:
            Violated if statement fails to mention affected_actions

        Args:
            statement: The consensus statement to check

        Returns:
            True if statement violates constraint, False if acceptable

        Example:
            >>> c = Constraint(
            ...     citizen_id=2,
            ...     type=ConstraintType.PROHIBITION,
            ...     constraint_text="no medication",
            ...     affected_actions=["medication", "SSRI"],
            ...     justification="faith"
            ... )
            >>> c.is_violated_by("Try SSRIs for depression")
            True  # Recommends SSRI (prohibited action)
            >>> c.is_violated_by("Therapy is an option")
            False  # Doesn't recommend prohibited action
        """
        statement_lower = statement.lower()

        if self.type == ConstraintType.PROHIBITION:
            # Violation: statement recommends a prohibited action
            # Look for prescriptive language + affected action
            prescriptive_words = [
                'should', 'recommend', 'try', 'start', 'take', 'use',
                'consider', 'accept', 'begin', 'pursue'
            ]

            # Check if statement prescribes any affected action
            for action in self.affected_actions:
                action_lower = action.lower()
                if action_lower in statement_lower:
                    # Check if it's in a prescriptive context
                    # (not just mentioning it as an option)
                    for prescriptive in prescriptive_words:
                        if prescriptive in statement_lower:
                            # Found prescriptive language + affected action
                            return True

            return False  # Mentioned but not prescribed, or not mentioned

        elif self.type == ConstraintType.REQUIREMENT:
            # Violation: statement fails to mention required action
            for action in self.affected_actions:
                if action.lower() in statement_lower:
                    return False  # Found required action mentioned

            return True  # Required action not mentioned = violation

        else:
            # Unknown constraint type
            raise ValueError(f"Unknown constraint type: {self.type}")

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            Formatted string for display
        """
        return (
            f"{self.type.value.upper()}: {self.constraint_text} "
            f"(citizen {self.citizen_id})"
        )

    def __repr__(self) -> str:
        """
        Developer-friendly representation.

        Returns:
            Complete repr for debugging
        """
        return (
            f"Constraint("
            f"citizen_id={self.citizen_id}, "
            f"type={self.type}, "
            f"text='{self.constraint_text}', "
            f"actions={self.affected_actions})"
        )
