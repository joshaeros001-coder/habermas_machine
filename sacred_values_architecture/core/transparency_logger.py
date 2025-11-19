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

"""Transparency Logger - Track All Constraint-Related Decisions.

For real-world deployment, users MUST understand:
1. Which sacred values were detected in their opinions
2. Which constraints were compiled from those values
3. Which candidate statements were filtered out (and why)
4. Whether the final consensus satisfies all constraints

This module provides comprehensive logging of the constraint handling process.

CRITICAL FOR TRUST:
If a system filters out statements based on constraints, it must explain
why to maintain user trust and enable debugging.
"""

from typing import List
from sacred_values_architecture.types import (
    SacredValue, Constraint, TransparencyLog
)
from sacred_values_architecture.core import constraint_compiler


class TransparencyLogger:
    """Logger for tracking constraint-related decisions during deliberation.

    This class provides methods to record all major events in the constraint
    handling process, building up a comprehensive log that can be displayed
    to users or used for debugging.

    Example:
        >>> logger = TransparencyLogger()
        >>> logger.log_sacred_value_detection(sacred_values)
        >>> logger.log_constraint_compilation(constraints)
        >>> logger.log_statement_filtered(statement, constraint, reason)
        >>> logger.get_log()
        TransparencyLog(constraints_detected=1, statements_filtered=3, ...)
    """

    def __init__(self):
        """Initialize an empty transparency log."""
        self._log = TransparencyLog()

    def log_sacred_value_detection(
        self,
        sacred_values: List[SacredValue],
        total_opinions: int
    ):
        """Log the results of sacred value detection.

        Args:
            sacred_values: List of detected sacred values
            total_opinions: Total number of citizen opinions analyzed
        """
        self._log.constraints_detected = len(sacred_values)
        self._log.detected_sacred_values = sacred_values

        # Record in filtering reasons for transparency
        if sacred_values:
            self._log.filtering_reasons.append(
                f"Detected {len(sacred_values)} sacred value(s) from {total_opinions} opinions"
            )
            for sv in sacred_values:
                self._log.filtering_reasons.append(
                    f"  - Citizen {sv.citizen_id} (confidence {sv.confidence:.2f}): "
                    f'"{sv.constraint_text}"'
                )
        else:
            self._log.filtering_reasons.append(
                f"No sacred values detected in {total_opinions} opinions"
            )

    def log_constraint_compilation(self, constraints: List[Constraint]):
        """Log the results of constraint compilation.

        Args:
            constraints: List of compiled constraints
        """
        self._log.compiled_constraints = constraints

        if constraints:
            self._log.filtering_reasons.append(
                f"\nCompiled {len(constraints)} constraint(s):"
            )
            for constraint in constraints:
                desc = constraint_compiler.describe_constraint(constraint)
                self._log.filtering_reasons.append(f"  - {desc}")
        else:
            self._log.filtering_reasons.append("\nNo constraints to enforce")

    def log_statement_generation(self, num_statements: int):
        """Log the number of statements generated.

        Args:
            num_statements: Number of candidate statements generated
        """
        self._log.statements_generated = num_statements
        self._log.filtering_reasons.append(
            f"\nGenerated {num_statements} candidate statements"
        )

    def log_statement_filtered(
        self,
        statement: str,
        constraint: Constraint,
        reason: str
    ):
        """Log that a statement was filtered for violating a constraint.

        Args:
            statement: The filtered statement
            constraint: The constraint that was violated
            reason: Explanation of the violation
        """
        self._log.statements_filtered += 1
        self._log.add_violation(statement, constraint, reason)

    def log_constraint_satisfaction_check(
        self,
        num_valid: int,
        num_invalid: int
    ):
        """Log the results of filtering statements by constraints.

        Args:
            num_valid: Number of statements that passed constraints
            num_invalid: Number of statements filtered out
        """
        if num_invalid > 0:
            self._log.filtering_reasons.append(
                f"\nFiltered {num_invalid} statement(s) for constraint violations"
            )
            self._log.filtering_reasons.append(
                f"Remaining valid statements: {num_valid}"
            )
        else:
            self._log.filtering_reasons.append(
                f"\nAll {num_valid} statements satisfy constraints"
            )

    def log_final_check(
        self,
        winning_statement: str,
        constraints: List[Constraint],
        passes: bool,
        reasons: List[str]
    ):
        """Log the final check of the winning statement against all constraints.

        Args:
            winning_statement: The final consensus statement
            constraints: All constraints that should be satisfied
            passes: Whether the winning statement satisfies all constraints
            reasons: List of violation reasons (empty if passes)
        """
        self._log.final_check_passed = passes
        self._log.constraints_satisfied = len(constraints) if passes else 0

        if passes:
            self._log.filtering_reasons.append(
                f"\n✓ Final consensus satisfies all {len(constraints)} constraint(s)"
            )
        else:
            self._log.filtering_reasons.append(
                f"\n✗ Final consensus VIOLATES constraint(s):"
            )
            for reason in reasons:
                self._log.filtering_reasons.append(f"  - {reason}")

    def log_infeasibility(self, reason: str):
        """Log that no feasible statement could be found.

        Args:
            reason: Explanation of why the problem is infeasible
        """
        self._log.filtering_reasons.append(f"\n✗ INFEASIBLE: {reason}")
        self._log.final_check_passed = False

    def get_log(self) -> TransparencyLog:
        """Get the complete transparency log.

        Returns:
            The accumulated TransparencyLog object
        """
        return self._log

    def print_summary(self):
        """Print a human-readable summary of the log to console."""
        print(self._log.summary())

    def get_detailed_report(self) -> str:
        """Get a detailed report of all logged events.

        Returns:
            Formatted string with complete event history

        Example:
            >>> logger = TransparencyLogger()
            >>> # ... log events ...
            >>> print(logger.get_detailed_report())
        """
        report = "=" * 80 + "\n"
        report += "SACRED VALUES CONSTRAINT TRANSPARENCY REPORT\n"
        report += "=" * 80 + "\n\n"

        report += "EVENT LOG:\n"
        report += "-" * 80 + "\n"
        for event in self._log.filtering_reasons:
            report += event + "\n"

        report += "\n" + "=" * 80 + "\n"
        report += "SUMMARY:\n"
        report += "-" * 80 + "\n"
        report += self._log.summary()

        return report
