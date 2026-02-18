#!/usr/bin/env python3
"""
Preference Space Exploration Test
==================================

Tests whether LLMs explore the full 7.9M preference profile space
or are constrained to a subspace due to opinion anchoring and RLHF biases.

SUPPORTS MULTIPLE PROVIDERS:
  - OpenAI: GPT-5.x, GPT-4o, o3, o1
  - Anthropic: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
  - Google: Gemini 2.0 Flash, Gemini 2.0 Pro

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
  python preference_space_test.py [num_runs] [provider] [model]

  Examples:
    python preference_space_test.py                    # 20 runs, openai gpt-5.2
    python preference_space_test.py 50                 # 50 runs, openai gpt-5.2
    python preference_space_test.py 20 anthropic       # 20 runs, claude-3-5-sonnet
    python preference_space_test.py 20 google          # 20 runs, gemini-2.0-flash
    python preference_space_test.py 30 openai gpt-4o   # 30 runs, specific model

  For full help: python preference_space_test.py --help

Author: Sacred Value Research Project
Date: December 2025 (Updated February 2026 for multi-provider support)
"""

import sys
import json
import random
import math
from collections import Counter
from datetime import datetime
from typing import List, Tuple, Dict

# =============================================================================
# LLM CLIENT IMPORTS
# =============================================================================
# We use LAZY IMPORTS for the LLM clients - they're only loaded when needed.
# This avoids dependency errors if you only have some packages installed.
#
# We support three providers for cross-model comparison:
#   - OpenAI: GPT-4o, GPT-5.x, o3 (RLHF-trained, largest market share)
#   - Anthropic: Claude 3.5 Sonnet, Claude 3 Opus (Constitutional AI training)
#   - Google: Gemini 2.0 Flash, Gemini 2.0 Pro (multimodal, Google's approach)
#
# Each client implements the same interface (sample_text method) so we can
# swap them easily. This lets us test if sacred value handling differs by model.
# =============================================================================
# Clients are imported in create_client() function below


# =============================================================================
# CONFIGURATION
# =============================================================================

DEFAULT_NUM_RUNS = 100
DEFAULT_PROVIDER = "openai"  # Which provider to use by default
THEORETICAL_SPACE = 24 ** 5  # 7,962,624

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================
# Maps provider names to:
#   - "default_model": The recommended model for testing
#   - "env_var": Which environment variable holds the API key
#   - "client_class": Which client class to instantiate
#   - "models": List of available models (for reference)
#
# Why these models?
#   - OpenAI gpt-5.2: Latest GPT model, strong reasoning
#   - Anthropic claude-3-5-sonnet: Balance of capability and cost
#   - Google gemini-2.0-flash: Fast, good for large experiments
# =============================================================================
PROVIDER_CONFIG = {
    # =========================================================================
    # BATCH 1: OpenAI Models (run these first)
    # =========================================================================
    "openai": {
        "default_model": "gpt-4o",
        "env_var": "OPENAI_API_KEY",
        "models": [
            "gpt-4o",           # Current flagship (May 2024)
            "gpt-4o-mini",      # Smaller, faster, cheaper
            "gpt-4-turbo",      # Previous flagship
            "gpt-4",            # Original GPT-4
            "gpt-3.5-turbo",    # Older but widely used
            "o1",               # Reasoning model (slower, thinks longer)
            "o1-mini",          # Smaller reasoning model
        ],
    },
    # =========================================================================
    # BATCH 2: Anthropic Models (run these second)
    # =========================================================================
    "anthropic": {
        "default_model": "claude-3-5-sonnet-20241022",
        "env_var": "ANTHROPIC_API_KEY",
        "models": [
            "claude-3-5-sonnet-20241022",  # Latest Sonnet (Oct 2024)
            "claude-3-opus-20240229",       # Most capable Claude 3
            "claude-3-sonnet-20240229",     # Previous Sonnet
            "claude-3-haiku-20240307",      # Fastest/cheapest
            "claude-3-5-haiku-20241022",    # Latest Haiku
            "claude-sonnet-4-20250514",     # Claude 4 Sonnet (if available)
        ],
    },
    # =========================================================================
    # BATCH 3: Google Models (run these third)
    # =========================================================================
    "google": {
        "default_model": "gemini-2.0-flash",
        "env_var": "GOOGLE_API_KEY",
        "models": [
            "gemini-2.0-flash",      # Latest Flash (fast)
            "gemini-2.0-flash-lite", # Even lighter
            "gemini-1.5-flash",      # Previous Flash
            "gemini-1.5-pro",        # Previous Pro
            "gemini-1.0-pro",        # Original Gemini Pro
            "gemini-2.5-pro-preview-05-06",  # Latest Pro preview
        ],
    },
}

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
# CLIENT FACTORY
# =============================================================================

def create_client(provider: str, model: str):
    """
    Create an LLM client for the specified provider.

    This is a FACTORY FUNCTION - it returns different client objects based on
    the provider name. All clients have the same interface (sample_text method)
    so the rest of the code doesn't need to know which provider it's using.

    WHAT IS A FACTORY FUNCTION?
    Instead of hard-coding "use OpenAI" everywhere, we say "give me a client for
    provider X" and this function figures out which class to instantiate.

    WHY LAZY IMPORTS?
    We import the client class INSIDE this function rather than at the top of
    the file. This means if you only use OpenAI, you don't need the anthropic
    or google-generativeai packages installed.

    Args:
        provider: One of "openai", "anthropic", or "google"
        model: The specific model name (e.g., "gpt-5.2", "claude-3-5-sonnet-20241022")

    Returns:
        An LLM client with sample_text() method

    Raises:
        ValueError: If provider is not recognized
        KeyError: If the API key environment variable is not set
        ImportError: If the required package is not installed
    """
    import os

    # Validate provider
    if provider not in PROVIDER_CONFIG:
        valid = ", ".join(PROVIDER_CONFIG.keys())
        raise ValueError(f"Unknown provider '{provider}'. Valid options: {valid}")

    config = PROVIDER_CONFIG[provider]

    # Check API key exists
    env_var = config["env_var"]
    if env_var not in os.environ:
        raise KeyError(
            f"{env_var} not found in environment.\n"
            f"Run: export {env_var}='your-api-key'"
        )

    # Create the appropriate client
    # All clients share these parameters for rate limiting:
    #   - sleep_periodically: Pause between calls to avoid rate limits
    #   - sleep_seconds: How long to pause
    #   - calls_between_sleeping: Pause every N calls
    common_args = {
        "model_name": model,
        "sleep_periodically": True,
        "sleep_seconds": 1.0,
        "calls_between_sleeping": 15,
    }

    if provider == "openai":
        # LAZY IMPORT: Only load OpenAI client when needed
        from habermas_machine.llm_client.openai_client import OpenAIClient
        return OpenAIClient(**common_args)

    elif provider == "anthropic":
        # LAZY IMPORT: Only load Anthropic client when needed
        from habermas_machine.llm_client.anthropic_client import AnthropicClient
        # Anthropic needs longer pauses due to token-based rate limits
        common_args["sleep_seconds"] = 3.0
        common_args["calls_between_sleeping"] = 5
        return AnthropicClient(**common_args)

    elif provider == "google":
        # LAZY IMPORT: Only load Google client when needed
        from habermas_machine.llm_client.aistudio_client import AIStudioClient
        # Google also benefits from longer pauses
        common_args["sleep_seconds"] = 5.0
        common_args["calls_between_sleeping"] = 5
        return AIStudioClient(**common_args)

    # This shouldn't happen due to earlier validation
    raise ValueError(f"No client implementation for provider: {provider}")


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


def get_ranking_for_citizen(client, opinion: str, seed: int) -> List[int] | None:
    """
    Get a single citizen's ranking of the 4 statements.

    The client can be any LLM client (OpenAI, Anthropic, Google) since they all
    share the same sample_text() interface. This is called DUCK TYPING in Python:
    we don't care what TYPE the client is, only that it has a sample_text method.
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

def run_experiment(num_runs: int, provider: str, model: str):
    """
    Run the preference space exploration experiment.

    Args:
        num_runs: Number of experimental runs (default 20)
        provider: Which API provider - "openai", "anthropic", or "google"
        model: Specific model name (e.g., "gpt-5.2", "claude-3-5-sonnet-20241022")

    This function:
    1. Creates the appropriate LLM client via factory
    2. Runs 'num_runs' ranking experiments with random seeds
    3. Collects all preference profiles (5-citizen ranking tuples)
    4. Analyzes coverage, entropy, and sacred value holder behavior
    5. Saves results to JSON for later comparison
    """
    print()
    print("=" * 70)
    print("PREFERENCE SPACE EXPLORATION EXPERIMENT")
    print("=" * 70)
    print(f"Provider:          {provider}")
    print(f"Model:             {model}")
    print(f"Number of runs:    {num_runs}")
    print(f"Citizens:          {len(OPINIONS)}")
    print(f"Statements:        {len(FIXED_STATEMENTS)} (fixed)")
    print(f"Rankings/citizen:  4! = 24")
    print(f"Theoretical space: 24^5 = {THEORETICAL_SPACE:,} profiles")
    print("=" * 70)
    print()

    # Initialize client using the factory function
    # This creates the right client for the provider (OpenAI/Anthropic/Google)
    print("Initializing LLM client...")
    try:
        client = create_client(provider, model)
    except (ValueError, KeyError) as e:
        print(f"ERROR: {e}")
        return
    print(f"Client ready: {provider}/{model}\n")

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
    print("=" * 70)
    print("ALL PROFILE DISTRIBUTION (every profile shown)")
    print("=" * 70)
    print(f"Total runs: {successful_runs} | Unique profiles: {unique_profiles} | Collisions: {successful_runs - unique_profiles}")
    print("-" * 70)

    if profile_counts:
        # Show ALL profiles, not just top 10
        for i, (profile, count) in enumerate(profile_counts.most_common(), 1):
            pct = count / successful_runs * 100
            # Mark profiles that appeared more than once (collisions)
            collision_marker = " ← COLLISION" if count > 1 else ""
            print(f"  {i:3d}. {profile}: {count:3d} times ({pct:5.1f}%){collision_marker}")

    print("-" * 70)
    print(f"SUMMARY: {unique_profiles} unique profiles from {successful_runs} runs")
    print(f"         {successful_runs - unique_profiles} collisions (same profile repeated)")
    print("=" * 70)

    # Entropy calculation
    # Initialize these outside the if block so they're available for results
    entropy = 0.0
    max_entropy = 0.0
    normalized_entropy = 0.0
    theoretical_max = math.log2(THEORETICAL_SPACE)  # 22.93 bits

    if all_profiles:
        probs = [c / successful_runs for c in profile_counts.values()]
        entropy = -sum(p * math.log2(p) for p in probs if p > 0)
        max_entropy = math.log2(successful_runs) if successful_runs > 1 else 0
        if max_entropy > 0:
            normalized_entropy = entropy / max_entropy

        print()
        print("Entropy Analysis:")
        print("-" * 40)
        print(f"  Observed entropy:     {entropy:.4f} bits")
        print(f"  Max if all unique:    {max_entropy:.4f} bits")
        print(f"  Theoretical max:      {theoretical_max:.4f} bits")
        print(f"  Normalized entropy:   {normalized_entropy:.4f}")

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
    # Include provider and entropy metrics for cross-model comparison
    results = {
        "timestamp": datetime.now().isoformat(),
        "provider": provider,
        "model": model,
        "num_runs": num_runs,
        "successful_runs": successful_runs,
        "unique_profiles": unique_profiles,
        "coverage_ratio": coverage_ratio,
        "theoretical_space": THEORETICAL_SPACE,
        # Entropy metrics for cross-model comparison
        "entropy": entropy,                          # Observed Shannon entropy
        "max_entropy": max_entropy,                  # Max possible with N runs
        "normalized_entropy": normalized_entropy,   # entropy / max_entropy
        "theoretical_max_entropy": theoretical_max,  # log2(7.9M) = 22.93 bits
        # Profile and sacred value data
        "profile_counts": {str(k): v for k, v in profile_counts.items()},
        "sacred_value_first_choices": dict(c2_first_choices),
        "sacred_value_last_choices": dict(c2_last_choices),
    }

    # Filename includes provider for easy identification
    # Example: preference_space_results_openai_gpt-5_2_20runs.json
    safe_model = model.replace('.', '_').replace('-', '_')
    filename = f"preference_space_results_{provider}_{safe_model}_{num_runs}runs.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print(f"Results saved to: {filename}")
    print("=" * 70)


# =============================================================================
# ENTRY POINT
# =============================================================================

def print_usage():
    """Print help message showing how to use this script."""
    print("""
Preference Space Exploration Test
==================================

USAGE:
    python preference_space_test.py [num_runs] [provider] [model]

ARGUMENTS:
    num_runs   Number of experimental runs (default: 20)
    provider   API provider: openai, anthropic, or google (default: openai)
    model      Specific model name (default: provider's default model)

EXAMPLES:
    # Run 20 tests with OpenAI gpt-5.2 (default)
    python preference_space_test.py

    # Run 50 tests with OpenAI gpt-5.2
    python preference_space_test.py 50

    # Run 20 tests with Anthropic's default model (Claude 3.5 Sonnet)
    python preference_space_test.py 20 anthropic

    # Run 30 tests with Google Gemini 2.0 Flash
    python preference_space_test.py 30 google

    # Run 20 tests with a specific model
    python preference_space_test.py 20 openai gpt-4o
    python preference_space_test.py 20 anthropic claude-3-opus-20240229
    python preference_space_test.py 20 google gemini-2.0-pro

PROVIDERS AND DEFAULT MODELS:
    openai    → gpt-5.2
    anthropic → claude-3-5-sonnet-20241022
    google    → gemini-2.0-flash

ENVIRONMENT VARIABLES REQUIRED:
    OPENAI_API_KEY      For openai provider
    ANTHROPIC_API_KEY   For anthropic provider
    GOOGLE_API_KEY      For google provider
""")


def print_models():
    """Print all available models organized by provider."""
    print("""
============================================================
  AVAILABLE MODELS BY PROVIDER
============================================================

BATCH 1: OpenAI (run first)
---------------------------""")
    for i, m in enumerate(PROVIDER_CONFIG["openai"]["models"], 1):
        print(f"  {i}. {m}")

    print("""
BATCH 2: Anthropic (run second)
-------------------------------""")
    for i, m in enumerate(PROVIDER_CONFIG["anthropic"]["models"], 1):
        print(f"  {i}. {m}")

    print("""
BATCH 3: Google (run third)
---------------------------""")
    for i, m in enumerate(PROVIDER_CONFIG["google"]["models"], 1):
        print(f"  {i}. {m}")

    print("""
============================================================
  HOW TO RUN
============================================================

Step 1: Export your API key
  export OPENAI_API_KEY='your-key'

Step 2: Run each model (20 runs each)
  python preference_space_test.py 20 openai gpt-4o
  python preference_space_test.py 20 openai gpt-4o-mini
  ... (continue for each model)

Step 3: Compare results
  python compare_results.py
""")


if __name__ == "__main__":
    # Check for help flag
    if len(sys.argv) >= 2 and sys.argv[1] in ["-h", "--help", "help"]:
        print_usage()
        sys.exit(0)

    # Check for list flag
    if len(sys.argv) >= 2 and sys.argv[1] in ["-l", "--list", "list"]:
        print_models()
        sys.exit(0)

    # Parse command line arguments
    # Defaults
    num_runs = DEFAULT_NUM_RUNS
    provider = DEFAULT_PROVIDER
    model = None  # Will use provider's default if not specified

    # Parse num_runs (first positional argument)
    if len(sys.argv) >= 2:
        try:
            num_runs = int(sys.argv[1])
        except ValueError:
            print(f"ERROR: Invalid number of runs: '{sys.argv[1]}'")
            print("Run with --help for usage information.")
            sys.exit(1)

    # Parse provider (second positional argument)
    if len(sys.argv) >= 3:
        provider = sys.argv[2].lower()
        if provider not in PROVIDER_CONFIG:
            valid = ", ".join(PROVIDER_CONFIG.keys())
            print(f"ERROR: Unknown provider '{provider}'")
            print(f"Valid providers: {valid}")
            sys.exit(1)

    # Parse model (third positional argument, or use provider's default)
    if len(sys.argv) >= 4:
        model = sys.argv[3]
    else:
        # Use the provider's default model
        model = PROVIDER_CONFIG[provider]["default_model"]

    # Print what we're about to do
    print()
    print("=" * 60)
    print("  PREFERENCE SPACE EXPLORATION TEST")
    print("=" * 60)
    print(f"  Provider: {provider}")
    print(f"  Model:    {model}")
    print(f"  Runs:     {num_runs}")
    print("=" * 60)
    print()

    # Run the experiment
    run_experiment(num_runs, provider, model)
