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

"""Simple example of Sacred Values Architecture.

This is a minimal working example with 3 citizens and 1 sacred value.
Run this to verify the system is working correctly.

Usage:
    export ANTHROPIC_API_KEY='your_key_here'  # Or GOOGLE_API_KEY
    cd sacred_values_architecture/
    python -m examples.simple_example
"""

import os
import sys

from sacred_values_architecture.machine import ConstrainedHabermasMachine
from sacred_values_architecture.statement_model import constrained_cot_model
from sacred_values_architecture.reward_model import cot_ranking_model
from sacred_values_architecture.social_choice import schulze_method, utils
from sacred_values_architecture.llm_client import anthropic_client, aistudio_client


def main():
    """Run a simple deliberation with one sacred value."""
    print("\n" + "="*80)
    print("SIMPLE EXAMPLE: Sacred Values Architecture")
    print("="*80)

    # Simple question with clear sacred value
    question = "Should our community center serve alcohol at events?"

    opinions = [
        "I think serving wine at events would make them more enjoyable for adults.",
        "As a Muslim, I cannot support serving alcohol - it violates my religious beliefs and I refuse to compromise on this matter of faith.",  # SACRED VALUE
        "Alcohol could help with fundraising but we should be mindful of different preferences.",
    ]

    print(f"\nQuestion: {question}")
    print("\nOpinions:")
    for i, op in enumerate(opinions, 1):
        print(f"  Citizen {i}: {op}")

    # Setup LLM client
    if os.environ.get('ANTHROPIC_API_KEY'):
        print("\nUsing: Anthropic Claude")
        client = anthropic_client.AnthropicClient()
    elif os.environ.get('GOOGLE_API_KEY'):
        print("\nUsing: Google AI Studio")
        client = aistudio_client.AIStudioClient(model_name="gemini-2.0-flash-exp")
    else:
        print("\n❌ ERROR: No API key found!")
        print("Set ANTHROPIC_API_KEY or GOOGLE_API_KEY")
        sys.exit(1)

    # Create machine
    machine = ConstrainedHabermasMachine(
        question=question,
        statement_client=client,
        reward_client=client,
        statement_model=constrained_cot_model.ConstrainedCOTModel(),
        reward_model=cot_ranking_model.COTRankingModel(),
        social_choice_method=schulze_method.Schulze(
            tie_breaking_method=utils.TieBreakingMethod.RANDOM
        ),
        num_candidates=4,  # Small for quick testing
        num_citizens=3,
        seed=42,
        verbose=True,
    )

    # Run deliberation
    print("\n" + "="*80)
    print("Running deliberation...")
    print("="*80)

    result = machine.mediate(opinions)

    # Show results
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    print(f"\n✓ Sacred values detected: {len(result.detected_sacred_values)}")
    if result.detected_sacred_values:
        for sv in result.detected_sacred_values:
            print(f"  - Citizen {sv.citizen_id}: \"{sv.constraint_text[:50]}...\"")

    print(f"\n✓ Constraints compiled: {len(result.compiled_constraints)}")
    if result.compiled_constraints:
        for c in result.compiled_constraints:
            print(f"  - Prohibits: {c.prohibited_actions}")

    print(f"\n✓ Winning statement:")
    print(f"  \"{result.winning_statement}\"")

    # Verify constraint respected
    consensus_lower = result.winning_statement.lower()
    has_alcohol = "alcohol" in consensus_lower or "wine" in consensus_lower or "drink" in consensus_lower

    if has_alcohol and result.compiled_constraints:
        print("\n⚠️  WARNING: Consensus mentions alcohol despite constraint!")
    elif result.compiled_constraints:
        print("\n✅ Constraint respected: no alcohol recommendation")

    print("\n" + "="*80)


if __name__ == "__main__":
    main()
