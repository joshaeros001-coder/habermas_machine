# Sacred Values Architecture

## Overview

This is a **research implementation** of democratic deliberation that properly handles **sacred values as lexicographic constraints**, not weighted preferences.

### The Problem with Standard Consensus Algorithms

The standard Habermas Machine (and most consensus algorithms) treat all input as **negotiable preferences** that can be compromised and traded off. This works well for secular cost-benefit reasoning but fails catastrophically for **sacred values**.

**Sacred values** are non-negotiable moral commitments:
- Religious objections ("I cannot take medication due to my faith")
- Moral absolutes ("I refuse to compromise on this principle")
- Deontological constraints ("This violates my conscience")

**What goes wrong**: Standard algorithms try to "find middle ground" by compromising sacred values like they would compromise cost preferences. This:
- ❌ Alienates sacred value holders
- ❌ Produces consensus that violates constraints
- ❌ Treats "I cannot" as "I would prefer not to"

### Our Solution: Lexicographic Constraints

**Key insight**: Sacred values should be modeled as **hard constraints**, not soft preferences.

```
Standard approach (WRONG):
  citizen_utility = w1*cost + w2*efficacy + w3*religious_concern
  → Tries to find optimal weighted average (compromises everything)

Our approach (CORRECT):
  FIRST: Satisfy all sacred value constraints
  THEN: Optimize among feasible alternatives
  → Lexicographic ordering (constraints trump optimization)
```

---

## Architecture

### 1. Sacred Value Detection

**Input**: Citizen opinion (text)
**Output**: `(is_sacred: bool, confidence: float, constraint_text: str)`

**Algorithm**:
```python
# Detect sacred values by identifying:
1. Absolute language ("cannot", "must not", "refuse to")
2. Religious/moral justifications ("faith", "conscience", "God")
3. Explicit rejection of trade-offs ("not negotiable", "no compromise")

# Confidence scoring:
both absolute + sacred markers → 0.95 confidence
only absolute markers → 0.70 confidence
only sacred markers → 0.60 confidence
```

### 2. Constraint Compilation

**Input**: All citizen opinions + detected sacred values
**Output**: List of `Constraint` objects

**Algorithm**:
```python
for each citizen:
    if sacred value detected:
        compile constraint:
            - citizen_id
            - constraint_text (what they cannot do)
            - affected_actions (keywords: ["medication", "SSRI"])
            - constraint_type ("prohibition" or "requirement")
```

### 3. Constraint-Aware Statement Generation

**CRITICAL DIFFERENCE**: Generate statements that **satisfy all constraints from the start**.

**Standard approach** (wrong):
```python
# Generate diverse candidates (some may violate constraints)
candidates = [
    "Try SSRIs with monitoring",  # Violates religious objection!
    "Try therapy first",
    "Combine medication and therapy",  # Violates religious objection!
    "Patient should choose"
]
```

**Our approach** (correct):
```python
# Compile constraints FIRST
constraints = [
    Constraint(citizen=2, text="cannot take medication",
               affects=["medication", "SSRI", "pharmaceutical"])
]

# Generate ONLY constraint-satisfying candidates
candidates = [
    "For those whose faith prohibits medication, therapy and spiritual
     support are valid paths. Others may choose medical treatment. Both
     approaches deserve equal respect.",
    "Treatment should honor deeply held beliefs. Non-pharmaceutical
     options include therapy, lifestyle changes, and spiritual practices.",
    "No single approach is right for everyone. Religious objections to
     medication are non-negotiable constraints that must be respected."
]

# Note: None of these recommend medication as primary option because
# that would violate the constraint!
```

### 4. Constraint Filter (Safety Net)

Even with constraint-aware generation, LLMs might occasionally produce constraint-violating statements.

**Algorithm**:
```python
def filter_violating_statements(candidates, constraints):
    """Remove any statement that violates a sacred value constraint."""
    feasible = []
    violated = []

    for statement in candidates:
        if violates_any_constraint(statement, constraints):
            violated.append((statement, get_violated_constraint(statement)))
        else:
            feasible.append(statement)

    return feasible, violated  # Log violations for transparency
```

### 5. Constrained Voting

**Standard Schulze**: Rank all candidates, select winner

**Our modification**:
1. Filter out constraint-violating candidates BEFORE voting
2. Only vote on feasible set
3. If feasible set is empty → flag as INFEASIBLE, explain why

**Infeasibility handling**:
```python
if len(feasible_candidates) == 0:
    return InfeasibleResult(
        reason="No consensus can satisfy all sacred value constraints",
        conflicting_constraints=[list of incompatible constraints],
        recommendation="Acknowledge moral pluralism; no single answer exists"
    )
```

### 6. Transparency Logging

Every step is logged with **WHY** decisions were made:

```python
TransparencyLog:
    - detected_sacred_values: [list of detected values with confidence]
    - compiled_constraints: [list of constraints]
    - generated_candidates: [all candidates before filtering]
    - filtered_out: [(statement, reason) for violations]
    - final_feasible_set: [candidates voters saw]
    - constraint_satisfaction: {constraint: satisfied/violated}
    - explanation: "Natural language summary of constraint handling"
```

This makes the system **auditable** and **explainable**.

---

## Key Differences from Standard Habermas Machine

| Aspect | Standard HM | Sacred Values Architecture |
|--------|-------------|----------------------------|
| **Philosophy** | Consensus = weighted average | Consensus = constraint satisfaction |
| **Sacred values** | Treated as preferences | Treated as hard constraints |
| **Generation** | Generate diverse candidates | Generate only feasible candidates |
| **Voting** | Vote on all candidates | Vote only on constraint-satisfying |
| **Infeasibility** | Never occurs (always finds "middle ground") | Explicitly handled (acknowledges incompatibility) |
| **Transparency** | Limited | Complete (why-log for all decisions) |

---

## Example: SSRI with Religious Objection

### Standard Habermas Machine (problematic):

**Input**:
- Citizen 1: "Try SSRIs, benefits outweigh risks"
- Citizen 2: "I cannot take medication due to my Christian faith"
- Citizens 3-5: Various secular perspectives

**Output (standard)**:
> "The jury recommends carefully weighing the benefits of SSRIs against personal preferences, including religious considerations. Patients should discuss their concerns with their doctor and make an informed choice."

**Problem**: Treats faith as "preference" alongside cost concerns. Suggests religious objection can be "weighed" against benefits. This is offensive and alienating to Citizen 2.

### Our Architecture (correct):

**Step 1 - Detect**:
- Sacred value detected in Citizen 2's opinion
- Confidence: 0.95
- Constraint: "cannot take medication"

**Step 2 - Compile**:
- Constraint(citizen=2, prohibition=["medication", "SSRI", "pharmaceutical"])

**Step 3 - Generate**:
- Generate ONLY statements that don't recommend medication as primary option
- Acknowledge religious objection as non-negotiable

**Step 4 - Vote**:
- Vote on feasible statements only

**Output (ours)**:
> "Treatment decisions must respect deeply held religious and moral convictions. For those whose faith prohibits pharmaceutical intervention, non-medical approaches including therapy, spiritual support, and lifestyle changes are valid paths. For others, SSRIs may be appropriate after consultation with a doctor. Both perspectives reflect legitimate values that cannot be compromised. No single approach is universally correct."

**Why this is better**:
- ✅ Explicitly validates sacred value as non-negotiable
- ✅ Doesn't suggest faith should be "weighed" against benefits
- ✅ Acknowledges moral pluralism (multiple valid paths)
- ✅ Citizen 2 feels respected, not alienated

---

## Theoretical Foundation

### Lexicographic Preferences

From decision theory and economics:

**Standard utility**: `U = w1*x1 + w2*x2 + w3*x3` (everything is traded off)

**Lexicographic utility**:
```
1. FIRST: Satisfy all constraints (binary: yes/no)
2. THEN: Among feasible alternatives, optimize preferences
```

**Mathematical notation**:
```
Option A ≻ Option B ⟺
    (A satisfies constraints AND B violates constraints) OR
    (both satisfy constraints AND U(A) > U(B))
```

Sacred values create **lexicographic orderings** where constraint satisfaction trumps all other considerations.

### Moral Foundations Theory

Sacred values come from:
- **Sanctity/Purity** foundation (religion, tradition)
- **Authority/Respect** foundation (conscience, duty)
- **Care/Harm** foundation (protecting vulnerable)

These foundations create **protected values** that resist trade-offs (Tetlock et al., 2000).

---

## Implementation Details

### Sacred Value Detection (NLP)

**Heuristics**:
```python
# Absolute language indicators
absolute_markers = [
    "cannot", "can't", "must not", "will not", "won't", "refuse to",
    "never", "under no circumstances", "not negotiable"
]

# Sacred justification indicators
sacred_markers = [
    # Religious
    "god", "faith", "religious", "spiritual", "prayer", "church",
    "christian", "muslim", "jewish", "hindu", "buddhist", "pastor",

    # Moral
    "conscience", "moral", "ethics", "integrity", "sacred", "values",
    "principle", "belief", "conviction"
]

# Trade-off rejection
anti_tradeoff = [
    "no compromise", "not a cost-benefit", "matter of conscience",
    "non-negotiable", "cannot be weighed"
]
```

**Confidence scoring**:
```python
def calculate_confidence(text):
    absolute = count_markers(text, absolute_markers)
    sacred = count_markers(text, sacred_markers)
    anti_trade = count_markers(text, anti_tradeoff)

    # High confidence: multiple marker types
    if (absolute >= 1 and sacred >= 1) or anti_trade >= 1:
        return 0.95

    # Medium: one marker type strongly present
    elif absolute >= 2 or sacred >= 2:
        return 0.70

    # Low: weak signals
    elif absolute >= 1 or sacred >= 1:
        return 0.50

    else:
        return 0.10
```

### Constraint Extraction

**Example**:
```python
opinion = """
As a devout Christian, I believe depression is a spiritual trial.
Taking medication would be rejecting God's plan and showing lack of faith.
My pastor teaches that true healing comes through prayer. I cannot
compromise on this - it's a matter of spiritual integrity.
"""

detected = detect_sacred_value(opinion)
# Returns: (True, 0.95, "I cannot compromise on this - it's a matter of...")

constraint = compile_constraint(detected, opinion)
# Returns: Constraint(
#     citizen_id=2,
#     type="prohibition",
#     constraint_text="cannot compromise on refusing medication",
#     affected_actions=["medication", "SSRI", "pharmaceutical", "drug"],
#     justification="spiritual integrity, faith, God's plan"
# )
```

---

## Usage

### Basic Example

```python
from sacred_values_architecture import SacredValuesDeliberation

# Initialize
deliberation = SacredValuesDeliberation(
    question="Should patient accept SSRIs?",
    llm_client=claude_client,
    num_candidates=4
)

# Provide opinions
opinions = [
    "Try SSRIs, benefits outweigh risks",
    "I cannot take medication due to my faith",  # Sacred value!
    "Weigh costs and benefits carefully",
    "Combine medication with therapy",
    "Consult your doctor"
]

# Run deliberation
result = deliberation.run(opinions)

# Access results
print(result.consensus_statement)
print(f"Sacred values detected: {result.sacred_values}")
print(f"Constraints satisfied: {result.all_constraints_satisfied}")

# View transparency log
print(result.transparency_log.explanation)
```

### Advanced: Handling Infeasibility

```python
# Conflicting sacred values
opinions = [
    "Abortion is murder and must be prohibited",  # Sacred value: pro-life
    "Bodily autonomy is sacred, abortion is a right"  # Sacred value: pro-choice
]

result = deliberation.run(opinions)

if result.is_infeasible:
    print(f"Reason: {result.infeasibility_reason}")
    print(f"Conflicting constraints: {result.conflicting_constraints}")
    # Output: "No consensus can satisfy both 'prohibit abortion' and
    #          'protect abortion rights'. These are incompatible constraints."
```

---

## Testing

### Test Suite

```bash
# Test sacred value detection
pytest tests/test_detector.py

# Test constraint compilation
pytest tests/test_compiler.py

# Test SSRI Christian case (your core example)
pytest tests/test_ssri_christian.py

# Test batch of 50 vignettes
pytest tests/test_batch.py
```

### Expected Test Results

**test_ssri_christian.py**:
```python
def test_christian_objection():
    """Verify religious objection is handled as constraint, not preference."""
    result = deliberation.run(ssri_opinions_with_christian_objection)

    # Assert sacred value detected
    assert len(result.sacred_values) == 1
    assert result.sacred_values[0].confidence > 0.9

    # Assert constraint compiled
    assert len(result.constraints) == 1
    assert "medication" in result.constraints[0].affected_actions

    # Assert final consensus doesn't violate constraint
    assert not recommends_medication(result.consensus_statement)

    # Assert transparency
    assert result.transparency_log.constraint_satisfaction["no_medication"] == True
```

---

## Research Contributions

This architecture makes **three key contributions**:

### 1. Formal Treatment of Sacred Values
- First implementation of lexicographic constraints in LLM-mediated deliberation
- Moves beyond "preference elicitation" to "constraint satisfaction"

### 2. Explainable Constraint Handling
- Complete transparency log (why-log) for all decisions
- Auditable: can verify that constraints were respected

### 3. Principled Infeasibility Handling
- Explicitly acknowledges when consensus is impossible
- Doesn't force compromise where none exists
- Validates moral pluralism

---

## Limitations & Future Work

### Current Limitations

1. **Detection is heuristic**: Uses keyword matching, not deep semantic understanding
2. **Binary classification**: Sacred vs non-sacred (reality is continuous)
3. **Single LLM**: Claude generates statements; no ensemble
4. **English only**: Sacred value detection not tested on other languages

### Future Improvements

1. **Fine-tuned detector**: Train a classifier on labeled sacred value dataset
2. **Confidence thresholds**: Let users set what confidence level triggers constraints
3. **Interactive clarification**: Ask citizens "Is this non-negotiable?" when uncertain
4. **Constraint negotiation**: When infeasible, help citizens clarify which constraints are truly non-negotiable

---

## Citation

If you use this architecture in research:

```bibtex
@software{sacred_values_architecture,
  title={Sacred Values Architecture: Lexicographic Constraints for Democratic Deliberation},
  author={[Your Name]},
  year={2024},
  note={Extension of Habermas Machine (Tessler et al., 2024) with proper sacred value handling}
}
```

**Original Habermas Machine**:
```bibtex
@article{tessler2024ai,
  title={AI can help humans find common ground in democratic deliberation},
  author={Tessler, Michael Henry and Bakker, Michiel A and Jarrett, Daniel and others},
  journal={Science},
  year={2024}
}
```

**Sacred Values Theory**:
```bibtex
@article{tetlock2003thinking,
  title={Thinking the unthinkable: Sacred values and taboo cognitions},
  author={Tetlock, Philip E},
  journal={Trends in Cognitive Sciences},
  volume={7},
  number={7},
  pages={320--324},
  year={2003}
}
```

---

## License

Same license as Habermas Machine (Apache 2.0)

---

**This is a research prototype demonstrating how to properly handle sacred values in AI-mediated deliberation. It challenges the assumption that all preferences are negotiable and shows how to respect non-negotiable moral commitments in consensus-building.**
