#!/usr/bin/env python3
"""
Simple Example: Sacred Value Detection and Constraint Compilation

This script demonstrates the core functionality of the sacred values architecture:
1. Detecting sacred values in citizen opinions
2. Compiling sacred values into formal constraints
3. Testing whether statements violate constraints

This is a minimal example showing just the detection and compilation steps,
without the full deliberation machinery. It helps verify that the core
components work correctly.

Usage:
    python simple_example.py

No API keys required for this example - it's purely algorithmic.
"""

import sys
import os

# Add parent directory to path so we can import the sacred_values_architecture package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sacred_values_architecture.core.sacred_value_detector import (
    detect_sacred_value,
    SacredValueDetector
)
from sacred_values_architecture.core.constraint_compiler import (
    compile_constraint,
    ConstraintCompiler
)
from sacred_values_architecture.models.constraint import ConstraintType


# ============================================================================
# EXAMPLE OPINIONS
# ============================================================================

# Opinion with sacred value (religious objection to medication)
SACRED_OPINION = """
As a devout Christian, I believe depression is a spiritual trial that God uses
for growth. Taking medication would be rejecting His plan and showing lack of
faith. My pastor teaches that true healing comes through prayer, fellowship,
and trusting God's timing. I cannot compromise on this - it's a matter of
spiritual integrity, not a cost-benefit calculation.
"""

# Opinion without sacred value (secular cost-benefit reasoning)
SECULAR_OPINION = """
I think the patient should try the SSRIs. Depression significantly impacts
quality of life and work productivity. While side effects like nausea and
sleep changes are possible, they're usually temporary and manageable. The
evidence shows SSRIs help about 60% of people with moderate depression.
If side effects are intolerable, the patient can discontinue. The potential
benefit outweighs the risk.
"""

# Test consensus statements (some violate constraint, some don't)
TEST_STATEMENTS = [
    # Statement 1: Violates constraint (prescribes medication)
    """
    The patient should try SSRIs as recommended by their doctor. While there
    are side effects, the benefits for moderate depression typically outweigh
    the risks. Close monitoring during the first few weeks is important.
    """,

    # Statement 2: Satisfies constraint (acknowledges sacred value)
    """
    Treatment decisions must respect deeply held religious and moral convictions.
    For those whose faith prohibits pharmaceutical intervention, non-medical
    approaches including therapy, spiritual support, and lifestyle changes are
    valid paths. For others, SSRIs may be appropriate after consultation with
    a doctor. Both perspectives reflect legitimate values that cannot be
    compromised.
    """,

    # Statement 3: Violates constraint (recommends medication without acknowledgment)
    """
    Given the evidence for SSRI effectiveness, the patient should start
    medication promptly. Delaying treatment risks prolonged suffering and
    reduced quality of life. Any concerns about side effects can be managed
    through dose adjustments.
    """,

    # Statement 4: Satisfies constraint (presents options without prescribing)
    """
    Multiple treatment approaches exist for depression, including therapy,
    medication, lifestyle changes, and spiritual practices. The choice should
    reflect the patient's individual circumstances, values, and beliefs.
    Professional guidance can help navigate these options.
    """,
]


def print_divider(char="=", length=80):
    """Print a divider line."""
    print(char * length)


def print_section(title):
    """Print a section header."""
    print("\n")
    print_divider()
    print(title)
    print_divider()


def main():
    """Run the simple example demonstrating detection and compilation."""

    print_section("SACRED VALUES ARCHITECTURE: Simple Example")

    print("\nThis example demonstrates:")
    print("  1. Sacred value detection (identifying non-negotiable commitments)")
    print("  2. Constraint compilation (converting values to formal constraints)")
    print("  3. Constraint violation checking (testing statements)")

    # ========================================================================
    # STEP 1: DETECT SACRED VALUES
    # ========================================================================

    print_section("STEP 1: SACRED VALUE DETECTION")

    print("\n" + "-"*80)
    print("Opinion 1 (Religious objection):")
    print("-"*80)
    print(SACRED_OPINION.strip())

    sacred_value = detect_sacred_value(SACRED_OPINION, citizen_id=1)

    if sacred_value:
        print("\n✅ SACRED VALUE DETECTED")
        print(f"  Confidence: {sacred_value.confidence:.2f}")
        print(f"  Markers found: {sacred_value.markers}")
        print(f"  Justification: {sacred_value.justification}")
        print(f"  Constraint text: {sacred_value.text}")
        print(f"  High confidence (>= 0.9): {sacred_value.is_high_confidence()}")
        print(f"  Religious basis: {sacred_value.is_religious()}")
    else:
        print("\n❌ No sacred value detected")

    print("\n" + "-"*80)
    print("Opinion 2 (Secular cost-benefit):")
    print("-"*80)
    print(SECULAR_OPINION.strip())

    secular_check = detect_sacred_value(SECULAR_OPINION, citizen_id=2)

    if secular_check:
        print("\n✅ Sacred value detected (unexpected!)")
        print(f"  Confidence: {secular_check.confidence:.2f}")
    else:
        print("\n✅ No sacred value detected (expected)")

    # ========================================================================
    # STEP 2: COMPILE CONSTRAINT
    # ========================================================================

    print_section("STEP 2: CONSTRAINT COMPILATION")

    if not sacred_value:
        print("\n❌ Cannot compile constraint - no sacred value detected")
        return

    print("\nCompiling sacred value into formal constraint...")

    try:
        constraint = compile_constraint(sacred_value)

        print("\n✅ CONSTRAINT COMPILED")
        print(f"  Type: {constraint.type.value.upper()}")
        print(f"  Constraint text: {constraint.constraint_text}")
        print(f"  Affected actions ({len(constraint.affected_actions)}): ")
        for i, action in enumerate(constraint.affected_actions[:10], 1):
            print(f"    {i}. {action}")
        if len(constraint.affected_actions) > 10:
            print(f"    ... and {len(constraint.affected_actions) - 10} more")
        print(f"  Justification: {constraint.justification}")
        print(f"  Citizen ID: {constraint.citizen_id}")

    except ValueError as e:
        print(f"\n❌ Failed to compile constraint: {e}")
        return

    # ========================================================================
    # STEP 3: TEST CONSTRAINT VIOLATIONS
    # ========================================================================

    print_section("STEP 3: CONSTRAINT VIOLATION TESTING")

    print("\nTesting whether consensus statements violate the constraint...")
    print("(Constraint: PROHIBITION against medication)")

    violations = []
    satisfies = []

    for i, statement in enumerate(TEST_STATEMENTS, 1):
        print(f"\n{'-'*80}")
        print(f"Test Statement {i}:")
        print(f"{'-'*80}")
        print(statement.strip()[:200] + "..." if len(statement.strip()) > 200 else statement.strip())

        violated = constraint.is_violated_by(statement)

        if violated:
            print("\n❌ VIOLATES CONSTRAINT")
            print("  This statement prescribes a prohibited action (medication).")
            print("  It should be FILTERED OUT before voting.")
            violations.append(i)
        else:
            print("\n✅ SATISFIES CONSTRAINT")
            print("  This statement does not prescribe prohibited actions.")
            print("  It can be included in the feasible set for voting.")
            satisfies.append(i)

    # ========================================================================
    # SUMMARY
    # ========================================================================

    print_section("SUMMARY")

    print(f"\nDetection Results:")
    print(f"  - Sacred values detected: 1 out of 2 opinions")
    print(f"  - Detection confidence: {sacred_value.confidence:.2f}")
    print(f"  - Constraint type: {constraint.type.value}")

    print(f"\nConstraint Compilation:")
    print(f"  - Successfully compiled: YES")
    print(f"  - Affected actions: {len(constraint.affected_actions)}")
    print(f"  - Justification: {constraint.justification}")

    print(f"\nViolation Testing:")
    print(f"  - Total statements tested: {len(TEST_STATEMENTS)}")
    print(f"  - Statements violating constraint: {len(violations)} (statements {violations})")
    print(f"  - Statements satisfying constraint: {len(satisfies)} (statements {satisfies})")

    print(f"\nKey Insight:")
    print(f"  In standard deliberation, all {len(TEST_STATEMENTS)} statements would be voted on.")
    print(f"  With sacred values architecture, only {len(satisfies)} feasible statements")
    print(f"  would reach the voting stage. The {len(violations)} violating statements")
    print(f"  would be filtered out, respecting the non-negotiable constraint.")

    print("\n" + "="*80)
    print("✅ EXAMPLE COMPLETE")
    print("="*80)

    print("\nNext Steps:")
    print("  1. Implement statement_generator.py (constraint-aware generation)")
    print("  2. Implement constraint_filter.py (automatic filtering)")
    print("  3. Implement constrained_voting.py (vote on feasible set only)")
    print("  4. Implement transparency_logger.py (audit trail)")
    print("  5. Run full deliberation with sacred values")


# ============================================================================
# BATCH EXAMPLE
# ============================================================================

def batch_example():
    """
    Demonstrate batch processing of multiple opinions.

    This shows how to detect sacred values across multiple citizens
    and compile all constraints at once.
    """
    print_section("BATCH PROCESSING EXAMPLE")

    opinions = [
        SECULAR_OPINION,  # Citizen 0: secular
        SACRED_OPINION,   # Citizen 1: sacred value
        "Therapy is often more effective than medication for depression.",  # Citizen 2: secular
        "I must not take medication. It violates my conscience.",  # Citizen 3: sacred value
        "Cost is the main concern - SSRIs can be expensive.",  # Citizen 4: secular
    ]

    print(f"\nProcessing {len(opinions)} opinions...\n")

    # Detect all sacred values
    detector = SacredValueDetector(confidence_threshold=0.7, verbose=False)
    sacred_values = detector.detect_batch(opinions)

    print(f"✅ Detection complete:")
    print(f"  - Sacred values found: {len(sacred_values)} out of {len(opinions)} citizens")

    for sv in sacred_values:
        print(f"\n  Citizen {sv.citizen_id}:")
        print(f"    - Confidence: {sv.confidence:.2f}")
        print(f"    - Markers: {sv.markers}")
        print(f"    - Text: {sv.text[:80]}...")

    # Compile all into constraints
    compiler = ConstraintCompiler(verbose=False)
    constraints = compiler.compile_batch(sacred_values)

    print(f"\n✅ Compilation complete:")
    print(f"  - Constraints compiled: {len(constraints)}")

    for c in constraints:
        print(f"\n  Citizen {c.citizen_id}:")
        print(f"    - Type: {c.type.value}")
        print(f"    - Affected actions: {len(c.affected_actions)} actions")
        print(f"    - Text: {c.constraint_text[:60]}...")

    print("\n" + "="*80)


if __name__ == "__main__":
    # Run simple example
    main()

    # Optionally run batch example
    print("\n\n")
    batch_example()
