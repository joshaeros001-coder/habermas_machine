#!/usr/bin/env python3
"""
Sacred Value Deliberation Analysis
===================================
Analyzes how different Gemini/Gemma models handle sacred values (non-negotiable
religious positions) in the Habermas Machine deliberative democracy framework.

Key metric: Where does Citizen 2 (sacred value holder) rank the winning statement?
- Rank 1 = Best outcome (winner respects sacred value)
- Rank 4 = Worst outcome (winner ignores sacred value)

Data source: Terminal logs from experimental runs on 2025-12-17
"""

import matplotlib.pyplot as plt
import numpy as np

# =============================================================================
# ACCURATE DATA FROM TERMINAL LOGS (2025-12-17)
# =============================================================================
# Format: (model_name, opinion_round_c2_rank, critique_round_c2_rank, retries)

DATA = [
    ("gemini-2.0-flash", 4, 3, 3),
    ("gemini-2.0-flash-thinking-exp", 4, 1, 4),
    ("gemini-2.5-pro", 1, 2, 0),
    ("gemini-2.5-pro-preview-06-05", 3, 4, 0),
    ("gemma-3-27b-it", 1, 4, 0),
    ("gemini-3-pro-preview", 4, 4, 7),
]

# Short names for plotting
SHORT_NAMES = [
    "Flash 2.0",
    "Flash-Think",
    "Pro 2.5",
    "Pro-Preview",
    "Gemma 27B",
    "Pro 3",
]

def create_figures():
    """Generate all analysis figures."""

    # Extract data
    opinion_ranks = [d[1] for d in DATA]
    critique_ranks = [d[2] for d in DATA]
    retries = [d[3] for d in DATA]

    # Calculate change (negative = improvement, positive = degradation)
    changes = [c - o for o, c in zip(opinion_ranks, critique_ranks)]

    # Set up style
    plt.style.use('seaborn-v0_8-whitegrid')
    colors = {'opinion': '#2ecc71', 'critique': '#3498db', 'rescue': '#27ae60', 'degrade': '#e74c3c'}

    # =========================================================================
    # FIGURE 1: Opinion vs Critique Round Rankings
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(12, 6))

    x = np.arange(len(SHORT_NAMES))
    width = 0.35

    bars1 = ax1.bar(x - width/2, opinion_ranks, width, label='Opinion Round',
                    color=colors['opinion'], edgecolor='black', linewidth=1.2)
    bars2 = ax1.bar(x + width/2, critique_ranks, width, label='Critique Round',
                    color=colors['critique'], edgecolor='black', linewidth=1.2)

    ax1.set_ylabel('Citizen 2 Rank of Winner\n(1=Best, 4=Worst)', fontsize=12)
    ax1.set_xlabel('Model', fontsize=12)
    ax1.set_title('Sacred Value Holder (Citizen 2) Ranking of Winning Statement\nAcross Deliberation Rounds',
                  fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(SHORT_NAMES, rotation=15, ha='right')
    ax1.set_ylim(0, 5)
    ax1.set_yticks([1, 2, 3, 4])
    ax1.legend(loc='upper right')
    ax1.axhline(y=2.5, color='gray', linestyle='--', alpha=0.5, label='Neutral')

    # Add value labels
    for bar in bars1:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{int(bar.get_height())}', ha='center', va='bottom', fontweight='bold')
    for bar in bars2:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                f'{int(bar.get_height())}', ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    fig1.savefig('fig1_ranking_comparison.png', dpi=150, bbox_inches='tight')
    print("Saved: fig1_ranking_comparison.png")

    # =========================================================================
    # FIGURE 2: Critique Round Effect (Rescue vs Degradation)
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(10, 6))

    bar_colors = [colors['rescue'] if c < 0 else colors['degrade'] if c > 0 else 'gray' for c in changes]
    bars = ax2.bar(SHORT_NAMES, [-c for c in changes], color=bar_colors, edgecolor='black', linewidth=1.2)

    ax2.set_ylabel('Improvement in C2 Ranking\n(Positive = Better for Sacred Value)', fontsize=12)
    ax2.set_xlabel('Model', fontsize=12)
    ax2.set_title('Effect of Critique Round on Sacred Value Accommodation\n(Rescue vs Degradation)',
                  fontsize=14, fontweight='bold')
    ax2.axhline(y=0, color='black', linewidth=1)
    ax2.set_ylim(-4, 4)

    # Add annotations
    for i, (bar, change) in enumerate(zip(bars, changes)):
        if change < 0:
            label = f"RESCUE\n(+{-change})"
        elif change > 0:
            label = f"DEGRADE\n({change})"
        else:
            label = "NO\nCHANGE"
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (0.3 if bar.get_height() >= 0 else -0.5),
                label, ha='center', va='bottom' if bar.get_height() >= 0 else 'top',
                fontsize=9, fontweight='bold')

    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    fig2.savefig('fig2_critique_effect.png', dpi=150, bbox_inches='tight')
    print("Saved: fig2_critique_effect.png")

    # =========================================================================
    # FIGURE 3: Technical Reliability (Template Retries)
    # =========================================================================
    fig3, ax3 = plt.subplots(figsize=(10, 5))

    retry_colors = ['#2ecc71' if r == 0 else '#f39c12' if r < 5 else '#e74c3c' for r in retries]
    bars = ax3.bar(SHORT_NAMES, retries, color=retry_colors, edgecolor='black', linewidth=1.2)

    ax3.set_ylabel('Template Format Retries', fontsize=12)
    ax3.set_xlabel('Model', fontsize=12)
    ax3.set_title('Technical Reliability: Template Format Compliance\n(Lower = Better)',
                  fontsize=14, fontweight='bold')

    for bar in bars:
        if bar.get_height() > 0:
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                    f'{int(bar.get_height())}', ha='center', va='bottom', fontweight='bold')

    plt.xticks(rotation=15, ha='right')
    plt.tight_layout()
    fig3.savefig('fig3_technical_reliability.png', dpi=150, bbox_inches='tight')
    print("Saved: fig3_technical_reliability.png")

    # =========================================================================
    # FIGURE 4: Summary Heatmap
    # =========================================================================
    fig4, ax4 = plt.subplots(figsize=(10, 6))

    # Create matrix: rows = models, cols = metrics
    matrix = np.array([
        opinion_ranks,
        critique_ranks,
        [5 - abs(c) for c in changes],  # Stability (5 = no change, 1 = big change)
    ]).T

    im = ax4.imshow(matrix, cmap='RdYlGn_r', aspect='auto', vmin=1, vmax=4)

    ax4.set_xticks([0, 1, 2])
    ax4.set_xticklabels(['Opinion\nRound', 'Critique\nRound', 'Stability\n(inverted)'])
    ax4.set_yticks(range(len(SHORT_NAMES)))
    ax4.set_yticklabels(SHORT_NAMES)
    ax4.set_title('Sacred Value Accommodation Summary\n(Green=Good for C2, Red=Bad)',
                  fontsize=14, fontweight='bold')

    # Add text annotations
    for i in range(len(SHORT_NAMES)):
        for j in range(3):
            val = matrix[i, j]
            ax4.text(j, i, f'{val:.0f}', ha='center', va='center',
                    color='white' if val > 2.5 else 'black', fontweight='bold')

    plt.colorbar(im, ax=ax4, label='Rank (1=Best, 4=Worst)')
    plt.tight_layout()
    fig4.savefig('fig4_summary_heatmap.png', dpi=150, bbox_inches='tight')
    print("Saved: fig4_summary_heatmap.png")

    # =========================================================================
    # PRINT SUMMARY TABLE
    # =========================================================================
    print("\n" + "="*70)
    print("SACRED VALUE DELIBERATION ANALYSIS - SUMMARY")
    print("="*70)
    print(f"{'Model':<30} {'Opinion':<10} {'Critique':<10} {'Change':<10} {'Pattern'}")
    print("-"*70)

    for i, (name, op, cr, ret) in enumerate(DATA):
        change = cr - op
        if change < 0:
            pattern = "RESCUE" if change <= -2 else "Improved"
        elif change > 0:
            pattern = "DEGRADED" if change >= 2 else "Worsened"
        else:
            pattern = "Stable"
        print(f"{name:<30} {op:<10} {cr:<10} {change:+<10} {pattern}")

    print("-"*70)
    print("\nKey Findings:")
    print("  - Flash-Thinking shows strongest RESCUE effect (4->1)")
    print("  - Gemma-27B shows strongest DEGRADATION (1->4)")
    print("  - Pro 2.5 best initial accommodation (rank 1)")
    print("  - Pro 3 had reliability issues (7+ retries)")
    print("="*70)

    plt.show()
    print("\nAll figures saved. Ready for presentation!")

if __name__ == "__main__":
    create_figures()
