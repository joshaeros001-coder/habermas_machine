#!/usr/bin/env python3
"""
Sacred Value Deliberation Analysis Script
==========================================
Analyzes Habermas Machine outputs to quantify how deliberative AI
handles irreducible value conflicts (sacred values vs secular preferences).

Author: [Your Name]
Date: 2024
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# Scientific plot styling
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
})


@dataclass
class RoundResult:
    """Results from a single deliberation round."""
    round_name: str
    statements: List[str]
    rankings: Dict[int, List[int]]  # citizen_id -> ranking list
    social_ranking: List[int]
    winner_index: int
    winner_text: str
    citizen2_rank_of_winner: int  # 1=best, 4=worst


@dataclass
class ModelResult:
    """Complete results for a single model."""
    model_name: str
    opinion_round: Optional[RoundResult] = None
    critique_round: Optional[RoundResult] = None
    template_retries: int = 0

    @property
    def critique_improved_c2(self) -> Optional[bool]:
        """Did the Critique Round improve Citizen 2's satisfaction?"""
        if self.opinion_round and self.critique_round:
            return self.critique_round.citizen2_rank_of_winner < self.opinion_round.citizen2_rank_of_winner
        return None

    @property
    def c2_delta(self) -> Optional[int]:
        """Change in C2's ranking (negative = improvement)."""
        if self.opinion_round and self.critique_round:
            return self.critique_round.citizen2_rank_of_winner - self.opinion_round.citizen2_rank_of_winner
        return None


def parse_ranking_string(ranking_str: str) -> List[int]:
    """Parse '2 > 3 > 1 > 4' into [2, 3, 1, 4]."""
    parts = ranking_str.replace(' ', '').split('>')
    return [int(p) for p in parts]


def get_citizen2_rank_of_winner(rankings: Dict[int, List[int]], winner_idx: int) -> int:
    """
    Get Citizen 2's ranking of the winning statement.
    Returns 1 (best) to 4 (worst).
    """
    c2_ranking = rankings.get(2, rankings.get('2', []))
    if not c2_ranking:
        return -1

    # winner_idx is 1-indexed in the rankings
    try:
        position = c2_ranking.index(winner_idx) + 1  # Convert to 1-indexed position
        return position
    except ValueError:
        return -1


def analyze_statement_language(text: str) -> Dict[str, bool]:
    """Analyze key language patterns in winning statement."""
    text_lower = text.lower()
    return {
        'uses_conscience': 'conscience' in text_lower,
        'uses_spiritual_integrity': 'spiritual integrity' in text_lower,
        'uses_matter_of_faith': 'matter of faith' in text_lower or 'matters of faith' in text_lower,
        'uses_valid_legitimate': 'valid' in text_lower and 'legitimate' in text_lower,
        'uses_preference': 'preference' in text_lower and 'spiritual' in text_lower,
        'has_dedicated_section': bool(re.search(r'\*\*.*(?:spiritual|faith|religious).*\*\*', text_lower)),
        'bifurcated_framing': 'for a patient' in text_lower and 'guided by faith' in text_lower,
    }


def load_results_from_json(filepath: str) -> Optional[ModelResult]:
    """Load and parse a results JSON file."""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        model_name = data.get('model', Path(filepath).stem)
        result = ModelResult(model_name=model_name)

        # Parse opinion round
        if 'opinion_round' in data:
            op = data['opinion_round']
            rankings = {}
            for k, v in op.get('rankings', {}).items():
                citizen_id = int(k.replace('citizen_', ''))
                rankings[citizen_id] = parse_ranking_string(v) if isinstance(v, str) else v

            winner_idx = op.get('winner_index', 1)
            result.opinion_round = RoundResult(
                round_name='Opinion',
                statements=op.get('statements', []),
                rankings=rankings,
                social_ranking=parse_ranking_string(op.get('social_ranking', '')) if isinstance(op.get('social_ranking'), str) else op.get('social_ranking', []),
                winner_index=winner_idx,
                winner_text=op.get('winner_text', ''),
                citizen2_rank_of_winner=get_citizen2_rank_of_winner(rankings, winner_idx)
            )

        # Parse critique round
        if 'critique_round' in data:
            cr = data['critique_round']
            rankings = {}
            for k, v in cr.get('rankings', {}).items():
                citizen_id = int(k.replace('citizen_', ''))
                rankings[citizen_id] = parse_ranking_string(v) if isinstance(v, str) else v

            winner_idx = cr.get('winner_index', 1)
            result.critique_round = RoundResult(
                round_name='Critique',
                statements=cr.get('statements', []),
                rankings=rankings,
                social_ranking=parse_ranking_string(cr.get('social_ranking', '')) if isinstance(cr.get('social_ranking'), str) else cr.get('social_ranking', []),
                winner_index=winner_idx,
                winner_text=cr.get('winner_text', ''),
                citizen2_rank_of_winner=get_citizen2_rank_of_winner(rankings, winner_idx)
            )

        result.template_retries = data.get('template_retries', 0)
        return result

    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None


def load_results_from_manual_data() -> List[ModelResult]:
    """
    Load results from manually recorded experimental data.
    This captures the findings from our conversation analysis.
    """
    results = []

    # Data structure: (model_name, opinion_c2_rank, critique_c2_rank, template_retries)
    # c2_rank: 1=best (ranked winner 1st), 4=worst (ranked winner last)

    experimental_data = [
        # Model name, Opinion Round C2 rank, Critique Round C2 rank, Template retries
        ("gemini-2.0-flash", 3, None, 0),  # Estimated from earlier discussion
        ("gemini-2.0-flash-lite", 4, None, 0),  # Minimal acknowledgment
        ("gemini-2.0-flash-thinking-exp", 4, 1, 4),  # LAST -> FIRST (rescued!)
        ("gemini-2.5-pro", 1, 2, 0),  # FIRST -> 2nd (best overall)
        ("gemini-2.5-pro-preview-06-05", 3, 4, 0),  # 3rd -> LAST (degraded)
        ("gemma-3-27b-it", 3, None, 2),  # Middle tier
    ]

    for model_name, op_rank, cr_rank, retries in experimental_data:
        result = ModelResult(model_name=model_name, template_retries=retries)

        if op_rank is not None:
            result.opinion_round = RoundResult(
                round_name='Opinion',
                statements=[],
                rankings={},
                social_ranking=[],
                winner_index=0,
                winner_text='',
                citizen2_rank_of_winner=op_rank
            )

        if cr_rank is not None:
            result.critique_round = RoundResult(
                round_name='Critique',
                statements=[],
                rankings={},
                social_ranking=[],
                winner_index=0,
                winner_text='',
                citizen2_rank_of_winner=cr_rank
            )

        results.append(result)

    return results


# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def plot_sacred_value_satisfaction(results: List[ModelResult], output_dir: str = '.'):
    """
    Figure 1: Sacred Value Holder's Satisfaction with Winning Statement
    Shows how well the winning statement serves the minority position.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    models = []
    opinion_ranks = []
    critique_ranks = []

    for r in results:
        models.append(r.model_name.replace('gemini-', '').replace('-', '\n'))
        opinion_ranks.append(r.opinion_round.citizen2_rank_of_winner if r.opinion_round else None)
        critique_ranks.append(r.critique_round.citizen2_rank_of_winner if r.critique_round else None)

    x = np.arange(len(models))
    width = 0.35

    # Plot bars
    opinion_vals = [v if v else 0 for v in opinion_ranks]
    critique_vals = [v if v else 0 for v in critique_ranks]

    bars1 = ax.bar(x - width/2, opinion_vals, width, label='Opinion Round',
                   color='#2ecc71', edgecolor='black', linewidth=0.5)
    bars2 = ax.bar(x + width/2, critique_vals, width, label='Critique Round',
                   color='#3498db', edgecolor='black', linewidth=0.5)

    # Mark missing data
    for i, (op, cr) in enumerate(zip(opinion_ranks, critique_ranks)):
        if op is None:
            ax.annotate('N/A', (x[i] - width/2, 0.2), ha='center', fontsize=8, color='gray')
        if cr is None:
            ax.annotate('N/A', (x[i] + width/2, 0.2), ha='center', fontsize=8, color='gray')

    # Formatting
    ax.set_xlabel('Model')
    ax.set_ylabel('Citizen 2 Rank of Winner\n(1=Best, 4=Worst)')
    ax.set_title('Sacred Value Holder\'s Satisfaction with Deliberation Outcome')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4])
    ax.axhline(y=2.5, color='red', linestyle='--', alpha=0.5, label='Neutral threshold')
    ax.legend(loc='upper right')

    # Add value labels
    for bar in bars1:
        if bar.get_height() > 0:
            ax.annotate(f'{int(bar.get_height())}',
                       xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        if bar.get_height() > 0:
            ax.annotate(f'{int(bar.get_height())}',
                       xy=(bar.get_x() + bar.get_width()/2, bar.get_height()),
                       ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig1_sacred_value_satisfaction.png'))
    plt.savefig(os.path.join(output_dir, 'fig1_sacred_value_satisfaction.pdf'))
    print(f"Saved: fig1_sacred_value_satisfaction.png/pdf")
    plt.close()


def plot_deliberation_dynamics(results: List[ModelResult], output_dir: str = '.'):
    """
    Figure 2: Effect of Critique Round on Sacred Value Holder
    Slope chart showing whether deliberation helps or hurts minority positions.
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # Filter to models with both rounds
    complete_results = [r for r in results if r.opinion_round and r.critique_round]

    for i, r in enumerate(complete_results):
        op_rank = r.opinion_round.citizen2_rank_of_winner
        cr_rank = r.critique_round.citizen2_rank_of_winner

        # Color based on improvement
        if cr_rank < op_rank:
            color = '#27ae60'  # Green = improved
            label = 'Improved'
        elif cr_rank > op_rank:
            color = '#e74c3c'  # Red = degraded
            label = 'Degraded'
        else:
            color = '#95a5a6'  # Gray = no change
            label = 'No change'

        # Plot line
        ax.plot([0, 1], [op_rank, cr_rank], 'o-', color=color,
                linewidth=2, markersize=10, alpha=0.8)

        # Add model name
        model_short = r.model_name.replace('gemini-', '').replace('-exp', '')
        ax.annotate(model_short, (1.02, cr_rank), va='center', fontsize=9)

    # Formatting
    ax.set_xlim(-0.1, 1.3)
    ax.set_ylim(0.5, 4.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(['Opinion Round', 'Critique Round'])
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(['1st\n(Best)', '2nd', '3rd', '4th\n(Worst)'])
    ax.set_ylabel('Citizen 2\'s Ranking of Winning Statement')
    ax.set_title('Deliberation Dynamics: Does the Critique Round\nHelp or Hurt the Sacred Value Holder?')

    # Invert y-axis so "better" is higher
    ax.invert_yaxis()

    # Add legend
    improved_patch = mpatches.Patch(color='#27ae60', label='Improved (C2 better off)')
    degraded_patch = mpatches.Patch(color='#e74c3c', label='Degraded (C2 worse off)')
    ax.legend(handles=[improved_patch, degraded_patch], loc='lower right')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig2_deliberation_dynamics.png'))
    plt.savefig(os.path.join(output_dir, 'fig2_deliberation_dynamics.pdf'))
    print(f"Saved: fig2_deliberation_dynamics.png/pdf")
    plt.close()


def plot_technical_reliability(results: List[ModelResult], output_dir: str = '.'):
    """
    Figure 3: Template Compliance (Technical Reliability)
    Shows which models struggled with output format requirements.
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    models = [r.model_name.replace('gemini-', '').replace('-', '\n') for r in results]
    retries = [r.template_retries for r in results]

    colors = ['#e74c3c' if r > 2 else '#f39c12' if r > 0 else '#27ae60' for r in retries]

    bars = ax.barh(models, retries, color=colors, edgecolor='black', linewidth=0.5)

    ax.set_xlabel('Template Retries (INCORRECT_TEMPLATE errors)')
    ax.set_title('Technical Reliability: Template Compliance by Model')
    ax.set_xlim(0, max(retries) + 1 if max(retries) > 0 else 5)

    # Add value labels
    for bar, val in zip(bars, retries):
        ax.annotate(f'{val}', xy=(val + 0.1, bar.get_y() + bar.get_height()/2),
                   va='center', fontsize=10)

    # Add legend
    perfect = mpatches.Patch(color='#27ae60', label='Perfect (0 retries)')
    minor = mpatches.Patch(color='#f39c12', label='Minor issues (1-2 retries)')
    major = mpatches.Patch(color='#e74c3c', label='Major issues (3+ retries)')
    ax.legend(handles=[perfect, minor, major], loc='lower right')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig3_technical_reliability.png'))
    plt.savefig(os.path.join(output_dir, 'fig3_technical_reliability.pdf'))
    print(f"Saved: fig3_technical_reliability.png/pdf")
    plt.close()


def plot_model_comparison_matrix(results: List[ModelResult], output_dir: str = '.'):
    """
    Figure 4: Model Comparison Matrix
    Comprehensive view of all metrics across models.
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    # Prepare data
    models = [r.model_name.replace('gemini-', '') for r in results]

    metrics = {
        'Opinion Round\nC2 Rank': [r.opinion_round.citizen2_rank_of_winner if r.opinion_round else np.nan for r in results],
        'Critique Round\nC2 Rank': [r.critique_round.citizen2_rank_of_winner if r.critique_round else np.nan for r in results],
        'Template\nRetries': [r.template_retries for r in results],
        'C2 Delta\n(neg=better)': [r.c2_delta if r.c2_delta is not None else np.nan for r in results],
    }

    data = np.array(list(metrics.values()))

    # Normalize for color mapping (handle NaN)
    data_normalized = np.zeros_like(data, dtype=float)
    for i, row in enumerate(data):
        valid = ~np.isnan(row)
        if valid.any():
            row_min, row_max = np.nanmin(row), np.nanmax(row)
            if row_max > row_min:
                data_normalized[i] = (row - row_min) / (row_max - row_min)
            else:
                data_normalized[i] = 0.5

    # Create heatmap
    im = ax.imshow(data_normalized, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=1)

    # Add text annotations
    for i in range(len(metrics)):
        for j in range(len(models)):
            val = data[i, j]
            if not np.isnan(val):
                text = f'{int(val)}' if val == int(val) else f'{val:.1f}'
                ax.text(j, i, text, ha='center', va='center', fontsize=10, fontweight='bold')
            else:
                ax.text(j, i, 'N/A', ha='center', va='center', fontsize=9, color='gray')

    # Formatting
    ax.set_xticks(np.arange(len(models)))
    ax.set_yticks(np.arange(len(metrics)))
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.set_yticklabels(list(metrics.keys()))
    ax.set_title('Model Comparison Matrix: Sacred Value Deliberation Performance')

    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.6)
    cbar.set_label('Relative Performance\n(Green=Better, Red=Worse)')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'fig4_model_comparison_matrix.png'))
    plt.savefig(os.path.join(output_dir, 'fig4_model_comparison_matrix.pdf'))
    print(f"Saved: fig4_model_comparison_matrix.png/pdf")
    plt.close()


def generate_findings_summary(results: List[ModelResult], output_dir: str = '.'):
    """
    Generate a text summary of key findings for publication.
    """
    summary = []
    summary.append("=" * 70)
    summary.append("SACRED VALUE DELIBERATION: KEY FINDINGS")
    summary.append("=" * 70)
    summary.append("")

    # Finding 1: Best model for sacred value holder
    best_opinion = min([r for r in results if r.opinion_round],
                       key=lambda x: x.opinion_round.citizen2_rank_of_winner)
    summary.append("FINDING 1: Best Model for Sacred Value Representation")
    summary.append(f"  Model: {best_opinion.model_name}")
    summary.append(f"  Citizen 2 ranked winning statement: {best_opinion.opinion_round.citizen2_rank_of_winner} (1=best)")
    summary.append("")

    # Finding 2: Critique round effect
    improved = [r for r in results if r.critique_improved_c2 == True]
    degraded = [r for r in results if r.critique_improved_c2 == False]
    summary.append("FINDING 2: Effect of Critique Round on Sacred Value Holder")
    summary.append(f"  Models where C2 outcome IMPROVED: {[r.model_name for r in improved]}")
    summary.append(f"  Models where C2 outcome DEGRADED: {[r.model_name for r in degraded]}")
    summary.append("")

    # Finding 3: Technical reliability
    perfect_compliance = [r for r in results if r.template_retries == 0]
    summary.append("FINDING 3: Technical Reliability (Template Compliance)")
    summary.append(f"  Perfect compliance (0 retries): {[r.model_name for r in perfect_compliance]}")
    summary.append(f"  Highest retries: {max(results, key=lambda x: x.template_retries).model_name} ({max(r.template_retries for r in results)} retries)")
    summary.append("")

    # Finding 4: The rescue phenomenon
    rescued = [r for r in results if r.opinion_round and r.critique_round
               and r.opinion_round.citizen2_rank_of_winner == 4
               and r.critique_round.citizen2_rank_of_winner == 1]
    if rescued:
        summary.append("FINDING 4: The 'Rescue' Phenomenon")
        summary.append(f"  Models where Critique Round rescued C2 from worst to best:")
        for r in rescued:
            summary.append(f"    - {r.model_name}: 4th -> 1st")
    summary.append("")

    # Finding 5: Sophistication paradox
    summary.append("FINDING 5: The Sophistication Paradox")
    summary.append("  Observation: More sophisticated statement generation does not guarantee")
    summary.append("  better outcomes for minority positions. Explicit bifurcation of")
    summary.append("  'medical' vs 'faith' frameworks may allow secular majority to")
    summary.append("  identify and vote down sacred value-friendly statements.")
    summary.append("")

    summary.append("=" * 70)

    # Write to file
    summary_text = '\n'.join(summary)
    with open(os.path.join(output_dir, 'findings_summary.txt'), 'w') as f:
        f.write(summary_text)

    print(summary_text)
    print(f"\nSaved: findings_summary.txt")


def main():
    """Main analysis pipeline."""
    print("=" * 70)
    print("SACRED VALUE DELIBERATION ANALYSIS")
    print("=" * 70)
    print()

    # Create output directory
    output_dir = '/home/user/habermas_machine/analysis_output'
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    print()

    # Try to load from JSON files first
    json_dir = '/home/user/habermas_machine'
    json_files = list(Path(json_dir).glob('results_*.json'))

    if json_files:
        print(f"Found {len(json_files)} result files:")
        for f in json_files:
            print(f"  - {f.name}")
        results = []
        for f in json_files:
            r = load_results_from_json(str(f))
            if r:
                results.append(r)
    else:
        print("No JSON result files found. Using manually recorded experimental data.")
        results = load_results_from_manual_data()

    print(f"\nLoaded {len(results)} model results")
    print()

    # Generate all visualizations
    print("Generating visualizations...")
    print("-" * 40)

    plot_sacred_value_satisfaction(results, output_dir)
    plot_deliberation_dynamics(results, output_dir)
    plot_technical_reliability(results, output_dir)
    plot_model_comparison_matrix(results, output_dir)

    print("-" * 40)
    print()

    # Generate findings summary
    print("Generating findings summary...")
    print("-" * 40)
    generate_findings_summary(results, output_dir)

    print()
    print("=" * 70)
    print("ANALYSIS COMPLETE")
    print(f"All outputs saved to: {output_dir}")
    print("=" * 70)


if __name__ == '__main__':
    main()
