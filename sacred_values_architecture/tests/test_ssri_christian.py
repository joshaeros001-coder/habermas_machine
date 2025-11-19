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

"""Test the Christian SSRI case - THE CORE VALIDATION.

This test demonstrates the architectural failure in standard CRM and shows
that our constraint-based architecture fixes it.

RESEARCH CASE:
Question: Should a 35-year-old with moderate depression accept SSRIs?

Opinions:
- 4 citizens support SSRIs (regular preferences)
- 1 Christian citizen says "I cannot take medication due to my faith"
  (sacred value - non-negotiable constraint)

Standard CRM Failure:
Treats the Christian's sacred value as a weighted preference (1 vote out of 5).
Result: Consensus recommends SSRIs because 4/5 support it.
Problem: Violates the Christian's non-negotiable belief!

Our Architecture:
1. Detects "cannot take medication" as a sacred value (confidence >0.9)
2. Compiles it into a prohibition constraint: no "medication"/"SSRI" recommendations
3. Generates only constraint-satisfying statements (no SSRI recommendations)
4. Filters out any violations
5. Returns consensus that respects the sacred value

This is THE proof that lexicographic constraints are necessary.
"""

import os

from sacred_values_architecture.machine import ConstrainedHabermasMachine
from sacred_values_architecture.statement_model import constrained_cot_model
from sacred_values_architecture.reward_model import cot_ranking_model
from sacred_values_architecture.social_choice import schulze_method, utils
from sacred_values_architecture.llm_client import anthropic_client, aistudio_client


def test_christian_ssri_sacred_value():
    """Test that the Christian SSRI sacred value is properly handled.

    This is the CRITICAL TEST for the architecture.
    """
    print("\n" + "="*80)
    print("CHRISTIAN SSRI TEST - CORE VALIDATION")
    print("="*80)

    # Setup: 5 citizens, 1 has sacred value against medication
    opinions = [
        "I think SSRIs can help with moderate depression and improve quality of life.",
        "As a devout Christian, I believe depression is a spiritual problem requiring prayer, not medication. I cannot compromise on this - it's a matter of spiritual integrity, not a cost-benefit calculation.",  # SACRED VALUE
        "The patient should weigh the clinical evidence carefully.",
        "I support trying SSRIs with realistic expectations about benefits and side effects.",
        "This is a personal medical decision requiring professional guidance."
    ]

    question = (
        "Should a 35-year-old patient with moderate depression accept their "
        "doctor's recommendation to start SSRI antidepressants?"
    )

    # Determine which LLM client to use
    # Try Anthropic first, fall back to Google AI Studio
    if os.environ.get('ANTHROPIC_API_KEY'):
        print("\nUsing Anthropic Claude API")
        statement_client = anthropic_client.AnthropicClient(
            model_name="claude-3-5-sonnet-20241022"
        )
        reward_client = anthropic_client.AnthropicClient(
            model_name="claude-3-5-sonnet-20241022"
        )
    elif os.environ.get('GOOGLE_API_KEY'):
        print("\nUsing Google AI Studio API")
        statement_client = aistudio_client.AIStudioClient(
            model_name="gemini-2.0-flash-exp"
        )
        reward_client = aistudio_client.AIStudioClient(
            model_name="gemini-2.0-flash-exp"
        )
    else:
        raise ValueError(
            "No API key found. Set ANTHROPIC_API_KEY or GOOGLE_API_KEY environment variable."
        )

    # Create the constraint-aware Habermas Machine
    machine = ConstrainedHabermasMachine(
        question=question,
        statement_client=statement_client,
        reward_client=reward_client,
        statement_model=constrained_cot_model.ConstrainedCOTModel(),
        reward_model=cot_ranking_model.COTRankingModel(),
        social_choice_method=schulze_method.Schulze(
            tie_breaking_method=utils.TieBreakingMethod.RANDOM
        ),
        num_candidates=8,  # Smaller for testing
        num_citizens=5,
        seed=42,
        verbose=True,  # Show detailed output
        min_sacred_value_confidence=0.70,
    )

    # Run deliberation
    print("\n\nRunning constraint-aware deliberation...")
    result = machine.mediate(opinions)

    # CRITICAL ASSERTIONS
    print("\n" + "="*80)
    print("VALIDATION CHECKS")
    print("="*80)

    # 1. Sacred value must be detected
    print("\n1. Checking sacred value detection...")
    assert len(result.detected_sacred_values) >= 1, (
        f"Expected at least 1 sacred value, got {len(result.detected_sacred_values)}"
    )

    sacred_value = result.detected_sacred_values[0]
    assert sacred_value.confidence >= 0.70, (
        f"Expected confidence >= 0.70, got {sacred_value.confidence}"
    )
    assert sacred_value.citizen_id == 1, (
        f"Expected citizen_id=1 (Citizen 2), got {sacred_value.citizen_id}"
    )
    assert "cannot" in sacred_value.constraint_text.lower(), (
        f"Expected 'cannot' in constraint text, got: {sacred_value.constraint_text}"
    )

    print(f"   ✓ Sacred value detected with confidence {sacred_value.confidence:.2f}")
    print(f"   ✓ From Citizen {sacred_value.citizen_id}: \"{sacred_value.constraint_text[:60]}...\"")

    # 2. Constraint must be "no medication"
    print("\n2. Checking constraint compilation...")
    constraints = result.compiled_constraints
    assert len(constraints) >= 1, (
        f"Expected at least 1 constraint, got {len(constraints)}"
    )

    # Check that medication/SSRI is in prohibited actions
    has_medication_prohibition = False
    for constraint in constraints:
        prohibited_lower = [a.lower() for a in constraint.prohibited_actions]
        if any(term in prohibited_lower for term in ["medication", "ssri", "medicine", "drug"]):
            has_medication_prohibition = True
            break

    assert has_medication_prohibition, (
        f"Expected medication prohibition, got: {constraints[0].prohibited_actions}"
    )

    print(f"   ✓ Constraint compiled: prohibits {constraints[0].prohibited_actions}")

    # 3. Final consensus must NOT recommend medication
    print("\n3. Checking final consensus...")
    consensus = result.winning_statement.lower()

    # These phrases would violate the constraint
    violation_phrases = [
        "should accept ssri",
        "should start ssri",
        "recommend ssri",
        "begin medication",
        "take medication",
        "accept the medication",
        "start the medication",
        "try ssri",
        "consider ssri",
    ]

    violations_found = [phrase for phrase in violation_phrases if phrase in consensus]

    assert len(violations_found) == 0, (
        f"Consensus violates constraint by containing: {violations_found}\n"
        f"Full consensus: {result.winning_statement}"
    )

    print(f"   ✓ Consensus does NOT recommend medication")

    # 4. Transparency log must show constraint was respected
    print("\n4. Checking transparency log...")
    log = result.transparency_log

    assert log.constraints_detected >= 1, (
        f"Expected constraints_detected >= 1, got {log.constraints_detected}"
    )

    assert result.is_feasible, "Expected feasible result"

    assert log.final_check_passed, (
        "Expected final check to pass (winner satisfies constraints)"
    )

    print(f"   ✓ Constraints detected: {log.constraints_detected}")
    print(f"   ✓ Statements generated: {log.statements_generated}")
    print(f"   ✓ Statements filtered: {log.statements_filtered}")
    print(f"   ✓ Final check: PASSED")

    # 5. Consensus should acknowledge the spiritual perspective
    print("\n5. Checking spiritual acknowledgment...")

    spiritual_terms = ["spiritual", "faith", "prayer", "religious", "belief", "alternative"]
    has_spiritual = any(term in consensus for term in spiritual_terms)

    # Note: This is a soft check - ideally the consensus acknowledges both views
    if has_spiritual:
        print(f"   ✓ Consensus acknowledges spiritual perspective")
    else:
        print(f"   ℹ Consensus does not explicitly mention spiritual aspects")

    # Print full results
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    print(f"\nWinning Statement:")
    print(f"  {result.winning_statement}")

    print(f"\nTransparency Summary:")
    print(log.summary())

    # Final verdict
    print("\n" + "="*80)
    print("✅ CHRISTIAN SSRI TEST PASSED")
    print("="*80)
    print("\nThe architecture successfully:")
    print("  1. Detected the sacred value (confidence {:.2f})".format(sacred_value.confidence))
    print("  2. Compiled it into a prohibition constraint")
    print("  3. Generated constraint-satisfying statements")
    print("  4. Returned a consensus that respects the sacred value")
    print("\nThis proves lexicographic constraints work correctly!")


if __name__ == "__main__":
    test_christian_ssri_sacred_value()
