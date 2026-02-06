#!/usr/bin/env python3
"""
CRM Experimental Flow Diagram
==============================

Shows the experimental workflow for the sacred value and
preference space exploration experiments.

Usage:
    python crm_experiment_flow_diagram.py

Output:
    crm_experiment_flow.png
    crm_experiment_flow.pdf
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle, Polygon
import numpy as np

fig = plt.figure(figsize=(20, 12))
ax = fig.add_subplot(1, 1, 1)
ax.set_xlim(0, 100)
ax.set_ylim(0, 60)
ax.set_aspect('equal')
ax.axis('off')
ax.set_facecolor('#FAFAFA')

# Colors
C = {
    'phase1': '#E3F2FD',
    'phase1_b': '#1976D2',
    'phase2': '#E8F5E9',
    'phase2_b': '#388E3C',
    'phase3': '#FFF3E0',
    'phase3_b': '#F57C00',
    'sacred': '#F3E5F5',
    'sacred_b': '#7B1FA2',
    'result': '#FFEBEE',
    'result_b': '#D32F2F',
    'arrow': '#455A64',
}

# Title
ax.text(50, 58, 'CRM: Collective Rational Model — Experimental Workflow',
        fontsize=18, fontweight='bold', ha='center', va='center')
ax.text(50, 55, 'Testing Sacred Values in AI-Mediated Deliberation',
        fontsize=12, ha='center', va='center', color='#757575', style='italic')

# ============================================================================
# PHASE 1: Input Configuration
# ============================================================================

phase1_box = FancyBboxPatch((2, 35), 25, 17, boxstyle="round,pad=0.02,rounding_size=0.5",
                             facecolor=C['phase1'], edgecolor=C['phase1_b'], linewidth=2)
ax.add_patch(phase1_box)
ax.text(14.5, 50, 'PHASE 1: Input Configuration', fontsize=11, ha='center', va='center',
        fontweight='bold', color=C['phase1_b'])

# Question
q_box = FancyBboxPatch((4, 45), 21, 4, boxstyle="round,pad=0.01,rounding_size=0.2",
                        facecolor='white', edgecolor=C['phase1_b'], linewidth=1)
ax.add_patch(q_box)
ax.text(14.5, 47, 'Deliberation Question', fontsize=9, ha='center', va='center', fontweight='bold')
ax.text(14.5, 45.5, '"Should patient take SSRIs?"', fontsize=7, ha='center', va='center',
        color='#616161', style='italic')

# Citizens
ax.text(14.5, 43.5, '5 Simulated Citizens:', fontsize=9, ha='center', va='center', fontweight='bold')

citizens_data = [
    ('C1', 'Pragmatic', '#E3F2FD'),
    ('C2', 'Sacred Value ★', '#F3E5F5'),
    ('C3', 'Balanced', '#E3F2FD'),
    ('C4', 'Moderate', '#E3F2FD'),
    ('C5', 'Deferential', '#E3F2FD'),
]

for i, (label, desc, color) in enumerate(citizens_data):
    x = 4 + (i % 3) * 7.5
    y = 41 - (i // 3) * 3.5
    c_box = FancyBboxPatch((x, y - 1.2), 6.5, 2.4, boxstyle="round,pad=0.01,rounding_size=0.2",
                            facecolor=color, edgecolor=C['sacred_b'] if i == 1 else C['phase1_b'],
                            linewidth=1.5 if i == 1 else 1)
    ax.add_patch(c_box)
    ax.text(x + 3.25, y, f'{label}: {desc}', fontsize=6, ha='center', va='center',
            fontweight='bold' if i == 1 else 'normal')

# Arrow
ax.annotate('', xy=(32, 43.5), xytext=(27, 43.5),
            arrowprops=dict(arrowstyle='->', color=C['arrow'], lw=2.5))

# ============================================================================
# PHASE 2: CRM Processing
# ============================================================================

phase2_box = FancyBboxPatch((32, 30), 35, 22, boxstyle="round,pad=0.02,rounding_size=0.5",
                             facecolor=C['phase2'], edgecolor=C['phase2_b'], linewidth=2)
ax.add_patch(phase2_box)
ax.text(49.5, 50, 'PHASE 2: CRM Processing', fontsize=11, ha='center', va='center',
        fontweight='bold', color=C['phase2_b'])

# Step 2a: Statement Generation
s2a = FancyBboxPatch((34, 44), 14, 5, boxstyle="round,pad=0.01,rounding_size=0.3",
                      facecolor='white', edgecolor=C['phase2_b'], linewidth=1.5)
ax.add_patch(s2a)
ax.text(41, 47, '2a. Generate', fontsize=9, ha='center', va='center', fontweight='bold')
ax.text(41, 45, 'Consensus Statements', fontsize=7, ha='center', va='center', color='#616161')

# Arrow down
ax.annotate('', xy=(41, 43), xytext=(41, 44),
            arrowprops=dict(arrowstyle='->', color=C['arrow'], lw=1.5))

# Step 2b: Ranking
s2b = FancyBboxPatch((34, 37), 14, 5, boxstyle="round,pad=0.01,rounding_size=0.3",
                      facecolor='white', edgecolor=C['phase2_b'], linewidth=1.5)
ax.add_patch(s2b)
ax.text(41, 40, '2b. Rank Statements', fontsize=9, ha='center', va='center', fontweight='bold')
ax.text(41, 38, 'Per Citizen Opinion', fontsize=7, ha='center', va='center', color='#616161')

# Arrow down
ax.annotate('', xy=(41, 36), xytext=(41, 37),
            arrowprops=dict(arrowstyle='->', color=C['arrow'], lw=1.5))

# Step 2c: Voting
s2c = FancyBboxPatch((34, 31), 14, 4.5, boxstyle="round,pad=0.01,rounding_size=0.3",
                      facecolor='white', edgecolor=C['phase2_b'], linewidth=1.5)
ax.add_patch(s2c)
ax.text(41, 34, '2c. Schulze Voting', fontsize=9, ha='center', va='center', fontweight='bold')
ax.text(41, 32, 'Aggregate Rankings', fontsize=7, ha='center', va='center', color='#616161')

# LLM Selection Box
llm_box = FancyBboxPatch((50, 37), 15, 12, boxstyle="round,pad=0.01,rounding_size=0.3",
                          facecolor='white', edgecolor=C['phase2_b'], linewidth=1.5)
ax.add_patch(llm_box)
ax.text(57.5, 47.5, 'LLM Backend', fontsize=9, ha='center', va='center', fontweight='bold')

llms = [('GPT-5.2', '#4CAF50'), ('GPT-5.1', '#8BC34A'), ('Claude 3.5', '#03A9F4'),
        ('Gemini 2.0', '#FF9800'), ('o3', '#9C27B0'), ('GPT-4o', '#607D8B')]
for i, (llm, color) in enumerate(llms):
    x = 51.5 + (i % 2) * 6
    y = 45 - (i // 2) * 3
    chip = FancyBboxPatch((x, y - 1), 5.5, 2, boxstyle="round,pad=0.01,rounding_size=0.2",
                           facecolor=color, edgecolor='white', linewidth=0.5, alpha=0.8)
    ax.add_patch(chip)
    ax.text(x + 2.75, y, llm, fontsize=6, ha='center', va='center', fontweight='bold', color='white')

# Arrow to results
ax.annotate('', xy=(72, 43.5), xytext=(67, 43.5),
            arrowprops=dict(arrowstyle='->', color=C['arrow'], lw=2.5))

# ============================================================================
# PHASE 3: Analysis & Results
# ============================================================================

phase3_box = FancyBboxPatch((72, 30), 26, 22, boxstyle="round,pad=0.02,rounding_size=0.5",
                             facecolor=C['phase3'], edgecolor=C['phase3_b'], linewidth=2)
ax.add_patch(phase3_box)
ax.text(85, 50, 'PHASE 3: Analysis', fontsize=11, ha='center', va='center',
        fontweight='bold', color=C['phase3_b'])

metrics = [
    ('Winner Statement', 'Consensus output'),
    ('Preference Profiles', '5-tuple: (7,15,18,7,18)'),
    ('Shannon Entropy', '0.569 bits observed'),
    ('Coverage Ratio', '3/20 = 0.15'),
    ('Kendall τ Distance', 'Pairwise agreement'),
    ('C2 Isolation Index', 'Sacred value rigidity'),
]

for i, (metric, desc) in enumerate(metrics):
    y = 47 - i * 3
    m_box = FancyBboxPatch((74, y - 1.2), 22, 2.6, boxstyle="round,pad=0.01,rounding_size=0.2",
                            facecolor='white', edgecolor=C['phase3_b'], linewidth=1)
    ax.add_patch(m_box)
    ax.text(76, y, metric, fontsize=8, ha='left', va='center', fontweight='bold')
    ax.text(95, y, desc, fontsize=6, ha='right', va='center', color='#757575')

# ============================================================================
# KEY FINDINGS BOX (Bottom)
# ============================================================================

findings_box = FancyBboxPatch((2, 3), 96, 23, boxstyle="round,pad=0.02,rounding_size=0.5",
                               facecolor=C['result'], edgecolor=C['result_b'], linewidth=2)
ax.add_patch(findings_box)
ax.text(50, 24, 'KEY FINDINGS', fontsize=14, ha='center', va='center',
        fontweight='bold', color=C['result_b'])

# Three columns of findings
# Column 1: Preference Space
ax.text(18, 21, 'Preference Space Collapse', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(18, 18, 'Theoretical: 7,962,624 profiles', fontsize=8, ha='center', va='center')
ax.text(18, 16, 'Observed: 3 unique profiles', fontsize=8, ha='center', va='center')
ax.text(18, 14, 'Coverage: 0.00004%', fontsize=8, ha='center', va='center')
ax.text(18, 11, '→ Opinion anchoring\n   collapses space', fontsize=8, ha='center', va='center',
        color=C['result_b'], fontweight='bold')

# Divider
ax.plot([35, 35], [6, 22], color='#BDBDBD', linewidth=1, linestyle='--')

# Column 2: Sacred Value Rigidity
ax.text(50, 21, 'Sacred Value Rigidity', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(50, 18, 'C2 First Choice: C (100%)', fontsize=8, ha='center', va='center')
ax.text(50, 16, 'C2 Last Choice: A (100%)', fontsize=8, ha='center', va='center')
ax.text(50, 14, 'C2 Variance: 0%', fontsize=8, ha='center', va='center')
ax.text(50, 11, '→ Sacred values create\n   fixed points in rankings', fontsize=8, ha='center', va='center',
        color=C['result_b'], fontweight='bold')

# Divider
ax.plot([65, 65], [6, 22], color='#BDBDBD', linewidth=1, linestyle='--')

# Column 3: Entropy Analysis
ax.text(82, 21, 'Entropy Analysis', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(82, 18, 'Observed: 0.569 bits', fontsize=8, ha='center', va='center')
ax.text(82, 16, 'Maximum: 4.32 bits', fontsize=8, ha='center', va='center')
ax.text(82, 14, 'Normalized: 13%', fontsize=8, ha='center', va='center')
ax.text(82, 11, '→ System 87%\n   deterministic', fontsize=8, ha='center', va='center',
        color=C['result_b'], fontweight='bold')

# Bottom citation
ax.text(50, 5, 'Based on prompted Habermas Machine architecture (Tessler et al., 2024) • CRM uses chain-of-thought prompting instead of fine-tuned Chinchilla',
        fontsize=8, ha='center', va='center', color='#9E9E9E', style='italic')

# ============================================================================
# Save
# ============================================================================

plt.tight_layout()
plt.savefig('crm_experiment_flow.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('crm_experiment_flow.pdf', bbox_inches='tight', facecolor='white')
print("Saved: crm_experiment_flow.png")
print("Saved: crm_experiment_flow.pdf")

plt.show()
