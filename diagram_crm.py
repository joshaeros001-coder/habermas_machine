#!/usr/bin/env python3
"""
CRM (Collective Rational Model) Architecture Diagram
=====================================================

Shows the prompted version with multiple LLM backends
used in this research. Two-round deliberation with critiques.

Usage:
    python diagram_crm.py

Output:
    diagram_crm.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# Set up figure
fig, ax = plt.subplots(figsize=(18, 12))
ax.set_xlim(0, 110)
ax.set_ylim(0, 75)
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
ax.text(55, 73, 'CRM: Collective Rational Model', fontsize=20, fontweight='bold',
        ha='center', va='center', color=COLORS['text'])
ax.text(55, 69, 'Our Adaptation for Sacred Value Research', fontsize=14,
        ha='center', va='center', color='#757575')
ax.text(55, 66, 'Prompted Version with Multiple LLM Backends', fontsize=11,
        ha='center', va='center', color='#9E9E9E', style='italic')

# ============================================================================
# Simulated Opinions Box (Left)
# ============================================================================
opinions_box = FancyBboxPatch((3, 28), 20, 32, boxstyle="round,pad=0.02,rounding_size=0.8",
                               facecolor=COLORS['human'], edgecolor=COLORS['human_border'], linewidth=3)
ax.add_patch(opinions_box)
ax.text(13, 57, 'Simulated\nCitizen Opinions', fontsize=12, ha='center', va='center', fontweight='bold')

# Individual citizens
citizens = [
    ('C1: Pragmatic', COLORS['human'], COLORS['human_border']),
    ('C2: Sacred Value', COLORS['sacred'], COLORS['sacred_border']),
    ('C3: Balanced', COLORS['human'], COLORS['human_border']),
    ('C4: Moderate', COLORS['human'], COLORS['human_border']),
    ('C5: Deferential', COLORS['human'], COLORS['human_border']),
]

for i, (label, fc, ec) in enumerate(citizens):
    y_pos = 52 - i * 4.5
    lw = 2.5 if i == 1 else 1.5
    c_box = FancyBboxPatch((5, y_pos - 1.5), 16, 3.5, boxstyle="round,pad=0.01,rounding_size=0.3",
                            facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(c_box)
    fw = 'bold' if i == 1 else 'normal'
    ax.text(13, y_pos, label, fontsize=9, ha='center', va='center', fontweight=fw)

# Arrow to CRM
ax.annotate('', xy=(28, 44), xytext=(23, 44),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=3))

# ============================================================================
# CRM Box (Center)
# ============================================================================
crm_box = FancyBboxPatch((28, 18), 48, 44, boxstyle="round,pad=0.02,rounding_size=0.8",
                          facecolor=COLORS['ai'], edgecolor=COLORS['ai_border'], linewidth=3)
ax.add_patch(crm_box)
ax.text(52, 58, 'COLLECTIVE RATIONAL MODEL (CRM)', fontsize=13, ha='center', va='center',
         fontweight='bold', color=COLORS['ai_border'])

# ----- Row 1: Statement Generation & Preference Ranking -----
gen_box = FancyBboxPatch((31, 49), 16, 7, boxstyle="round,pad=0.01,rounding_size=0.5",
                          facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(gen_box)
ax.text(39, 54, 'Statement\nGeneration', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(39, 50.5, '(Prompted)', fontsize=8, ha='center', va='center', color='#757575')

# Arrow: Generation to Ranking
ax.annotate('', xy=(49, 52.5), xytext=(47, 52.5),
            arrowprops=dict(arrowstyle='->', color=COLORS['ai_border'], lw=2))

rank_box = FancyBboxPatch((49, 49), 16, 7, boxstyle="round,pad=0.01,rounding_size=0.5",
                           facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(rank_box)
ax.text(57, 54, 'Preference\nRanking', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(57, 50.5, '(Prompted)', fontsize=8, ha='center', va='center', color='#757575')

# Arrow: Ranking to Schulze
ax.annotate('', xy=(67, 52.5), xytext=(65, 52.5),
            arrowprops=dict(arrowstyle='->', color=COLORS['ai_border'], lw=2))

schulze_box = FancyBboxPatch((67, 49), 7, 7, boxstyle="round,pad=0.01,rounding_size=0.5",
                              facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(schulze_box)
ax.text(70.5, 52.5, 'Schulze\nVote', fontsize=8, ha='center', va='center', fontweight='bold')

# ----- Row 2: LLM Backend -----
llm_box = FancyBboxPatch((31, 38), 43, 9, boxstyle="round,pad=0.01,rounding_size=0.5",
                          facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(llm_box)
ax.text(52.5, 45, 'LLM Backend (Interchangeable)', fontsize=10, ha='center', va='center', fontweight='bold')

# LLM chips
llms = [
    ('GPT-5.x', '#4CAF50'),
    ('Claude 3.5', '#2196F3'),
    ('Gemini 2.0', '#FF9800'),
    ('o3', '#9C27B0'),
]
for i, (llm, color) in enumerate(llms):
    x_pos = 33 + i * 10
    chip = FancyBboxPatch((x_pos, 39), 8, 3, boxstyle="round,pad=0.01,rounding_size=0.3",
                           facecolor=color, edgecolor='white', linewidth=1, alpha=0.9)
    ax.add_patch(chip)
    ax.text(x_pos + 4, 40.5, llm, fontsize=7, ha='center', va='center',
            fontweight='bold', color='white')

# ----- Row 3: Critique Integration -----
critique_box = FancyBboxPatch((31, 28), 22, 7, boxstyle="round,pad=0.01,rounding_size=0.5",
                               facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(critique_box)
ax.text(42, 33, 'Critique Integration', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(42, 29.5, 'Opinions + Winner + Critiques', fontsize=7, ha='center', va='center', color='#757575')

# Arrow: down from Schulze to Critique
ax.annotate('', xy=(52, 35), xytext=(70.5, 49),
            arrowprops=dict(arrowstyle='->', color=COLORS['ai_border'], lw=1.5,
                           connectionstyle="angle,angleA=0,angleB=90"))

# ----- Row 4: Final Output Selection -----
final_box = FancyBboxPatch((55, 28), 18, 7, boxstyle="round,pad=0.01,rounding_size=0.5",
                            facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(final_box)
ax.text(64, 33, 'Final Statement\nSelection', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(64, 29.5, '(Revised Winner)', fontsize=7, ha='center', va='center', color='#757575')

# Arrow: Critique to Final
ax.annotate('', xy=(55, 31.5), xytext=(53, 31.5),
            arrowprops=dict(arrowstyle='->', color=COLORS['ai_border'], lw=2))

# ----- Row 5: Round labels -----
ax.text(52, 21, 'Round 1: Generate → Rank → Vote → Initial Winner', fontsize=9, ha='center', va='center',
        color='#757575', style='italic')
ax.text(52, 18.5, 'Round 2: Integrate Critiques → Revise → Rank → Vote → Final Winner', fontsize=9, ha='center', va='center',
        color='#757575', style='italic')

# ============================================================================
# Arrow to output
# ============================================================================
ax.annotate('', xy=(81, 44), xytext=(76, 44),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=3))

# ============================================================================
# Outputs Box (Right)
# ============================================================================
output_box = FancyBboxPatch((81, 28), 24, 32, boxstyle="round,pad=0.02,rounding_size=0.8",
                             facecolor=COLORS['output'], edgecolor=COLORS['output_border'], linewidth=3)
ax.add_patch(output_box)
ax.text(93, 57, 'Outputs &\nMetrics', fontsize=12, ha='center', va='center', fontweight='bold')

# Output items
outputs = [
    'Winner Statement',
    'Preference Profiles',
    'Shannon Entropy',
    'Coverage Ratio',
    'Kendall τ Distance',
    'C2 Isolation Index',
]
for i, out in enumerate(outputs):
    y_pos = 52 - i * 3.5
    ax.text(93, y_pos, f'• {out}', fontsize=9, ha='center', va='center', color='#616161')

# ============================================================================
# Key Differences Box (Bottom)
# ============================================================================
diff_box = FancyBboxPatch((10, 3), 90, 12, boxstyle="round,pad=0.02,rounding_size=0.5",
                           facecolor='#ECEFF1', edgecolor='#607D8B', linewidth=2)
ax.add_patch(diff_box)
ax.text(55, 12, 'Key Differences from Original Habermas Machine:', fontsize=11,
        ha='center', va='center', fontweight='bold')
ax.text(55, 8, 'Prompted LLMs (not fine-tuned Chinchilla)  |  Multiple interchangeable backends  |  Sacred value testing  |  Entropy & isolation analysis',
        fontsize=10, ha='center', va='center', color='#616161')
ax.text(55, 5, 'Same deliberation protocol: Opinions → Statements → Rankings → Schulze Vote → Critiques → Revised Winner',
        fontsize=9, ha='center', va='center', color='#9E9E9E', style='italic')

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
           frameon=True, fancybox=True, bbox_to_anchor=(0.5, -0.01))

# ============================================================================
# Save
# ============================================================================
plt.tight_layout()
plt.savefig('diagram_crm.png', dpi=300, bbox_inches='tight', facecolor='white')
print("Saved: diagram_crm.png")
plt.show()
