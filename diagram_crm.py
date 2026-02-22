#!/usr/bin/env python3
"""
CRM (Collective Rational Model) Architecture Diagram
=====================================================

Shows the prompted version with multiple LLM backends.
Two-round deliberation: Winner₁ sent to citizens for critique,
critiques fed back into CRM for Round 2.

Usage:
    python diagram_crm.py

Output:
    diagram_crm.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# Set up figure
fig, ax = plt.subplots(figsize=(18, 14))
ax.set_xlim(0, 110)
ax.set_ylim(0, 80)
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
    'feedback': '#FF5722',
    'text': '#212121',
}

# Title
ax.text(55, 78, 'CRM: Collective Rational Model', fontsize=20, fontweight='bold',
        ha='center', va='center', color=COLORS['text'])


# ============================================================================
# Simulated Opinions Box (Left)
# ============================================================================
opinions_box = FancyBboxPatch((3, 30), 20, 34, boxstyle="round,pad=0.02,rounding_size=0.8",
                               facecolor=COLORS['human'], edgecolor=COLORS['human_border'], linewidth=3)
ax.add_patch(opinions_box)
ax.text(13, 61, 'Simulated\nCitizen Opinions', fontsize=12, ha='center', va='center', fontweight='bold')

# Individual citizens
citizens = [
    ('C1: Pragmatic', COLORS['human'], COLORS['human_border']),
    ('C2: Sacred Value', COLORS['sacred'], COLORS['sacred_border']),
    ('C3: Balanced', COLORS['human'], COLORS['human_border']),
    ('C4: Moderate', COLORS['human'], COLORS['human_border']),
    ('C5: Deferential', COLORS['human'], COLORS['human_border']),
]

for i, (label, fc, ec) in enumerate(citizens):
    y_pos = 56 - i * 4.5
    lw = 2.5 if i == 1 else 1.5
    c_box = FancyBboxPatch((5, y_pos - 1.5), 16, 3.5, boxstyle="round,pad=0.01,rounding_size=0.3",
                            facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(c_box)
    fw = 'bold' if i == 1 else 'normal'
    ax.text(13, y_pos, label, fontsize=9, ha='center', va='center', fontweight=fw)

# Arrow: Opinions to CRM
ax.annotate('', xy=(28, 52), xytext=(23, 52),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=3))
ax.text(25.5, 54, 'Opinions', fontsize=8, ha='center', va='center', color='#616161')

# ============================================================================
# CRM Box (Center)
# ============================================================================
crm_box = FancyBboxPatch((28, 35), 48, 30, boxstyle="round,pad=0.02,rounding_size=0.8",
                          facecolor=COLORS['ai'], edgecolor=COLORS['ai_border'], linewidth=3)
ax.add_patch(crm_box)
ax.text(52, 62, 'COLLECTIVE RATIONAL MODEL (CRM)', fontsize=13, ha='center', va='center',
         fontweight='bold', color=COLORS['ai_border'])

# ----- Row 1: Statement Generation → Preference Ranking → Schulze Vote -----
gen_box = FancyBboxPatch((31, 52), 16, 8, boxstyle="round,pad=0.01,rounding_size=0.5",
                          facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(gen_box)
ax.text(39, 57, 'Statement\nGeneration', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(39, 53, '(Prompted)', fontsize=8, ha='center', va='center', color='#757575')

# Arrow: Generation to Ranking
ax.annotate('', xy=(49, 56), xytext=(47, 56),
            arrowprops=dict(arrowstyle='->', color=COLORS['ai_border'], lw=2))

rank_box = FancyBboxPatch((49, 52), 16, 8, boxstyle="round,pad=0.01,rounding_size=0.5",
                           facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(rank_box)
ax.text(57, 57, 'Preference\nRanking', fontsize=10, ha='center', va='center', fontweight='bold')
ax.text(57, 53, '(Prompted)', fontsize=8, ha='center', va='center', color='#757575')

# Arrow: Ranking to Schulze
ax.annotate('', xy=(67, 56), xytext=(65, 56),
            arrowprops=dict(arrowstyle='->', color=COLORS['ai_border'], lw=2))

schulze_box = FancyBboxPatch((67, 52), 7, 8, boxstyle="round,pad=0.01,rounding_size=0.5",
                              facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(schulze_box)
ax.text(70.5, 56, 'Schulze\nVote', fontsize=9, ha='center', va='center', fontweight='bold')

# ----- Row 2: LLM Backend -----
llm_box = FancyBboxPatch((31, 38), 43, 10, boxstyle="round,pad=0.01,rounding_size=0.5",
                          facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(llm_box)
ax.text(52.5, 46, 'LLM Backend (Interchangeable)', fontsize=10, ha='center', va='center', fontweight='bold')

# LLM chips
llms = [
    ('GPT-5.x', '#4CAF50'),
    ('Claude 3.5', '#2196F3'),
    ('Gemini 2.0', '#FF9800'),
    ('o3', '#9C27B0'),
]
for i, (llm, color) in enumerate(llms):
    x_pos = 33 + i * 10
    chip = FancyBboxPatch((x_pos, 39.5), 8, 3.5, boxstyle="round,pad=0.01,rounding_size=0.3",
                           facecolor=color, edgecolor='white', linewidth=1, alpha=0.9)
    ax.add_patch(chip)
    ax.text(x_pos + 4, 41.25, llm, fontsize=8, ha='center', va='center',
            fontweight='bold', color='white')

# ============================================================================
# Arrow to output
# ============================================================================
ax.annotate('', xy=(81, 52), xytext=(76, 52),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=3))

# ============================================================================
# Outputs Box (Right)
# ============================================================================
output_box = FancyBboxPatch((81, 30), 24, 34, boxstyle="round,pad=0.02,rounding_size=0.8",
                             facecolor=COLORS['output'], edgecolor=COLORS['output_border'], linewidth=3)
ax.add_patch(output_box)
ax.text(93, 61, 'Outputs &\nMetrics', fontsize=12, ha='center', va='center', fontweight='bold')

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
    y_pos = 55 - i * 3.5
    ax.text(93, y_pos, f'• {out}', fontsize=9, ha='center', va='center', color='#616161')

# ============================================================================
# Feedback Loop: Winner₁ → Citizens (Critique) → Back to CRM
# ============================================================================

# Critique box at citizens (positioned first so we know where to draw arrows)
critique_box = FancyBboxPatch((5, 18), 16, 7, boxstyle="round,pad=0.01,rounding_size=0.4",
                               facecolor='white', edgecolor=COLORS['feedback'], linewidth=2)
ax.add_patch(critique_box)
ax.text(13, 21.5, 'Citizens\nCritique', fontsize=9, ha='center', va='center',
        fontweight='bold', color=COLORS['feedback'])

# Arrow from CRM down (Winner₁ out)
ax.plot([52, 52], [35, 28], color=COLORS['feedback'], linewidth=2.5)
ax.text(54, 31, 'Winner₁', fontsize=9, ha='left', va='center', color=COLORS['feedback'], fontweight='bold')

# Arrow going left to citizens (connects to RIGHT side of critique box)
ax.plot([52, 21], [28, 28], color=COLORS['feedback'], linewidth=2.5)
ax.plot([21, 21], [28, 25], color=COLORS['feedback'], linewidth=2.5)
ax.annotate('', xy=(21, 21.5), xytext=(21, 24),
            arrowprops=dict(arrowstyle='->', color=COLORS['feedback'], lw=2.5))

# Arrow from critique back to CRM (from bottom of critique box)
ax.plot([13, 13], [18, 14], color=COLORS['feedback'], linewidth=2.5)
ax.plot([13, 52], [14, 14], color=COLORS['feedback'], linewidth=2.5)
ax.plot([52, 52], [14, 35], color=COLORS['feedback'], linewidth=2.5)
ax.annotate('', xy=(52, 35), xytext=(52, 25),
            arrowprops=dict(arrowstyle='->', color=COLORS['feedback'], lw=2.5))
ax.text(32, 12, 'Critiques + Opinions → Round 2 → Final Winner', fontsize=9,
        ha='center', va='center', color=COLORS['feedback'], fontweight='bold')

# Round labels
ax.text(52, 68, 'Round 1: Opinions → Generate → Rank → Vote → Winner₁', fontsize=10,
        ha='center', va='center', color='#455A64', fontweight='bold')
ax.text(52, 11, 'Round 2: Opinions + Winner₁ + Critiques → Generate → Rank → Vote → Final Winner',
        fontsize=10, ha='center', va='center', color=COLORS['feedback'], fontweight='bold')

# ============================================================================
# Key Differences Box (Bottom)
# ============================================================================
diff_box = FancyBboxPatch((10, 2), 90, 7, boxstyle="round,pad=0.02,rounding_size=0.5",
                           facecolor='#ECEFF1', edgecolor='#607D8B', linewidth=2)
ax.add_patch(diff_box)
ax.text(55, 6.5, 'Key Differences from Original Habermas Machine:', fontsize=10,
        ha='center', va='center', fontweight='bold')
ax.text(55, 3.5, 'Prompted LLMs (not fine-tuned Chinchilla)  |  Multiple backends (GPT, Claude, Gemini, o3)  |  Sacred value testing',
        fontsize=9, ha='center', va='center', color='#616161')

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
    mpatches.Patch(facecolor='white', edgecolor=COLORS['feedback'],
                   linewidth=2, label='Round 2 Feedback'),
]

fig.legend(handles=legend_elements, loc='lower center', ncol=5, fontsize=9,
           frameon=True, fancybox=True, bbox_to_anchor=(0.5, -0.01))

# ============================================================================
# Save
# ============================================================================
plt.tight_layout()
plt.savefig('diagram_crm.png', dpi=300, bbox_inches='tight', facecolor='white')
print("Saved: diagram_crm.png")
plt.show()
