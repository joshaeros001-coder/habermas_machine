"""
Constrained Statement Generator

ADAPTED FROM: habermas_machine/statement_model/ (scattered across cot_model.py and others)
KEY CHANGE: Adds constraint injection and post-generation filtering
WHY: Standard CRM generates arbitrary statements; we generate ONLY feasible statements

This is the CORE INNOVATION for statement generation:
1. Detect sacred values in opinions
2. Compile constraints from sacred values
3. Inject constraints into generation prompt
4. Generate candidates that should satisfy constraints
5. Post-filter to ensure no violations (safety net)

The constraint injection (step 3) is the main innovation - we tell the LLM about
hard constraints BEFORE generation, not after.
"""

from typing import List, Tuple, Optional
from ..llm_client.base_client import LLMClient
from ..models.sacred_value import SacredValue
from ..models.constraint import Constraint
from ..core.sacred_value_detector import SacredValueDetector
from ..core.constraint_compiler import ConstraintCompiler
from ..core.constraint_filter import filter_violating_statements
from .prompts import (
    build_constrained_generation_prompt,
    parse_generated_candidates
)


class ConstrainedStatementGenerator:
    """
    Generate consensus statements that satisfy sacred value constraints.

    This is the main statement generation component. It orchestrates:
    1. Sacred value detection
    2. Constraint compilation
    3. Constraint-aware prompt building
    4. LLM-based generation
    5. Post-generation filtering (safety net)

    The key innovation is step 3: injecting constraints into the prompt so
    the LLM generates feasible statements from the start.

    Attributes:
        llm_client: LLM client for generation (e.g., Anthropic Claude)
        detector: Sacred value detector
        compiler: Constraint compiler
        num_candidates: How many candidates to generate
        temperature: LLM temperature for generation
        verbose: Whether to print generation details

    Example:
        >>> generator = ConstrainedStatementGenerator(
        ...     llm_client=AnthropicClient("claude-3-5-sonnet-20241022"),
        ...     num_candidates=4
        ... )
        >>> candidates, constraints = generator.generate(question, opinions)
        >>> # All candidates should satisfy constraints
    """

    def __init__(
        self,
        llm_client: LLMClient,
        num_candidates: int = 4,
        temperature: float = 0.8,
        confidence_threshold: float = 0.7,
        verbose: bool = False
    ):
        """
        Initialize the constrained generator.

        Args:
            llm_client: LLM client for text generation
            num_candidates: Number of candidate statements to generate
            temperature: LLM sampling temperature (higher = more diverse)
            confidence_threshold: Minimum confidence for sacred value detection
            verbose: If True, print detailed generation information
        """
        self.llm_client = llm_client
        self.num_candidates = num_candidates
        self.temperature = temperature
        self.verbose = verbose

        # Initialize detection and compilation components
        self.detector = SacredValueDetector(
            confidence_threshold=confidence_threshold,
            verbose=verbose
        )
        self.compiler = ConstraintCompiler(verbose=verbose)

    def generate(
        self,
        question: str,
        opinions: List[str]
    ) -> Tuple[List[str], List[SacredValue], List[Constraint]]:
        """
        Generate constraint-satisfying consensus statement candidates.

        This is the main entry point. It performs the full pipeline:
        1. Detect sacred values in opinions
        2. Compile constraints from sacred values
        3. Build constraint-aware prompt
        4. Generate candidates using LLM
        5. Filter out any constraint violations (safety net)

        Args:
            question: The deliberation question
            opinions: List of citizen opinions (strings)

        Returns:
            Tuple of:
            - candidates: List of feasible consensus statements
            - sacred_values: List of detected sacred values
            - constraints: List of compiled constraints

        Raises:
            ValueError: If generation fails or produces no valid candidates

        Example:
            >>> question = "Should patient take SSRIs?"
            >>> opinions = [op1, op2, op3]  # op2 has sacred value
            >>> candidates, svs, cs = generator.generate(question, opinions)
            >>> len(candidates)
            3  # Some may have been filtered
            >>> len(cs)
            1  # One constraint detected
        """
        if self.verbose:
            print("\n" + "="*80)
            print("CONSTRAINED STATEMENT GENERATION")
            print("="*80)

        # STEP 1: Detect sacred values
        # This identifies which citizens have non-negotiable commitments
        if self.verbose:
            print("\nStep 1: Detecting sacred values...")

        sacred_values = self.detector.detect_batch(opinions)

        if self.verbose:
            print(f"✓ Detected {len(sacred_values)} sacred value(s)")
            for sv in sacred_values:
                print(f"  - Citizen {sv.citizen_id}: {sv.confidence:.2f} confidence")

        # STEP 2: Compile constraints
        # Convert sacred values into formal constraints
        if self.verbose:
            print("\nStep 2: Compiling constraints...")

        constraints = self.compiler.compile_batch(sacred_values)

        if self.verbose:
            print(f"✓ Compiled {len(constraints)} constraint(s)")
            for c in constraints:
                print(f"  - {c.type.value.upper()}: {c.constraint_text[:60]}...")

        # STEP 3: Build constraint-aware prompt
        # This is the CORE INNOVATION: inject constraints into prompt
        if self.verbose:
            print("\nStep 3: Building constraint-aware prompt...")

        prompt = build_constrained_generation_prompt(
            question=question,
            opinions=opinions,
            constraints=constraints,
            num_candidates=self.num_candidates
        )

        if self.verbose:
            print(f"✓ Prompt built ({len(prompt)} chars)")
            if constraints:
                print(f"  Constraints injected: {len(constraints)}")
            else:
                print("  No constraints (standard generation)")

        # STEP 4: Generate candidates using LLM
        # The LLM should generate feasible statements because we told it about constraints
        if self.verbose:
            print("\nStep 4: Generating candidates with LLM...")
            print(f"  Model: {type(self.llm_client).__name__}")
            print(f"  Temperature: {self.temperature}")

        try:
            response = self.llm_client.sample_text(
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=4096
            )

            if self.verbose:
                print(f"✓ LLM response received ({len(response)} chars)")

        except Exception as e:
            raise ValueError(f"LLM generation failed: {e}")

        # STEP 5: Parse candidates from response
        candidates = parse_generated_candidates(response)

        if self.verbose:
            print(f"✓ Parsed {len(candidates)} candidates")

        if not candidates:
            raise ValueError("No candidates could be parsed from LLM response")

        # STEP 6: Filter constraint violations (safety net)
        # Even though we told the LLM about constraints, we verify compliance
        # This is a SAFETY NET - ideally no filtering needed if LLM followed instructions
        if constraints:
            if self.verbose:
                print("\nStep 6: Filtering constraint violations (safety net)...")

            feasible, filtered_out = filter_violating_statements(
                candidates, constraints, verbose=self.verbose
            )

            if self.verbose:
                print(f"✓ Filtering complete:")
                print(f"  Feasible: {len(feasible)}")
                print(f"  Filtered out: {len(filtered_out)}")

                if filtered_out:
                    print("\n  ⚠️ WARNING: Some candidates violated constraints!")
                    print("  This means the LLM didn't fully respect the prompt instructions.")
                    for stmt, violated_c in filtered_out:
                        print(f"    - Violated by Citizen {violated_c.citizen_id} constraint")

            if not feasible:
                raise ValueError(
                    f"All {len(candidates)} generated candidates violated constraints. "
                    "No feasible statements could be generated. "
                    "The constraints may be too restrictive or conflicting."
                )

            candidates = feasible

        if self.verbose:
            print("\n" + "="*80)
            print(f"GENERATION COMPLETE: {len(candidates)} feasible candidates")
            print("="*80)

        return candidates, sacred_values, constraints

    def generate_with_known_constraints(
        self,
        question: str,
        opinions: List[str],
        constraints: List[Constraint]
    ) -> List[str]:
        """
        Generate candidates given pre-compiled constraints.

        This is useful when you've already detected and compiled constraints
        and just want to generate statements.

        Args:
            question: The deliberation question
            opinions: Citizen opinions
            constraints: Pre-compiled constraints to enforce

        Returns:
            List of feasible consensus statements

        Example:
            >>> # If you already have constraints from previous detection
            >>> candidates = generator.generate_with_known_constraints(
            ...     question, opinions, existing_constraints
            ... )
        """
        if self.verbose:
            print(f"\nGenerating with {len(constraints)} known constraint(s)...")

        # Build prompt with given constraints
        prompt = build_constrained_generation_prompt(
            question=question,
            opinions=opinions,
            constraints=constraints,
            num_candidates=self.num_candidates
        )

        # Generate
        response = self.llm_client.sample_text(
            prompt=prompt,
            temperature=self.temperature,
            max_tokens=4096
        )

        # Parse
        candidates = parse_generated_candidates(response)

        if not candidates:
            raise ValueError("No candidates could be parsed from LLM response")

        # Filter violations (safety net)
        if constraints:
            feasible, _ = filter_violating_statements(candidates, constraints)

            if not feasible:
                raise ValueError("All generated candidates violated constraints")

            candidates = feasible

        return candidates


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

    from ..llm_client.anthropic_client import AnthropicClient

    print("="*80)
    print("CONSTRAINED STATEMENT GENERATION EXAMPLE")
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
    ]

    print("\nInitializing generator with Claude...")
    llm_client = AnthropicClient("claude-3-5-sonnet-20241022")
    generator = ConstrainedStatementGenerator(
        llm_client=llm_client,
        num_candidates=4,
        verbose=True
    )

    print("\nGenerating constraint-satisfying consensus statements...")
    try:
        candidates, sacred_values, constraints = generator.generate(question, opinions)

        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)

        print(f"\nSacred Values Detected: {len(sacred_values)}")
        for sv in sacred_values:
            print(f"  - Citizen {sv.citizen_id}: '{sv.text}'")

        print(f"\nConstraints Compiled: {len(constraints)}")
        for c in constraints:
            print(f"  - {c.type.value.upper()}: {c.constraint_text}")

        print(f"\nFeasible Candidates Generated: {len(candidates)}")
        for i, candidate in enumerate(candidates, 1):
            print(f"\n  {i}. {candidate}")

        print("\n" + "="*80)
        print("✅ All candidates satisfy sacred value constraints")
        print("="*80)

    except ValueError as e:
        print(f"\n❌ Generation failed: {e}")
        sys.exit(1)
