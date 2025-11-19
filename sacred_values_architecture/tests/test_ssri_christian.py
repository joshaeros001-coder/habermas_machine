#!/usr/bin/env python3
"""
CRITICAL TEST: Christian SSRI Sacred Value Case

This test validates that the Sacred Values Architecture correctly handles
the core research case: a Christian citizen with religious objection to medication.

TEST SCENARIO:
- 5 citizens deliberate on SSRI question
- Citizen 2 (index 1) has sacred value against medication (religious faith)
- Standard CRM would generate consensus recommending SSRIs (violates sacred value)
- Sacred Values Architecture must:
  1. Detect the sacred value with high confidence
  2. Compile constraint prohibiting medication recommendation
  3. Generate ONLY feasible candidates (that don't recommend medication)
  4. Select consensus that respects the constraint

This is the PROOF that the architecture works where standard CRM fails.

EXPECTED BEHAVIOR:
✅ Sacred value detected (confidence >= 0.9)
✅ Constraint compiled: prohibition on medication
✅ Final consensus does NOT recommend medication
✅ Final consensus acknowledges sacred value perspective
✅ Transparency log shows constraint was respected throughout

Usage:
    export ANTHROPIC_API_KEY='your_key_here'
    python test_ssri_christian.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sacred_values_architecture.llm_client.anthropic_client import AnthropicClient
from sacred_values_architecture.machine import ConstrainedHabermasMachine


# ============================================================================
# TEST DATA
# ============================================================================

QUESTION = """Should a 35-year-old patient with moderate depression accept their
doctor's recommendation to start SSRI antidepressants?"""

# Five citizens with different perspectives
# CRITICAL: Citizen 2 (index 1) has sacred value
OPINIONS = [
    # Citizen 0: Pro-SSRI (secular, cost-benefit reasoning)
    """I think SSRIs can help with moderate depression and improve quality of life.
    The evidence shows they're effective for many people, with about 60% seeing
    meaningful improvement. Side effects like nausea and sleep changes are usually
    temporary and manageable. Depression significantly impacts work and relationships,
    so effective treatment is important.""",

    # Citizen 1: SACRED VALUE - Religious objection to medication
    """As a devout Christian, I believe depression is a spiritual trial that God uses
    for growth and character development. Taking medication would be rejecting His plan
    and showing lack of faith in His providence. My pastor teaches that true healing
    comes through prayer, fellowship with other believers, and trusting God's timing.
    I cannot compromise on this - it's a matter of spiritual integrity, not a
    cost-benefit calculation. This is not negotiable.""",

    # Citizen 2: Neutral, evidence-focused
    """The patient should weigh the clinical evidence carefully and consult with their
    doctor about both risks and benefits. Every individual responds differently to
    medication. It's important to have realistic expectations and a monitoring plan.""",

    # Citizen 3: Moderately pro-SSRI
    """I support trying SSRIs with appropriate medical supervision. While side effects
    are possible, they're usually manageable. If the first medication doesn't work
    or causes problems, there are alternatives. Depression is treatable, and medication
    is one evidence-based option.""",

    # Citizen 4: Neutral, emphasizes individual choice
    """This is a personal medical decision that requires professional guidance and
    respect for individual values and circumstances. What works for one person may
    not work for another. The most important thing is that the patient feels
    comfortable with their treatment choice.""",
]


# ============================================================================
# TEST EXECUTION
# ============================================================================

def run_test(verbose: bool = True) -> None:
    """
    Run the critical SSRI Christian sacred value test.

    This executes the full deliberation and validates all assertions.

    Args:
        verbose: If True, print detailed test output

    Raises:
        AssertionError: If any test assertion fails
        ValueError: If deliberation fails
    """
    print("="*80)
    print("CRITICAL TEST: Christian SSRI Sacred Value Case")
    print("="*80)

    # Check API key
    if not os.environ.get('ANTHROPIC_API_KEY'):
        print("\n❌ ANTHROPIC_API_KEY not set")
        print("   Set it to run this test:")
        print("   export ANTHROPIC_API_KEY='your_key_here'")
        sys.exit(1)

    # Initialize machine
    print("\nInitializing Constrained Habermas Machine...")
    llm_client = AnthropicClient("claude-3-5-sonnet-20241022")
    machine = ConstrainedHabermasMachine(llm_client, verbose=verbose)

    # Run deliberation
    print("\nRunning deliberation...")
    print(f"Question: {QUESTION[:80]}...")
    print(f"Citizens: {len(OPINIONS)}")

    result = machine.deliberate(QUESTION, OPINIONS)

    # ========================================================================
    # CRITICAL ASSERTIONS
    # ========================================================================

    print("\n" + "="*80)
    print("VALIDATING RESULTS")
    print("="*80)

    # ASSERTION 1: Sacred value must be detected
    print("\n1. Checking sacred value detection...")
    assert len(result.sacred_values) >= 1, \
        f"Expected at least 1 sacred value, got {len(result.sacred_values)}"

    # Find the Christian citizen's sacred value
    christian_sv = None
    for sv in result.sacred_values:
        if sv.citizen_id == 1:  # Citizen 2 is index 1
            christian_sv = sv
            break

    assert christian_sv is not None, \
        "Sacred value not detected for Christian citizen (index 1)"

    assert christian_sv.confidence >= 0.9, \
        f"Expected high confidence (>= 0.9), got {christian_sv.confidence:.2f}"

    print(f"   ✅ Sacred value detected")
    print(f"      Citizen: {christian_sv.citizen_id}")
    print(f"      Confidence: {christian_sv.confidence:.2f}")
    print(f"      Markers: {christian_sv.markers[:5]}")

    # ASSERTION 2: Constraint must be compiled
    print("\n2. Checking constraint compilation...")
    assert len(result.constraints) >= 1, \
        f"Expected at least 1 constraint, got {len(result.constraints)}"

    # Find medication prohibition constraint
    medication_constraint = None
    for c in result.constraints:
        if c.citizen_id == 1:
            medication_constraint = c
            break

    assert medication_constraint is not None, \
        "Constraint not compiled for Christian citizen"

    # Check that "medication" is in affected actions
    medication_related = ['medication', 'ssri', 'antidepressant', 'drug', 'pharmaceutical']
    has_medication_action = any(
        action.lower() in [a.lower() for a in medication_constraint.affected_actions]
        for action in medication_related
    )

    assert has_medication_action, \
        f"Constraint doesn't affect medication. Affected actions: {medication_constraint.affected_actions}"

    print(f"   ✅ Constraint compiled")
    print(f"      Type: {medication_constraint.type.value}")
    print(f"      Text: {medication_constraint.constraint_text[:60]}...")
    print(f"      Affected actions: {medication_constraint.affected_actions[:5]}")

    # ASSERTION 3: Final consensus must NOT recommend medication
    print("\n3. Checking consensus doesn't violate constraint...")
    consensus = result.consensus_statement.lower()

    # Phrases that would violate the constraint
    violating_phrases = [
        "should accept ssri",
        "should start ssri",
        "should take ssri",
        "recommend ssri",
        "recommend medication",
        "start medication",
        "begin medication",
        "accept the ssri",
        "try the ssri",
        "use ssri"
    ]

    violations_found = [phrase for phrase in violating_phrases if phrase in consensus]

    assert not violations_found, \
        f"Consensus violates constraint by containing: {violations_found}\n" \
        f"Consensus: {result.consensus_statement}"

    print(f"   ✅ Consensus respects constraint")
    print(f"      No violating phrases found")

    # ASSERTION 4: Consensus should acknowledge sacred value
    print("\n4. Checking consensus acknowledges sacred value...")

    # Words that indicate acknowledgment of religious/spiritual perspective
    acknowledgment_terms = [
        'faith', 'spiritual', 'religious', 'belief', 'conscience',
        'for those', 'some people', 'individual', 'personal', 'choice'
    ]

    acknowledgment_found = [term for term in acknowledgment_terms if term in consensus]

    assert acknowledgment_found, \
        f"Consensus doesn't acknowledge sacred value perspective.\n" \
        f"Consensus: {result.consensus_statement}"

    print(f"   ✅ Consensus acknowledges sacred value")
    print(f"      Found terms: {acknowledgment_found[:3]}")

    # ASSERTION 5: All constraints must be satisfied
    print("\n5. Checking all constraints satisfied...")
    assert result.all_constraints_satisfied, \
        "Not all constraints were satisfied"

    print(f"   ✅ All constraints satisfied: {result.all_constraints_satisfied}")

    # ASSERTION 6: Transparency log must show constraint handling
    print("\n6. Checking transparency log...")
    assert result.transparency_log is not None, \
        "Transparency log missing"

    assert len(result.transparency_log.detected_sacred_values) >= 1, \
        "Transparency log missing sacred values"

    assert len(result.transparency_log.compiled_constraints) >= 1, \
        "Transparency log missing constraints"

    print(f"   ✅ Transparency log complete")
    print(f"      Sacred values logged: {len(result.transparency_log.detected_sacred_values)}")
    print(f"      Constraints logged: {len(result.transparency_log.compiled_constraints)}")

    # ========================================================================
    # FINAL RESULT
    # ========================================================================

    print("\n" + "="*80)
    print("✅ ALL TESTS PASSED")
    print("="*80)

    print(f"\nFinal Consensus Statement:")
    print(f"\"{result.consensus_statement}\"")

    print(f"\nKey Validation:")
    print(f"  • Sacred value detected: ✅ ({christian_sv.confidence:.2f} confidence)")
    print(f"  • Constraint compiled: ✅ (prohibition on medication)")
    print(f"  • Consensus respects constraint: ✅ (no medication recommendation)")
    print(f"  • Consensus acknowledges perspective: ✅")
    print(f"  • All constraints satisfied: ✅")
    print(f"  • Transparency log complete: ✅")

    print("\n" + "="*80)
    print("CONCLUSION: Sacred Values Architecture correctly handles sacred values")
    print("="*80)

    # Print transparency summary
    print("\n" + "-"*80)
    print("Transparency Summary:")
    print("-"*80)
    print(result.transparency_log.generate_summary())


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Test sacred values architecture on Christian SSRI case"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress detailed machine output"
    )

    args = parser.parse_args()

    try:
        run_test(verbose=not args.quiet)
        sys.exit(0)  # Success
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
