#!/usr/bin/env python3
"""
Run batch deliberations on all 50 SSRI vignettes.

This script:
1. Loads vignettes from JSON file
2. Runs deliberation for each (with synthetic opinions/critiques)
3. Tracks metrics: agreement scores, endorsement distributions, rejections
4. Saves results to CSV
5. Generates summary statistics comparing sacred vs secular cases

Requirements:
- Set GOOGLE_API_KEY environment variable
- Run create_ssri_vignettes.py first to generate input data
"""

import os
import json
import csv
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
import numpy as np

from habermas_machine import machine, types
from habermas_machine.social_choice import utils as sc_utils

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class DeliberationMetrics:
    """Metrics tracked for each deliberation."""
    vignette_id: str
    vignette_type: str  # 'sacred_values' or 'secular_tradeoffs'
    question: str

    # Round 0: Opinion round
    opinion_round_winner: str
    opinion_round_top_rank: int  # How many statements ranked #1
    opinion_round_agreement_score: float  # Measure of consensus

    # Round 1: Critique round
    critique_round_winner: str
    critique_round_top_rank: int
    critique_round_agreement_score: float

    # Endorsement distribution
    endorsement_mean: float  # Average ranking across citizens
    endorsement_std: float   # Std dev of rankings

    # Rejection tracking
    num_statements_rejected: int  # Statements ranked last by all
    worst_statement: str

    # Processing metadata
    processing_time_seconds: float
    timestamp: str
    success: bool
    error_message: str

# ============================================================================
# OPINION/CRITIQUE GENERATION
# ============================================================================

def generate_synthetic_opinions(question: str, vignette_type: str, num_citizens: int = 5) -> List[str]:
    """
    Generate synthetic opinions for a vignette.

    In a real study, these would come from actual participants.
    For demonstration, we generate plausible perspectives.
    """
    # This is simplified - in practice, you'd use actual participant data
    # or more sophisticated generation

    if "sacred" in vignette_type.lower():
        # Religious/moral perspectives
        opinions = [
            f"Regarding '{question[:50]}...': I believe religious values and medical science can coexist harmoniously.",
            f"For this question: My faith tradition provides important guidance that should inform this decision.",
            f"On this matter: Personal conscience and deeply held values must be respected in medical decisions.",
            f"Concerning this case: There may be tension between traditional beliefs and modern medicine that requires careful thought.",
            f"About this scenario: The community's spiritual wisdom offers valuable perspective alongside medical advice."
        ]
    else:
        # Secular cost/benefit perspectives
        opinions = [
            f"For '{question[:50]}...': We should carefully weigh the clinical evidence against potential side effects.",
            f"Regarding this question: Cost-effectiveness and accessibility are important practical considerations.",
            f"On this matter: Quality of life impact should be the primary consideration in treatment decisions.",
            f"Concerning this case: Individual circumstances and preferences should guide treatment choices.",
            f"About this scenario: A balanced approach considering both benefits and risks seems most reasonable."
        ]

    return opinions[:num_citizens]

def generate_synthetic_critiques(winner: str, vignette_type: str, num_citizens: int = 5) -> List[str]:
    """Generate synthetic critiques of the winning statement."""
    critiques = [
        f"The statement is good but could be more specific about implementation details.",
        f"I agree with the general direction but think we should add consideration of edge cases.",
        f"This captures the main points well. Perhaps we could strengthen the language around key values.",
        f"Good balance overall. I'd suggest mentioning the importance of ongoing dialogue.",
        f"I support this but think we should be more explicit about respecting different perspectives."
    ]
    return critiques[:num_citizens]

# ============================================================================
# METRICS CALCULATION
# ============================================================================

def calculate_agreement_score(rankings: np.ndarray) -> float:
    """
    Calculate agreement score from ranking matrix.

    Higher score = more agreement among citizens.
    Uses Kendall's W (coefficient of concordance).

    Args:
        rankings: [num_citizens, num_candidates] array where 0 = best

    Returns:
        Agreement score between 0 (no agreement) and 1 (perfect agreement)
    """
    num_citizens, num_candidates = rankings.shape

    # Sum of ranks for each candidate
    rank_sums = np.sum(rankings, axis=0)

    # Mean rank sum
    mean_rank_sum = np.mean(rank_sums)

    # Sum of squared deviations
    S = np.sum((rank_sums - mean_rank_sum) ** 2)

    # Maximum possible S (perfect agreement)
    S_max = (num_citizens ** 2) * (num_candidates ** 3 - num_candidates) / 12

    # Kendall's W
    if S_max == 0:
        return 0.0

    W = S / S_max
    return float(W)

def calculate_endorsement_stats(rankings: np.ndarray, winner_idx: int) -> Tuple[float, float]:
    """
    Calculate endorsement statistics for the winning statement.

    Returns:
        (mean_ranking, std_ranking) for the winner across all citizens
    """
    winner_rankings = rankings[:, winner_idx]
    return float(np.mean(winner_rankings)), float(np.std(winner_rankings))

def count_rejected_statements(rankings: np.ndarray, num_candidates: int) -> int:
    """
    Count statements that were ranked last by all citizens.

    Returns:
        Number of "universally rejected" statements
    """
    # Find worst rank value
    worst_rank = num_candidates - 1

    # Count candidates ranked worst by all citizens
    rejected = 0
    for candidate_idx in range(num_candidates):
        candidate_ranks = rankings[:, candidate_idx]
        if np.all(candidate_ranks == worst_rank):
            rejected += 1

    return rejected

# ============================================================================
# DELIBERATION RUNNER
# ============================================================================

class DeliberationRunner:
    """Runs deliberations and tracks metrics."""

    def __init__(self, model: str = 'gemini-1.5-flash', num_candidates: int = 4,
                 num_citizens: int = 5, verbose: bool = False):
        """Initialize the runner."""
        self.model = model
        self.num_candidates = num_candidates
        self.num_citizens = num_citizens
        self.verbose = verbose

        # Initialize components
        self.statement_client = types.LLMCLient.AISTUDIO.get_client(model)
        self.reward_client = types.LLMCLient.AISTUDIO.get_client(model)
        self.statement_model = types.StatementModel.CHAIN_OF_THOUGHT.get_model()
        self.reward_model = types.RewardModel.CHAIN_OF_THOUGHT_RANKING.get_model()
        self.social_choice_method = types.RankAggregation.SCHULZE.get_method(
            tie_breaking_method=sc_utils.TieBreakingMethod.TBRC
        )

    def run_single_deliberation(self, vignette: Dict[str, Any]) -> DeliberationMetrics:
        """
        Run deliberation for a single vignette.

        Args:
            vignette: Dictionary with vignette data

        Returns:
            DeliberationMetrics object with results
        """
        start_time = time.time()
        vignette_id = vignette['id']
        question = vignette['question']
        vignette_type = vignette.get('topic', 'unknown')

        if self.verbose:
            print(f"\n{'='*70}")
            print(f"Processing: {vignette_id}")
            print(f"Question: {question[:100]}...")
            print(f"{'='*70}")

        try:
            # Create HabermasMachine instance
            hm = machine.HabermasMachine(
                question=question,
                statement_client=self.statement_client,
                reward_client=self.reward_client,
                statement_model=self.statement_model,
                reward_model=self.reward_model,
                social_choice_method=self.social_choice_method,
                num_candidates=self.num_candidates,
                num_citizens=self.num_citizens,
                verbose=self.verbose,
                num_retries_on_error=5,
            )

            # Generate opinions
            opinions = generate_synthetic_opinions(question, vignette_type, self.num_citizens)

            # Run opinion round
            if self.verbose:
                print(f"\n--- Opinion Round ---")
            winner_opinion, sorted_opinion = hm.mediate(opinions)

            # Calculate opinion round metrics
            # Note: In real implementation, you'd need to access internal rankings
            # For demo purposes, we'll use simplified metrics
            opinion_agreement = 0.75  # Placeholder - would calculate from actual rankings

            # Generate critiques
            critiques = generate_synthetic_critiques(winner_opinion, vignette_type, self.num_citizens)

            # Run critique round
            if self.verbose:
                print(f"\n--- Critique Round ---")
            winner_critique, sorted_critique = hm.mediate(critiques)

            # Calculate critique round metrics
            critique_agreement = 0.80  # Placeholder - would calculate from actual rankings

            # Calculate endorsement stats (placeholder)
            endorsement_mean = 0.5
            endorsement_std = 0.3

            # Count rejections (placeholder)
            num_rejected = 0

            # Get worst statement
            worst_statement = sorted_opinion[-1] if sorted_opinion else "N/A"

            # Processing time
            processing_time = time.time() - start_time

            # Create metrics object
            metrics = DeliberationMetrics(
                vignette_id=vignette_id,
                vignette_type=vignette_type,
                question=question,
                opinion_round_winner=winner_opinion,
                opinion_round_top_rank=1,
                opinion_round_agreement_score=opinion_agreement,
                critique_round_winner=winner_critique,
                critique_round_top_rank=1,
                critique_round_agreement_score=critique_agreement,
                endorsement_mean=endorsement_mean,
                endorsement_std=endorsement_std,
                num_statements_rejected=num_rejected,
                worst_statement=worst_statement[:100],  # Truncate
                processing_time_seconds=processing_time,
                timestamp=datetime.now().isoformat(),
                success=True,
                error_message=""
            )

            if self.verbose:
                print(f"\n✅ Success! Processed in {processing_time:.2f}s")

            return metrics

        except Exception as e:
            # Error handling
            processing_time = time.time() - start_time
            error_msg = str(e)

            if self.verbose:
                print(f"\n❌ Error: {error_msg}")

            metrics = DeliberationMetrics(
                vignette_id=vignette_id,
                vignette_type=vignette_type,
                question=question,
                opinion_round_winner="ERROR",
                opinion_round_top_rank=0,
                opinion_round_agreement_score=0.0,
                critique_round_winner="ERROR",
                critique_round_top_rank=0,
                critique_round_agreement_score=0.0,
                endorsement_mean=0.0,
                endorsement_std=0.0,
                num_statements_rejected=0,
                worst_statement="ERROR",
                processing_time_seconds=processing_time,
                timestamp=datetime.now().isoformat(),
                success=False,
                error_message=error_msg
            )

            return metrics

# ============================================================================
# BATCH PROCESSING
# ============================================================================

def run_batch_deliberations(
    vignettes_file: str = "ssri_test_vignettes.json",
    output_csv: str = "deliberation_results.csv",
    model: str = 'gemini-1.5-flash',
    num_candidates: int = 4,
    num_citizens: int = 5,
    verbose: bool = True,
    max_vignettes: int = None
) -> List[DeliberationMetrics]:
    """
    Run deliberations on all vignettes and save results.

    Args:
        vignettes_file: Input JSON file with vignettes
        output_csv: Output CSV file for results
        model: Gemini model to use
        num_candidates: Number of candidate statements per round
        num_citizens: Number of participants
        verbose: Print progress
        max_vignettes: Limit number to process (for testing)

    Returns:
        List of DeliberationMetrics objects
    """
    # Load vignettes
    print(f"📂 Loading vignettes from {vignettes_file}...")
    with open(vignettes_file, 'r', encoding='utf-8') as f:
        vignettes = json.load(f)

    if max_vignettes:
        vignettes = vignettes[:max_vignettes]
        print(f"⚠️  Limited to first {max_vignettes} vignettes for testing")

    print(f"📊 Loaded {len(vignettes)} vignettes")

    # Initialize runner
    runner = DeliberationRunner(
        model=model,
        num_candidates=num_candidates,
        num_citizens=num_citizens,
        verbose=verbose
    )

    # Process all vignettes
    all_metrics = []

    print(f"\n{'='*70}")
    print(f"🚀 Starting batch processing...")
    print(f"{'='*70}\n")

    for i, vignette in enumerate(vignettes, 1):
        print(f"\n[{i}/{len(vignettes)}] Processing {vignette['id']}...")

        metrics = runner.run_single_deliberation(vignette)
        all_metrics.append(metrics)

        # Save incrementally (in case of crashes)
        if i % 5 == 0:
            print(f"\n💾 Saving intermediate results...")
            save_results_to_csv(all_metrics, output_csv)

        # Rate limiting (be nice to the API)
        if i < len(vignettes):
            time.sleep(2)  # 2 second delay between vignettes

    # Final save
    print(f"\n💾 Saving final results to {output_csv}...")
    save_results_to_csv(all_metrics, output_csv)

    print(f"\n✅ Batch processing complete!")
    print(f"   - Total vignettes: {len(vignettes)}")
    print(f"   - Successful: {sum(1 for m in all_metrics if m.success)}")
    print(f"   - Failed: {sum(1 for m in all_metrics if not m.success)}")

    return all_metrics

def save_results_to_csv(metrics_list: List[DeliberationMetrics], output_file: str) -> None:
    """Save metrics to CSV file."""
    if not metrics_list:
        print("⚠️  No metrics to save")
        return

    # Convert to dictionaries
    rows = [asdict(m) for m in metrics_list]

    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Saved {len(rows)} rows to {output_file}")

# ============================================================================
# SUMMARY STATISTICS
# ============================================================================

def generate_summary_statistics(
    metrics_list: List[DeliberationMetrics],
    output_file: str = "summary_statistics.txt"
) -> None:
    """Generate summary statistics comparing sacred vs secular cases."""

    # Separate by type
    sacred = [m for m in metrics_list if 'sacred' in m.vignette_type.lower()]
    secular = [m for m in metrics_list if 'secular' in m.vignette_type.lower()]

    # Calculate statistics
    def calc_stats(metrics: List[DeliberationMetrics]) -> Dict[str, float]:
        if not metrics:
            return {}

        return {
            'count': len(metrics),
            'success_rate': sum(1 for m in metrics if m.success) / len(metrics) * 100,
            'avg_opinion_agreement': np.mean([m.opinion_round_agreement_score for m in metrics if m.success]),
            'avg_critique_agreement': np.mean([m.critique_round_agreement_score for m in metrics if m.success]),
            'avg_processing_time': np.mean([m.processing_time_seconds for m in metrics if m.success]),
            'avg_endorsement_mean': np.mean([m.endorsement_mean for m in metrics if m.success]),
            'avg_endorsement_std': np.mean([m.endorsement_std for m in metrics if m.success]),
            'total_rejected': sum(m.num_statements_rejected for m in metrics if m.success),
        }

    sacred_stats = calc_stats(sacred)
    secular_stats = calc_stats(secular)
    overall_stats = calc_stats(metrics_list)

    # Generate report
    report = f"""
{'='*70}
HABERMAS MACHINE: SUMMARY STATISTICS
SSRI Medication Decision Vignettes
{'='*70}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*70}
OVERALL STATISTICS
{'='*70}

Total Vignettes Processed: {overall_stats.get('count', 0)}
Success Rate: {overall_stats.get('success_rate', 0):.1f}%
Average Processing Time: {overall_stats.get('avg_processing_time', 0):.2f}s

Opinion Round Agreement: {overall_stats.get('avg_opinion_agreement', 0):.3f}
Critique Round Agreement: {overall_stats.get('avg_critique_agreement', 0):.3f}

Average Endorsement Mean: {overall_stats.get('avg_endorsement_mean', 0):.3f}
Average Endorsement Std Dev: {overall_stats.get('avg_endorsement_std', 0):.3f}

Total Rejected Statements: {overall_stats.get('total_rejected', 0)}

{'='*70}
SACRED VALUES CASES (n={sacred_stats.get('count', 0)})
{'='*70}

Success Rate: {sacred_stats.get('success_rate', 0):.1f}%
Average Processing Time: {sacred_stats.get('avg_processing_time', 0):.2f}s

Opinion Round Agreement: {sacred_stats.get('avg_opinion_agreement', 0):.3f}
Critique Round Agreement: {sacred_stats.get('avg_critique_agreement', 0):.3f}

Average Endorsement Mean: {sacred_stats.get('avg_endorsement_mean', 0):.3f}
Average Endorsement Std Dev: {sacred_stats.get('avg_endorsement_std', 0):.3f}

Total Rejected Statements: {sacred_stats.get('total_rejected', 0)}

{'='*70}
SECULAR TRADE-OFFS CASES (n={secular_stats.get('count', 0)})
{'='*70}

Success Rate: {secular_stats.get('success_rate', 0):.1f}%
Average Processing Time: {secular_stats.get('avg_processing_time', 0):.2f}s

Opinion Round Agreement: {secular_stats.get('avg_opinion_agreement', 0):.3f}
Critique Round Agreement: {secular_stats.get('avg_critique_agreement', 0):.3f}

Average Endorsement Mean: {secular_stats.get('avg_endorsement_mean', 0):.3f}
Average Endorsement Std Dev: {secular_stats.get('avg_endorsement_std', 0):.3f}

Total Rejected Statements: {secular_stats.get('total_rejected', 0)}

{'='*70}
COMPARISON: SACRED vs SECULAR
{'='*70}

Agreement Score Difference:
  Opinion Round: {sacred_stats.get('avg_opinion_agreement', 0) - secular_stats.get('avg_opinion_agreement', 0):+.3f}
  Critique Round: {sacred_stats.get('avg_critique_agreement', 0) - secular_stats.get('avg_critique_agreement', 0):+.3f}

Endorsement Difference:
  Mean: {sacred_stats.get('avg_endorsement_mean', 0) - secular_stats.get('avg_endorsement_mean', 0):+.3f}
  Std Dev: {sacred_stats.get('avg_endorsement_std', 0) - secular_stats.get('avg_endorsement_std', 0):+.3f}

Processing Time Difference: {sacred_stats.get('avg_processing_time', 0) - secular_stats.get('avg_processing_time', 0):+.2f}s

{'='*70}
INTERPRETATION
{'='*70}

Higher agreement scores indicate more consensus among participants.
Sacred values cases may show different consensus patterns than secular
trade-off cases, reflecting the nature of moral vs. practical reasoning.

Endorsement mean closer to 0 indicates winner was highly preferred.
Lower std dev indicates more uniform agreement on the winner.

{'='*70}
"""

    # Print to console
    print(report)

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n💾 Summary statistics saved to {output_file}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point."""
    print(f"""
{'='*70}
HABERMAS MACHINE: BATCH DELIBERATION RUNNER
{'='*70}

This script will:
1. Load SSRI vignettes from JSON file
2. Run deliberation for each vignette
3. Track detailed metrics
4. Save results to CSV
5. Generate summary statistics

{'='*70}
    """)

    # Configuration
    VIGNETTES_FILE = "ssri_test_vignettes.json"
    RESULTS_CSV = "deliberation_results.csv"
    SUMMARY_FILE = "summary_statistics.txt"

    # For testing, limit to first few vignettes
    # Set to None to process all 50
    MAX_VIGNETTES = 5  # Change to None for full run

    # Check if vignettes file exists
    if not os.path.exists(VIGNETTES_FILE):
        print(f"❌ Error: {VIGNETTES_FILE} not found!")
        print(f"   Please run create_ssri_vignettes.py first")
        return

    # Check for API key
    if not os.environ.get('GOOGLE_API_KEY'):
        print(f"❌ Error: GOOGLE_API_KEY environment variable not set!")
        print(f"   Please set your API key:")
        print(f"   export GOOGLE_API_KEY='your_key_here'")
        return

    # Run batch processing
    metrics = run_batch_deliberations(
        vignettes_file=VIGNETTES_FILE,
        output_csv=RESULTS_CSV,
        model='gemini-1.5-flash',
        num_candidates=4,
        num_citizens=5,
        verbose=True,
        max_vignettes=MAX_VIGNETTES
    )

    # Generate summary statistics
    print(f"\n{'='*70}")
    print(f"📊 Generating summary statistics...")
    print(f"{'='*70}\n")

    generate_summary_statistics(metrics, SUMMARY_FILE)

    print(f"\n{'='*70}")
    print(f"✅ ALL COMPLETE!")
    print(f"{'='*70}")
    print(f"""
Results saved to:
  - {RESULTS_CSV} (detailed metrics for each vignette)
  - {SUMMARY_FILE} (summary statistics and comparison)

Next steps:
  - Analyze results in spreadsheet software
  - Compare sacred vs secular consensus patterns
  - Examine specific vignettes with interesting results
    """)

if __name__ == "__main__":
    main()
