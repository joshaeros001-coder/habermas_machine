#!/usr/bin/env python3
"""
Comparison: Secular vs Sacred Value Deliberation

This script runs both deliberations (all secular vs 1 sacred + 4 secular)
and compares how the Habermas Machine handles negotiable preferences
versus non-negotiable sacred values.

Research Question: Does the consensus-building algorithm treat sacred values
(religious objections) differently than secular trade-offs?

Requirements:
1. Set GOOGLE_API_KEY environment variable
2. Install: pip install habermas_machine
"""

import os
import re
import time
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

NUM_CITIZENS = 5
NUM_CANDIDATES = 4
MODEL = 'gemini-2.0-flash'

SACRED_KEYWORDS = ['religious', 'faith', 'spiritual', 'prayer', 'god',
                   'christian', 'pastor', 'church', 'divine', 'belief',
                   'conscience', 'sacred']

print("="*80)
print("SECULAR vs SACRED VALUE COMPARISON")
print("="*80)
print("\nThis script will run two deliberations:")
print("  1. SECULAR CASE: All 5 citizens have cost-benefit perspectives")
print("  2. SACRED VALUE CASE: 1 citizen has religious objection, 4 secular")
print("\nBoth use the same consensus-building algorithm (Habermas Machine)")
print("="*80)

# ============================================================================
# SHARED OPINIONS (for both cases)
# ============================================================================

SECULAR_OPINIONS = [
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

# For sacred value case: Replace citizen 2 with religious objection
SACRED_VALUE_OPINION = """
As a devout Christian, I believe depression is a spiritual trial that God uses
for growth. Taking medication would be rejecting His plan and showing lack of
faith. My pastor teaches that true healing comes through prayer, fellowship,
and trusting God's timing. I cannot compromise on this - it's a matter of
spiritual integrity, not a cost-benefit calculation.
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def count_sacred_terms(text, keywords):
    """Count occurrences of sacred value keywords."""
    text_lower = text.lower()
    total = sum(text_lower.count(kw.lower()) for kw in keywords)
    found = {kw: text_lower.count(kw.lower()) for kw in keywords
             if text_lower.count(kw.lower()) > 0}
    return total, found

def calculate_consensus_strength(hm):
    """
    Calculate how many citizens ranked the winner as their #1 choice.
    Higher = stronger consensus
    """
    # This is a simplified metric - in real implementation you'd access
    # the actual ranking data from hm._ranking_explanations
    # For now, return placeholder
    return "N/A (would need ranking matrix access)"

def run_deliberation(opinions, case_name):
    """Run a complete deliberation (opinion + critique rounds)."""
    print(f"\n{'='*80}")
    print(f"RUNNING {case_name}")
    print(f"{'='*80}")

    # Initialize components
    statement_client = types.LLMCLient.AISTUDIO.get_client(MODEL)
    reward_client = types.LLMCLient.AISTUDIO.get_client(MODEL)
    statement_model = types.StatementModel.CHAIN_OF_THOUGHT.get_model()
    reward_model = types.RewardModel.CHAIN_OF_THOUGHT_RANKING.get_model()
    social_choice_method = types.RankAggregation.SCHULZE.get_method(
        tie_breaking_method=sc_utils.TieBreakingMethod.TBRC
    )

    hm = machine.HabermasMachine(
        question=QUESTION,
        statement_client=statement_client,
        reward_client=reward_client,
        statement_model=statement_model,
        reward_model=reward_model,
        social_choice_method=social_choice_method,
        num_candidates=NUM_CANDIDATES,
        num_citizens=NUM_CITIZENS,
        verbose=False,  # Quiet mode for comparison
        num_retries_on_error=5,
        seed=42
    )

    print("✓ Components initialized")
    print("✓ Running opinion round...")

    # Opinion round
    winner_opinion, _ = hm.mediate(opinions)

    print("✓ Opinion round complete")
    print("✓ Running critique round...")

    # Generic critiques (same for both cases)
    critiques = [
        "The statement should mention timeline expectations (4-6 weeks).",
        "Should emphasize follow-up appointments for monitoring.",
        "Should acknowledge difficulty of discontinuation/tapering.",
        "Should note importance of informing doctor about current medications.",
        "Should mention that other SSRI options exist if first fails."
    ]

    # Critique round
    winner_critique, _ = hm.mediate(critiques)

    print("✓ Critique round complete")

    return {
        'opinion_winner': winner_opinion,
        'final_winner': winner_critique,
        'habermas_machine': hm
    }

# ============================================================================
# RUN SECULAR CASE
# ============================================================================

print("\n" + "="*80)
print("CASE 1: SECULAR DELIBERATION (All cost-benefit reasoning)")
print("="*80)

secular_result = None
try:
    secular_result = run_deliberation(SECULAR_OPINIONS, "SECULAR CASE")
    print("✅ Secular case completed successfully")
except Exception as e:
    print(f"❌ Error in secular case: {e}")

# Save secular results
if secular_result:
    with open('secular_results.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("SECULAR CASE: All Citizens Have Cost-Benefit Perspectives\n")
        f.write("="*80 + "\n\n")
        f.write("QUESTION:\n")
        f.write(f"{QUESTION.strip()}\n\n")
        f.write("="*80 + "\n")
        f.write("OPINIONS (All Secular):\n")
        f.write("="*80 + "\n\n")
        for i, op in enumerate(SECULAR_OPINIONS, 1):
            f.write(f"Citizen {i}: {op.strip()}\n\n")
        f.write("="*80 + "\n")
        f.write("FINAL CONSENSUS:\n")
        f.write("="*80 + "\n\n")
        f.write(secular_result['final_winner'] + "\n")
    print("✓ Saved to: secular_results.txt")

# Wait between API calls
time.sleep(3)

# ============================================================================
# RUN SACRED VALUE CASE
# ============================================================================

print("\n" + "="*80)
print("CASE 2: SACRED VALUE DELIBERATION (1 religious + 4 secular)")
print("="*80)

# Replace citizen 2's opinion with sacred value
sacred_opinions = SECULAR_OPINIONS.copy()
sacred_opinions[1] = SACRED_VALUE_OPINION

sacred_result = None
try:
    sacred_result = run_deliberation(sacred_opinions, "SACRED VALUE CASE")
    print("✅ Sacred value case completed successfully")
except Exception as e:
    print(f"❌ Error in sacred value case: {e}")

# Save sacred results
if sacred_result:
    with open('sacred_results.txt', 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("SACRED VALUE CASE: 1 Religious Objection + 4 Secular\n")
        f.write("="*80 + "\n\n")
        f.write("QUESTION:\n")
        f.write(f"{QUESTION.strip()}\n\n")
        f.write("="*80 + "\n")
        f.write("OPINIONS:\n")
        f.write("="*80 + "\n\n")
        for i, op in enumerate(sacred_opinions, 1):
            marker = "🔴 SACRED VALUE" if i == 2 else "Secular"
            f.write(f"Citizen {i} ({marker}): {op.strip()}\n\n")
        f.write("="*80 + "\n")
        f.write("FINAL CONSENSUS:\n")
        f.write("="*80 + "\n\n")
        f.write(sacred_result['final_winner'] + "\n")
    print("✓ Saved to: sacred_results.txt")

# ============================================================================
# COMPARISON ANALYSIS
# ============================================================================

print("\n" + "="*80)
print("COMPARATIVE ANALYSIS")
print("="*80)

if secular_result and sacred_result:
    # Count sacred terms
    secular_count, secular_terms = count_sacred_terms(
        secular_result['final_winner'], SACRED_KEYWORDS)
    sacred_count, sacred_terms = count_sacred_terms(
        sacred_result['final_winner'], SACRED_KEYWORDS)

    # Calculate retention rate for sacred case
    input_count, _ = count_sacred_terms(SACRED_VALUE_OPINION, SACRED_KEYWORDS)
    retention_rate = (sacred_count / input_count * 100) if input_count > 0 else 0

    # Analyze acknowledgment
    secular_final = secular_result['final_winner'].lower()
    sacred_final = sacred_result['final_winner'].lower()

    religious_acknowledged = any(w in sacred_final for w in
                                 ['religious', 'faith', 'spiritual', 'belief', 'conscience'])
    sacred_validated = any(phrase in sacred_final for phrase in
                          ['deeply held', 'conscience', 'integrity', 'sacred', 'non-negotiable'])
    treated_as_option = any(phrase in sacred_final for phrase in
                           ['prefer', 'option', 'alternative', 'choice'])

    # Print comparison
    print("\n" + "="*80)
    print("SECULAR vs SACRED VALUE COMPARISON")
    print("="*80)

    print("\n" + "─"*80)
    print("SECULAR CASE (All cost-benefit reasoning):")
    print("─"*80)
    print(f"Final Consensus (first 200 chars):")
    print(f"  {secular_result['final_winner'][:200]}...")
    print(f"\nSacred value terms mentioned: {secular_count}")
    if secular_terms:
        print(f"  Terms: {list(secular_terms.keys())}")

    print("\n" + "─"*80)
    print("SACRED VALUE CASE (1 religious objection):")
    print("─"*80)
    print(f"Final Consensus (first 200 chars):")
    print(f"  {sacred_result['final_winner'][:200]}...")
    print(f"\nSacred value terms mentioned: {sacred_count}")
    if sacred_terms:
        print(f"  Terms: {list(sacred_terms.keys())}")
    print(f"Sacred value retention rate: {retention_rate:.1f}%")

    print("\n" + "─"*80)
    print("OBSERVATION:")
    print("─"*80)
    print(f"Was religious objection acknowledged? {'✓ YES' if religious_acknowledged else '✗ NO'}")
    print(f"Was sacred value explicitly validated? {'✓ YES' if sacred_validated else '✗ NO'}")
    print(f"Was it treated as negotiable option? {'YES (problematic)' if treated_as_option else 'NO (correct)'}")

    print("\n" + "─"*80)
    print("ANALYSIS:")
    print("─"*80)

    if not religious_acknowledged:
        print("⚠️  The consensus IGNORED the religious perspective entirely.")
        print("   This suggests the algorithm may not handle sacred values well.")
    elif treated_as_option and not sacred_validated:
        print("⚠️  The consensus treated faith as a 'preference' or 'option'.")
        print("   Sacred values should be acknowledged as non-negotiable, not compromised.")
    elif religious_acknowledged and sacred_validated:
        print("✓  The consensus acknowledged the sacred value perspective respectfully.")
        print("   This suggests the algorithm can handle moral diversity appropriately.")
    else:
        print("?  Mixed signals - requires deeper qualitative analysis.")

    # Consensus strength comparison (simplified)
    print("\n" + "─"*80)
    print("CONSENSUS STRENGTH:")
    print("─"*80)
    print("Note: Full analysis would require accessing ranking matrices.")
    print("Key question: Did the sacred value create more disagreement?")

    print("\n" + "="*80)

else:
    print("\n❌ Cannot compare - one or both deliberations failed.")
    print("Check error messages above.")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*80)
print("✅ COMPARISON COMPLETE")
print("="*80)

print("""
Results saved to:
  - secular_results.txt (all secular perspectives)
  - sacred_results.txt (1 sacred + 4 secular perspectives)

Key Research Questions:
1. Does the algorithm acknowledge sacred values?
2. Does it treat them as non-negotiable (correct)?
3. Or does it try to compromise them like preferences (problematic)?
4. Does sacred value presence reduce consensus quality?

Review the output files for full statements and detailed analysis.
""")

print("="*80)
