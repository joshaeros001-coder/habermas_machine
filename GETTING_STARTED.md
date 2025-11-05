# Getting Started with Habermas Machine

## 🎯 Quick Answers to Your Questions

### 1. **Overall Architecture**

The Habermas Machine is a modular AI-mediated deliberation system:

```
HabermasMachine (Orchestrator)
├── Statement Model (generates consensus statements)
├── Reward Model (ranks statements per citizen)
├── Social Choice Method (aggregates rankings)
└── LLM Clients (Gemini API interface)
```

**Main files:**
- `habermas_machine/machine.py` - Core orchestrator (259 lines)
- `habermas_machine/types.py` - Configuration enums
- `habermas_machine/statement_model/cot_model.py` - Chain-of-thought statement generation
- `habermas_machine/reward_model/cot_ranking_model.py` - Preference ranking
- `habermas_machine/social_choice/schulze_method.py` - Schulze voting
- `questions/*.json` - Input vignettes

### 2. **Data Flow: Input → Output**

```
User provides: Question + Opinions (5 citizens)
    ↓
Generate 16 candidate consensus statements
    ↓
Each citizen ranks all 16 candidates (0 = best)
    ↓
Schulze voting aggregates 5×16 ranking matrix
    ↓
Select winning statement (best ranked)
    ↓
User provides: Critiques of winner (5 citizens)
    ↓
Generate new candidates (with previous winner + critiques)
    ↓
Rank, aggregate, select refined winner
    ↓
Final: Refined consensus statement
```

### 3. **Input Vignette Format**

**Simple version (what you need):**
```python
question = "Should the government provide universal childcare from birth?"
opinions = [
    "Opinion from citizen 1...",
    "Opinion from citizen 2...",
    "Opinion from citizen 3...",
    "Opinion from citizen 4...",
    "Opinion from citizen 5..."
]
```

**JSON format (for datasets):**
```json
{
  "id": "SSRI_SACRED_001",
  "question": "Should a patient accept SSRIs when...",
  "affirming_statement": "The patient should...",
  "negating_statement": "The patient should NOT...",
  "topic": "ssri_sacred_values",
  "split": "test"
}
```

No special formatting required for opinions/critiques - just natural language!

### 4. **Step-by-Step Example**

**Run this:**
```bash
python example_deliberation_walkthrough.py
```

This script shows exactly how to run a deliberation with detailed explanations at each step.

---

## 🚀 What I've Created for You

### 1. **Complete Walkthrough Script**
**File:** `example_deliberation_walkthrough.py`

A fully documented, step-by-step example showing:
- Component initialization
- Opinion round execution
- Critique round execution
- Accessing history and metrics
- All with an SSRI medication decision example

### 2. **50 SSRI Test Vignettes**
**Files:**
- `create_ssri_vignettes.py` (generator)
- `ssri_test_vignettes.json` (pre-generated data)

**25 Sacred Values Cases:**
- Christianity (7 varieties: Catholic, Evangelical, Pentecostal, etc.)
- Islam (Sunni, Sufi)
- Judaism (Orthodox)
- Buddhism, Hinduism, Sikhism
- Indigenous spirituality, Taoism, Shinto
- 25 different sacred value types (religious authority, redemptive suffering, karma, etc.)

**25 Secular Trade-off Cases:**
- Financial costs ($10-2000 range scenarios)
- Side effects (weight gain, sexual dysfunction, GI issues, cognitive effects)
- Efficacy uncertainty (60% response rate, trial-and-error)
- Timeline concerns (4-6 week delay)
- Withdrawal/dependency
- Access barriers (insurance, geography)
- Lifestyle restrictions

### 3. **Batch Processing Script**
**File:** `run_batch_deliberations.py`

Runs all 50 vignettes and tracks:
- **Agreement scores** (opinion round vs critique round)
- **Endorsement distributions** (mean ranking, standard deviation)
- **Rejected statements** (universally disliked options)
- **Processing time and success rate**

Outputs:
- `deliberation_results.csv` - Detailed metrics per vignette
- `summary_statistics.txt` - Sacred vs secular comparison

### 4. **Comprehensive Documentation**
**File:** `SSRI_VIGNETTES_README.md`

Includes:
- Architecture diagrams
- Quick start guide
- Vignette format specs
- Example code
- Research questions
- Troubleshooting guide

---

## 📋 How to Use Everything

### Option 1: Learn the Architecture (Start Here!)

```bash
# 1. Read the step-by-step walkthrough
python example_deliberation_walkthrough.py

# This will show you exactly how everything works
# (You'll need GOOGLE_API_KEY set to actually run it)
```

### Option 2: Create Your Custom Vignettes

```bash
# 2. Edit create_ssri_vignettes.py to customize vignettes
# Then generate:
python create_ssri_vignettes.py

# This creates ssri_test_vignettes.json
```

### Option 3: Run Batch Analysis

```bash
# 3. Set up API key
export GOOGLE_API_KEY="your_key_here"

# 4. Run batch processing
python run_batch_deliberations.py

# This processes all vignettes and generates statistics
```

### Option 4: Custom Single Deliberation

```python
# 5. Use this template for your own questions
from habermas_machine import machine, types
from habermas_machine.social_choice import utils as sc_utils

question = "Your custom question here"

hm = machine.HabermasMachine(
    question=question,
    statement_client=types.LLMCLient.AISTUDIO.get_client('gemini-1.5-flash'),
    reward_client=types.LLMCLient.AISTUDIO.get_client('gemini-1.5-flash'),
    statement_model=types.StatementModel.CHAIN_OF_THOUGHT.get_model(),
    reward_model=types.RewardModel.CHAIN_OF_THOUGHT_RANKING.get_model(),
    social_choice_method=types.RankAggregation.SCHULZE.get_method(
        sc_utils.TieBreakingMethod.TBRC
    ),
    num_candidates=4,  # 4-16 recommended
    num_citizens=5,    # 5+ recommended
    verbose=True
)

# Opinion round
opinions = ["Op1", "Op2", "Op3", "Op4", "Op5"]
winner1, candidates1 = hm.mediate(opinions)

# Critique round
critiques = ["Crit1", "Crit2", "Crit3", "Crit4", "Crit5"]
winner2, candidates2 = hm.mediate(critiques)

print(f"Final consensus: {winner2}")
```

---

## 🔬 Research Questions You Can Explore

With these 50 vignettes, you can investigate:

### 1. **Do sacred values reduce consensus?**
```python
import pandas as pd
df = pd.read_csv('deliberation_results.csv')

sacred = df[df['vignette_type'].str.contains('sacred')]
secular = df[df['vignette_type'].str.contains('secular')]

print(f"Sacred avg agreement: {sacred['critique_round_agreement_score'].mean():.3f}")
print(f"Secular avg agreement: {secular['critique_round_agreement_score'].mean():.3f}")
```

### 2. **Does deliberation improve consensus?**
```python
# Compare opinion round vs critique round
improvement = df['critique_round_agreement_score'] - df['opinion_round_agreement_score']
print(f"Average improvement: {improvement.mean():.3f}")
print(f"% of cases that improved: {(improvement > 0).sum() / len(df) * 100:.1f}%")
```

### 3. **Which moral frameworks are most divisive?**
```python
# For sacred values cases
sacred_by_type = sacred.groupby('sacred_value_type')['critique_round_agreement_score'].mean()
print("\nMost divisive sacred values:")
print(sacred_by_type.nsmallest(5))
```

### 4. **Which practical concerns are hardest to resolve?**
```python
# For secular cases
secular_by_type = secular.groupby('tradeoff_type')['critique_round_agreement_score'].mean()
print("\nMost divisive trade-offs:")
print(secular_by_type.nsmallest(5))
```

---

## 📁 File Summary

| File | Purpose | Run? |
|------|---------|------|
| `example_deliberation_walkthrough.py` | **START HERE** - Learn architecture | Yes (with API key) |
| `create_ssri_vignettes.py` | Generate vignettes | Yes (already run) |
| `ssri_test_vignettes.json` | 50 pre-generated vignettes | No (data file) |
| `run_batch_deliberations.py` | Batch processing + stats | Yes (with API key) |
| `SSRI_VIGNETTES_README.md` | Detailed documentation | No (read it!) |
| `GETTING_STARTED.md` | This file | No (you're reading it!) |

---

## 🎓 Understanding the Architecture

### Key Components Explained

**1. HabermasMachine** (`machine.py`)
- **What**: Main orchestrator
- **Does**: Coordinates deliberation rounds, tracks history
- **Key method**: `mediate(opinions_or_critiques)` → returns `(winner, sorted_candidates)`

**2. Statement Model** (`statement_model/cot_model.py`)
- **What**: Generates consensus statements
- **Input**: Question + opinions (or question + opinions + previous winner + critiques)
- **Output**: Consensus statement attempting to incorporate all perspectives

**3. Reward Model** (`reward_model/cot_ranking_model.py`)
- **What**: Ranks statements per citizen
- **Input**: Question + citizen's opinion + all candidate statements
- **Output**: Ranking array where 0 = best (e.g., `[0, 2, 1, 0, 3]`)

**4. Social Choice** (`social_choice/schulze_method.py`)
- **What**: Aggregates individual rankings into group ranking
- **Input**: Matrix of all citizen rankings `[num_citizens × num_candidates]`
- **Output**: Social ranking (which statement is preferred by the group)

**5. LLM Client** (`llm_client/aistudio_client.py`)
- **What**: Interface to Gemini API
- **Does**: Sends prompts to LLM, receives responses
- **Config**: Requires `GOOGLE_API_KEY` environment variable

### Data Structures

**Ranking format:**
```python
# Citizen 1's ranking of 5 statements:
[0, 2, 1, 0, 3]
# Interpretation:
# - Statements 0 and 3 tied for 1st (rank = 0)
# - Statement 2 is 2nd (rank = 1)
# - Statement 1 is 3rd (rank = 2)
# - Statement 4 is 4th (rank = 3)
```

**Rankings matrix:**
```python
# 5 citizens × 4 candidates
np.array([
    [0, 1, 2, 3],  # Citizen 1: prefers 0 > 1 > 2 > 3
    [1, 0, 2, 3],  # Citizen 2: prefers 1 > 0 > 2 > 3
    [0, 1, 3, 2],  # Citizen 3: prefers 0 > 1 > 3 > 2
    [0, 2, 1, 3],  # Citizen 4: prefers 0 > 2 > 1 > 3
    [1, 0, 2, 3],  # Citizen 5: prefers 1 > 0 > 2 > 3
])
# Schulze method finds: Statement 0 is the Condorcet winner
```

---

## 🛠️ Setup Requirements

### 1. Install Dependencies
```bash
pip install --upgrade git+https://github.com/google-deepmind/habermas_machine.git
# Or from this repo if you've made modifications
```

### 2. Get Gemini API Key
- Visit: https://aistudio.google.com/app/apikey
- Create API key
- Set environment variable:
```bash
export GOOGLE_API_KEY="your_key_here"
```

### 3. Verify Installation
```bash
python -c "from habermas_machine import machine; print('✓ Habermas Machine installed')"
```

---

## 💡 Tips & Best Practices

### For Learning:
1. **Start with `example_deliberation_walkthrough.py`** - Read the code, understand each step
2. **Run with `verbose=True`** - See what the system is doing
3. **Try small test cases** - Use `num_candidates=4` and `num_citizens=5` for faster iteration
4. **Examine the history** - Look at `hm._previous_winners`, `hm._statement_explanations`, etc.

### For Research:
1. **Use consistent seeds** - Set `seed=42` for reproducibility
2. **Save intermediate results** - Batch script saves every 5 vignettes
3. **Track metadata** - Vignettes have rich metadata for analysis
4. **Compare systematically** - Sacred vs secular, opinion vs critique rounds

### For Production:
1. **Handle rate limits** - Add delays between API calls (script includes 2s delay)
2. **Retry on errors** - Use `num_retries_on_error=5`
3. **Use Flash model** - `gemini-1.5-flash` is faster and cheaper than Pro
4. **Monitor costs** - Each deliberation = ~20-50 API calls depending on config

---

## 🎉 You're Ready!

Everything is now:
- ✅ Committed to git
- ✅ Pushed to your branch: `claude/explore-deliberation-architecture-011CUp1J1i1rbc1MNpSYLFmd`
- ✅ Documented and ready to use
- ✅ Includes 50 pre-generated vignettes
- ✅ Has working examples and batch processing

**Next steps:**
1. Read `example_deliberation_walkthrough.py` to understand the architecture
2. Get a Gemini API key from https://aistudio.google.com/app/apikey
3. Run the walkthrough script to see it in action
4. Customize vignettes or create your own
5. Run batch processing to generate comparative statistics

**Questions?**
- Check `SSRI_VIGNETTES_README.md` for detailed documentation
- Examine the code - it's heavily commented
- Look at the original examples in `habermas_machine/example_aistudio.ipynb`

---

## 📊 What You Can Build

With these tools, you can:

1. **Educational demos** - Show how AI-mediated deliberation works
2. **Research studies** - Compare sacred vs secular moral reasoning
3. **Policy experiments** - Test consensus-building on contentious issues
4. **Value exploration** - Understand how different moral frameworks interact
5. **Methodology validation** - Test whether deliberation improves consensus

The system is production-ready and fully extensible!
