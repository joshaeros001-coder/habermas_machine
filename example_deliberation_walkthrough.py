#!/usr/bin/env python3
"""
Step-by-step walkthrough: Running a single deliberation scenario

This example demonstrates the complete flow of the Habermas Machine
for SSRI medication decision-making.

Requirements:
1. Set GOOGLE_API_KEY environment variable
2. Install: pip install habermas_machine
"""

import os
from habermas_machine import machine, types
from habermas_machine.social_choice import utils as sc_utils

# ============================================================================
# STEP 1: SETUP AND CONFIGURATION
# ============================================================================

print("="*70)
print("HABERMAS MACHINE: STEP-BY-STEP DELIBERATION WALKTHROUGH")
print("="*70)

# Set your API key (get from https://aistudio.google.com/app/apikey)
# os.environ['GOOGLE_API_KEY'] = 'your_api_key_here'

# Define the deliberation question (the "vignette")
QUESTION = """
Should a 35-year-old patient with moderate depression accept their
doctor's recommendation to start taking SSRI antidepressants, given
the potential benefits (reduced symptoms, improved quality of life)
and risks (side effects, dependency concerns)?
"""

# Configuration parameters
NUM_CITIZENS = 5        # Number of participants in deliberation
NUM_CANDIDATES = 4      # Number of consensus statements to generate per round
MODEL = 'gemini-1.5-flash'  # Gemini model to use

print(f"\n📋 QUESTION: {QUESTION.strip()}")
print(f"\n⚙️  Configuration:")
print(f"   - Citizens: {NUM_CITIZENS}")
print(f"   - Candidate statements per round: {NUM_CANDIDATES}")
print(f"   - Model: {MODEL}")

# ============================================================================
# STEP 2: INITIALIZE COMPONENTS
# ============================================================================

print("\n" + "="*70)
print("STEP 2: INITIALIZING COMPONENTS")
print("="*70)

# Create LLM clients (separate clients for statement generation and ranking)
statement_client = types.LLMCLient.AISTUDIO.get_client(MODEL)
reward_client = types.LLMCLient.AISTUDIO.get_client(MODEL)
print("✓ LLM clients initialized (Gemini)")

# Create statement generation model (uses chain-of-thought reasoning)
statement_model = types.StatementModel.CHAIN_OF_THOUGHT.get_model()
print("✓ Statement model: Chain-of-Thought")

# Create reward/ranking model (uses chain-of-thought reasoning)
reward_model = types.RewardModel.CHAIN_OF_THOUGHT_RANKING.get_model()
print("✓ Reward model: Chain-of-Thought Ranking")

# Create social choice aggregation method (Schulze voting with tie-breaking)
social_choice_method = types.RankAggregation.SCHULZE.get_method(
    tie_breaking_method=sc_utils.TieBreakingMethod.TBRC
)
print("✓ Social choice: Schulze method with TBRC tie-breaking")

# ============================================================================
# STEP 3: CREATE HABERMAS MACHINE INSTANCE
# ============================================================================

print("\n" + "="*70)
print("STEP 3: CREATING HABERMAS MACHINE")
print("="*70)

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
    seed=42  # For reproducibility
)

print("✓ HabermasMachine initialized and ready")

# ============================================================================
# STEP 4: DEFINE INITIAL OPINIONS (SECULAR TRADE-OFFS)
# ============================================================================

print("\n" + "="*70)
print("STEP 4: COLLECTING INITIAL OPINIONS")
print("="*70)

# Example: Secular perspectives on SSRI decision
# (Focusing on cost, side effects, efficacy)
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

print("📝 Opinions collected from 5 citizens")
for i, opinion in enumerate(OPINIONS, 1):
    print(f"\n   Citizen {i}: {opinion.strip()[:100]}...")

# ============================================================================
# STEP 5: RUN OPINION ROUND
# ============================================================================

print("\n" + "="*70)
print("STEP 5: RUNNING OPINION ROUND")
print("="*70)
print("\nThis will:")
print("  1. Generate 4 candidate consensus statements")
print("  2. Each citizen ranks the candidates")
print("  3. Schulze method aggregates rankings")
print("  4. Select winning statement")
print("\n" + "-"*70 + "\n")

# Run the mediation - this returns (winner, sorted_candidates)
winner_opinion, sorted_statements_opinion = hm.mediate(OPINIONS)

print("\n" + "="*70)
print("OPINION ROUND RESULTS")
print("="*70)
print(f"\n🏆 WINNING STATEMENT:\n{winner_opinion}\n")

print("\n📊 ALL CANDIDATES (sorted by preference):")
for i, stmt in enumerate(sorted_statements_opinion, 1):
    print(f"\n   Rank {i}: {stmt[:150]}...")

# ============================================================================
# STEP 6: DEFINE CRITIQUES
# ============================================================================

print("\n" + "="*70)
print("STEP 6: COLLECTING CRITIQUES OF WINNING STATEMENT")
print("="*70)

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

print("📝 Critiques collected from 5 citizens")
for i, critique in enumerate(CRITIQUES, 1):
    print(f"\n   Citizen {i}: {critique.strip()[:100]}...")

# ============================================================================
# STEP 7: RUN CRITIQUE ROUND
# ============================================================================

print("\n" + "="*70)
print("STEP 7: RUNNING CRITIQUE ROUND")
print("="*70)
print("\nThis will:")
print("  1. Generate new candidates incorporating critiques + previous winner")
print("  2. Each citizen ranks the new candidates")
print("  3. Schulze method aggregates rankings")
print("  4. Select refined winning statement")
print("\n" + "-"*70 + "\n")

# Run second mediation round with critiques
winner_critique, sorted_statements_critique = hm.mediate(CRITIQUES)

print("\n" + "="*70)
print("CRITIQUE ROUND RESULTS")
print("="*70)
print(f"\n🏆 REFINED WINNING STATEMENT:\n{winner_critique}\n")

print("\n📊 ALL CANDIDATES (sorted by preference):")
for i, stmt in enumerate(sorted_statements_critique, 1):
    print(f"\n   Rank {i}: {stmt[:150]}...")

# ============================================================================
# STEP 8: EXAMINE FULL HISTORY
# ============================================================================

print("\n" + "="*70)
print("STEP 8: DELIBERATION HISTORY")
print("="*70)

print(f"\n📈 Total rounds: {hm._round}")
print(f"\n🎯 All winning statements across rounds:")
for i, winner in enumerate(hm._previous_winners):
    print(f"\n   Round {i}: {winner[:150]}...")

print(f"\n📚 Statement generation metadata available:")
print(f"   - Statement explanations: {len(hm._statement_explanations)} rounds")
print(f"   - Ranking explanations: {len(hm._ranking_explanations)} rounds")
print(f"   - Candidate history: {len(hm._previous_candidates)} rounds")

# ============================================================================
# STEP 9: ACCESS DETAILED DATA
# ============================================================================

print("\n" + "="*70)
print("STEP 9: ACCESSING DETAILED DATA")
print("="*70)

# Get ranking explanations from the last round
if hm._ranking_explanations:
    print("\n💭 Example ranking explanation (Citizen 1, Last Round):")
    last_round_rankings = hm._ranking_explanations[-1]
    if last_round_rankings:
        citizen_1_explanation = last_round_rankings[0][1]  # (ranking, explanation)
        print(f"   {citizen_1_explanation[:200]}...")

# Get statement generation explanations
if hm._statement_explanations:
    print("\n💭 Example statement generation explanation (Last Round, First Candidate):")
    last_round_statements = hm._statement_explanations[-1]
    if last_round_statements:
        first_statement_explanation = last_round_statements[0][1]  # (statement, explanation)
        print(f"   {first_statement_explanation[:200]}...")

# ============================================================================
# COMPLETE!
# ============================================================================

print("\n" + "="*70)
print("✅ DELIBERATION COMPLETE!")
print("="*70)
print("""
Summary of what happened:
1. ✓ Initialized HabermasMachine with Gemini backend
2. ✓ Collected 5 citizen opinions on SSRI decision
3. ✓ Generated 4 consensus statement candidates
4. ✓ Each citizen ranked all candidates
5. ✓ Schulze voting selected winning statement
6. ✓ Collected 5 critiques of the winner
7. ✓ Generated new candidates incorporating feedback
8. ✓ Re-ranked and selected refined winner
9. ✓ Stored complete history and explanations

The final consensus incorporates diverse perspectives and has been
refined through democratic deliberation!
""")

print("\n" + "="*70)
print("NEXT STEPS")
print("="*70)
print("""
To run this example:
1. Set GOOGLE_API_KEY environment variable
2. pip install habermas_machine
3. python example_deliberation_walkthrough.py

To create 50 test vignettes:
- See the companion script: create_ssri_vignettes.py
- Generates JSON file with sacred vs secular cases
- Ready for batch processing
""")
