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

"""Constraint-Aware Habermas Machine - Main Deliberation Orchestrator.

ADAPTED FROM: habermas_machine.machine.HabermasMachine
CHANGES: Added sacred value detection, constraint compilation, and filtering
WHY: Standard CRM doesn't handle sacred values as lexicographic constraints

ARCHITECTURAL FLOW:
Standard CRM:
  1. Generate statements (arbitrary)
  2. Rank statements
  3. Vote
  4. Return winner

This System:
  1. Detect sacred values in opinions
  2. Compile constraints from sacred values
  3. Generate only constraint-satisfying statements
  4. Filter out any constraint violations
  5. Rank remaining statements
  6. Vote on valid options only
  7. Verify winner satisfies constraints
  8. Return winner + transparency log

KEY INNOVATION: Constraint-first approach ensures sacred values are lexicographic
constraints, not weighted preferences.
"""

from collections.abc import Sequence
from typing import List

import numpy as np

from sacred_values_architecture import types, utils
from sacred_values_architecture.llm_client import base_client
from sacred_values_architecture.reward_model import base_model as base_reward_model
from sacred_values_architecture.social_choice import base_method as base_social_choice
from sacred_values_architecture.statement_model import constrained_cot_model
from sacred_values_architecture.core import sacred_value_detector
from sacred_values_architecture.core import constraint_compiler
from sacred_values_architecture.core import transparency_logger


class ConstrainedHabermasMachine:
    """Mediates deliberation with sacred value constraints.

    ADAPTED FROM: HabermasMachine
    CHANGES: Two-phase approach - detect constraints, then generate feasible statements
    WHY: Ensures sacred values are respected as hard constraints

    This is the MAIN ENTRY POINT for the sacred values architecture.
    """

    def __init__(
        self,
        question: str,
        statement_client: base_client.LLMClient,
        reward_client: base_client.LLMClient,
        statement_model: constrained_cot_model.ConstrainedCOTModel,
        reward_model: base_reward_model.BaseRankingModel,
        social_choice_method: base_social_choice.Base,
        num_candidates: int = 16,
        num_citizens: int = 5,
        seed: int | None = None,
        verbose: bool = False,
        num_retries_on_error: int | None = 8,
        min_sacred_value_confidence: float = 0.70,
    ):
        """Initializes the Constraint-Aware Habermas Machine.

        Args:
            question: The deliberation question
            statement_client: LLM client for statement generation
            reward_client: LLM client for ranking
            statement_model: Constraint-aware statement generation model
            reward_model: Ranking model
            social_choice_method: Voting aggregation method (e.g., Schulze)
            num_candidates: Number of candidate statements to generate
            num_citizens: Number of citizens in the deliberation
            seed: Random seed for reproducibility
            verbose: Whether to print progress
            num_retries_on_error: Number of retries on LLM errors
            min_sacred_value_confidence: Minimum confidence to treat as sacred value
        """
        # Standard CRM parameters
        self._question = question
        self._round = 0
        self._critiques = []
        self._statement_client = statement_client
        self._reward_client = reward_client
        self._statement_model = statement_model
        self._reward_model = reward_model
        self._social_choice_method = social_choice_method
        self._num_candidates = num_candidates
        self._rng = np.random.default_rng(seed)
        self._num_citizens = num_citizens
        self._previous_winners = []
        self._ranking_explanations = []
        self._previous_tied_rankings = []
        self._previous_untied_rankings = []
        self._statement_explanations = []
        self._previous_candidates = []
        self._verbose = verbose
        self._opinions = []
        self._num_retries_on_error = num_retries_on_error

        # NEW: Sacred value parameters
        self._min_sacred_value_confidence = min_sacred_value_confidence
        self._detected_sacred_values: List[types.SacredValue] = []
        self._compiled_constraints: List[types.Constraint] = []
        self._transparency_logger = transparency_logger.TransparencyLogger()

    def _get_new_seed(self):
        """Generates a new random seed."""
        return self._rng.integers(np.iinfo(np.int32).max)

    def _detect_and_compile_constraints(self, opinions: List[str]):
        """PHASE 1: Detect sacred values and compile constraints.

        NEW METHOD: This is the core innovation.

        Args:
            opinions: List of citizen opinions
        """
        if self._verbose:
            print("\n" + "="*80)
            print("PHASE 1: DETECTING SACRED VALUES")
            print("="*80)

        # Step 1: Detect sacred values in opinions
        all_sacred_values = sacred_value_detector.detect_sacred_values_batch(opinions)

        # Step 2: Filter by confidence threshold
        self._detected_sacred_values = sacred_value_detector.filter_by_confidence(
            all_sacred_values, min_confidence=self._min_sacred_value_confidence
        )

        # Step 3: Log detection results
        self._transparency_logger.log_sacred_value_detection(
            self._detected_sacred_values,
            total_opinions=len(opinions)
        )

        if self._verbose:
            print(f"\nDetected {len(self._detected_sacred_values)} sacred value(s):")
            for sv in self._detected_sacred_values:
                print(f"  {sacred_value_detector.get_sacred_value_summary(sv)}")

        # Step 4: Compile constraints
        self._compiled_constraints = constraint_compiler.compile_constraints_batch(
            self._detected_sacred_values
        )

        # Step 5: Log constraint compilation
        self._transparency_logger.log_constraint_compilation(self._compiled_constraints)

        if self._verbose:
            print(f"\nCompiled {len(self._compiled_constraints)} constraint(s):")
            for constraint in self._compiled_constraints:
                print(f"  {constraint_compiler.describe_constraint(constraint)}")

    def _generate_statements(
        self,
    ) -> tuple[list[str], list[str]]:  # statements, explanations.
        """PHASE 2: Generate constraint-satisfying candidate statements.

        ADAPTED FROM: HabermasMachine._generate_statements
        CHANGES: Passes constraints to statement model
        WHY: Guide LLM to generate only feasible statements

        Returns:
            Tuple of (statements, explanations)
        """
        if self._verbose:
            print("\n" + "="*80)
            print("PHASE 2: GENERATING CONSTRAINT-SATISFYING STATEMENTS")
            print("="*80)

        statements = []
        explanations = []

        for i in range(self._num_candidates):
            # Shuffle the opinions and critiques to avoid ordering bias
            indices = self._rng.permutation(self._num_citizens)
            shuffled_opinions = [self._opinions[j] for j in indices]
            shuffled_critiques = (
                [self._critiques[-1][i] for i in indices] if self._critiques else None
            )

            # CRITICAL: Pass constraints to statement generation
            statement, explanation = self._statement_model.generate_statement(
                llm_client=self._statement_client,
                question=self._question,
                opinions=shuffled_opinions,
                previous_winner=(
                    self._previous_winners[-1] if self._previous_winners else None
                ),
                critiques=shuffled_critiques,
                seed=self._get_new_seed(),
                num_retries_on_error=self._num_retries_on_error,
                constraints=self._compiled_constraints,  # NEW: Inject constraints
            )
            statements.append(statement)
            explanations.append(explanation)

        # Log statement generation
        self._transparency_logger.log_statement_generation(len(statements))

        if self._verbose:
            print(f"\nGenerated {len(statements)} candidate statements")

        return statements, explanations

    def _filter_statements_by_constraints(
        self,
        statements: List[str]
    ) -> tuple[List[str], List[int]]:
        """PHASE 3: Filter out statements that violate constraints.

        NEW METHOD: Critical safety check.

        Even though we guide the LLM to generate constraint-satisfying statements,
        we must verify and filter. LLMs can sometimes ignore instructions.

        Args:
            statements: List of candidate statements

        Returns:
            Tuple of (valid_statements, valid_indices)
        """
        if not self._compiled_constraints:
            # No constraints to enforce
            return statements, list(range(len(statements)))

        if self._verbose:
            print("\n" + "="*80)
            print("PHASE 3: FILTERING CONSTRAINT VIOLATIONS")
            print("="*80)

        valid_statements = []
        valid_indices = []

        for i, statement in enumerate(statements):
            passes, reasons = constraint_compiler.check_statement_against_all_constraints(
                statement, self._compiled_constraints
            )

            if passes:
                valid_statements.append(statement)
                valid_indices.append(i)
            else:
                # Log violation
                for reason in reasons:
                    # Find which constraint was violated
                    for constraint in self._compiled_constraints:
                        if f"Citizen {constraint.citizen_id}" in reason:
                            self._transparency_logger.log_statement_filtered(
                                statement, constraint, reason
                            )
                            break

                if self._verbose:
                    print(f"\n✗ Filtered statement {i+1}:")
                    print(f"  \"{statement[:80]}...\"")
                    for reason in reasons:
                        print(f"  Reason: {reason}")

        # Log filtering results
        num_filtered = len(statements) - len(valid_statements)
        self._transparency_logger.log_constraint_satisfaction_check(
            num_valid=len(valid_statements),
            num_invalid=num_filtered
        )

        if self._verbose:
            print(f"\n✓ {len(valid_statements)}/{len(statements)} statements pass constraints")

        return valid_statements, valid_indices

    def _get_rankings(
        self, statements: list[str]
    ) -> tuple[np.ndarray, list[None | str]]:
        """PHASE 4: Get citizen rankings over valid candidate statements.

        COPIED FROM: HabermasMachine._get_rankings
        No changes needed - ranking logic is the same.

        Args:
            statements: List of valid statements to rank

        Returns:
            Tuple of (rankings array, explanations)
        """
        if self._verbose:
            print("\n" + "="*80)
            print("PHASE 4: RANKING STATEMENTS")
            print("="*80)

        all_rankings = []
        explanations = []

        for i in range(self._num_citizens):
            # Shuffle the statements to avoid ordering bias
            num_statements = len(statements)
            indices = self._rng.permutation(num_statements)
            shuffled_statements = [statements[j] for j in indices]

            ranking, explanation = self._reward_model.predict_ranking(
                llm_client=self._reward_client,
                question=self._question,
                opinion=self._opinions[i],
                statements=shuffled_statements,
                previous_winner=(
                    self._previous_winners[-1] if self._round > 0 else None
                ),
                critique=self._critiques[-1][i] if self._round > 0 else None,
                seed=self._get_new_seed(),
                num_retries_on_error=self._num_retries_on_error,
            )

            if ranking is None:
                raise ValueError(
                    f"Ranking is None for citizen {i+1}. Explanation: {explanation}"
                )

            unshuffled_ranking = np.full_like(ranking, fill_value=types.RANKING_MOCK)
            unshuffled_ranking[indices] = ranking
            all_rankings.append(unshuffled_ranking)
            explanations.append(explanation)

        return np.array(all_rankings), explanations

    def mediate(
        self, opinions_or_critiques: Sequence[str]
    ) -> types.DeliberationResult:
        """Run constraint-aware mediation and return results.

        ADAPTED FROM: HabermasMachine.mediate
        CHANGES: Added constraint detection, filtering, and transparency logging
        WHY: Implement the full constraint-aware deliberation process

        Args:
            opinions_or_critiques: Citizen opinions (round 0) or critiques (later rounds)

        Returns:
            DeliberationResult with winning statement and transparency log
        """
        if len(opinions_or_critiques) != self._num_citizens:
            raise ValueError(
                f"Expected {self._num_citizens} opinions or critiques, got"
                f" {len(opinions_or_critiques)}."
            )

        # Store opinions or critiques
        if self._round == 0:
            self._opinions = list(opinions_or_critiques)
        else:
            self._critiques.append(list(opinions_or_critiques))

        if self._verbose:
            print("\n" + "="*80)
            if self._round == 0:
                print("OPINION ROUND - CONSTRAINT-AWARE DELIBERATION")
            else:
                print(f"CRITIQUE ROUND {self._round} - CONSTRAINT-AWARE DELIBERATION")
            print("="*80)
            print(f"\nQuestion: {self._question}")
            print("\nOpinions:")
            for i, opinion in enumerate(self._opinions):
                print(f"  Citizen {i + 1}: {opinion}")

        # PHASE 1: Detect and compile constraints (first round only)
        if self._round == 0:
            self._detect_and_compile_constraints(self._opinions)

        # PHASE 2: Generate constraint-satisfying statements
        all_statements, statement_explanations = self._generate_statements()

        # PHASE 3: Filter out constraint violations
        valid_statements, valid_indices = self._filter_statements_by_constraints(
            all_statements
        )

        # Check if we have any valid statements
        if not valid_statements:
            # INFEASIBLE: No statements satisfy all constraints
            reason = (
                f"No statements could be generated that satisfy all "
                f"{len(self._compiled_constraints)} constraints. "
                f"The constraints may be contradictory or too restrictive."
            )
            self._transparency_logger.log_infeasibility(reason)

            return types.InfeasibleResult(
                reason=reason,
                detected_sacred_values=self._detected_sacred_values,
                compiled_constraints=self._compiled_constraints,
                transparency_log=self._transparency_logger.get_log(),
            )

        # PHASE 4: Rank valid statements
        all_rankings, ranking_explanations = self._get_rankings(valid_statements)

        if self._verbose:
            print("\nRankings:")
            for i, ranking in enumerate(all_rankings):
                print(
                    f"  Citizen {i + 1}:"
                    f" {utils.numerical_ranking_to_ordinal_text(ranking)}"
                )

        # PHASE 5: Aggregate rankings to find winner
        if self._verbose:
            print("\n" + "="*80)
            print("PHASE 5: AGGREGATING VOTES")
            print("="*80)

        tied_social_ranking, untied_social_ranking = (
            self._social_choice_method.aggregate(
                all_rankings, seed=self._get_new_seed()
            )
        )

        if self._verbose:
            print("\nSocial ranking:")
            print(utils.numerical_ranking_to_ordinal_text(untied_social_ranking))

        # Get the sorted indices based on the social_ranking
        sorted_indices = np.argsort(untied_social_ranking)

        # Reorder the valid statements
        sorted_statements = [valid_statements[i] for i in sorted_indices]
        winner = sorted_statements[0]

        # PHASE 6: Verify winner satisfies all constraints
        if self._verbose:
            print("\n" + "="*80)
            print("PHASE 6: VERIFYING WINNER SATISFIES CONSTRAINTS")
            print("="*80)

        passes, reasons = constraint_compiler.check_statement_against_all_constraints(
            winner, self._compiled_constraints
        )

        self._transparency_logger.log_final_check(
            winner, self._compiled_constraints, passes, reasons
        )

        if self._verbose:
            if passes:
                print(f"\n✓ Winner satisfies all {len(self._compiled_constraints)} constraints")
            else:
                print(f"\n✗ WARNING: Winner violates constraints!")
                for reason in reasons:
                    print(f"  {reason}")

        if self._verbose:
            print(f"\nWinning statement: {winner}")
            print("\n" + "="*80)

        # Store round data
        self._ranking_explanations.append(ranking_explanations)
        self._statement_explanations.append(statement_explanations)
        self._previous_winners.append(winner)
        self._previous_candidates.append(sorted_statements)
        self._round += 1

        # Return comprehensive result
        return types.DeliberationResult(
            winning_statement=winner,
            all_statements=sorted_statements,
            detected_sacred_values=self._detected_sacred_values,
            compiled_constraints=self._compiled_constraints,
            transparency_log=self._transparency_logger.get_log(),
            is_feasible=True,
        )
