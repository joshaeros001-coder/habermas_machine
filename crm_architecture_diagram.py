#!/usr/bin/env python3
"""
CRM (Collective Rational Model) Architecture Diagram
=====================================================

Generates a presentation-ready diagram showing the difference between:
- Original Habermas Machine (fine-tuned Chinchilla)
- CRM: Prompted version with multiple LLM backends (GPT, Claude, Gemini)

For academic presentation purposes.

Usage:
    python crm_architecture_diagram.py

Output:
    crm_architecture_diagram.png
    crm_architecture_diagram.pdf

Author: Sacred Value Research Project
Date: February 2026
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
from matplotlib.lines import Line2D
import numpy as np

# Set up the figure with two panels
fig = plt.figure(figsize=(18, 14))

# Color scheme
COLORS = {
    'human': '#E8F5E9',          # Light green - human input
    'human_border': '#4CAF50',   # Green border
    'ai_original': '#FFEBEE',    # Light red - original Chinchilla
    'ai_original_border': '#F44336',
    'ai_crm': '#E3F2FD',         # Light blue - CRM/prompted LLMs
    'ai_crm_border': '#2196F3',
    'output': '#FFF8E1',         # Light yellow - outputs
    'output_border': '#FFC107',
    'sacred': '#F3E5F5',         # Light purple - sacred value
    'sacred_border': '#9C27B0',
    'arrow': '#455A64',
    'text': '#212121',
    'background': '#FAFAFA',
}

# ============================================================================
# PANEL A: Original Habermas Machine (Top)
# ============================================================================

ax1 = fig.add_subplot(2, 1, 1)
ax1.set_xlim(0, 100)
ax1.set_ylim(0, 50)
ax1.set_aspect('equal')
ax1.axis('off')
ax1.set_facecolor(COLORS['background'])

# Title
ax1.text(50, 48, 'A. Original Habermas Machine (Tessler et al., 2024)',
         fontsize=16, fontweight='bold', ha='center', va='top', color=COLORS['text'])
ax1.text(50, 45, 'Fine-tuned Chinchilla Model (No Public Access)',
         fontsize=12, ha='center', va='top', color='#757575', style='italic')

# Human Opinions Box
opinions_box = FancyBboxPatch((5, 25), 18, 15, boxstyle="round,pad=0.02,rounding_size=0.5",
                               facecolor=COLORS['human'], edgecolor=COLORS['human_border'], linewidth=2)
ax1.add_patch(opinions_box)
ax1.text(14, 37, 'Human\nOpinions', fontsize=10, ha='center', va='center', fontweight='bold')
ax1.text(14, 29, 'n participants\nwrite views', fontsize=8, ha='center', va='center', color='#616161')

# Arrow to HM
ax1.annotate('', xy=(28, 32.5), xytext=(23, 32.5),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2))

# Habermas Machine Box (Original)
hm_box = FancyBboxPatch((28, 22), 30, 21, boxstyle="round,pad=0.02,rounding_size=0.5",
                         facecolor=COLORS['ai_original'], edgecolor=COLORS['ai_original_border'], linewidth=3)
ax1.add_patch(hm_box)
ax1.text(43, 40, 'HABERMAS MACHINE', fontsize=11, ha='center', va='center',
         fontweight='bold', color=COLORS['ai_original_border'])

# Inner components
# Generative Model
gen_box = FancyBboxPatch((30, 33), 12, 7, boxstyle="round,pad=0.01,rounding_size=0.3",
                          facecolor='white', edgecolor=COLORS['ai_original_border'], linewidth=1.5)
ax1.add_patch(gen_box)
ax1.text(36, 37.5, 'Generative\nModel', fontsize=8, ha='center', va='center', fontweight='bold')
ax1.text(36, 34, '(Chinchilla)', fontsize=7, ha='center', va='center', color='#757575')

# PRM
prm_box = FancyBboxPatch((44, 33), 12, 7, boxstyle="round,pad=0.01,rounding_size=0.3",
                          facecolor='white', edgecolor=COLORS['ai_original_border'], linewidth=1.5)
ax1.add_patch(prm_box)
ax1.text(50, 37.5, 'Preference\nReward Model', fontsize=8, ha='center', va='center', fontweight='bold')
ax1.text(50, 34, '(Chinchilla)', fontsize=7, ha='center', va='center', color='#757575')

# Schulze Voting
schulze_box = FancyBboxPatch((35, 24), 16, 6, boxstyle="round,pad=0.01,rounding_size=0.3",
                              facecolor='white', edgecolor=COLORS['ai_original_border'], linewidth=1.5)
ax1.add_patch(schulze_box)
ax1.text(43, 27, 'Schulze Voting', fontsize=9, ha='center', va='center', fontweight='bold')

# Arrow to output
ax1.annotate('', xy=(63, 32.5), xytext=(58, 32.5),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2))

# Output Box
output_box = FancyBboxPatch((63, 25), 18, 15, boxstyle="round,pad=0.02,rounding_size=0.5",
                             facecolor=COLORS['output'], edgecolor=COLORS['output_border'], linewidth=2)
ax1.add_patch(output_box)
ax1.text(72, 37, 'Consensus\nStatement', fontsize=10, ha='center', va='center', fontweight='bold')
ax1.text(72, 29, 'Group opinion\nwinner', fontsize=8, ha='center', va='center', color='#616161')

# Key characteristics
ax1.text(88, 38, 'Key Features:', fontsize=9, fontweight='bold', ha='left', color=COLORS['text'])
ax1.text(88, 35, '• Fine-tuned on\n  450MB dataset', fontsize=8, ha='left', color='#616161')
ax1.text(88, 30, '• Chinchilla backbone\n  (not public)', fontsize=8, ha='left', color='#616161')
ax1.text(88, 25, '• Trained reward model', fontsize=8, ha='left', color='#616161')

# ============================================================================
# PANEL B: CRM - Collective Rational Model (Bottom)
# ============================================================================

ax2 = fig.add_subplot(2, 1, 2)
ax2.set_xlim(0, 100)
ax2.set_ylim(0, 50)
ax2.set_aspect('equal')
ax2.axis('off')
ax2.set_facecolor(COLORS['background'])

# Title
ax2.text(50, 48, 'B. CRM: Collective Rational Model (This Research)',
         fontsize=16, fontweight='bold', ha='center', va='top', color=COLORS['text'])
ax2.text(50, 45, 'Prompted Version with Multiple LLM Backends',
         fontsize=12, ha='center', va='top', color='#757575', style='italic')

# Simulated Opinions Box (with sacred value highlight)
opinions_box2 = FancyBboxPatch((2, 20), 20, 22, boxstyle="round,pad=0.02,rounding_size=0.5",
                                facecolor=COLORS['human'], edgecolor=COLORS['human_border'], linewidth=2)
ax2.add_patch(opinions_box2)
ax2.text(12, 40, 'Simulated\nCitizen Opinions', fontsize=10, ha='center', va='center', fontweight='bold')

# Individual citizen boxes
citizens = ['C1: Pragmatic', 'C2: Sacred Value', 'C3: Balanced', 'C4: Moderate', 'C5: Deferential']
colors_c = [COLORS['human'], COLORS['sacred'], COLORS['human'], COLORS['human'], COLORS['human']]
borders_c = [COLORS['human_border'], COLORS['sacred_border'], COLORS['human_border'],
             COLORS['human_border'], COLORS['human_border']]

for i, (citizen, fc, ec) in enumerate(zip(citizens, colors_c, borders_c)):
    y_pos = 35 - i * 4
    c_box = FancyBboxPatch((4, y_pos - 1.5), 16, 3, boxstyle="round,pad=0.01,rounding_size=0.2",
                            facecolor=fc, edgecolor=ec, linewidth=1.5 if i == 1 else 1)
    ax2.add_patch(c_box)
    ax2.text(12, y_pos, citizen, fontsize=7, ha='center', va='center',
             fontweight='bold' if i == 1 else 'normal',
             color=COLORS['sacred_border'] if i == 1 else COLORS['text'])

# Arrow to CRM
ax2.annotate('', xy=(27, 31), xytext=(22, 31),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2))

# CRM Box
crm_box = FancyBboxPatch((27, 15), 35, 27, boxstyle="round,pad=0.02,rounding_size=0.5",
                          facecolor=COLORS['ai_crm'], edgecolor=COLORS['ai_crm_border'], linewidth=3)
ax2.add_patch(crm_box)
ax2.text(44.5, 40, 'COLLECTIVE RATIONAL MODEL (CRM)', fontsize=11, ha='center', va='center',
         fontweight='bold', color=COLORS['ai_crm_border'])

# Statement Generation (Prompted)
gen_box2 = FancyBboxPatch((29, 31), 14, 7, boxstyle="round,pad=0.01,rounding_size=0.3",
                           facecolor='white', edgecolor=COLORS['ai_crm_border'], linewidth=1.5)
ax2.add_patch(gen_box2)
ax2.text(36, 35.5, 'Statement\nGeneration', fontsize=8, ha='center', va='center', fontweight='bold')
ax2.text(36, 32, '(Prompted)', fontsize=7, ha='center', va='center', color='#757575')

# Ranking Model (Prompted)
rank_box = FancyBboxPatch((45, 31), 14, 7, boxstyle="round,pad=0.01,rounding_size=0.3",
                           facecolor='white', edgecolor=COLORS['ai_crm_border'], linewidth=1.5)
ax2.add_patch(rank_box)
ax2.text(52, 35.5, 'Preference\nRanking', fontsize=8, ha='center', va='center', fontweight='bold')
ax2.text(52, 32, '(Prompted)', fontsize=7, ha='center', va='center', color='#757575')

# LLM Backends
llm_box = FancyBboxPatch((32, 22), 24, 7, boxstyle="round,pad=0.01,rounding_size=0.3",
                          facecolor='white', edgecolor=COLORS['ai_crm_border'], linewidth=1.5)
ax2.add_patch(llm_box)
ax2.text(44, 26.5, 'LLM Backend (Interchangeable)', fontsize=8, ha='center', va='center', fontweight='bold')

# LLM options
llms = ['GPT-5.x', 'Claude 3.5', 'Gemini 2.0', 'o3']
for i, llm in enumerate(llms):
    x_pos = 34 + i * 6
    llm_chip = FancyBboxPatch((x_pos, 22.5), 5.5, 2.5, boxstyle="round,pad=0.01,rounding_size=0.2",
                               facecolor='#E8EAF6', edgecolor='#3F51B5', linewidth=1)
    ax2.add_patch(llm_chip)
    ax2.text(x_pos + 2.75, 23.75, llm, fontsize=6, ha='center', va='center', fontweight='bold')

# Schulze Voting
schulze_box2 = FancyBboxPatch((35, 16), 18, 5, boxstyle="round,pad=0.01,rounding_size=0.3",
                               facecolor='white', edgecolor=COLORS['ai_crm_border'], linewidth=1.5)
ax2.add_patch(schulze_box2)
ax2.text(44, 18.5, 'Schulze Voting', fontsize=9, ha='center', va='center', fontweight='bold')

# Arrow to outputs
ax2.annotate('', xy=(67, 31), xytext=(62, 31),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=2))

# Outputs Box
output_box2 = FancyBboxPatch((67, 18), 18, 22, boxstyle="round,pad=0.02,rounding_size=0.5",
                              facecolor=COLORS['output'], edgecolor=COLORS['output_border'], linewidth=2)
ax2.add_patch(output_box2)
ax2.text(76, 38, 'Outputs', fontsize=10, ha='center', va='center', fontweight='bold')

# Output items
outputs = ['Winner Statement', 'Preference Profiles', 'Kendall τ Distance', 'Entropy Metrics', 'Isolation Index']
for i, out in enumerate(outputs):
    y_pos = 34 - i * 3.5
    ax2.text(76, y_pos, f'• {out}', fontsize=7, ha='center', va='center', color='#616161')

# Key differences box
diff_box = FancyBboxPatch((87, 18), 12, 22, boxstyle="round,pad=0.02,rounding_size=0.3",
                           facecolor='#ECEFF1', edgecolor='#607D8B', linewidth=1.5)
ax2.add_patch(diff_box)
ax2.text(93, 38, 'Key\nDifferences', fontsize=8, fontweight='bold', ha='center', va='center')
ax2.text(93, 33, '• Prompted\n  (not fine-tuned)', fontsize=7, ha='center', va='center', color='#616161')
ax2.text(93, 28, '• Multiple LLM\n  backends', fontsize=7, ha='center', va='center', color='#616161')
ax2.text(93, 23, '• Sacred value\n  testing', fontsize=7, ha='center', va='center', color='#616161')
ax2.text(93, 19, '• Entropy\n  analysis', fontsize=7, ha='center', va='center', color='#616161')

# ============================================================================
# Legend
# ============================================================================

legend_elements = [
    mpatches.Patch(facecolor=COLORS['human'], edgecolor=COLORS['human_border'],
                   linewidth=1.5, label='Human/Simulated Input'),
    mpatches.Patch(facecolor=COLORS['ai_original'], edgecolor=COLORS['ai_original_border'],
                   linewidth=1.5, label='Original HM (Chinchilla)'),
    mpatches.Patch(facecolor=COLORS['ai_crm'], edgecolor=COLORS['ai_crm_border'],
                   linewidth=1.5, label='CRM (Prompted LLMs)'),
    mpatches.Patch(facecolor=COLORS['sacred'], edgecolor=COLORS['sacred_border'],
                   linewidth=1.5, label='Sacred Value Holder'),
    mpatches.Patch(facecolor=COLORS['output'], edgecolor=COLORS['output_border'],
                   linewidth=1.5, label='Output/Results'),
]

fig.legend(handles=legend_elements, loc='lower center', ncol=5, fontsize=9,
           frameon=True, fancybox=True, shadow=True, bbox_to_anchor=(0.5, 0.02))

# ============================================================================
# Add connecting annotation between panels
# ============================================================================

fig.text(0.5, 0.5, '⬇ Our Adaptation ⬇', fontsize=12, ha='center', va='center',
         fontweight='bold', color='#455A64',
         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='#455A64', linewidth=2))

# ============================================================================
# Save
# ============================================================================

plt.tight_layout(rect=[0, 0.05, 1, 1])
plt.savefig('crm_architecture_diagram.png', dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig('crm_architecture_diagram.pdf', bbox_inches='tight', facecolor='white')
print("Saved: crm_architecture_diagram.png")
print("Saved: crm_architecture_diagram.pdf")

# Also show
plt.show()
