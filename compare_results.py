#!/usr/bin/env python3
"""
Cross-Model Results Comparison
===============================

Compares preference space exploration results across different LLM providers.
This is the analysis tool for Phase 1 of the sacred value research.

WHAT IT DOES:
1. Reads JSON result files from preference_space_test.py
2. Compares entropy, coverage ratio, and sacred value rigidity across models
3. Generates summary tables and visualizations

USAGE:
    python compare_results.py

    Or with specific files:
    python compare_results.py results1.json results2.json results3.json

OUTPUT:
    - Text summary table to console
    - comparison_results.json with aggregated data
    - comparison_chart.png (if matplotlib available)

Author: Sacred Value Research Project
Date: February 2026
"""

import json
import glob
import sys
from typing import List, Dict, Any
from datetime import datetime


def load_results(filenames: List[str] = None) -> List[Dict[str, Any]]:
    """
    Load result JSON files.

    Args:
        filenames: List of files to load. If None, find all matching files.

    Returns:
        List of result dictionaries

    WHY THIS APPROACH?
    We look for files matching the naming pattern from preference_space_test.py:
    preference_space_results_*.json

    This lets you run experiments, then just call compare_results.py
    without specifying files - it finds them automatically.
    """
    if filenames:
        files = filenames
    else:
        # Find all result files in current directory
        files = glob.glob("preference_space_results_*.json")

    if not files:
        print("No result files found!")
        print("Run preference_space_test.py first to generate results.")
        return []

    results = []
    for f in sorted(files):
        try:
            with open(f, 'r') as fp:
                data = json.load(fp)
                data['_filename'] = f  # Track source file
                results.append(data)
                print(f"Loaded: {f}")
        except Exception as e:
            print(f"Error loading {f}: {e}")

    return results


def print_comparison_table(results: List[Dict[str, Any]]):
    """
    Print a formatted comparison table.

    This shows the key metrics side-by-side for easy comparison:
    - Provider/Model: Which LLM was tested
    - Runs: Number of experimental runs
    - Unique: Number of unique preference profiles observed
    - Coverage: unique / runs (higher = more exploration)
    - Entropy: Shannon entropy in bits (higher = more random)
    - Norm.Ent: Normalized entropy (0-1 scale)
    - C2 Rigid: Whether sacred value holder (C2) had 100% same first/last choice
    """
    if not results:
        return

    print()
    print("=" * 90)
    print("CROSS-MODEL COMPARISON: PREFERENCE SPACE EXPLORATION")
    print("=" * 90)
    print()

    # Header
    header = f"{'Provider':<12} {'Model':<30} {'Runs':>6} {'Unique':>7} {'Coverage':>9} {'Entropy':>8} {'Norm.Ent':>9} {'C2 Rigid':>9}"
    print(header)
    print("-" * 90)

    # Data rows
    for r in results:
        provider = r.get('provider', 'unknown')
        model = r.get('model', 'unknown')[:28]  # Truncate long model names
        runs = r.get('successful_runs', 0)
        unique = r.get('unique_profiles', 0)
        coverage = r.get('coverage_ratio', 0)
        entropy = r.get('entropy', 0)
        norm_ent = r.get('normalized_entropy', 0)

        # Check C2 rigidity (sacred value holder)
        # C2 is "rigid" if they always put the same statement first and last
        first_choices = r.get('sacred_value_first_choices', {})
        last_choices = r.get('sacred_value_last_choices', {})

        # Check if there's only one first choice and one last choice
        c2_rigid = len(first_choices) == 1 and len(last_choices) == 1
        rigid_str = "Yes" if c2_rigid else "No"

        row = f"{provider:<12} {model:<30} {runs:>6} {unique:>7} {coverage:>9.4f} {entropy:>8.4f} {norm_ent:>9.4f} {rigid_str:>9}"
        print(row)

    print("-" * 90)
    print()


def analyze_sacred_value_patterns(results: List[Dict[str, Any]]):
    """
    Analyze how each model handles the sacred value holder (C2).

    WHAT WE'RE LOOKING FOR:
    - Does C2 always rank the same statement first? (rigidity)
    - Does C2's preferred statement vary by model? (model-dependent)
    - Do different models "respect" the sacred value differently?

    WHY THIS MATTERS:
    Sacred values are defined as non-negotiable. If C2 represents a person
    with a sacred value (religious objection to SSRIs), their ranking
    SHOULD be highly consistent regardless of what other citizens say.

    If it's NOT consistent, it suggests the LLM is "persuading" C2 away
    from their sacred value - which is exactly what we're studying.
    """
    if not results:
        return

    print("=" * 60)
    print("SACRED VALUE HOLDER (C2) ANALYSIS")
    print("=" * 60)
    print()

    for r in results:
        provider = r.get('provider', 'unknown')
        model = r.get('model', 'unknown')
        runs = r.get('successful_runs', 0)

        print(f"Provider: {provider}, Model: {model}")
        print("-" * 40)

        # First choice distribution
        first_choices = r.get('sacred_value_first_choices', {})
        print("  C2's First Choice (most preferred statement):")
        for stmt_num, count in sorted(first_choices.items()):
            # Convert number to letter (1=A, 2=B, etc.)
            letter = chr(64 + int(stmt_num))
            pct = count / runs * 100 if runs > 0 else 0
            bar = "█" * int(pct / 5)  # Simple text bar chart
            print(f"    Statement {letter}: {count:3d}/{runs} ({pct:5.1f}%) {bar}")

        # Last choice distribution
        last_choices = r.get('sacred_value_last_choices', {})
        print("  C2's Last Choice (least preferred statement):")
        for stmt_num, count in sorted(last_choices.items()):
            letter = chr(64 + int(stmt_num))
            pct = count / runs * 100 if runs > 0 else 0
            bar = "█" * int(pct / 5)
            print(f"    Statement {letter}: {count:3d}/{runs} ({pct:5.1f}%) {bar}")

        # Rigidity assessment
        is_rigid = len(first_choices) == 1 and len(last_choices) == 1
        if is_rigid:
            first_letter = chr(64 + int(list(first_choices.keys())[0]))
            last_letter = chr(64 + int(list(last_choices.keys())[0]))
            print(f"  → C2 is RIGID: Always ranks {first_letter} first, {last_letter} last")
        else:
            print(f"  → C2 is VARIABLE: Rankings change across runs")

        print()


def compute_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute aggregate statistics across all results.

    Returns a dictionary with:
    - Number of models tested
    - Average entropy
    - Average coverage ratio
    - Models with rigid C2
    - Best/worst performers
    """
    if not results:
        return {}

    n = len(results)

    # Compute averages
    avg_entropy = sum(r.get('entropy', 0) for r in results) / n
    avg_coverage = sum(r.get('coverage_ratio', 0) for r in results) / n
    avg_norm_entropy = sum(r.get('normalized_entropy', 0) for r in results) / n

    # Count models with rigid C2
    rigid_count = sum(
        1 for r in results
        if len(r.get('sacred_value_first_choices', {})) == 1
        and len(r.get('sacred_value_last_choices', {})) == 1
    )

    # Find best/worst by entropy
    by_entropy = sorted(results, key=lambda r: r.get('entropy', 0))
    lowest_entropy = by_entropy[0] if by_entropy else None
    highest_entropy = by_entropy[-1] if by_entropy else None

    stats = {
        "num_models": n,
        "avg_entropy": avg_entropy,
        "avg_coverage": avg_coverage,
        "avg_normalized_entropy": avg_norm_entropy,
        "rigid_c2_count": rigid_count,
        "rigid_c2_percentage": rigid_count / n * 100 if n > 0 else 0,
        "lowest_entropy_model": f"{lowest_entropy.get('provider')}/{lowest_entropy.get('model')}" if lowest_entropy else None,
        "lowest_entropy_value": lowest_entropy.get('entropy') if lowest_entropy else None,
        "highest_entropy_model": f"{highest_entropy.get('provider')}/{highest_entropy.get('model')}" if highest_entropy else None,
        "highest_entropy_value": highest_entropy.get('entropy') if highest_entropy else None,
    }

    return stats


def print_summary(stats: Dict[str, Any]):
    """Print a summary of the aggregate statistics."""
    if not stats:
        return

    print("=" * 60)
    print("SUMMARY STATISTICS")
    print("=" * 60)
    print()
    print(f"  Models compared:         {stats['num_models']}")
    print(f"  Average entropy:         {stats['avg_entropy']:.4f} bits")
    print(f"  Average coverage:        {stats['avg_coverage']:.4f}")
    print(f"  Average norm. entropy:   {stats['avg_normalized_entropy']:.4f}")
    print()
    print(f"  C2 rigid in:             {stats['rigid_c2_count']}/{stats['num_models']} models ({stats['rigid_c2_percentage']:.1f}%)")
    print()
    print(f"  Lowest entropy:          {stats['lowest_entropy_model']} ({stats['lowest_entropy_value']:.4f} bits)")
    print(f"  Highest entropy:         {stats['highest_entropy_model']} ({stats['highest_entropy_value']:.4f} bits)")
    print()


def save_comparison(results: List[Dict[str, Any]], stats: Dict[str, Any]):
    """Save comparison results to JSON."""
    output = {
        "timestamp": datetime.now().isoformat(),
        "num_results": len(results),
        "statistics": stats,
        "results": [
            {
                "provider": r.get('provider'),
                "model": r.get('model'),
                "entropy": r.get('entropy'),
                "normalized_entropy": r.get('normalized_entropy'),
                "coverage_ratio": r.get('coverage_ratio'),
                "unique_profiles": r.get('unique_profiles'),
                "successful_runs": r.get('successful_runs'),
            }
            for r in results
        ]
    }

    with open("comparison_results.json", 'w') as f:
        json.dump(output, f, indent=2)

    print("Saved: comparison_results.json")


def main():
    """Main entry point."""
    print()
    print("=" * 60)
    print("  CROSS-MODEL COMPARISON TOOL")
    print("  Phase 1: Preference Space Exploration Analysis")
    print("=" * 60)
    print()

    # Load results
    if len(sys.argv) > 1:
        files = sys.argv[1:]
    else:
        files = None  # Auto-detect

    results = load_results(files)

    if not results:
        print("\nNo results to compare. Run preference_space_test.py first:")
        print("  python preference_space_test.py 20 openai")
        print("  python preference_space_test.py 20 anthropic")
        print("  python preference_space_test.py 20 google")
        return

    print(f"\nLoaded {len(results)} result file(s).")

    # Print comparison table
    print_comparison_table(results)

    # Analyze sacred value patterns
    analyze_sacred_value_patterns(results)

    # Compute and print statistics
    stats = compute_statistics(results)
    print_summary(stats)

    # Save comparison
    save_comparison(results, stats)

    print("=" * 60)
    print("  INTERPRETATION")
    print("=" * 60)
    print("""
    LOW ENTROPY (< 1.0 bits):
      The model is highly deterministic. Given the same opinions,
      it produces nearly identical rankings every time.
      → Strong opinion anchoring / RLHF bias

    HIGH ENTROPY (> 3.0 bits):
      The model explores more of the preference space.
      Rankings vary significantly between runs.
      → More "deliberative" behavior

    C2 RIGIDITY:
      If C2 (sacred value holder) is rigid (100% same ranking),
      the model correctly represents the non-negotiable nature
      of sacred values.

      If C2 varies, the model may be "persuading" them away
      from their sacred value - a key finding for the research.
    """)


if __name__ == "__main__":
    main()
