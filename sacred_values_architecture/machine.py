"""
Constrained Habermas Machine - Main Deliberation Orchestrator

ADAPTED FROM: habermas_machine/caucus.py and other orchestration files
KEY CHANGE: Adds sacred value detection and constraint-first generation
WHY: Standard CRM generates arbitrary statements; we generate constraint-satisfying ones

This is the MAIN ORCHESTRATOR that implements the full constrained deliberation pipeline:

1. DETECT: Identify sacred values in opinions
2. COMPILE: Convert sacred values to formal constraints
3. GENERATE: Create ONLY feasible (constraint-satisfying) candidate statements
4. VOTE: Citizens vote on feasible statements
5. LOG: Track all constraint-related decisions for transparency

ARCHITECTURAL INNOVATION:
Standard CRM: opinions → generate statements → vote → consensus
Sacred Values: opinions → detect constraints → generate feasible statements → vote → consensus

The key difference is detecting constraints BEFORE generation, not after.
This is a CONSTRAINT-FIRST approach.
"""

from typing import List, Optional
from dataclasses import dataclass

from .llm_client.base_client import LLMClient
from .models.sacred_value import SacredValue
from .models.constraint import Constraint
from .models.deliberation_result import DeliberationResult, TransparencyLog
from .core.sacred_value_detector import SacredValueDetector
from .core.constraint_compiler import ConstraintCompiler
from .core.constraint_filter import check_infeasibility
from .core.transparency_logger import TransparencyLogger
from .statement_model.constrained_generator import ConstrainedStatementGenerator
from .voting.simple_voting import SimpleVoting, VotingResult


@dataclass
class MachineConfig:
    """
    Configuration for the Constrained Habermas Machine.

    Attributes:
        num_candidates: Number of candidate statements to generate
        temperature: LLM temperature for generation
        sacred_value_threshold: Minimum confidence to treat as sacred value
        verbose: Whether to print detailed process information
    """
    num_candidates: int = 4
    temperature: float = 0.8
    sacred_value_threshold: float = 0.7
    verbose: bool = True


class ConstrainedHabermasMachine:
    """
    Main deliberation machine that respects sacred values as hard constraints.

    This orchestrates the full constraint-based deliberation process:
    1. Detect sacred values in citizen opinions
    2. Compile sacred values into formal constraints
    3. Check for constraint infeasibility (conflicting constraints)
    4. Generate candidate statements that satisfy ALL constraints
    5. Vote on feasible candidates to select consensus
    6. Create complete transparency log

    This is the CORE CONTRIBUTION: a deliberation system that treats sacred
    values as lexicographic constraints, not weighted preferences.

    Attributes:
        llm_client: LLM client for statement generation
        config: Machine configuration
        detector: Sacred value detector
        compiler: Constraint compiler
        generator: Constrained statement generator
        voting: Voting system
        logger: Transparency logger

    Example:
        >>> from llm_client import AnthropicClient
        >>> client = AnthropicClient("claude-3-5-sonnet-20241022")
        >>> machine = ConstrainedHabermasMachine(client, verbose=True)
        >>> result = machine.deliberate(question, opinions)
        >>> print(result.consensus_statement)
        >>> print(result.transparency_log.generate_summary())
    """

    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[MachineConfig] = None,
        verbose: bool = True
    ):
        """
        Initialize the constrained deliberation machine.

        Args:
            llm_client: LLM client for statement generation
            config: Machine configuration (uses defaults if None)
            verbose: Whether to print detailed information
        """
        self.llm_client = llm_client
        self.config = config or MachineConfig(verbose=verbose)

        # Initialize all components
        self.detector = SacredValueDetector(
            confidence_threshold=self.config.sacred_value_threshold,
            verbose=self.config.verbose
        )

        self.compiler = ConstraintCompiler(
            verbose=self.config.verbose
        )

        self.generator = ConstrainedStatementGenerator(
            llm_client=llm_client,
            num_candidates=self.config.num_candidates,
            temperature=self.config.temperature,
            confidence_threshold=self.config.sacred_value_threshold,
            verbose=self.config.verbose
        )

        self.voting = SimpleVoting(verbose=self.config.verbose)

        self.logger = TransparencyLogger()

    def deliberate(
        self,
        question: str,
        opinions: List[str]
    ) -> DeliberationResult:
        """
        Run the full constrained deliberation process.

        This is the main entry point. It orchestrates all steps:
        1. Detect sacred values
        2. Compile constraints
        3. Check feasibility
        4. Generate feasible candidates
        5. Vote on candidates
        6. Create transparency log
        7. Return complete result

        Args:
            question: The deliberation question
            opinions: List of citizen opinions (one per citizen)

        Returns:
            DeliberationResult containing:
            - Consensus statement (if found)
            - All detected sacred values
            - All compiled constraints
            - Transparency log with complete audit trail
            - Feasibility status

        Raises:
            ValueError: If deliberation fails (e.g., no feasible statements)

        Example:
            >>> question = "Should patient take SSRIs?"
            >>> opinions = [op1, op2, op3, op4, op5]  # op2 has sacred value
            >>> result = machine.deliberate(question, opinions)
            >>> result.consensus_statement
            "For those whose faith prohibits medication, therapy is valid..."
            >>> result.all_constraints_satisfied
            True
            >>> len(result.sacred_values)
            1
        """
        if self.config.verbose:
            print("\n" + "="*80)
            print("CONSTRAINED HABERMAS MACHINE - DELIBERATION START")
            print("="*80)
            print(f"\nQuestion: {question}")
            print(f"Citizens: {len(opinions)}")

        # ====================================================================
        # PHASE 1: SACRED VALUE DETECTION
        # ====================================================================
        # Identify which citizens have non-negotiable commitments

        if self.config.verbose:
            print("\n" + "-"*80)
            print("PHASE 1: SACRED VALUE DETECTION")
            print("-"*80)

        sacred_values = self.detector.detect_batch(opinions)

        # Log detection
        self.logger.log_detection(sacred_values)

        if self.config.verbose:
            print(f"\n✓ Detected {len(sacred_values)} sacred value(s)")
            if not sacred_values:
                print("  All perspectives are negotiable preferences")
                print("  Standard consensus generation will be used")

        # ====================================================================
        # PHASE 2: CONSTRAINT COMPILATION
        # ====================================================================
        # Convert sacred values into formal constraints

        if self.config.verbose:
            print("\n" + "-"*80)
            print("PHASE 2: CONSTRAINT COMPILATION")
            print("-"*80)

        constraints = self.compiler.compile_batch(sacred_values)

        # Log compilation
        self.logger.log_compilation(constraints)

        if self.config.verbose:
            print(f"\n✓ Compiled {len(constraints)} constraint(s)")

        # ====================================================================
        # PHASE 3: FEASIBILITY CHECK
        # ====================================================================
        # Check if constraints are mutually compatible

        if self.config.verbose and constraints:
            print("\n" + "-"*80)
            print("PHASE 3: FEASIBILITY CHECK")
            print("-"*80)

        is_infeasible, infeasibility_reason = check_infeasibility(constraints)

        if is_infeasible:
            # Constraints conflict - no consensus possible
            if self.config.verbose:
                print("\n❌ INFEASIBILITY DETECTED")
                print(f"   Reason: {infeasibility_reason}")

            self.logger.log_infeasibility(infeasibility_reason)
            transparency_log = self.logger.create_log()

            # Return infeasible result
            return DeliberationResult(
                question=question,
                opinions=opinions,
                consensus_statement=None,
                ranked_candidates=[],
                sacred_values=sacred_values,
                constraints=constraints,
                all_constraints_satisfied=False,
                is_infeasible=True,
                infeasibility_reason=infeasibility_reason,
                conflicting_constraints=[],  # TODO: Extract from infeasibility check
                transparency_log=transparency_log
            )

        if self.config.verbose and constraints:
            print("\n✓ All constraints are compatible")
            print("  Consensus is feasible")

        # ====================================================================
        # PHASE 4: CONSTRAINED STATEMENT GENERATION
        # ====================================================================
        # Generate ONLY statements that satisfy ALL constraints

        if self.config.verbose:
            print("\n" + "-"*80)
            print("PHASE 4: CONSTRAINED STATEMENT GENERATION")
            print("-"*80)

        try:
            # This is the KEY INNOVATION:
            # We generate candidates with constraints injected into the prompt
            # So the LLM generates ONLY feasible statements from the start
            candidates, _, _ = self.generator.generate(question, opinions)

            # Log generation
            self.logger.log_generation(candidates)

            # The generator already filters violations, so all candidates
            # in this list should be feasible
            # Log filtering (empty filtered_out list since generator already filtered)
            self.logger.log_filtering([], candidates)

            if self.config.verbose:
                print(f"\n✓ Generated {len(candidates)} feasible candidate(s)")

        except ValueError as e:
            # Generation failed (e.g., all candidates violated constraints)
            if self.config.verbose:
                print(f"\n❌ Generation failed: {e}")

            self.logger.log_infeasibility(f"Statement generation failed: {e}")
            transparency_log = self.logger.create_log()

            return DeliberationResult(
                question=question,
                opinions=opinions,
                consensus_statement=None,
                ranked_candidates=[],
                sacred_values=sacred_values,
                constraints=constraints,
                all_constraints_satisfied=False,
                is_infeasible=True,
                infeasibility_reason=f"Could not generate feasible statements: {e}",
                conflicting_constraints=[],
                transparency_log=transparency_log
            )

        # ====================================================================
        # PHASE 5: VOTING
        # ====================================================================
        # Vote on feasible candidates to select consensus

        if self.config.verbose:
            print("\n" + "-"*80)
            print("PHASE 5: VOTING ON FEASIBLE SET")
            print("-"*80)

        voting_result = self.voting.vote(candidates, opinions)

        # Log consensus
        self.logger.log_consensus(voting_result.winner)

        if self.config.verbose:
            print(f"\n✓ Consensus selected: Candidate {voting_result.winner_index + 1}")

        # ====================================================================
        # PHASE 6: TRANSPARENCY LOG
        # ====================================================================
        # Create complete audit trail

        transparency_log = self.logger.create_log()

        # ====================================================================
        # FINAL RESULT
        # ====================================================================

        if self.config.verbose:
            print("\n" + "="*80)
            print("DELIBERATION COMPLETE")
            print("="*80)
            print(f"\nConsensus Statement:")
            print(f'"{voting_result.winner}"')
            print(f"\nSacred Values: {len(sacred_values)}")
            print(f"Constraints: {len(constraints)}")
            print(f"All Constraints Satisfied: {True}")

        # Build and return result
        result = DeliberationResult(
            question=question,
            opinions=opinions,
            consensus_statement=voting_result.winner,
            ranked_candidates=candidates,  # All candidates are ranked by voting
            sacred_values=sacred_values,
            constraints=constraints,
            all_constraints_satisfied=True,  # By construction (we only voted on feasible)
            is_infeasible=False,
            infeasibility_reason=None,
            conflicting_constraints=[],
            transparency_log=transparency_log
        )

        return result


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    import os
    import sys

    # Check for API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("⚠️ ANTHROPIC_API_KEY not set. Set it to run this example:")
        print("   export ANTHROPIC_API_KEY='your_key_here'")
        sys.exit(1)

    from llm_client.anthropic_client import AnthropicClient

    print("="*80)
    print("CONSTRAINED HABERMAS MACHINE - EXAMPLE")
    print("="*80)

    # Example: SSRI deliberation with religious objection
    question = """Should a 35-year-old patient with moderate depression accept their
doctor's recommendation to start SSRI antidepressants?"""

    opinions = [
        """I think SSRIs can help with moderate depression and improve quality of life.
        The evidence shows they're effective for many people.""",

        """As a devout Christian, I believe depression is a spiritual trial that God
        uses for growth. Taking medication would be rejecting His plan and showing
        lack of faith. I cannot compromise on this - it's a matter of spiritual
        integrity, not a cost-benefit calculation.""",

        """The patient should weigh the clinical evidence carefully and consult with
        their doctor about risks and benefits.""",

        """I support trying SSRIs with realistic expectations. Side effects are possible
        but usually manageable.""",

        """This is a personal medical decision that requires professional guidance
        and respect for individual values.""",
    ]

    print("\nInitializing machine with Claude...")
    llm_client = AnthropicClient("claude-3-5-sonnet-20241022")
    machine = ConstrainedHabermasMachine(llm_client, verbose=True)

    print("\nRunning deliberation...")
    try:
        result = machine.deliberate(question, opinions)

        print("\n" + "="*80)
        print("FINAL RESULT")
        print("="*80)

        print(f"\n✅ Consensus Statement:")
        print(f'"{result.consensus_statement}"')

        print(f"\n✅ Sacred Values Respected: {len(result.sacred_values)}")
        for sv in result.sacred_values:
            print(f"   - Citizen {sv.citizen_id}: {sv.confidence:.2f} confidence")

        print(f"\n✅ Constraints Satisfied: {result.all_constraints_satisfied}")

        print("\n" + "-"*80)
        print("Transparency Log:")
        print("-"*80)
        print(result.transparency_log.generate_summary())

    except Exception as e:
        print(f"\n❌ Deliberation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
