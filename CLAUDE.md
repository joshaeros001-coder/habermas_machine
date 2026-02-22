# CLAUDE.md — Sacred Value Research (Habermas Machine)

## Project Overview

This is Joshua Attih's PhD research repo investigating how different LLMs handle sacred values in AI-mediated deliberation. It is a **fork of Google DeepMind's official `habermas_machine` repository**, extended with multi-provider LLM support for cross-model comparison experiments.

We call this variant the **CRM (Collective Rationale Model)** — it uses the prompted (not fine-tuned) Habermas Machine architecture with different LLM backends, unlike the original which used a Chinchilla fine-tuned model.

**Researcher:** Joshua Attih, PhD student, Computer Science, University of New Mexico
**PI:** Melanie Moses, ARIA (AI Research Institute for Advancing Trustworthy AI for Mental and Behavioral Health)

## Research Question

Does the Habermas Machine's consensus-building process systematically disadvantage participants who hold sacred values (non-negotiable, trade-off resistant positions)? How does this vary across different LLM backends?

### Key Findings So Far
- The same deliberation architecture produces dramatically different outcomes for the sacred value holder depending on which LLM is used
- Linguistic quality of consensus statements does NOT predict minority satisfaction
- Structural placement and framing (e.g., "preference" vs. "conscience" language) prove more determinative
- Patterns of "rescue" (deliberation improves minority accommodation) vs. "degradation" (deliberation worsens it) vary by model

### Key Concepts
- **Sacred/protected values:** Non-negotiable positions (Baron & Spranca 1997) that cannot be captured by scalar utility
- **Commensuration bias:** The systematic tendency of aggregation systems to treat sacred values as tradeable preferences
- **4-vs-1 configuration:** 1 sacred value holder + 4 secular cost-benefit reasoners
- **Rescue vs. degradation:** Whether the critique round improves or worsens the sacred value holder's ranking of the winner

## Repository Structure

```
habermas_machine/                    # Root
├── habermas_machine/                # Core package (DeepMind's original + our extensions)
│   ├── machine.py                   # Main HabermasMachine class — the deliberation engine
│   ├── types.py                     # Data types, enums for models/methods
│   ├── utils.py                     # Shared utilities
│   ├── llm_client/                  # LLM provider clients
│   │   ├── base_client.py           # Abstract base class
│   │   ├── aistudio_client.py       # Google AI Studio (Gemini models)
│   │   ├── openai_client.py         # OpenAI (GPT, o-series models)
│   │   ├── anthropic_client.py      # Anthropic (Claude models) — NOT YET TESTED
│   │   └── mock_client.py           # For unit tests
│   ├── reward_model/                # Ranking/reward models
│   │   ├── cot_ranking_model.py     # Chain-of-thought ranking (primary)
│   │   └── base_model.py            # Abstract base
│   ├── social_choice/               # Voting/aggregation methods
│   │   ├── schulze_method.py        # Schulze method implementation (primary)
│   │   └── utils.py                 # Tie-breaking, ballot processing
│   └── statement_model/             # Consensus statement generation
│       ├── cot_model.py             # Chain-of-thought generation (primary)
│       └── base_model.py            # Abstract base
├── analysis/                        # Analysis notebooks and utilities
│   ├── habermas_machine_data_preprocessing.ipynb  # DeepMind's original
│   ├── Kendall_Tau_Analysis.ipynb  # Joshua's main analysis (Kendall tau, isolation indices)
│   └── live_loading.py              # Data loading utilities
├── questions/                       # Deliberation questions
│   └── 230118_chinchilla_questions.json  # Original DeepMind questions
├── example_sacred_value_test.py     # ⭐ MAIN EXPERIMENT SCRIPT — runs full deliberation
├── preference_space_test.py         # Separate experiment: LLM preference space exploration
├── compare_results.py               # Compares preference_space results across models
├── results_*.json                   # ⭐ DELIBERATION RESULTS (18 models completed)
├── preference_space_results_*.json  # Preference space exploration results (separate experiment)
├── terminal_log_*.txt               # Raw terminal output with detailed voting data
└── CLAUDE.md                        # This file
```

## Two Separate Experiments

### Experiment 1: Sacred Value Deliberation (THE CORE RESEARCH)
- **Script:** `example_sacred_value_test.py`
- **What it does:** Runs a full 2-round Habermas Machine deliberation (opinion round → critique round) with 5 simulated citizens, where Citizen 2 holds a sacred value (religious objection to SSRI medication)
- **Output files:** `results_MODEL.json` — contains opinions, critiques, all ranked candidate statements, winning statements, and metadata
- **Terminal logs:** `terminal_log_MODEL_TIMESTAMP.txt` — contains INDIVIDUAL CITIZEN RANKINGS that are NOT in the JSON (critical for analysis)
- **Scenario:** SSRI medication decision with religious objection
- **Models completed:** 18 total
  - Gemini family (10): gemini-2.0-flash, flash-lite, flash-thinking-exp, 2.5-flash, 2.5-flash-lite, 2.5-pro, 2.5-pro-preview-03-25, 2.5-pro-preview-06-05, 3-pro-preview, gemma-3-27b-it
  - OpenAI family (8): gpt-3.5-turbo (via preference_space only), gpt-4-turbo, gpt-4o, gpt-4.1, gpt-5.1, gpt-5.2, o1, o3, o3-mini
- **Models NOT YET RUN:** All Anthropic/Claude models (client exists but untested)
- **Analysis:** Primary analysis notebook in `analysis/sacred_value_analysis.ipynb` (Kendall tau distance, isolation indices, rescue/degradation patterns)

### Experiment 2: Preference Space Exploration (SUPPLEMENTARY)
- **Script:** `preference_space_test.py`
- **What it does:** Tests whether LLMs explore the full 7.9M preference profile space (24^5 possible profiles for 5 citizens ranking 4 statements) or cluster into subspaces
- **Output files:** `preference_space_results_MODEL_Nruns.json` — contains entropy, coverage ratio, unique profile counts
- **Analysis:** `compare_results.py` reads these files and generates comparison tables
- **Status:** Runs completed for several OpenAI models; this is where Claude Code browser sessions hit context limits

## Critical Technical Details

### The Shuffle-Misattribution Problem
`machine.py` (~line 150) shuffles opinion order before each statement generation to prevent position bias. This means opinion citations in generated statements (e.g., "Opinion 2, 3, 5") refer to SHUFFLED positions, NOT original citizen IDs. The sacred value holder (Citizen 2) may be cited under a different number. Analysis must account for this.

### Terminal Logs Are Essential
The JSON results files do NOT contain individual citizen rankings. These are only printed to terminal (when verbose=True) and captured in terminal log files. Any analysis of how Citizen 2 ranked the winner requires parsing terminal logs, not just JSON.

### Rate Limiting
Different providers need different rate limiting configurations:
- Google AI Studio free tier: 15 RPM → sleep 5s every 5 calls
- OpenAI: higher RPM → sleep 2s every 10 calls
- Anthropic: TBD (not yet configured)

### Results File Naming
- `results_MODEL.json` = full deliberation run (Experiment 1)
- `preference_space_results_MODEL_Nruns.json` = preference space exploration (Experiment 2)
- These are DIFFERENT experiments with DIFFERENT data structures. Do not confuse them.

## Files to Ignore or Deprecate
- `sacred_value_analysis.py` — DEPRECATED. Throwaway plotting script with hardcoded Gemini data. Real analysis is in the Colab notebook.
- `check_models.py`, `check_claude_models.py`, `test_api_keys.py`, `test_import.py` — utility/debugging scripts, not research code
- `crm_architecture_diagram.*`, `diagram_*.py` — presentation diagrams, not actively developed

## Environment Setup

```bash
cd ~/Documents/habermas_machine
source venv/bin/activate  # Python virtual environment
# API keys needed in environment:
# GOOGLE_API_KEY (for Gemini models)
# OPENAI_API_KEY (for GPT/o-series models)
# ANTHROPIC_API_KEY (for Claude models — not yet used)
```

**requirements.txt is incomplete.** It only lists `numpy` and `google-generativeai`. The actual dependencies include `openai`, and will need `anthropic` for Claude model testing. Update requirements.txt before sharing the repo.

## Current State and Next Steps

### Completed
- [x] Multi-provider client architecture (Google, OpenAI, Anthropic stub)
- [x] 18 model deliberation runs (10 Gemini + 8 OpenAI)
- [x] Terminal logs captured for all runs
- [x] Preference space exploration for OpenAI models
- [x] Architecture diagrams for CRM

### In Progress
- [ ] Analysis notebook: Kendall tau distance, isolation indices across all 18 models
- [ ] Consolidating individual citizen rankings from terminal logs into structured data

### Next
- [ ] Run Anthropic/Claude models (Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku minimum)
- [ ] Complete cross-model comparison analysis
- [ ] Update requirements.txt with all actual dependencies
- [ ] Commit all untracked results files and logs to git
- [ ] Consider: additional deliberation scenarios beyond SSRI (to test generalizability)

## Git State
- Current branch: `claude/debug-google-api-billing-01Gxe1PTVgKqLq56NBe3Sn4a` (should probably be renamed)
- 3 modified files not committed: `diagram_crm.py`, `example_sacred_value_test.py`, `base_client.py`
- ~40 untracked files (all results, logs, diagrams, utility scripts)
- All results and logs should be committed before any further work

## How to Run Experiments

### Run a single deliberation (Experiment 1):
```bash
# Edit MODEL variable in example_sacred_value_test.py, then:
python example_sacred_value_test.py
# Produces: results_MODEL.json + terminal_log_MODEL_TIMESTAMP.txt
```

### Run preference space exploration (Experiment 2):
```bash
python preference_space_test.py 100 openai gpt-4o
# Produces: preference_space_results_openai_gpt_4o_100runs.json
```

### Run analysis:
Analysis is in the Jupyter notebook at `analysis/Kendall_Tau_Analysis.ipynb`