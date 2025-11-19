"""
Prompt Templates for Constraint-Aware Statement Generation

ADAPTED FROM: habermas_machine/statement_model/ (scattered across files)
KEY CHANGE: Adds explicit constraint injection into prompts
WHY: Standard CRM doesn't tell the LLM about hard constraints; we need to inject them

This module contains prompt templates that:
1. Present the deliberation question
2. Present all citizen opinions
3. INJECT SACRED VALUE CONSTRAINTS (NEW)
4. Instruct LLM to generate consensus statements that satisfy constraints

The constraint injection is the critical innovation.
"""

from typing import List
from ..models.constraint import Constraint


def format_constraint_for_prompt(constraint: Constraint) -> str:
    """
    Format a single constraint for injection into the LLM prompt.

    This creates a natural language description of the constraint that the LLM
    can understand and respect during generation.

    Args:
        constraint: The constraint to format

    Returns:
        Natural language constraint description

    Example:
        >>> constraint = Constraint(
        ...     citizen_id=2,
        ...     type=ConstraintType.PROHIBITION,
        ...     constraint_text="cannot take medication",
        ...     affected_actions=["medication", "SSRI", "drug"],
        ...     justification="religious faith"
        ... )
        >>> format_constraint_for_prompt(constraint)
        "⚠️ HARD CONSTRAINT: Citizen 2 stated 'cannot take medication' (justification: religious faith).
         You MUST NOT generate a consensus that recommends: medication, SSRI, drug.
         This is a non-negotiable sacred value that cannot be compromised."
    """
    # Format the constraint type
    if constraint.type.value == "prohibition":
        constraint_type_text = "MUST NOT"
        action_verb = "recommends or prescribes"
    else:  # requirement
        constraint_type_text = "MUST"
        action_verb = "includes or mandates"

    # Format affected actions
    actions_list = ", ".join(constraint.affected_actions[:5])
    if len(constraint.affected_actions) > 5:
        actions_list += f", and {len(constraint.affected_actions) - 5} other related terms"

    # Build the constraint description
    constraint_desc = f"""⚠️ HARD CONSTRAINT from Citizen {constraint.citizen_id}:
   Statement: "{constraint.constraint_text}"
   Justification: {constraint.justification}

   You {constraint_type_text} generate consensus statements that {action_verb}: {actions_list}

   This is a NON-NEGOTIABLE sacred value. Any consensus that violates this constraint
   will be automatically rejected. You must generate statements that respect this
   constraint while finding common ground with other citizens."""

    return constraint_desc


def build_constrained_generation_prompt(
    question: str,
    opinions: List[str],
    constraints: List[Constraint],
    num_candidates: int = 4
) -> str:
    """
    Build a prompt for constraint-aware consensus statement generation.

    This is the CORE INNOVATION: injecting sacred value constraints directly
    into the generation prompt so the LLM generates ONLY feasible statements.

    Standard CRM: Generates arbitrary statements, hopes they work
    Our approach: Tell LLM about constraints upfront, generate feasible statements

    Args:
        question: The deliberation question
        opinions: List of citizen opinions (strings)
        constraints: List of compiled sacred value constraints
        num_candidates: Number of candidate statements to generate

    Returns:
        Complete prompt string for the LLM

    Example:
        >>> prompt = build_constrained_generation_prompt(
        ...     question="Should patient take SSRIs?",
        ...     opinions=[op1, op2, op3],
        ...     constraints=[medication_prohibition],
        ...     num_candidates=4
        ... )
        >>> # Prompt will instruct LLM to avoid recommending medication
    """
    # Start with the basic task description
    prompt = f"""You are mediating a citizens' jury deliberation. The jury must reach a consensus
statement that addresses the following question:

QUESTION: {question}

The jury consists of {len(opinions)} citizens with different perspectives:

"""

    # Add each citizen's opinion
    for i, opinion in enumerate(opinions):
        prompt += f"""CITIZEN {i}:
{opinion.strip()}

"""

    # Add constraint section if any constraints exist
    if constraints:
        prompt += f"""\n{'='*80}
⚠️⚠️⚠️ SACRED VALUE CONSTRAINTS ⚠️⚠️⚠️
{'='*80}

The following citizens have expressed SACRED VALUES - deeply held moral or religious
commitments that are NON-NEGOTIABLE. These are NOT ordinary preferences that can be
compromised through voting. They are HARD CONSTRAINTS that the consensus MUST satisfy.

"""
        # Add each constraint
        for constraint in constraints:
            prompt += format_constraint_for_prompt(constraint)
            prompt += "\n\n"

        prompt += f"""{'='*80}

CRITICAL INSTRUCTION: You MUST generate consensus statements that satisfy ALL of the
above constraints. Any statement that violates a sacred value constraint will be
automatically filtered out and cannot be selected as the final consensus.

Think of these as FEASIBILITY CONSTRAINTS in an optimization problem:
- Standard deliberation: Maximize agreement (unconstrained optimization)
- This deliberation: Maximize agreement SUBJECT TO satisfying all sacred value constraints
                     (constrained optimization)

"""

    # Add generation instructions
    prompt += f"""YOUR TASK:

Generate {num_candidates} distinct consensus statement candidates that:

1. ADDRESS THE QUESTION: Directly respond to the deliberation question
2. FIND COMMON GROUND: Identify points of agreement among citizens
3. RESPECT ALL CONSTRAINTS: {"Satisfy all sacred value constraints listed above" if constraints else "Balance all citizen preferences"}
4. BE SPECIFIC: Provide actionable guidance, not vague platitudes
5. BE FAIR: Acknowledge different perspectives where appropriate

"""

    if constraints:
        prompt += """CONSTRAINT SATISFACTION STRATEGIES:

- ACKNOWLEDGE the sacred value explicitly ("For those whose faith prohibits...")
- OFFER ALTERNATIVES that respect the constraint ("non-pharmaceutical approaches...")
- FRAME AS CHOICE rather than prescription ("individuals may choose...")
- AVOID PRESCRIPTIVE LANGUAGE for constrained actions ("should not", "must", "recommend")

"""

    # Add output format instructions
    prompt += f"""OUTPUT FORMAT:

Generate exactly {num_candidates} candidates, each labeled CANDIDATE 1, CANDIDATE 2, etc.

Each candidate should be 2-4 sentences that could serve as the jury's consensus statement.

CANDIDATE 1:
[Your first consensus statement here]

CANDIDATE 2:
[Your second consensus statement here]

... and so on.

BEGIN GENERATION:
"""

    return prompt


def build_simple_generation_prompt(
    question: str,
    opinions: List[str],
    num_candidates: int = 4
) -> str:
    """
    Build a simple generation prompt WITHOUT constraints.

    This is used when no sacred values are detected - falls back to
    standard consensus generation.

    Args:
        question: The deliberation question
        opinions: List of citizen opinions
        num_candidates: Number of candidates to generate

    Returns:
        Simple generation prompt

    Example:
        >>> prompt = build_simple_generation_prompt(question, opinions)
    """
    # Just call the constrained version with empty constraints list
    return build_constrained_generation_prompt(
        question=question,
        opinions=opinions,
        constraints=[],
        num_candidates=num_candidates
    )


# ============================================================================
# PARSING UTILITIES
# ============================================================================

def parse_generated_candidates(response: str) -> List[str]:
    """
    Parse candidate statements from LLM response.

    The LLM generates statements in the format:
    CANDIDATE 1:
    [statement text]

    CANDIDATE 2:
    [statement text]

    This function extracts each statement.

    Args:
        response: The raw LLM response text

    Returns:
        List of parsed candidate statements

    Example:
        >>> response = '''
        ... CANDIDATE 1:
        ... The patient should consider therapy.
        ...
        ... CANDIDATE 2:
        ... Multiple treatment options exist.
        ... '''
        >>> parse_generated_candidates(response)
        ['The patient should consider therapy.', 'Multiple treatment options exist.']
    """
    candidates = []

    # Split by "CANDIDATE N:" markers
    lines = response.split('\n')

    current_candidate = []
    in_candidate = False

    for line in lines:
        line_stripped = line.strip()

        # Check if this is a candidate marker
        if line_stripped.startswith('CANDIDATE'):
            # Save previous candidate if exists
            if current_candidate:
                candidate_text = '\n'.join(current_candidate).strip()
                if candidate_text:
                    candidates.append(candidate_text)

            # Start new candidate
            # Check if the statement is on the same line after the colon
            if ':' in line_stripped:
                parts = line_stripped.split(':', 1)
                if len(parts) > 1 and parts[1].strip():
                    # Statement starts on same line
                    current_candidate = [parts[1].strip()]
                else:
                    # Statement starts on next line
                    current_candidate = []
                in_candidate = True
            else:
                current_candidate = []
                in_candidate = True

        elif in_candidate and line_stripped:
            # Add to current candidate
            current_candidate.append(line_stripped)

        elif in_candidate and not line_stripped:
            # Empty line - might be end of candidate or just spacing
            # We'll continue accumulating until we hit next CANDIDATE marker
            pass

    # Don't forget the last candidate
    if current_candidate:
        candidate_text = '\n'.join(current_candidate).strip()
        if candidate_text:
            candidates.append(candidate_text)

    return candidates


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    from ..models.constraint import Constraint, ConstraintType

    print("="*80)
    print("CONSTRAINT-AWARE PROMPT GENERATION EXAMPLE")
    print("="*80)

    # Example: SSRI deliberation with religious objection
    question = """Should a 35-year-old patient with moderate depression accept their
doctor's recommendation to start SSRI antidepressants?"""

    opinions = [
        "I think SSRIs can help with moderate depression. The evidence shows they're effective.",
        "As a devout Christian, I believe depression is a spiritual trial. I cannot take medication due to my faith.",
        "The patient should weigh the evidence carefully and consult their doctor.",
        "I support trying SSRIs with realistic expectations about benefits and side effects.",
    ]

    # Create a constraint (religious objection to medication)
    constraint = Constraint(
        citizen_id=1,
        type=ConstraintType.PROHIBITION,
        constraint_text="cannot take medication due to my faith",
        affected_actions=["medication", "SSRI", "antidepressant", "drug", "pharmaceutical"],
        justification="religious faith"
    )

    # Build constrained prompt
    prompt = build_constrained_generation_prompt(
        question=question,
        opinions=opinions,
        constraints=[constraint],
        num_candidates=3
    )

    print("\n" + "-"*80)
    print("GENERATED PROMPT (first 1000 chars):")
    print("-"*80)
    print(prompt[:1000])
    print("...")
    print("\n" + "="*80)
    print("This prompt explicitly tells the LLM to avoid recommending medication.")
    print("The LLM will generate ONLY feasible statements that respect the constraint.")
    print("="*80)
