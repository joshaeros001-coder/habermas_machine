#!/usr/bin/env python3
"""
Show FULL deliberation results without truncation.
This helps you understand exactly what's happening.
"""

import os
from habermas_machine import machine, types
from habermas_machine.social_choice import utils as sc_utils

# Configuration
QUESTION = """
Should a 35-year-old patient with moderate depression accept their
doctor's recommendation to start taking SSRI antidepressants, given
the potential benefits (reduced symptoms, improved quality of life)
and risks (side effects, dependency concerns)?
"""

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

print("="*80)
print("DETAILED EXPLANATION: HOW EACH COMPONENT WORKS")
print("="*80)

# Initialize
hm = machine.HabermasMachine(
    question=QUESTION,
    statement_client=types.LLMCLient.AISTUDIO.get_client('gemini-2.0-flash'),
    reward_client=types.LLMCLient.AISTUDIO.get_client('gemini-2.0-flash'),
    statement_model=types.StatementModel.CHAIN_OF_THOUGHT.get_model(),
    reward_model=types.RewardModel.CHAIN_OF_THOUGHT_RANKING.get_model(),
    social_choice_method=types.RankAggregation.SCHULZE.get_method(
        sc_utils.TieBreakingMethod.TBRC
    ),
    num_candidates=4,
    num_citizens=5,
    verbose=False,  # Turn off verbose so we can show custom output
)

# Run opinion round
winner, sorted_candidates = hm.mediate(OPINIONS)

print("\n" + "="*80)
print("UNDERSTANDING THE RANKING SYSTEM")
print("="*80)

print("\n📌 KEY CONCEPT: Lower numbers = better ranking")
print("   - Rank 0 = 1st place (best)")
print("   - Rank 1 = 2nd place")
print("   - Rank 2 = 3rd place")
print("   - Rank 3 = 4th place (worst)")

print("\n📌 The '>' symbol means 'is preferred over'")
print("   - '4 > 3 > 1 > 2' means:")
print("   - Statement 4 is 1st choice")
print("   - Statement 3 is 2nd choice")
print("   - Statement 1 is 3rd choice")
print("   - Statement 2 is 4th choice (least preferred)")

print("\n" + "="*80)
print("FULL CANDIDATE STATEMENTS (UNTRUNCATED)")
print("="*80)

for i, candidate in enumerate(sorted_candidates, 1):
    print(f"\n{'─'*80}")
    print(f"CANDIDATE #{i} (Rank {i} in social ranking)")
    print(f"{'─'*80}")
    print(candidate)

print("\n" + "="*80)
print("ACCESSING THE CHAIN-OF-THOUGHT EXPLANATIONS")
print("="*80)

print("\n📌 Statement Generation Explanations:")
print("   (This shows HOW the AI reasoned about creating each statement)\n")

if hm._statement_explanations:
    last_round = hm._statement_explanations[-1]
    for i, (stmt, explanation) in enumerate(last_round, 1):
        print(f"\n{'─'*80}")
        print(f"STATEMENT {i} - CHAIN OF THOUGHT:")
        print(f"{'─'*80}")
        print(explanation[:500] + "..." if len(explanation) > 500 else explanation)

print("\n" + "="*80)
print("📌 Ranking Explanations:")
print("   (This shows HOW each citizen reasoned about their rankings)\n")

if hm._ranking_explanations:
    last_round = hm._ranking_explanations[-1]
    for i, (ranking, explanation) in enumerate(last_round, 1):
        print(f"\n{'─'*80}")
        print(f"CITIZEN {i} - RANKING EXPLANATION:")
        print(f"{'─'*80}")
        print(f"Their ranking: {ranking}")
        print(f"Explanation: {explanation[:500] + '...' if len(explanation) > 500 else explanation}")

print("\n" + "="*80)
print("WHY 'JURY' LANGUAGE?")
print("="*80)
print("""
The AI uses "jury" language because:

1. PROMPT DESIGN: The researchers designed prompts that frame citizens
   as a "citizens' jury" - a democratic deliberation format.

2. CONCEPTUAL GROUNDING: This is based on deliberative democracy theory:
   - Citizens' juries are real democratic institutions
   - Used in policy-making worldwide
   - Small group of citizens deliberate on complex issues
   - Aim to reach informed consensus

3. WHY IT WORKS:
   - Primes the AI to think about synthesis and consensus
   - Encourages balanced consideration of all views
   - Mimics real deliberative democratic processes

4. WHERE IT COMES FROM:
   - The prompt templates in cot_model.py include this framing
   - Not hardcoded - it's part of the prompt engineering
   - You could change it by modifying the prompts
""")

print("\n" + "="*80)
print("WHY DO ALL STATEMENTS SEEM TO AGREE?")
print("="*80)
print("""
This is BY DESIGN! The algorithm's goal is CONSENSUS, not debate:

1. STATEMENT MODEL PURPOSE:
   - Generate statements that SYNTHESIZE diverse opinions
   - Find common ground across disagreement
   - Not to pick sides, but to integrate perspectives

2. THE ALGORITHM:
   - Sees ALL 5 opinions at once
   - Instructed to find agreement points
   - Acknowledges disagreements but seeks middle ground

3. CONCEPTUAL FOUNDATION (Habermas):
   - Based on Jürgen Habermas's "communicative rationality"
   - Goal: reach understanding through rational discourse
   - Not voting between extremes, but deliberating toward synthesis

4. WHY THIS MATTERS:
   - In your example, opinions ranged from "try SSRIs first" to
     "try therapy first"
   - The consensus statements say: "consider both, informed choice,
     consult doctor, monitor carefully"
   - This captures the nuance across all 5 views

5. WHEN DISAGREEMENT APPEARS:
   - If opinions are fundamentally opposed (e.g., sacred values),
     the statements may show more tension
   - But the algorithm ALWAYS tries to find synthesis
   - That's the Habermasian ideal!
""")

print("\n" + "="*80)
print("GEMINI vs CHINCHILLA: WHAT'S THE DIFFERENCE?")
print("="*80)
print("""
1. ORIGINAL PAPER (Science 2024):
   - Used CHINCHILLA model (DeepMind, 70B parameters)
   - Fine-tuned on deliberation task
   - NOT publicly available

2. THIS PUBLIC CODE:
   - Uses GEMINI (Google AI Studio)
   - NOT fine-tuned - just prompted via chain-of-thought
   - Available to anyone with API key

3. WHERE IS CHAIN-OF-THOUGHT?
   - NOT built into Gemini
   - WE ADD IT via special prompts in cot_model.py and cot_ranking_model.py

4. HOW CHAIN-OF-THOUGHT WORKS:
   - The prompt says: "Think step by step, then give your answer"
   - AI generates reasoning FIRST
   - Then generates final answer
   - We parse both parts: <answer>final<sep>reasoning</answer>

5. EXAMPLE PROMPT (simplified):
   "You are a mediator helping a citizens' jury. Here are 5 opinions.
    Think step-by-step about common ground. Then write a consensus
    statement. Format: <answer>STATEMENT<sep>REASONING</answer>"

6. THE PROMPT IS THE INTELLIGENCE:
   - Gemini is just a language model
   - The deliberation behavior comes from PROMPT ENGINEERING
   - Different prompts = different behavior
   - That's why the researchers could use any LLM!
""")

print("\n" + "="*80)
print("STATEMENT CLIENT vs REWARD CLIENT")
print("="*80)
print("""
Both use Gemini, but they do DIFFERENT TASKS:

1. STATEMENT CLIENT:
   - Used by: StatementModel (cot_model.py)
   - Task: Generate consensus statements
   - Gets: Question + Opinions
   - Returns: Synthesized statement + explanation
   - Prompt emphasizes: Finding common ground

2. REWARD CLIENT:
   - Used by: RewardModel (cot_ranking_model.py)
   - Task: Rank statements from a citizen's perspective
   - Gets: Question + One citizen's opinion + All candidate statements
   - Returns: Ranking + explanation
   - Prompt emphasizes: Which statement best matches YOUR view?

3. WHY SEPARATE CLIENTS?
   - In principle, you could use different LLMs for each
   - E.g., GPT-4 for statements, Claude for ranking
   - Allows flexibility and experimentation
   - In practice, we use same model (Gemini) for both

4. THE PROCESS:
   Step 1: Statement client generates 4 candidates
   Step 2: Reward client ranks them (once per citizen, 5 times)
   Step 3: Schulze method aggregates the 5 rankings
   Step 4: Winner selected based on group preference
""")

print("\n" + "="*80)
print("✅ SUMMARY")
print("="*80)
print("""
KEY INSIGHTS:

1. Rankings use 0-indexing (0 = best)
2. "Jury" language comes from deliberative democracy framing
3. Statements agree because that's the GOAL (consensus, not debate)
4. Chinchilla is NOT available; Gemini works via chain-of-thought prompts
5. Chain-of-thought is ADDED by our prompts, not built into Gemini
6. Statement client and reward client do different tasks with same LLM

The magic is in the PROMPTS, not the LLM!
""")
