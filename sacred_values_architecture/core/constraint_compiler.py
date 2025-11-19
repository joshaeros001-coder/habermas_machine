# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Constraint Compiler - Converts Sacred Values to Enforceable Constraints.

After detecting sacred values, we need to compile them into structured constraints
that can be:
1. Injected into LLM prompts to guide statement generation
2. Checked against candidate statements to filter violations
3. Explained in the transparency log

COMPILATION PROCESS:
1. Parse the constraint text to identify prohibited/required actions
2. Extract key terms that indicate violations
3. Create structured Constraint object
4. Provide natural language description for transparency

This is where we go from "I cannot take medication due to my faith" to
a machine-checkable constraint like: prohibited_actions=["medication", "SSRI", "pharmaceutical"]
"""

from typing import List, Set
import re

from sacred_values_architecture.types import SacredValue, Constraint, ConstraintType


# ==============================================================================
# ACTION EXTRACTION PATTERNS
# ==============================================================================

# Common medical/action terms that might be prohibited or required
COMMON_ACTIONS = {
    # Medical interventions
    "medication", "medicine", "drug", "pharmaceutical", "prescription",
    "ssri", "antidepressant", "antidepressants", "pills",

    # Therapies
    "therapy", "psychotherapy", "counseling", "treatment",

    # Alternative approaches
    "prayer", "spiritual", "faith-based", "religious",
    "meditation", "mindfulness", "exercise",

    # General actions
    "surgery", "procedure", "intervention", "hospitalization",
}


# ==============================================================================
# CORE COMPILATION FUNCTION
# ==============================================================================

def compile_constraint(sacred_value: SacredValue) -> Constraint:
    """Compile a sacred value into an enforceable constraint.

    This converts natural language sacred values into structured constraints
    that can be checked programmatically.

    ALGORITHM:
    1. Determine constraint type (prohibition vs requirement)
    2. Extract prohibited/required actions from the text
    3. Create structured Constraint object

    Args:
        sacred_value: The detected sacred value to compile

    Returns:
        Constraint object with structured prohibited/required actions

    Example:
        >>> sv = SacredValue(
        ...     citizen_id=1,
        ...     constraint_text="I cannot take medication due to my faith",
        ...     ...
        ... )
        >>> constraint = compile_constraint(sv)
        >>> constraint.constraint_type
        ConstraintType.PROHIBITION
        >>> "medication" in constraint.prohibited_actions
        True
    """
    constraint_text = sacred_value.constraint_text.lower()

    # STEP 1: Determine constraint type
    # Look for prohibition markers ("cannot", "must not") vs requirement markers ("must", "need to")
    prohibition_indicators = [
        "cannot", "can't", "must not", "mustn't", "refuse", "won't", "will not",
        "against", "opposed to", "no", "never", "reject"
    ]
    requirement_indicators = [
        "must", "need to", "require", "have to", "should", "ought to"
    ]

    has_prohibition = any(ind in constraint_text for ind in prohibition_indicators)
    has_requirement = any(ind in constraint_text for ind in requirement_indicators)

    if has_prohibition:
        constraint_type = ConstraintType.PROHIBITION
    elif has_requirement:
        constraint_type = ConstraintType.REQUIREMENT
    else:
        # Default to prohibition if unclear
        constraint_type = ConstraintType.PROHIBITION

    # STEP 2: Extract prohibited/required actions
    # Look for action terms in the constraint text
    prohibited_actions = []
    required_elements = []

    if constraint_type == ConstraintType.PROHIBITION:
        # Extract what is being prohibited
        # Look for common action terms mentioned in the text
        for action in COMMON_ACTIONS:
            if action in constraint_text:
                prohibited_actions.append(action)

        # Also extract words near "cannot", "refuse", etc.
        # Pattern: "cannot [word]" or "refuse [word]" or "against [word]"
        prohibition_patterns = [
            r"cannot\s+(\w+)",
            r"can't\s+(\w+)",
            r"refuse\s+(?:to\s+)?(\w+)",
            r"against\s+(?:my\s+)?(\w+)",
            r"won't\s+(\w+)",
            r"will not\s+(\w+)",
            r"no\s+(\w+)",
        ]

        for pattern in prohibition_patterns:
            matches = re.findall(pattern, constraint_text)
            for match in matches:
                if match not in prohibited_actions and len(match) > 3:
                    prohibited_actions.append(match)

    elif constraint_type == ConstraintType.REQUIREMENT:
        # Extract what is being required
        for action in COMMON_ACTIONS:
            if action in constraint_text:
                required_elements.append(action)

        # Pattern: "must [word]" or "need [word]"
        requirement_patterns = [
            r"must\s+(\w+)",
            r"need\s+to\s+(\w+)",
            r"require\s+(\w+)",
            r"should\s+(\w+)",
        ]

        for pattern in requirement_patterns:
            matches = re.findall(pattern, constraint_text)
            for match in matches:
                if match not in required_elements and len(match) > 3:
                    required_elements.append(match)

    # STEP 3: Handle special case - identify what they DO want (for context)
    # If someone says "cannot take medication", they might mention prayer/faith
    # Extract these as context for alternative recommendations
    if constraint_type == ConstraintType.PROHIBITION:
        # Look for what they DO support
        positive_terms = ["prayer", "spiritual", "faith", "religious", "god",
                          "therapy", "counseling", "exercise", "meditation"]
        for term in positive_terms:
            if term in constraint_text and term not in prohibited_actions:
                # These are NOT prohibited, they're alternatives
                # Don't add to required_elements (too strong), just note them
                pass

    # STEP 4: Create structured Constraint object
    constraint = Constraint(
        sacred_value=sacred_value,
        prohibited_actions=prohibited_actions,
        required_elements=required_elements,
        constraint_type=constraint_type,
    )

    return constraint


# ==============================================================================
# BATCH COMPILATION
# ==============================================================================

def compile_constraints_batch(sacred_values: List[SacredValue]) -> List[Constraint]:
    """Compile multiple sacred values into constraints.

    Args:
        sacred_values: List of detected sacred values

    Returns:
        List of compiled constraints

    Example:
        >>> sacred_values = detect_sacred_values_batch(opinions)
        >>> constraints = compile_constraints_batch(sacred_values)
        >>> len(constraints)
        2
    """
    return [compile_constraint(sv) for sv in sacred_values]


# ==============================================================================
# CONSTRAINT CHECKING
# ==============================================================================

def check_statement_against_constraint(
    statement: str,
    constraint: Constraint
) -> tuple[bool, str]:
    """Check if a statement violates a constraint.

    This is the core validation function used to filter out constraint-violating
    candidate statements.

    Args:
        statement: The candidate statement to check
        constraint: The constraint to check against

    Returns:
        Tuple of:
        - passes: True if statement satisfies constraint, False if it violates
        - reason: Explanation of why it failed (empty string if it passes)

    Example:
        >>> statement = "You should start taking SSRI medication"
        >>> constraint = Constraint(..., prohibited_actions=["medication", "ssri"])
        >>> passes, reason = check_statement_against_constraint(statement, constraint)
        >>> passes
        False
        >>> "medication" in reason.lower()
        True
    """
    statement_lower = statement.lower()

    if constraint.constraint_type == ConstraintType.PROHIBITION:
        # Check if statement contains any prohibited actions
        for action in constraint.prohibited_actions:
            if action.lower() in statement_lower:
                # Found a violation
                reason = (
                    f"Statement contains prohibited action '{action}' "
                    f"(Citizen {constraint.citizen_id} constraint: "
                    f'"{constraint.sacred_value.constraint_text}")'
                )
                return False, reason

        # No prohibitions found - passes
        return True, ""

    elif constraint.constraint_type == ConstraintType.REQUIREMENT:
        # Check if statement contains all required elements
        for element in constraint.required_elements:
            if element.lower() not in statement_lower:
                # Missing a requirement
                reason = (
                    f"Statement missing required element '{element}' "
                    f"(Citizen {constraint.citizen_id} constraint: "
                    f'"{constraint.sacred_value.constraint_text}")'
                )
                return False, reason

        # All requirements found - passes
        return True, ""

    else:
        # Unknown constraint type - default to pass
        return True, ""


def check_statement_against_all_constraints(
    statement: str,
    constraints: List[Constraint]
) -> tuple[bool, List[str]]:
    """Check if a statement violates ANY constraints.

    A statement must satisfy ALL constraints to be valid.

    Args:
        statement: The candidate statement to check
        constraints: List of all constraints to check

    Returns:
        Tuple of:
        - passes: True if satisfies all constraints, False if violates any
        - reasons: List of violation reasons (empty if passes)

    Example:
        >>> statement = "Consider medication or therapy"
        >>> constraints = [constraint1, constraint2]
        >>> passes, reasons = check_statement_against_all_constraints(statement, constraints)
        >>> if not passes:
        ...     print(f"Failed: {reasons}")
    """
    reasons = []

    for constraint in constraints:
        passes, reason = check_statement_against_constraint(statement, constraint)
        if not passes:
            reasons.append(reason)

    # Statement passes only if it satisfies ALL constraints
    all_pass = len(reasons) == 0
    return all_pass, reasons


# ==============================================================================
# CONSTRAINT DESCRIPTION FOR TRANSPARENCY
# ==============================================================================

def describe_constraint(constraint: Constraint) -> str:
    """Generate human-readable description of a constraint.

    Used in transparency logs to explain what constraints are being enforced.

    Args:
        constraint: The constraint to describe

    Returns:
        Natural language description

    Example:
        >>> constraint = Constraint(..., prohibited_actions=["medication"])
        >>> describe_constraint(constraint)
        "Citizen 1 prohibits: medication (from: 'I cannot take medication due to my faith')"
    """
    citizen_id = constraint.citizen_id
    constraint_text = constraint.sacred_value.constraint_text

    if constraint.constraint_type == ConstraintType.PROHIBITION:
        actions_str = ", ".join(constraint.prohibited_actions)
        return (
            f"Citizen {citizen_id} prohibits: {actions_str} "
            f"(from: '{constraint_text}')"
        )
    elif constraint.constraint_type == ConstraintType.REQUIREMENT:
        elements_str = ", ".join(constraint.required_elements)
        return (
            f"Citizen {citizen_id} requires: {elements_str} "
            f"(from: '{constraint_text}')"
        )
    else:
        return f"Citizen {citizen_id} constraint: '{constraint_text}'"


def get_constraint_injection_prompt(constraints: List[Constraint]) -> str:
    """Generate prompt text to inject constraints into LLM generation.

    This is how we guide the LLM to generate only constraint-satisfying statements.

    CRITICAL for constraint-first generation: Rather than generating arbitrary
    statements and filtering, we tell the LLM upfront what constraints exist.

    Args:
        constraints: List of constraints to inject

    Returns:
        Formatted text to add to LLM prompt

    Example:
        >>> prompt_addition = get_constraint_injection_prompt(constraints)
        >>> full_prompt = base_prompt + "\n\n" + prompt_addition
    """
    if not constraints:
        return ""

    prompt = "\n\nIMPORTANT CONSTRAINTS:\n"
    prompt += "The following citizens have expressed non-negotiable constraints that MUST be respected:\n\n"

    for i, constraint in enumerate(constraints, 1):
        citizen_id = constraint.citizen_id
        constraint_text = constraint.sacred_value.constraint_text

        if constraint.constraint_type == ConstraintType.PROHIBITION:
            actions_str = ", ".join(constraint.prohibited_actions)
            prompt += (
                f"{i}. Citizen {citizen_id} stated: \"{constraint_text}\"\n"
                f"   Therefore, DO NOT recommend or mention: {actions_str}\n\n"
            )
        elif constraint.constraint_type == ConstraintType.REQUIREMENT:
            elements_str = ", ".join(constraint.required_elements)
            prompt += (
                f"{i}. Citizen {citizen_id} stated: \"{constraint_text}\"\n"
                f"   Therefore, consensus MUST include: {elements_str}\n\n"
            )

    prompt += (
        "Your consensus statement must satisfy ALL these constraints. "
        "Do not generate statements that violate any citizen's non-negotiable beliefs.\n"
    )

    return prompt
