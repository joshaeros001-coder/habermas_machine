#!/usr/bin/env python3
"""
Example: Using Anthropic's Claude with the Habermas Machine

This demonstrates how to use Claude (claude-3-5-sonnet-20241022) as the LLM
backend for the Habermas Machine deliberation system.

Requirements:
1. Set ANTHROPIC_API_KEY environment variable
2. Install: pip install anthropic
3. Install: pip install habermas_machine

Usage:
    export ANTHROPIC_API_KEY="your_api_key_here"
    python example_anthropic_claude.py
"""

import os
from habermas_machine import machine, types
from habermas_machine.social_choice import utils as sc_utils

# ============================================================================
# CONFIGURATION
# ============================================================================

QUESTION = """
Should a 35-year-old patient with moderate depression accept their
doctor's recommendation to start taking SSRI antidepressants, given
the potential benefits (reduced symptoms, improved quality of life)
and risks (side effects, dependency concerns)?
"""

# Claude model to use
MODEL = 'claude-3-5-sonnet-20241022'

# Deliberation parameters
NUM_CITIZENS = 5
NUM_CANDIDATES = 4

print("="*80)
print("HABERMAS MACHINE with ANTHROPIC CLAUDE")
print("="*80)
print(f"\n📋 Question: {QUESTION.strip()}")
print(f"\n⚙️  Configuration:")
print(f"   - Model: {MODEL}")
print(f"   - Citizens: {NUM_CITIZENS}")
print(f"   - Candidates per round: {NUM_CANDIDATES}")

# Check for API key
if not os.environ.get('ANTHROPIC_API_KEY'):
    print("\n❌ ERROR: ANTHROPIC_API_KEY environment variable not set!")
    print("   Get your API key from: https://console.anthropic.com/")
    print("   Then run: export ANTHROPIC_API_KEY='your_key_here'")
    exit(1)

print("\n✓ API key found")

# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

print("\n" + "="*80)
print("INITIALIZING COMPONENTS")
print("="*80)

# Create Claude clients using the types enum
statement_client = types.LLMCLient.ANTHROPIC.get_client(MODEL)
reward_client = types.LLMCLient.ANTHROPIC.get_client(MODEL)

print("✓ Anthropic Claude clients initialized")

# Create statement and reward models (chain-of-thought)
statement_model = types.StatementModel.CHAIN_OF_THOUGHT.get_model()
reward_model = types.RewardModel.CHAIN_OF_THOUGHT_RANKING.get_model()

print("✓ Chain-of-thought models initialized")

# Create social choice method (Schulze voting)
social_choice_method = types.RankAggregation.SCHULZE.get_method(
    tie_breaking_method=sc_utils.TieBreakingMethod.TBRC
)

print("✓ Schulze voting method initialized")

# ============================================================================
# CREATE HABERMAS MACHINE
# ============================================================================

print("\n" + "="*80)
print("CREATING HABERMAS MACHINE")
print("="*80)

hm = machine.HabermasMachine(
    question=QUESTION,
    statement_client=statement_client,
    reward_client=reward_client,
    statement_model=statement_model,
    reward_model=reward_model,
    social_choice_method=social_choice_method,
    num_candidates=NUM_CANDIDATES,
    num_citizens=NUM_CITIZENS,
    verbose=True,  # Show detailed output
    num_retries_on_error=5,
    seed=42  # Note: Claude doesn't use seeds, but this is for other components
)

print("✓ HabermasMachine initialized with Claude backend")

# ============================================================================
# DEFINE CITIZEN OPINIONS
# ============================================================================

print("\n" + "="*80)
print("CITIZEN OPINIONS")
print("="*80)

OPINIONS = [
    """
    I think the patient should try the SSRIs. Depression significantly
    impacts quality of life and work productivity. While side effects like
    nausea and sleep changes are possible, they're usually temporary and
    manageable. The evidence shows SSRIs help about 60% of people with
    moderate depression. If side effects are intolerable, the patient can
    discontinue. The potential benefit outweighs the risk.
    """,

    """
    I'm hesitant about jumping straight to medication. SSRIs can be expensive
    if not covered by insurance, and there are alternatives worth trying first.
    Cognitive behavioral therapy has comparable effectiveness for moderate
    depression without medication risks. I'd recommend trying therapy, exercise,
    and sleep improvements for 2-3 months before considering SSRIs. Medication
    should be a second-line option.
    """,

    """
    The patient should carefully weigh the costs and benefits. SSRIs have
    helped millions but come with real side effects - sexual dysfunction,
    weight gain, and initial anxiety can be difficult. Some people also
    struggle to discontinue them. I'd suggest a trial period of 6-8 weeks
    with close monitoring. If helpful, continue. If not, explore other options
    like different medications or therapy combinations.
    """,

    """
    I support starting SSRIs but with realistic expectations. They're not
    a magic cure - they typically reduce symptoms by 40-60%, not eliminate
    them entirely. The patient should combine medication with lifestyle
    changes and possibly therapy for best results. Cost is a consideration
    too - generic SSRIs are affordable but brand-name versions can be pricey.
    Overall, worth trying given moderate depression severity.
    """,

    """
    This is a personal medical decision requiring professional guidance.
    Depression at moderate levels warrants treatment, but the choice between
    medication, therapy, or both depends on individual circumstances - previous
    treatment history, severity of symptoms, patient preferences, and financial
    situation. I'd trust the doctor's recommendation but ensure the patient
    feels informed about alternatives and has realistic expectations about
    outcomes and timeline.
    """
]

for i, opinion in enumerate(OPINIONS, 1):
    print(f"\nCitizen {i}: {opinion.strip()[:100]}...")

# ============================================================================
# RUN OPINION ROUND
# ============================================================================

print("\n" + "="*80)
print("RUNNING OPINION ROUND")
print("="*80)
print("\nClaude will now:")
print("  1. Generate 4 consensus statement candidates")
print("  2. Have each citizen rank the candidates")
print("  3. Use Schulze voting to select the winner")
print("\n" + "-"*80 + "\n")

winner_opinion, sorted_opinion = hm.mediate(OPINIONS)

print("\n" + "="*80)
print("OPINION ROUND RESULTS")
print("="*80)
print(f"\n🏆 WINNING STATEMENT:\n{winner_opinion}\n")

# ============================================================================
# DEFINE CRITIQUES
# ============================================================================

print("\n" + "="*80)
print("CITIZEN CRITIQUES")
print("="*80)

CRITIQUES = [
    """
    The statement is good but should mention timeline expectations.
    SSRIs typically take 4-6 weeks to show full effects, which is
    important for patients to know so they don't give up too early.
    """,

    """
    I agree with the balanced approach but think we should emphasize
    the importance of regular follow-up appointments to monitor both
    effectiveness and side effects. This isn't a "set it and forget it"
    treatment.
    """,

    """
    The statement should acknowledge that stopping SSRIs can be difficult
    and requires tapering under medical supervision. Patients should know
    this isn't necessarily a short-term commitment.
    """,

    """
    Good overall, but I think we should add something about the importance
    of informing the doctor about all current medications and health
    conditions to avoid dangerous drug interactions.
    """,

    """
    I appreciate the balanced perspective. Maybe add that if this SSRI
    doesn't work, there are other SSRIs and medication classes to try.
    First medication failure doesn't mean medication won't help at all.
    """
]

for i, critique in enumerate(CRITIQUES, 1):
    print(f"\nCitizen {i}: {critique.strip()[:100]}...")

# ============================================================================
# RUN CRITIQUE ROUND
# ============================================================================

print("\n" + "="*80)
print("RUNNING CRITIQUE ROUND")
print("="*80)
print("\nClaude will now:")
print("  1. Generate refined candidates incorporating critiques")
print("  2. Have each citizen rank the new candidates")
print("  3. Select the refined consensus")
print("\n" + "-"*80 + "\n")

winner_critique, sorted_critique = hm.mediate(CRITIQUES)

print("\n" + "="*80)
print("CRITIQUE ROUND RESULTS")
print("="*80)
print(f"\n🏆 REFINED WINNING STATEMENT:\n{winner_critique}\n")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("✅ DELIBERATION COMPLETE")
print("="*80)

print(f"""
Summary:
  - Backend: Anthropic Claude ({MODEL})
  - Rounds completed: {hm._round}
  - Total citizens: {NUM_CITIZENS}
  - Candidates per round: {NUM_CANDIDATES}

Process:
  1. ✓ Collected diverse citizen opinions
  2. ✓ Claude generated consensus statement candidates
  3. ✓ Citizens ranked candidates (via Claude perspective-taking)
  4. ✓ Schulze voting selected winner
  5. ✓ Citizens critiqued the winner
  6. ✓ Claude generated refined consensus incorporating feedback

Result:
  Claude successfully mediated democratic deliberation, finding common
  ground across diverse perspectives on SSRI medication decisions.
""")

print("="*80)
print("\nNote: Claude's outputs may differ from Gemini's outputs for the same")
print("prompts due to different model architectures and training. Both should")
print("successfully perform the consensus-building task, but with potentially")
print("different linguistic styles and emphasis.")
print("="*80)
