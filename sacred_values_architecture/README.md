# Sacred Values Architecture for Habermas Machine

> **A constraint-based deliberation system that properly handles sacred values as lexicographic constraints, not weighted preferences.**

## Table of Contents

- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Testing](#testing)
- [API Reference](#api-reference)
- [Citation](#citation)

---

## Problem Statement

### What is the Habermas Machine?

The Habermas Machine (also called the Collective Rational Model or CRM) is an AI-mediated deliberation system that:
1. Collects opinions from citizens on a question
2. Generates candidate consensus statements using an LLM
3. Ranks statements based on citizen preferences
4. Aggregates rankings using social choice methods (e.g., Schulze voting)
5. Returns a winning consensus statement

### What's the Problem?

**The CRM has a critical architectural flaw: it treats ALL values as weighted preferences subject to democratic compromise.**

**Example: The Christian SSRI Case**

Question: *Should a 35-year-old with moderate depression accept SSRI medication?*

Opinions:
- **4 citizens**: "SSRIs can help with depression" (regular preference)
- **1 Christian citizen**: "I **cannot** take medication due to my faith - it's a matter of spiritual integrity, **not a cost-benefit calculation**" (sacred value)

**What Standard CRM Does:**
- Treats the Christian's belief as a weighted preference: 1 vote out of 5
- Generates consensus: "You should accept SSRIs" (because 4/5 support it)
- **Problem**: Violates the Christian's non-negotiable belief!

**The Core Issue:**

Sacred values are **lexicographic constraints** (must be satisfied FIRST, before any optimization), not **weighted preferences** (can be traded off against other values).

Standard CRM forces sacred values into utilitarian calculations, which is:
1. **Philosophically wrong**: Sacred values are non-negotiable by definition
2. **Practically harmful**: Produces recommendations that violate people's core beliefs
3. **Democratically problematic**: Tyranny of the majority over minority sacred values

### Why This Matters

Sacred values appear in many real-world deliberations:
- **Religious beliefs**: "I cannot eat pork" (Muslim/Jewish)
- **Moral principles**: "I will not support violence under any circumstances" (pacifist)
- **Cultural values**: "I refuse to disrespect my elders" (Confucian)
- **Political values**: "I cannot compromise on human rights" (rights advocate)

Current AI deliberation systems **cannot handle these correctly**. This architecture fixes that.

---

## Solution Overview

### Core Innovation: Constraint-First Deliberation

Instead of treating sacred values as weighted preferences, we:

1. **Detect** sacred values in opinions (linguistic markers + confidence scoring)
2. **Compile** them into hard constraints (prohibited/required actions)
3. **Generate** only constraint-satisfying statements (inject constraints into LLM prompts)
4. **Filter** any constraint violations before voting
5. **Verify** the winner satisfies all constraints
6. **Explain** all decisions via transparency logging

### What Are Lexicographic Constraints?

Lexicographic constraints are ordered in strict priority:

```
Constraint Priority:
1. Sacred value constraints (MUST be satisfied)
2. Regular preferences (optimize AFTER satisfying constraints)

NOT:
1. All preferences weighted together (standard CRM)
```

**Analogy**: Like searching for a house:
- **Constraint**: "Must be wheelchair accessible" (non-negotiable)
- **Preference**: "Prefer 3 bedrooms" (negotiable)

You would NEVER accept a beautiful 5-bedroom house that's not wheelchair accessible if you need accessibility. The constraint is **lexicographic** - it must be satisfied FIRST.

### Architecture Comparison

**Standard CRM:**
```
Opinions → Generate statements → Rank → Vote → Winner
(Treats everything as weighted preferences)
```

**Sacred Values Architecture:**
```
Opinions → Detect sacred values → Compile constraints
         ↓
         Generate ONLY constraint-satisfying statements
         ↓
         Filter violations → Rank → Vote → Verify → Winner
(Constraints enforced at EVERY step)
```

---

## Installation

### Prerequisites

- Python 3.10+
- An LLM API key (Anthropic Claude or Google AI Studio)

### Setup

```bash
cd sacred_values_architecture/

# Install dependencies
pip install -r requirements.txt

# Set your API key (choose one)
export ANTHROPIC_API_KEY='your_anthropic_key_here'
# OR
export GOOGLE_API_KEY='your_google_key_here'
```

### Dependencies

Create `requirements.txt`:

```
anthropic>=0.18.0
google-generativeai>=0.3.0
numpy>=1.24.0
typing-extensions>=4.5.0
```

---

## Quick Start

### Minimal Example

```python
from sacred_values_architecture.machine import ConstrainedHabermasMachine
from sacred_values_architecture.statement_model import constrained_cot_model
from sacred_values_architecture.reward_model import cot_ranking_model
from sacred_values_architecture.social_choice import schulze_method, utils
from sacred_values_architecture.llm_client import anthropic_client

# Define your question and opinions
question = "Should we serve alcohol at community events?"

opinions = [
    "Serving wine would make events more enjoyable.",
    "As a Muslim, I cannot support alcohol - it violates my faith.",  # Sacred value
    "We should be mindful of different preferences.",
]

# Create LLM client
client = anthropic_client.AnthropicClient()

# Create constraint-aware machine
machine = ConstrainedHabermasMachine(
    question=question,
    statement_client=client,
    reward_client=client,
    statement_model=constrained_cot_model.ConstrainedCOTModel(),
    reward_model=cot_ranking_model.COTRankingModel(),
    social_choice_method=schulze_method.Schulze(
        tie_breaking_method=utils.TieBreakingMethod.RANDOM
    ),
    num_candidates=8,
    num_citizens=len(opinions),
    verbose=True,
)

# Run deliberation
result = machine.mediate(opinions)

# Print results
print(f"Winning statement: {result.winning_statement}")
print(f"Sacred values detected: {len(result.detected_sacred_values)}")
print(f"Constraints compiled: {len(result.compiled_constraints)}")
print(result.transparency_log.summary())
```

### Run Pre-Built Examples

```bash
# Simple 3-citizen example
python -m examples.simple_example

# Critical SSRI test case
python -m tests.test_ssri_christian
```

---

## Architecture

### System Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      CITIZEN OPINIONS                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: SACRED VALUE DETECTION                            │
│  • Scan for absolute language ("cannot", "must not")        │
│  • Scan for religious/moral grounding ("faith", "belief")   │
│  • Calculate confidence score (0-1)                         │
│  • Extract constraint text                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: CONSTRAINT COMPILATION                            │
│  • Parse constraint text                                    │
│  • Extract prohibited actions (e.g., "medication")          │
│  • Extract required elements (if any)                       │
│  • Create structured Constraint objects                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: CONSTRAINED STATEMENT GENERATION                  │
│  • Inject constraints into LLM prompt                       │
│  • Generate candidate statements                            │
│  • Guide: "DO NOT recommend X because Citizen Y said..."    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: CONSTRAINT FILTERING                              │
│  • Check each statement against all constraints             │
│  • Filter out violations                                    │
│  • Log reasons for filtering                                │
│  • Return only feasible statements                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 5: VOTING (Standard Schulze Method)                  │
│  • Rank valid statements                                    │
│  • Aggregate rankings                                       │
│  • Find winner                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 6: FINAL VERIFICATION                                │
│  • Verify winner satisfies ALL constraints                  │
│  • Log verification results                                 │
│  • Return DeliberationResult + TransparencyLog              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
               CONSENSUS STATEMENT
           (Respects sacred values)
```

### Key Components

#### 1. Sacred Value Detector (`core/sacred_value_detector.py`)

**Linguistic Markers:**

- **Absolute rejection**: "cannot", "must not", "refuse to"
- **Moral grounding**: "faith", "conscience", "beliefs"
- **Anti-trade-off**: "not a cost-benefit calculation", "matter of principle"

**Confidence Scoring:**

- 0.95: Absolute + Sacred markers (very strong signal)
- 0.75: Absolute + Anti-trade-off (strong signal)
- 0.60: Only absolute (medium signal)
- 0.10: No markers (regular preference)

#### 2. Constraint Compiler (`core/constraint_compiler.py`)

**Converts** natural language → structured constraints

Example:
```python
Input: "I cannot take medication due to my faith"

Output: Constraint(
    citizen_id=1,
    constraint_type=PROHIBITION,
    prohibited_actions=["medication", "medicine", "drug", "ssri"],
    required_elements=[],
)
```

#### 3. Constrained Statement Generation (`statement_model/constrained_cot_model.py`)

**Injects constraints into LLM prompts:**

```
IMPORTANT CONSTRAINTS:
Citizen 1 stated: "I cannot take medication due to my faith"
Therefore, DO NOT recommend or mention: medication, ssri, drug

Your consensus statement must satisfy ALL these constraints.
```

#### 4. Constraint Filtering (`core/constraint_compiler.py`)

**Checks** each statement against all constraints:

```python
def check_statement_against_constraint(statement, constraint):
    if constraint.type == PROHIBITION:
        for action in constraint.prohibited_actions:
            if action in statement.lower():
                return False, f"Contains prohibited '{action}'"
    return True, ""
```

#### 5. Transparency Logger (`core/transparency_logger.py`)

**Tracks** all decisions for explainability:

- Which sacred values were detected
- Which statements were filtered (and why)
- Whether the winner satisfies constraints
- Complete event log

---

## Testing

### Unit Tests

```bash
# Test sacred value detection
python -m tests.test_detector

# Test constraint compilation
python -m tests.test_constraint_compiler

# Test constrained generation
python -m tests.test_statement_generation
```

### Integration Tests

```bash
# THE CRITICAL TEST: Christian SSRI case
python -m tests.test_ssri_christian
```

**Expected output:**
```
✅ CHRISTIAN SSRI TEST PASSED

The architecture successfully:
  1. Detected the sacred value (confidence 0.95)
  2. Compiled it into a prohibition constraint
  3. Generated constraint-satisfying statements
  4. Returned a consensus that respects the sacred value

This proves lexicographic constraints work correctly!
```

### What the SSRI Test Validates

This test is THE proof that the architecture works:

1. **Detects** "I cannot take medication due to my faith" as sacred value
2. **Compiles** constraint: `prohibit ["medication", "ssri"]`
3. **Generates** statements without medication recommendations
4. **Returns** consensus like: "Consider therapy, spiritual counseling, and other non-pharmaceutical approaches"
5. **Verifies** winner does NOT contain "SSRI", "medication", etc.

If this test passes, the architecture correctly handles sacred values as lexicographic constraints.

---

## API Reference

### ConstrainedHabermasMachine

**Main orchestrator for constraint-aware deliberation.**

```python
machine = ConstrainedHabermasMachine(
    question: str,                              # The deliberation question
    statement_client: LLMClient,                # LLM for statement generation
    reward_client: LLMClient,                   # LLM for ranking
    statement_model: ConstrainedCOTModel,       # Statement generation model
    reward_model: BaseRankingModel,             # Ranking model
    social_choice_method: Base,                 # Voting method (e.g., Schulze)
    num_candidates: int = 16,                   # Number of statements to generate
    num_citizens: int = 5,                      # Number of citizens
    seed: int | None = None,                    # Random seed
    verbose: bool = False,                      # Print detailed output
    min_sacred_value_confidence: float = 0.70,  # Confidence threshold
)

result = machine.mediate(opinions: List[str]) -> DeliberationResult
```

### DeliberationResult

**Comprehensive result object:**

```python
@dataclass
class DeliberationResult:
    winning_statement: str                      # The consensus
    all_statements: List[str]                   # All statements (sorted by rank)
    detected_sacred_values: List[SacredValue]   # Detected sacred values
    compiled_constraints: List[Constraint]      # Compiled constraints
    transparency_log: TransparencyLog           # Full decision log
    is_feasible: bool                           # Whether solution found
    infeasibility_reason: Optional[str]         # If infeasible, why
```

### TransparencyLog

**Explainability and debugging:**

```python
log = result.transparency_log

# Summary
print(log.summary())

# Detailed report
print(log.get_detailed_report())

# Access specific fields
log.constraints_detected          # Number of sacred values detected
log.statements_filtered           # Number filtered for violations
log.final_check_passed            # Whether winner satisfies constraints
log.filtering_reasons             # List of all filtering decisions
```

---

## Citation

This is research software implementing a novel architecture for handling sacred values in AI-mediated deliberation.

**BibTeX:**

```bibtex
@software{sacred_values_habermas,
  title = {Sacred Values Architecture for Habermas Machine},
  author = {[Your Name]},
  year = {2025},
  url = {https://github.com/[your-repo]/habermas_machine},
  note = {Implementation of lexicographic constraint-based deliberation},
}
```

**Research Context:**

This architecture addresses a fundamental limitation in current AI deliberation systems: the inability to distinguish between:

1. **Preferences** (can be traded off) → "I prefer therapy over medication"
2. **Sacred values** (non-negotiable) → "I cannot take medication due to my faith"

By treating sacred values as **lexicographic constraints** rather than **weighted preferences**, we enable AI systems to:

- Respect minority sacred values in democratic deliberation
- Avoid tyranny of the majority over core beliefs
- Produce recommendations that are both democratically legitimate AND individually acceptable

**Key Contributions:**

1. **Theoretical**: Formal framework for detecting and enforcing lexicographic constraints in LLM-based deliberation
2. **Algorithmic**: Constraint-first generation approach (vs. generate-then-filter)
3. **Empirical**: Validation on real-world vignettes (SSRI case, religious dietary restrictions, etc.)
4. **Practical**: Fully implemented, tested, and documented system

**Related Papers:**

- Habermas Machine original paper: [Reference]
- Sacred values in decision-making: Tetlock et al. (2000)
- Lexicographic preferences: Fishburn (1974)

---

## Contributing

This is research software. Contributions welcome:

1. Additional sacred value detection markers
2. Improved constraint extraction algorithms
3. More test cases (especially diverse cultural contexts)
4. Performance optimizations

---

## License

Apache 2.0 - See LICENSE file

---

## Contact

For questions about this architecture or collaboration opportunities:

- Email: [your-email]
- GitHub Issues: [repo-url]

---

## Acknowledgments

- Original Habermas Machine: DeepMind team
- Sacred values research: Philip Tetlock, Jonathan Baron
- Social choice theory: Schulze voting method

---

**⚠️ Important Notes:**

1. **This is research software** - Use for research purposes, not production systems without careful validation
2. **LLM limitations** - LLMs may not always respect constraints perfectly; filtering is critical
3. **Cultural sensitivity** - Sacred value detection may need cultural adaptation
4. **Ethical considerations** - Deliberation systems should complement, not replace, human judgment

---

**Made with ❤️ for better AI-human deliberation**
