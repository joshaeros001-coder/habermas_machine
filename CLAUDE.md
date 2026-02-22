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
│   ├── __init__.py                  # Package initialization
│   ├── machine.py                   # HabermasMachine class — the deliberation engine (260 lines)
│   ├── machine_test.py              # Unit tests for machine
│   ├── types.py                     # Enums: LLMClient, RewardModel, StatementModel, RankAggregation
│   ├── types_test.py                # Unit tests for types
│   ├── utils.py                     # Shared utilities (ranking conversion, etc.)
│   ├── utils_test.py                # Unit tests for utils
│   ├── example_aistudio.ipynb       # Example notebook using Google AI Studio
│   │
│   ├── llm_client/                  # LLM provider clients
│   │   ├── __init__.py
│   │   ├── base_client.py           # Abstract LLMClient base (DEFAULT_MAX_TOKENS=4096, TEMP=0.8)
│   │   ├── aistudio_client.py       # Google AI Studio (Gemini models)
│   │   ├── openai_client.py         # OpenAI (GPT, o-series models) — FULLY IMPLEMENTED
│   │   ├── anthropic_client.py      # Anthropic (Claude models) — IMPLEMENTED, NOT YET TESTED
│   │   ├── mock_client.py           # Mock client for unit tests
│   │   └── utils.py                 # Client utilities (truncation, etc.)
│   │
│   ├── reward_model/                # Ranking/reward models
│   │   ├── __init__.py
│   │   ├── base_model.py            # Abstract BaseRankingModel class
│   │   ├── cot_ranking_model.py     # Chain-of-thought ranking (PRIMARY)
│   │   ├── cot_ranking_model_test.py
│   │   ├── length_based_model.py    # Length-based ranking (NAIVE BASELINE)
│   │   ├── length_based_model_test.py
│   │   ├── mock_ranking_model.py    # Mock for unit tests
│   │   └── mock_ranking_model_test.py
│   │
│   ├── social_choice/               # Voting/aggregation methods
│   │   ├── __init__.py
│   │   ├── base_method.py           # Abstract Base class
│   │   ├── schulze_method.py        # Schulze method implementation (PRIMARY)
│   │   ├── schulze_method_test.py
│   │   ├── mock_method.py           # Mock for unit tests
│   │   ├── mock_method_test.py
│   │   ├── utils.py                 # Tie-breaking, ballot processing, TieBreakingMethod enum
│   │   └── utils_test.py
│   │
│   └── statement_model/             # Consensus statement generation
│       ├── __init__.py
│       ├── base_model.py            # Abstract BaseStatementModel class
│       ├── cot_model.py             # Chain-of-thought generation (PRIMARY)
│       ├── cot_model_test.py
│       └── mock_statement_model.py  # Mock for unit tests
│
├── analysis/                        # Analysis notebooks and utilities
│   ├── Kendall_Tau_Analysis.ipynb   # ⭐ MAIN ANALYSIS NOTEBOOK (Kendall tau, isolation indices)
│   ├── habermas_machine_data_preprocessing.ipynb  # DeepMind's original preprocessing
│   ├── live_loading.py              # Data loading utilities
│   ├── live_loading_test.py         # Unit tests
│   ├── serialise.py                 # Serialization utilities
│   ├── types.py                     # Analysis-specific types
│   ├── mocks.py                     # Mock data for testing
│   └── readme.md                    # Analysis documentation
│
├── questions/                       # Deliberation questions
│   └── 230118_chinchilla_questions.json  # Original DeepMind questions (1.9 MB)
│
├── example_sacred_value_test.py     # ⭐ MAIN EXPERIMENT SCRIPT — runs full deliberation (415 lines)
├── preference_space_test.py         # Experiment 2: LLM preference space exploration (788 lines)
├── compare_results.py               # Compares preference_space results across models
│
├── results_*.json                   # ⭐ DELIBERATION RESULTS (18 models completed)
├── preference_space_results_*.json  # Preference space exploration results (8 runs)
├── terminal_log_*.txt               # Raw terminal output with individual citizen rankings (18 logs)
│
├── diagram_crm.py                   # CRM architecture diagram generator
├── diagram_crm.png                  # Generated CRM diagram
├── diagram_original_hm.py           # Original Habermas Machine diagram generator
├── diagram_original_hm.png          # Generated original HM diagram
├── crm_architecture_diagram.png     # Architecture diagram
├── crm_architecture_diagram.pdf     # PDF version
├── crm_experiment_flow_diagram.py   # Experiment flow visualization
│
├── check_models.py                  # Fetches available models from all providers
├── check_claude_models.py           # Checks Claude models specifically
├── test_api_keys.py                 # Tests API key validity
├── test_import.py                   # Simple import test
├── sacred_value_analysis.py         # DEPRECATED: throwaway plotting script
│
├── requirements.txt                 # INCOMPLETE — see note below
├── setup.py                         # Package setup
├── README.md                        # Original DeepMind README
├── CONTRIBUTING.md                  # Contribution guidelines
├── LICENSE                          # Apache 2.0
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
  - **Gemini family (10):** gemini-2.0-flash, gemini-2.0-flash-lite, gemini-2.0-flash-thinking-exp, gemini-2.5-flash, gemini-2.5-flash-lite, gemini-2.5-pro, gemini-2.5-pro-preview-03-25, gemini-2.5-pro-preview-06-05, gemini-3-pro-preview, gemma-3-27b-it
  - **OpenAI family (8):** gpt-4-turbo, gpt-4o, gpt-4.1, gpt-5.1, gpt-5.2, o1, o3, o3-mini
- **Models NOT YET RUN:** All Anthropic/Claude models (client exists but untested)
- **Analysis:** `analysis/Kendall_Tau_Analysis.ipynb` (Kendall tau distance, isolation indices, rescue/degradation patterns)

### Experiment 2: Preference Space Exploration (SUPPLEMENTARY)
- **Script:** `preference_space_test.py`
- **What it does:** Tests whether LLMs explore the full 7.9M preference profile space (24^5 possible profiles for 5 citizens ranking 4 statements) or cluster into subspaces
- **Output files:** `preference_space_results_PROVIDER_MODEL_Nruns.json` — contains entropy, coverage ratio, unique profile counts
- **Completed runs (8):**
  - gpt-3.5-turbo (100 runs)
  - gpt-4 (100 runs)
  - gpt-4-turbo (100 runs)
  - gpt-4o (20 runs, 100 runs)
  - gpt-4o-mini (100 runs)
  - gpt-5.2 (20 runs)
  - o1 (100 runs)
- **Analysis:** `compare_results.py` reads these files and generates comparison tables

## Critical Technical Details

### The Shuffle-Misattribution Problem
`machine.py` (lines 105-110) shuffles opinion order before each statement generation to prevent position bias:
```python
# Shuffle the opinions and critiques to avoid ordering bias.
indices = self._rng.permutation(self._num_citizens)
shuffled_opinions = [self._opinions[j] for j in indices]
```
This means opinion citations in generated statements (e.g., "Opinion 2, 3, 5") refer to SHUFFLED positions, NOT original citizen IDs. The sacred value holder (Citizen 2) may be cited under a different number. Analysis must account for this.

### Terminal Logs Are Essential
The JSON results files do NOT contain individual citizen rankings. These are only printed to terminal (when verbose=True) and captured in terminal log files. Any analysis of how Citizen 2 ranked the winner requires parsing terminal logs, not just JSON.

Example from terminal output:
```
Rankings:
    Citizen 1: 1st, 2nd, 3rd, 4th, ...
    Citizen 2: 4th, 3rd, 1st, 2nd, ...  # Sacred value holder's rankings
    ...
```

### Rate Limiting
Different providers need different rate limiting configurations (configured in respective client files):
- **Google AI Studio free tier:** 15 RPM → sleep 5s every 5 calls (`aistudio_client.py`)
- **OpenAI:** higher RPM → sleep 2s every 10 calls (`openai_client.py`)
- **Anthropic:** sleep 3s every 5 calls (`anthropic_client.py`)

### LLM Client Constants (from `base_client.py`)
```python
DEFAULT_TEMPERATURE = 0.8
DEFAULT_MAX_TOKENS = 4096  # Increased to 8192 for some CoT models
DEFAULT_TIMEOUT_SECONDS = 60
```

### Results File Naming
- `results_MODEL.json` = full deliberation run (Experiment 1)
- `preference_space_results_PROVIDER_MODEL_Nruns.json` = preference space exploration (Experiment 2)
- These are DIFFERENT experiments with DIFFERENT data structures. Do not confuse them.

## Files to Ignore or Deprecate
- `sacred_value_analysis.py` — DEPRECATED. Throwaway plotting script with hardcoded Gemini data. Real analysis is in the Jupyter notebook.
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
- [x] Terminal logs captured for all 18 runs
- [x] Preference space exploration for OpenAI models (8 runs)
- [x] Architecture diagrams for CRM
- [x] Main analysis notebook (Kendall_Tau_Analysis.ipynb)
- [x] Kendall tau distance analysis for all 18 models (both opinion and critique rounds)
- [x] Sacred holder isolation index calculations for all 18 models
- [x] Individual citizen rankings consolidated from terminal logs into structured data
- [x] Cross-model comparison analysis (Gemini vs GPT statistical comparison)
- [x] Visualization suite: exclusion ratios, isolation indices, distance comparisons

### In Progress
- [ ] Interpretation and write-up of cross-model comparison findings

### Next
- [ ] Run Anthropic/Claude models (Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku minimum)
- [ ] Update requirements.txt with all actual dependencies
- [ ] Consider: additional deliberation scenarios beyond SSRI (to test generalizability)

## Git State
- **Current branch:** `sacred-value-experiments`
- **Main branch:** `main`
- **Status:** Clean (all changes committed)
- **Recent commits:**
  - `e0d08b9` Add CLAUDE.md, analysis notebook, prepare for Claude Code terminal setup
  - `5ba3316` Fix o1 model failures by increasing max_tokens to 8192
  - `08e8585` Show ALL profiles in output, not just top 10
  - `9a03077` Change default runs from 20 to 100 for statistical significance
  - `131acfa` Expand model lists to 6-7 models per provider for systematic testing

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

## Architecture Overview

The HabermasMachine class (`machine.py`) orchestrates the deliberation:

1. **Opinion Round:** Collect initial opinions from all citizens
2. **Statement Generation:** LLM generates `num_candidates` (default 16) candidate consensus statements
3. **Ranking:** Each citizen's opinion is used to predict their preference ranking over statements
4. **Aggregation:** Schulze voting method aggregates individual rankings into social ranking
5. **Critique Round:** Citizens critique the winning statement
6. **Refinement:** Process repeats with critiques informing new statement generation

Key components:
- **StatementModel** (`cot_model.py`): Chain-of-thought statement generation
- **RewardModel** (`cot_ranking_model.py`): Chain-of-thought preference ranking
- **SocialChoice** (`schulze_method.py`): Schulze ranked-choice voting
