#!/usr/bin/env python3
"""
CRM (Collective Rational Model) Architecture Diagram
=====================================================

Shows the prompted version with multiple LLM backends
used in this research.

Usage:
    python diagram_crm.py

Output:
    diagram_crm.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# Set up figure
fig, ax = plt.subplots(figsize=(16, 10))
ax.set_xlim(0, 100)
ax.set_ylim(0, 65)
ax.set_aspect('equal')
ax.axis('off')
ax.set_facecolor('#FAFAFA')

# Colors
COLORS = {
    'human': '#E8F5E9',
    'human_border': '#4CAF50',
    'ai': '#E3F2FD',
    'ai_border': '#1976D2',
    'output': '#FFF8E1',
    'output_border': '#FFC107',
    'sacred': '#F3E5F5',
    'sacred_border': '#7B1FA2',
    'arrow': '#455A64',
    'text': '#212121',
}

# Title
ax.text(50, 63, 'CRM: Collective Rational Model', fontsize=20, fontweight='bold',
        ha='center', va='center', color=COLORS['text'])
ax.text(50, 59, 'Our Adaptation for Sacred Value Research', fontsize=14,
        ha='center', va='center', color='#757575')
ax.text(50, 56, 'Prompted Version with Multiple LLM Backends', fontsize=11,
        ha='center', va='center', color='#9E9E9E', style='italic')

# ============================================================================
# Simulated Opinions Box (Left)
# ============================================================================
opinions_box = FancyBboxPatch((3, 22), 20, 28, boxstyle="round,pad=0.02,rounding_size=0.8",
                               facecolor=COLORS['human'], edgecolor=COLORS['human_border'], linewidth=3)
ax.add_patch(opinions_box)
ax.text(13, 47, 'Simulated\nCitizen Opinions', fontsize=12, ha='center', va='center', fontweight='bold')

# Individual citizens
citizens = [
    ('C1: Pragmatic', COLORS['human'], COLORS['human_border']),
    ('C2: Sacred Value', COLORS['sacred'], COLORS['sacred_border']),
    ('C3: Balanced', COLORS['human'], COLORS['human_border']),
    ('C4: Moderate', COLORS['human'], COLORS['human_border']),
    ('C5: Deferential', COLORS['human'], COLORS['human_border']),
]

for i, (label, fc, ec) in enumerate(citizens):
    y_pos = 42 - i * 4.5
    lw = 2.5 if i == 1 else 1.5
    c_box = FancyBboxPatch((5, y_pos - 1.5), 16, 3.5, boxstyle="round,pad=0.01,rounding_size=0.3",
                            facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(c_box)
    fw = 'bold' if i == 1 else 'normal'
    ax.text(13, y_pos, label, fontsize=9, ha='center', va='center', fontweight=fw)

# Arrow to CRM
ax.annotate('', xy=(28, 36), xytext=(23, 36),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=3))

# ============================================================================
# CRM Box (Center)
# ============================================================================
crm_box = FancyBboxPatch((28, 14), 40, 40, boxstyle="round,pad=0.02,rounding_size=0.8",
                          facecolor=COLORS['ai'], edgecolor=COLORS['ai_border'], linewidth=3)
ax.add_patch(crm_box)
ax.text(48, 50, 'COLLECTIVE RATIONAL MODEL', fontsize=13, ha='center', va='center',
         fontweight='bold', color=COLORS['ai_border'])
ax.text(48, 47, '(CRM)', fontsize=11, ha='center', va='center',
         fontweight='bold', color=COLORS['ai_border'])

# Statement Generation
gen_box = FancyBboxPatch((30, 38), 16, 7, boxstyle="round,pad=0.01,rounding_size=0.5",
                          facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(gen_box)
ax.text(38, 43, 'Statement\nGeneration', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(38, 39.5, '(Prompted)', fontsize=8, ha='center', va='center', color='#757575')

# Preference Ranking
rank_box = FancyBboxPatch((50, 38), 16, 7, boxstyle="round,pad=0.01,rounding_size=0.5",
                           facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(rank_box)
ax.text(58, 43, 'Preference\nRanking', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(58, 39.5, '(Prompted)', fontsize=8, ha='center', va='center', color='#757575')

# LLM Backend Box
llm_box = FancyBboxPatch((32, 27), 32, 9, boxstyle="round,pad=0.01,rounding_size=0.5",
                          facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(llm_box)
ax.text(48, 34, 'LLM Backend (Interchangeable)', fontsize=10, ha='center', va='center', fontweight='bold')

# LLM chips
llms = [
    ('GPT-5.x', '#4CAF50'),
    ('Claude 3.5', '#2196F3'),
    ('Gemini 2.0', '#FF9800'),
    ('o3', '#9C27B0'),
]
for i, (llm, color) in enumerate(llms):
    x_pos = 34 + i * 7.5
    chip = FancyBboxPatch((x_pos, 28), 6.5, 3, boxstyle="round,pad=0.01,rounding_size=0.3",
                           facecolor=color, edgecolor='white', linewidth=1, alpha=0.9)
    ax.add_patch(chip)
    ax.text(x_pos + 3.25, 29.5, llm, fontsize=7, ha='center', va='center',
            fontweight='bold', color='white')

# Schulze Voting
schulze_box = FancyBboxPatch((37, 16), 22, 7, boxstyle="round,pad=0.01,rounding_size=0.5",
                              facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(schulze_box)
ax.text(48, 19.5, 'Schulze Voting', fontsize=11, ha='center', va='center', fontweight='bold')

# Internal arrows
ax.annotate('', xy=(48, 37), xytext=(48, 23),
            arrowprops=dict(arrowstyle='->', color=COLORS['ai_border'], lw=1.5,
                           connectionstyle="arc3,rad=0"))

# Arrow to output
ax.annotate('', xy=(73, 36), xytext=(68, 36),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=3))

# ============================================================================
# Outputs Box (Right)
# ============================================================================
output_box = FancyBboxPatch((73, 22), 24, 28, boxstyle="round,pad=0.02,rounding_size=0.8",
                             facecolor=COLORS['output'], edgecolor=COLORS['output_border'], linewidth=3)
ax.add_patch(output_box)
ax.text(85, 47, 'Outputs &\nMetrics', fontsize=12, ha='center', va='center', fontweight='bold')

# Output items
outputs = [
    'Winner Statement',
    'Preference Profiles',
    'Shannon Entropy',
    'Coverage Ratio',
    'Kendall \u03C4 Distance',
    'C2 Isolation Index',
]
for i, out in enumerate(outputs):
    y_pos = 42 - i * 3.5
    ax.text(85, y_pos, f'\u2022 {out}', fontsize=9, ha='center', va='center', color='#616161')

# ============================================================================
# Key Differences Box (Bottom)
# ============================================================================
diff_box = FancyBboxPatch((15, 2), 70, 10, boxstyle="round,pad=0.02,rounding_size=0.5",
                           facecolor='#ECEFF1', edgecolor='#607D8B', linewidth=2)
ax.add_patch(diff_box)
ax.text(50, 9.5, 'Key Differences from Original Habermas Machine:', fontsize=11,
        ha='center', va='center', fontweight='bold')
ax.text(50, 5.5, 'Prompted (not fine-tuned)  |  Multiple LLM backends  |  Sacred value testing  |  Entropy & isolation analysis',
        fontsize=10, ha='center', va='center', color='#616161')

# ============================================================================
# Legend
# ============================================================================
legend_elements = [
    mpatches.Patch(facecolor=COLORS['human'], edgecolor=COLORS['human_border'],
                   linewidth=2, label='Simulated Input'),
    mpatches.Patch(facecolor=COLORS['sacred'], edgecolor=COLORS['sacred_border'],
                   linewidth=2, label='Sacred Value Holder (C2)'),
    mpatches.Patch(facecolor=COLORS['ai'], edgecolor=COLORS['ai_border'],
                   linewidth=2, label='CRM System'),
    mpatches.Patch(facecolor=COLORS['output'], edgecolor=COLORS['output_border'],
                   linewidth=2, label='Outputs'),
]

fig.legend(handles=legend_elements, loc='lower center', ncol=4, fontsize=10,
           frameon=True, fancybox=True, bbox_to_anchor=(0.5, -0.02))

# ============================================================================
# Save
# ============================================================================
plt.tight_layout()
plt.savefig('diagram_crm.png', dpi=300, bbox_inches='tight', facecolor='white')
print("Saved: diagram_crm.png")
plt.show()
