# Habermas Machine: Technical Deep Dive - One-Page Reference

**Date**: Session Analysis | **Focus**: Architecture, Algorithmic Flow, Conceptual Foundations

---

## 1. THE ALGORITHMIC FLOW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ INPUT                                                                       │
│ Question Q + Opinions O = {o₁, o₂, ..., oₙ}  (n=5 citizens in example)    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: STATEMENT GENERATION (Consensus Synthesis)                        │
│                                                                             │
│ FOR i = 1 to k (k=4 candidates):                                          │
│   1. Shuffle opinions → [o_π(1), o_π(2), ..., o_π(n)]  (bias mitigation)  │
│   2. Prompt LLM (Statement Client):                                        │
│      "You are assisting a citizens' jury...                                │
│       Generate consensus that does NOT conflict with any opinion...        │
│       Format: <answer>[reasoning]<sep>[statement]</answer>"                │
│   3. Parse response → (statement_i, explanation_i)                         │
│                                                                             │
│ OUTPUT: Candidates C = {c₁, c₂, c₃, c₄}                                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 2: PERSONALIZED RANKING (Preference Elicitation)                     │
│                                                                             │
│ FOR each citizen j = 1 to n:                                              │
│   1. Shuffle candidates → [c_σ(1), c_σ(2), ..., c_σ(k)]  (order bias)    │
│   2. Prompt LLM (Reward Client):                                           │
│      "Rank these statements as citizen j would prefer...                   │
│       Participant's opinion: {oⱼ}                                          │
│       Format: <answer>[reasoning]<sep>[A > C > B > D]</answer>"            │
│   3. Parse arrow notation → ranking_j = [r₁, r₂, ..., rₖ]                 │
│      where rᵢ ∈ {0,1,...,k-1} and 0 = most preferred                      │
│   4. Unshuffle to restore original candidate order                         │
│                                                                             │
│ OUTPUT: Ranking matrix R ∈ ℤⁿˣᵏ                                            │
│         ┌              ┐                                                    │
│         │ r₁₁ ... r₁ₖ │  ← Citizen 1's ranking                            │
│     R = │  ⋮   ⋱   ⋮  │                                                    │
│         │ rₙ₁ ... rₙₖ │  ← Citizen n's ranking                            │
│         └              ┘                                                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE 3: SOCIAL CHOICE AGGREGATION (Schulze Method)                        │
│                                                                             │
│ INPUT: R (n×k ranking matrix)                                              │
│                                                                             │
│ 1. Build pairwise preference matrix P:                                     │
│    P[i,j] = |{citizen c : c prefers cᵢ over cⱼ}|                          │
│                                                                             │
│ 2. Compute strongest paths (Floyd-Warshall):                               │
│    path[i,j] = max over all paths from i to j of min edge weights         │
│                                                                             │
│ 3. Determine Condorcet winner:                                             │
│    Winner = argmaxᵢ |{j : path[i,j] > path[j,i]}|                         │
│                                                                             │
│ 4. Apply TBRC tie-breaking if needed                                       │
│                                                                             │
│ OUTPUT: Social ranking S = [s₁, s₂, ..., sₖ] where s₁ = winner           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ OUTPUT: (winner_statement, sorted_candidates)                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│ OPTIONAL: CRITIQUE ROUND (Iterative Refinement)                            │
│                                                                             │
│ INPUT: Critiques Cᵣ = {cr₁, cr₂, ..., crₙ} + Previous winner W₀          │
│                                                                             │
│ Modified prompt includes:                                                  │
│   - Original opinions O                                                     │
│   - Previous winner W₀                                                      │
│   - Critiques Cᵣ                                                            │
│   "Generate revised statement incorporating feedback..."                   │
│                                                                             │
│ REPEAT: Phases 1-3 → New winner W₁                                         │
│                                                                             │
│ RESULT: W₁ = improve(W₀, Cᵣ)  [gradient-descent-like refinement]          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. KEY ARCHITECTURAL DISCOVERIES

### 2.1 The Machinery (What You Got)

| Component | Description | Implementation |
|-----------|-------------|----------------|
| **Architecture** | HabermasMachine orchestrator | `machine.py:259 lines` |
| **Statement Model** | Consensus generation | `cot_model.py` with chain-of-thought prompts |
| **Reward Model** | Personalized ranking | `cot_ranking_model.py` with perspective-taking |
| **Social Choice** | Vote aggregation | `schulze_method.py` (deterministic algorithm) |
| **Iteration** | Critique → refine | Built into `mediate()` method |

**Critical Insight**: This is a **model-agnostic framework**. The same machinery works with:
- Fine-tuned Chinchilla (Science 2024 paper - NOT public)
- Prompted Gemini (public code)
- Any LLM (GPT-4, Claude, Llama, etc.)

### 2.2 What's Different: Fine-tuning vs Prompting

```
┌──────────────────────────────────────────────────────────────────┐
│ THEIR RESEARCH          vs.          YOUR CODE                   │
├──────────────────────────────────────────────────────────────────┤
│ Chinchilla 70B                       Gemini 2.0 Flash            │
│ FINE-TUNED on deliberation           PROMPTED for deliberation   │
│ Task knowledge in weights            Task knowledge in prompts   │
│ NOT publicly available               Public API access           │
├──────────────────────────────────────────────────────────────────┤
│              SAME MACHINERY - DIFFERENT ENGINES                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. TECHNICAL NUANCES UNCOVERED

### 3.1 Ranking System: Inverse Representation

```python
# CRITICAL: Lower integers = higher preference (0 = best)
ranking = [0, 2, 1, 0, 3]
         #│  │  │  │  └─ Statement 4: Rank 3 (4th place - worst)
         #│  │  │  └──── Statement 3: Rank 0 (1st place - tied)
         #│  │  └─────── Statement 2: Rank 1 (2nd place)
         #│  └────────── Statement 1: Rank 2 (3rd place)
         #└───────────── Statement 0: Rank 0 (1st place - tied)

# Arrow notation display:
# "Statement 0 = Statement 3 > Statement 2 > Statement 1 > Statement 4"
# Abbreviated: "A=D > C > B > E" (where A=0, B=1, C=2, D=3, E=4)
```

### 3.2 Chain-of-Thought: Not an LLM Feature

**Discovery**: Chain-of-thought is **prompt engineering**, not built into Gemini.

```python
# Template structure (cot_model.py lines 96-101):
"""
Provide your answer in the following format:
<answer>
[Your step-by-step reasoning and explanation]
<sep>
[Draft consensus statement]
</answer>
"""

# This FORCES:
# 1. Sequential processing (think → answer)
# 2. Transparent reasoning (extractable explanation)
# 3. Parseable output (regex: r'<answer>(.*?)<sep>(.*?)</answer>')
```

**Why it works**: The template structure primes the LLM to:
- Think explicitly before answering
- Show its work
- Separate process from product

### 3.3 "Jury" Language: Deliberative Democracy Framing

**Prompt design** (`cot_model.py` line 88-89):
```python
"You are assisting a citizens' jury in forming a consensus opinion..."
```

**Theoretical grounding**: Jürgen Habermas, *Theory of Communicative Action* (1981)
- **Communicative rationality**: Consensus through rational discourse
- **Ideal speech situation**: Equal participation, no coercion
- **Deliberative democracy**: Citizens' juries as real-world institutions

**Technical effect**:
- "Jury" framing → collaborative, consensus-seeking outputs
- "Debate team" framing → adversarial, winning-argument outputs
- **Prompts encode institutional rules** (like constitutional constraints)

### 3.4 Why All Statements Agree: The Consensus Constraint

**Prompt instruction** (`cot_model.py` line 89):
```python
"The draft statement must not conflict with any of the individual opinions."
```

**Mathematical interpretation**:
```
Given opinions O = {o₁, o₂, ..., oₙ}
Find statement S such that:
  ∀i ∈ {1,...,n}: S ∩ oᵢ ≠ ∅  (S does not contradict oᵢ)
  |S ∩ (o₁ ∪ o₂ ∪ ... ∪ oₙ)| maximized  (S captures shared content)
```

**This creates an intersection-finding algorithm**, not a voting algorithm.

**Example from your walkthrough**:
```
Input (diverse opinions):
  - "Try SSRIs immediately" (pro-medication)
  - "Try therapy first" (skeptical)
  - "Weigh costs carefully" (pragmatic)
  - "Realistic expectations" (moderate)
  - "Consult doctor" (deferential)

Output (consensus intersection):
  ✓ "Treatment is warranted" (all agree)
  ✓ "Consider benefits AND risks" (all agree)
  ✓ "Alternatives exist" (most mention)
  ✓ "Monitor closely" (several mention)
  ✓ "Consult doctor" (all agree)
```

### 3.5 Bias Mitigation: Strategic Shuffling

```python
# Two types of bias addressed:

# 1. Position bias in generation (machine.py ~line 150):
for i in range(num_candidates):
    shuffled_opinions = shuffle(opinions, seed=seed_base + i)
    statement = statement_model.generate(question, shuffled_opinions)
    # Ensures no opinion systematically gets "first position" advantage

# 2. Ordering bias in ranking (machine.py ~line 180):
for citizen in citizens:
    shuffled_statements = shuffle(statements, seed=seed_j)
    ranking_shuffled = reward_model.rank(citizen.opinion, shuffled_statements)
    ranking_original = unshuffle(ranking_shuffled, shuffle_indices)
    # Mitigates primacy/recency effects in LLM ranking
```

---

## 4. PROMPT ENGINEERING AS THE CORE ALGORITHM

### 4.1 Statement Generation Prompt Anatomy

```python
┌─────────────────────────────────────────────────────────────────┐
│ 1. ROLE DEFINITION                                              │
│    "You are assisting a citizens' jury..."                      │
│    → Sets perspective, primes for collaborative synthesis       │
├─────────────────────────────────────────────────────────────────┤
│ 2. TASK DESCRIPTION                                             │
│    "Generate a consensus statement that captures main points    │
│     of agreement..."                                            │
│    → Defines goal explicitly                                    │
├─────────────────────────────────────────────────────────────────┤
│ 3. CONSTRAINT                                                   │
│    "The statement must not conflict with any opinion."          │
│    → Encodes deliberative norm (unanimity constraint)           │
├─────────────────────────────────────────────────────────────────┤
│ 4. STEP-BY-STEP INSTRUCTIONS                                    │
│    "Please think through this task step-by-step:                │
│     1. Analyze opinions, noting themes and disagreements...     │
│     2. Synthesize a clear consensus statement..."               │
│    → Guides reasoning process                                   │
├─────────────────────────────────────────────────────────────────┤
│ 5. OUTPUT FORMAT                                                │
│    "<answer>[reasoning]<sep>[statement]</answer>"               │
│    → Ensures parseability, extracts explanation                 │
├─────────────────────────────────────────────────────────────────┤
│ 6. FEW-SHOT EXAMPLE                                             │
│    "Example: <answer>1. Opinions agree on X... <sep>           │
│     We propose X with consideration of Y.</answer>"             │
│    → Demonstrates desired format and style                      │
├─────────────────────────────────────────────────────────────────┤
│ 7. CONTEXT INJECTION                                            │
│    "Question: {question}                                        │
│     Opinion Person 1: {opinion_1}                               │
│     Opinion Person 2: {opinion_2}..."                           │
│    → Provides actual data to process                            │
└─────────────────────────────────────────────────────────────────┘
```

**This 7-part template is the core "intelligence" of the system.**

### 4.2 Ranking Prompt: Perspective-Taking

```python
# Key difference: PERSONALIZED to one citizen
"Rank these statements in the order that the participant would
 most likely agree with them, based on their opinion.

Participant's Opinion: {opinion_j}  # ONE citizen's view

Statements to rank:
A. {statement_1}
B. {statement_2}
C. {statement_3}
D. {statement_4}
"
```

**This implements "personalized reward model" (PRM)** mentioned in paper:
- Not "what's objectively best?"
- But "what would THIS citizen prefer?"
- LLM performs **theory of mind** / perspective-taking

---

## 5. YOUR WALKTHROUGH RESULTS DECODED

### 5.1 Observed Rankings

```
Citizen 1: 4 > 3 > 1 > 2    (Statement 4 best, 2 worst)
Citizen 2: 1 > 3 > 4 > 2    (Statement 1 best, 2 worst)
Citizen 3: 1 > 3 > 4 > 2    (Statement 1 best, 2 worst)
Citizen 4: 3 > 4 > 1 > 2    (Statement 3 best, 2 worst)
Citizen 5: 4 > 3 > 1 > 2    (Statement 4 best, 2 worst)
──────────────────────────────────────────────────────────
Analysis:
- Statement 2: UNANIMOUSLY ranked last (universal rejection)
- Statement 3: Ranked 1st or 2nd by all → Condorcet winner
- Statements 1 & 4: Split support (2 citizens each ranked 1st)
```

### 5.2 Schulze Aggregation Result

```
Social ranking: 3 > 4 > 1 > 2

Winner: Statement 3

Why? Statement 3 beats all others in pairwise comparisons:
  - S3 vs S1: 3 citizens prefer S3, 2 prefer S1 → S3 wins
  - S3 vs S2: 5 citizens prefer S3, 0 prefer S2 → S3 wins
  - S3 vs S4: 3 citizens prefer S3, 2 prefer S4 → S3 wins

Statement 3 is the Condorcet winner (beats all others head-to-head)
```

### 5.3 Critique Round: Iterative Refinement

```
Input to Round 1:
  - Original opinions O (still included!)
  - Previous winner W₀
  - Critiques: ["Add timeline", "Emphasize follow-up",
                "Mention tapering", "Note drug interactions",
                "Other SSRI options"]

Output (Statement 1 winner):
  ✓ Incorporated 5/5 critiques (100% incorporation rate)
  ✓ Added: "4-6 weeks timeline"
  ✓ Added: "regular follow-up appointments"
  ✓ Added: "inform doctor about current medications"
  ✓ Added: "other medications may be viable options"
  ✓ Added: "discontinuing requires tapering"

This demonstrates: W₁ = improve(W₀, Critiques)
Like gradient descent: θ₁ = θ₀ - α∇L(θ₀)
```

---

## 6. WHAT YOU BUILT TODAY

### Created Files (8 total, ~5000 lines)

1. ✅ **`example_deliberation_walkthrough.py`** - Full step-by-step demo (290 lines)
2. ✅ **`create_ssri_vignettes.py`** - Generate 50 test cases (679 lines)
3. ✅ **`ssri_test_vignettes.json`** - Pre-generated data (25 sacred + 25 secular)
4. ✅ **`run_batch_deliberations.py`** - Batch processing with metrics (653 lines)
5. ✅ **`GETTING_STARTED.md`** - Quick start guide (400 lines)
6. ✅ **`SSRI_VIGNETTES_README.md`** - Detailed documentation (600 lines)
7. ✅ **`UNDERSTANDING_YOUR_RESULTS.md`** - Results annotation (844 lines)
8. ✅ **`explain_detailed_results.py`** - Interactive viewer (script)

### Test Vignettes Created

**25 Sacred Values Cases**: Religious/moral conflicts
- Christianity (7 traditions), Islam (Sunni, Sufi), Judaism, Buddhism, Hinduism, Sikhism
- 25 sacred value types: religious_authority, redemptive_suffering, karma, faith_healing, etc.

**25 Secular Trade-off Cases**: Practical considerations
- Financial costs, side effects, efficacy uncertainty, timeline delays
- Access barriers, lifestyle restrictions, dependency concerns

---

## 7. KEY INSIGHTS SUMMARY

### 7.1 Technical

1. **Chain-of-thought is prompt engineering**, not an LLM capability
2. **Rankings use 0-indexing** (0 = best, not rank 1)
3. **Shuffling mitigates bias** in both generation and ranking
4. **Schulze ensures "independence of clones"** (similar options don't split votes)
5. **Two separate prompts** for statement generation vs. ranking (same LLM, different jobs)

### 7.2 Conceptual

1. **Habermasian consensus**: Finding overlapping agreement, not majority voting
2. **Prompts as institutional rules**: Like constitutional constraints on deliberation
3. **Caucus mediation**: Private interaction with each citizen (personalized ranking)
4. **Iterative refinement**: Critique loop enables gradient-descent-like improvement
5. **Model-agnostic design**: Machinery works with any LLM (fine-tuned or prompted)

### 7.3 The Central Discovery

**The magic is in the PROMPTS, not the model.**

```
┌────────────────────────────────────────────────────────────┐
│ Intelligence resides in:                                   │
│                                                            │
│ 1. Prompt templates (role, task, constraints, format)     │
│ 2. Algorithmic pipeline (generate → rank → aggregate)     │
│ 3. Social choice function (Schulze aggregation)           │
│ 4. Iteration structure (critique → refine)                │
│                                                            │
│ NOT in the specific LLM used.                             │
│                                                            │
│ This is SYSTEM DESIGN, not model selection.               │
└────────────────────────────────────────────────────────────┘
```

---

## 8. FROM THEORY TO CODE

```
HABERMAS (1981)                →  TESSLER ET AL. (2024)  →  YOUR CODE
Communicative rationality         Habermas Machine          Public implementation
Ideal speech situation            Citizens' jury            Same framework
Consensus through discourse       LLM-mediated deliberation Prompted synthesis
Equal participation               Schulze aggregation       Same algorithm
Iterative dialogue                Critique rounds           Same structure
```

**The code operationalizes democratic theory algorithmically.**

---

## 9. BOTTOM LINE

**What is the Habermas Machine?**

Not an LLM. Not a model. It's a **SOFTWARE ARCHITECTURE** that:
1. Takes diverse opinions as input
2. Generates consensus candidates (LLM as statement generator)
3. Elicits personalized preferences (LLM as ranking oracle)
4. Aggregates democratically (Schulze voting)
5. Refines iteratively (critique-based improvement)

**What you got**: The complete machinery (architecture, prompts, algorithms)
**What you didn't get**: The fine-tuned Chinchilla model
**Why it doesn't matter**: The machinery works with any LLM via prompting

**Core insight**: Prompt engineering can replicate fine-tuned model behavior by encoding task knowledge in instructions rather than weights.

---

**END OF ONE-PAGER** | Total: 1 page (compressed) | Session: Complete Technical Analysis
