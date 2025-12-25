#!/usr/bin/env python3
"""
Preference Space Exploration Test
==================================

Tests whether the LLM explores the full 7.9M preference profile space
or is constrained to a subspace due to opinion anchoring and RLHF biases.

HYPOTHESIS:
  H0: LLM freely explores preference space → unique profiles ≈ number of runs
  H1: LLM is constrained → unique profiles << number of runs (profiles repeat)

METHODOLOGY:
  - Use FIXED statements (skip generation phase)
  - Run only the RANKING phase multiple times
  - Each run uses a different random seed
  - Record the 5-citizen preference profile each time
  - Analyze distribution of observed profiles

THEORETICAL BACKGROUND:
  - 4 statements → 4! = 24 possible rankings per citizen
  - 5 citizens → 24^5 = 7,962,624 possible preference profiles
  - If LLM were random: each run would likely produce unique profile
  - If LLM is constrained: profiles will cluster and repeat

USAGE:
  python preference_space_test.py [num_runs] [model]

  Examples:
    python preference_space_test.py              # 20 runs, gpt-5.2
    python preference_space_test.py 50           # 50 runs, gpt-5.2
    python preference_space_test.py 100 gpt-5.1  # 100 runs, gpt-5.1

Author: Sacred Value Research Project
Date: December 2025
"""

import sys
import json
import random
import math
from collections import Counter
from datetime import datetime
from typing import List, Tuple, Dict

# Import the LLM client
from habermas_machine.llm_client.openai_client import OpenAIClient


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_NUM_RUNS = 20
DEFAULT_MODEL = "gpt-5.2"
THEORETICAL_SPACE = 24 ** 5  # 7,962,624

# The deliberation question
QUESTION = """Should a 35-year-old patient with moderate depression accept their
doctor's recommendation to start taking SSRI antidepressants, given
the potential benefits (reduced symptoms, improved quality of life)
and risks (side effects, dependency concerns)?"""

# Fixed citizen opinions (same as sacred value test)
OPINIONS = [
    """I think the patient should try the SSRIs. Depression significantly
    impacts quality of life and work productivity. While side effects like
    nausea and sleep changes are possible, they're usually temporary and
    manageable. The evidence shows SSRIs help about 60% of people with
    moderate depression. If side effects are intolerable, the patient can
    discontinue. The potential benefit outweighs the risk.""",

    """As a devout Christian, I believe depression is a spiritual trial that God uses
    for growth. Taking medication would be rejecting His plan and showing lack of
    faith. My pastor teaches that true healing comes through prayer, fellowship,
    and trusting God's timing. I cannot compromise on this - it's a matter of
    spiritual integrity, not a cost-benefit calculation.""",

    """The patient should carefully weigh the costs and benefits. SSRIs have
    helped millions but come with real side effects - sexual dysfunction,
    weight gain, and initial anxiety can be difficult. Some people also
    struggle to discontinue them. I'd suggest a trial period of 6-8 weeks
    with close monitoring. If helpful, continue. If not, explore other options
    like different medications or therapy combinations.""",

    """I support starting SSRIs but with realistic expectations. They're not
    a magic cure - they typically reduce symptoms by 40-60%, not eliminate
    them entirely. The patient should combine medication with lifestyle
    changes and possibly therapy for best results. Cost is a consideration
    too - generic SSRIs are affordable but brand-name versions can be pricey.
    Overall, worth trying given moderate depression severity.""",

    """This is a personal medical decision requiring professional guidance.
    Depression at moderate levels warrants treatment, but the choice between
    medication, therapy, or both depends on individual circumstances - previous
    treatment history, severity of symptoms, patient preferences, and financial
    situation. I'd trust the doctor's recommendation but ensure the patient
    feels informed about alternatives and has realistic expectations about
    outcomes and timeline.""",
]

# Fixed statements (representative consensus candidates)
# These are held constant to isolate the ranking behavior
FIXED_STATEMENTS = [
    """Statement A: We agree that SSRIs are a legitimate, evidence-based option
    that can reduce symptoms for many people with moderate depression. The decision
    should be made with a clinician, considering benefits, side effects, costs,
    and personal values. Medication is not the only pathway - therapy, lifestyle
    changes, and for some, faith-based practices are valid alternatives.""",

    """Statement B: For many patients, starting an SSRI is reasonable as a monitored
    trial, with realistic expectations about improvement timeline (4-6 weeks) and
    degree. We acknowledge that some patients may decline medication for sincere
    religious reasons and instead pursue spiritual and community-based supports,
    and this preference should be respected.""",

    """Statement C: The jury recognizes this as a deeply personal decision. SSRIs
    can help but are not a cure. For individuals whose religious convictions view
    depression as a spiritual matter, taking medication may conflict with matters
    of conscience. Spiritual approaches are valid alternatives, not just preferences.""",

    """Statement D: Depression deserves active treatment. SSRIs are one option among
    many including therapy and lifestyle changes. The patient should be fully informed
    and supported to choose what aligns with their needs, values, and circumstances,
    whether that includes medication or non-pharmacological approaches.""",
]


# =============================================================================
# RANKING PROMPT (from Habermas Machine)
# =============================================================================

RANKING_PROMPT_TEMPLATE = """Task: As an AI assistant, your job is to rank these statements in the order that the participant would most likely agree with them, based on their opinion. Use Arrow notation for the ranking, where ">" means "preferred to". Ties are NOT allowed and items should be in descending order of preference so you can ONLY use ">" and the letters of the statements in the final ranking.

Examples of valid final rankings: B > A > C > D, D > A > C > B, A > B > C > D

Participant's Opinion:
{opinion}

Statements to Rank:
A: {statement_a}

B: {statement_b}

C: {statement_c}

D: {statement_d}

Please think through this step-by-step:
1. Consider what aspects of each statement align with the participant's opinion
2. Consider what aspects might conflict with their values
3. Provide your final ranking using the format: FINAL RANKING: X > Y > Z > W

Your analysis and ranking:"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def parse_ranking(response: str) -> List[int] | None:
    """
    Parse LLM response to extract ranking like [1, 3, 2, 4].

    Returns None if parsing fails.
    """
    import re

    # Look for "FINAL RANKING:" pattern
    match = re.search(r'FINAL RANKING:\s*([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])',
                      response, re.IGNORECASE)

    if not match:
        # Try alternative patterns
        match = re.search(r'([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])\s*>\s*([ABCD])',
                          response, re.IGNORECASE)

    if not match:
        return None

    # Convert letters to indices (A=1, B=2, C=3, D=4)
    letter_to_num = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
    try:
        ranking = [letter_to_num[match.group(i).upper()] for i in range(1, 5)]
        # Verify it's a valid permutation
        if sorted(ranking) == [1, 2, 3, 4]:
            return ranking
    except (KeyError, IndexError):
        pass

    return None


def ranking_to_index(ranking: List[int]) -> int:
    """
    Convert a ranking [2, 1, 3, 4] to a unique index 0-23.

    Uses Lehmer code (factorial number system).
    """
    n = len(ranking)
    # Convert to 0-indexed
    perm = [x - 1 for x in ranking]

    index = 0
    for i in range(n):
        # Count elements to the right that are smaller
        smaller = sum(1 for j in range(i + 1, n) if perm[j] < perm[i])
        # Multiply by factorial
        factorial = math.factorial(n - 1 - i)
        index += smaller * factorial

    return index


def profile_to_tuple(rankings: List[List[int]]) -> Tuple[int, ...]:
    """
    Convert 5 rankings to a tuple of indices for hashing.
    """
    return tuple(ranking_to_index(r) for r in rankings)


def get_ranking_for_citizen(client: OpenAIClient, opinion: str, seed: int) -> List[int] | None:
    """
    Get a single citizen's ranking of the 4 statements.
    """
    prompt = RANKING_PROMPT_TEMPLATE.format(
        opinion=opinion.strip(),
        statement_a=FIXED_STATEMENTS[0].strip(),
        statement_b=FIXED_STATEMENTS[1].strip(),
        statement_c=FIXED_STATEMENTS[2].strip(),
        statement_d=FIXED_STATEMENTS[3].strip(),
    )

    response = client.sample_text(
        prompt,
        max_tokens=1024,
        temperature=0.8,
        seed=seed,
    )

    return parse_ranking(response)


# =============================================================================
# MAIN EXPERIMENT
# =============================================================================

def run_experiment(num_runs: int, model: str):
    """
    Run the preference space exploration experiment.
    """
    print()
    print("=" * 70)
    print("PREFERENCE SPACE EXPLORATION EXPERIMENT")
    print("=" * 70)
    print(f"Model:             {model}")
    print(f"Number of runs:    {num_runs}")
    print(f"Citizens:          {len(OPINIONS)}")
    print(f"Statements:        {len(FIXED_STATEMENTS)} (fixed)")
    print(f"Rankings/citizen:  4! = 24")
    print(f"Theoretical space: 24^5 = {THEORETICAL_SPACE:,} profiles")
    print("=" * 70)
    print()

    # Initialize client
    print("Initializing LLM client...")
    client = OpenAIClient(
        model_name=model,
        sleep_periodically=True,
        sleep_seconds=1.0,
        calls_between_sleeping=15,
    )
    print("Client ready.\n")

    # Storage
    all_profiles = []           # List of profile tuples
    all_raw_rankings = []       # List of raw rankings for inspection
    failed_runs = 0

    # Run experiment
    for run in range(num_runs):
        print(f"Run {run + 1}/{num_runs}...", end=" ", flush=True)

        # Generate base seed for this run
        base_seed = random.randint(1, 1000000)

        # Get ranking for each citizen
        rankings = []
        success = True

        for i, opinion in enumerate(OPINIONS):
            # Each citizen gets a different seed derived from base
            citizen_seed = base_seed + i * 1000

            ranking = get_ranking_for_citizen(client, opinion, citizen_seed)

            if ranking is None:
                print(f"FAILED (citizen {i+1})")
                success = False
                break

            rankings.append(ranking)

        if not success:
            failed_runs += 1
            continue

        # Convert to profile tuple
        profile = profile_to_tuple(rankings)
        all_profiles.append(profile)
        all_raw_rankings.append(rankings)

        # Show sacred value holder's ranking (citizen 2)
        c2_ranking = rankings[1]
        print(f"C2 ranked: {c2_ranking[0]}>{c2_ranking[1]}>{c2_ranking[2]}>{c2_ranking[3]}")

    # ==========================================================================
    # ANALYSIS
    # ==========================================================================

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)

    successful_runs = len(all_profiles)
    unique_profiles = len(set(all_profiles))

    print(f"Successful runs:      {successful_runs}/{num_runs}")
    print(f"Failed runs:          {failed_runs}")
    print(f"Unique profiles:      {unique_profiles}")
    print(f"Coverage ratio:       {unique_profiles / max(successful_runs, 1):.4f}")
    print(f"Space explored:       {unique_profiles / THEORETICAL_SPACE * 100:.8f}%")

    # Profile frequency
    profile_counts = Counter(all_profiles)

    print()
    print("Profile Distribution:")
    print("-" * 40)

    if profile_counts:
        for i, (profile, count) in enumerate(profile_counts.most_common(10)):
            pct = count / successful_runs * 100
            print(f"  {i+1}. {profile}: {count} times ({pct:.1f}%)")

    # Entropy calculation
    if all_profiles:
        probs = [c / successful_runs for c in profile_counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        max_entropy = math.log2(successful_runs) if successful_runs > 1 else 0
        theoretical_max = math.log2(THEORETICAL_SPACE)

        print()
        print("Entropy Analysis:")
        print("-" * 40)
        print(f"  Observed entropy:     {entropy:.4f} bits")
        print(f"  Max if all unique:    {max_entropy:.4f} bits")
        print(f"  Theoretical max:      {theoretical_max:.4f} bits")
        if max_entropy > 0:
            print(f"  Normalized entropy:   {entropy / max_entropy:.4f}")

    # Sacred value holder analysis
    print()
    print("Sacred Value Holder (Citizen 2) Analysis:")
    print("-" * 40)

    c2_rankings = [r[1] for r in all_raw_rankings]  # Index 1 = Citizen 2
    c2_first_choices = Counter(r[0] for r in c2_rankings)
    c2_last_choices = Counter(r[3] for r in c2_rankings)

    print("  First choice distribution:")
    for stmt, count in sorted(c2_first_choices.items()):
        letter = chr(64 + stmt)  # 1=A, 2=B, etc.
        print(f"    Statement {letter}: {count} times ({count/successful_runs*100:.1f}%)")

    print("  Last choice distribution:")
    for stmt, count in sorted(c2_last_choices.items()):
        letter = chr(64 + stmt)
        print(f"    Statement {letter}: {count} times ({count/successful_runs*100:.1f}%)")

    # Hypothesis conclusion
    print()
    print("=" * 70)
    print("CONCLUSION")
    print("=" * 70)

    coverage_ratio = unique_profiles / max(successful_runs, 1)

    if coverage_ratio > 0.9:
        print("H0 SUPPORTED: LLM explores preference space freely.")
        print("Each run produces a nearly unique preference profile.")
    elif coverage_ratio > 0.5:
        print("PARTIAL CONSTRAINT: LLM has moderate exploration freedom.")
        print("Some repetition of profiles, but not severe clustering.")
    else:
        print("H1 SUPPORTED: LLM is CONSTRAINED to a subspace.")
        print("High repetition of profiles - opinions anchor rankings.")
        print(f"Effective space: ~{unique_profiles} profiles, not {THEORETICAL_SPACE:,}")

    # Save results
    results = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "num_runs": num_runs,
        "successful_runs": successful_runs,
        "unique_profiles": unique_profiles,
        "coverage_ratio": coverage_ratio,
        "theoretical_space": THEORETICAL_SPACE,
        "profile_counts": {str(k): v for k, v in profile_counts.items()},
        "sacred_value_first_choices": dict(c2_first_choices),
        "sacred_value_last_choices": dict(c2_last_choices),
    }

    filename = f"preference_space_results_{model.replace('.', '_')}_{num_runs}runs.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print(f"Results saved to: {filename}")
    print("=" * 70)


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    # Parse command line arguments
    num_runs = DEFAULT_NUM_RUNS
    model = DEFAULT_MODEL

    if len(sys.argv) >= 2:
        try:
            num_runs = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number of runs: {sys.argv[1]}")
            sys.exit(1)

    if len(sys.argv) >= 3:
        model = sys.argv[2]

    print(f"\nPreference Space Exploration Test")
    print(f"Model: {model}, Runs: {num_runs}")
    print()

    run_experiment(num_runs, model)
