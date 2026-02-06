#!/usr/bin/env python3
"""
Original Habermas Machine Architecture Diagram
===============================================

Shows the original fine-tuned Chinchilla-based architecture
from Tessler et al., 2024.

Usage:
    python diagram_original_hm.py

Output:
    diagram_original_hm.png
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# Set up figure
fig, ax = plt.subplots(figsize=(14, 8))
ax.set_xlim(0, 100)
ax.set_ylim(0, 60)
ax.set_aspect('equal')
ax.axis('off')
ax.set_facecolor('#FAFAFA')

# Colors
COLORS = {
    'human': '#E8F5E9',
    'human_border': '#4CAF50',
    'ai': '#FFEBEE',
    'ai_border': '#F44336',
    'output': '#FFF8E1',
    'output_border': '#FFC107',
    'arrow': '#455A64',
    'text': '#212121',
}

# Title
ax.text(50, 57, 'Original Habermas Machine', fontsize=20, fontweight='bold',
        ha='center', va='center', color=COLORS['text'])
ax.text(50, 53, 'Tessler et al., Science (2024)', fontsize=14,
        ha='center', va='center', color='#757575')
ax.text(50, 50, 'Fine-tuned Chinchilla Model (No Public Access)', fontsize=11,
        ha='center', va='center', color='#9E9E9E', style='italic')

# ============================================================================
# Human Opinions Box (Left)
# ============================================================================
opinions_box = FancyBboxPatch((5, 20), 18, 20, boxstyle="round,pad=0.02,rounding_size=0.8",
                               facecolor=COLORS['human'], edgecolor=COLORS['human_border'], linewidth=3)
ax.add_patch(opinions_box)
ax.text(14, 36, 'Human\nOpinions', fontsize=14, ha='center', va='center', fontweight='bold')
ax.text(14, 27, 'n participants\nprivately write\ntheir views', fontsize=10, ha='center', va='center', color='#616161')

# Arrow to HM
ax.annotate('', xy=(28, 30), xytext=(23, 30),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=3))

# ============================================================================
# Habermas Machine Box (Center)
# ============================================================================
hm_box = FancyBboxPatch((28, 12), 40, 36, boxstyle="round,pad=0.02,rounding_size=0.8",
                         facecolor=COLORS['ai'], edgecolor=COLORS['ai_border'], linewidth=3)
ax.add_patch(hm_box)
ax.text(48, 44, 'HABERMAS MACHINE', fontsize=14, ha='center', va='center',
         fontweight='bold', color=COLORS['ai_border'])

# Generative Model
gen_box = FancyBboxPatch((31, 32), 16, 9, boxstyle="round,pad=0.01,rounding_size=0.5",
                          facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(gen_box)
ax.text(39, 38, 'Generative\nModel', fontsize=11, ha='center', va='center', fontweight='bold')
ax.text(39, 33.5, '(Chinchilla)', fontsize=9, ha='center', va='center', color='#757575')

# Preference Reward Model
prm_box = FancyBboxPatch((49, 32), 16, 9, boxstyle="round,pad=0.01,rounding_size=0.5",
                          facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(prm_box)
ax.text(57, 38, 'Preference\nReward Model', fontsize=11, ha='center', va='center', fontweight='bold')
ax.text(57, 33.5, '(Chinchilla)', fontsize=9, ha='center', va='center', color='#757575')

# Schulze Voting
schulze_box = FancyBboxPatch((37, 16), 22, 8, boxstyle="round,pad=0.01,rounding_size=0.5",
                              facecolor='white', edgecolor=COLORS['ai_border'], linewidth=2)
ax.add_patch(schulze_box)
ax.text(48, 20, 'Schulze Voting', fontsize=12, ha='center', va='center', fontweight='bold')

# Internal arrows
ax.annotate('', xy=(48, 31), xytext=(48, 24),
            arrowprops=dict(arrowstyle='->', color=COLORS['ai_border'], lw=1.5))

# Arrow to output
ax.annotate('', xy=(73, 30), xytext=(68, 30),
            arrowprops=dict(arrowstyle='->', color=COLORS['arrow'], lw=3))

# ============================================================================
# Consensus Statement Box (Right)
# ============================================================================
output_box = FancyBboxPatch((73, 20), 18, 20, boxstyle="round,pad=0.02,rounding_size=0.8",
                             facecolor=COLORS['output'], edgecolor=COLORS['output_border'], linewidth=3)
ax.add_patch(output_box)
ax.text(82, 36, 'Consensus\nStatement', fontsize=14, ha='center', va='center', fontweight='bold')
ax.text(82, 27, 'Group opinion\nwinner returned\nto participants', fontsize=10, ha='center', va='center', color='#616161')

# ============================================================================
# Key Features Box (Bottom)
# ============================================================================
features_box = FancyBboxPatch((20, 2), 60, 8, boxstyle="round,pad=0.02,rounding_size=0.5",
                               facecolor='#ECEFF1', edgecolor='#607D8B', linewidth=2)
ax.add_patch(features_box)
ax.text(50, 7.5, 'Key Features:', fontsize=11, ha='center', va='center', fontweight='bold')
ax.text(50, 4, 'Fine-tuned on 450MB dataset  |  Chinchilla backbone (not public)  |  Trained reward model',
        fontsize=10, ha='center', va='center', color='#616161')

# ============================================================================
# Legend
# ============================================================================
legend_elements = [
    mpatches.Patch(facecolor=COLORS['human'], edgecolor=COLORS['human_border'],
                   linewidth=2, label='Human Input'),
    mpatches.Patch(facecolor=COLORS['ai'], edgecolor=COLORS['ai_border'],
                   linewidth=2, label='AI System (Chinchilla)'),
    mpatches.Patch(facecolor=COLORS['output'], edgecolor=COLORS['output_border'],
                   linewidth=2, label='Output'),
]

fig.legend(handles=legend_elements, loc='lower center', ncol=3, fontsize=10,
           frameon=True, fancybox=True, bbox_to_anchor=(0.5, -0.02))

# ============================================================================
# Save
# ============================================================================
plt.tight_layout()
plt.savefig('diagram_original_hm.png', dpi=300, bbox_inches='tight', facecolor='white')
print("Saved: diagram_original_hm.png")
plt.show()
