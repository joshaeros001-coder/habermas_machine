"""
Constraint Compilation Module

This module converts detected sacred values into formal constraints that can be
checked against consensus statements.

A sacred value like "I cannot take medication due to my faith" becomes a
Constraint object with:
- Type: PROHIBITION (cannot do X)
- Affected actions: ["medication", "SSRI", "pharmaceutical", "drug"]
- Constraint text: "cannot take medication"

The compilation process:
1. Classify constraint type (prohibition vs requirement)
2. Extract affected actions (what is prohibited/required)
3. Create formal Constraint object
4. Validate constraint is well-formed

This enables automatic checking of whether a consensus statement violates
the sacred value constraint.
"""

from typing import List, Optional
import re
from ..models.sacred_value import SacredValue
from ..models.constraint import Constraint, ConstraintType


# ============================================================================
# ACTION EXTRACTION PATTERNS
# ============================================================================
# These patterns help extract what action is being constrained

# Medical/pharmaceutical actions (for SSRI vignette context)
MEDICAL_ACTION_KEYWORDS = [
    "medication", "medicine", "drug", "pharmaceutical", "prescription",
    "ssri", "antidepressant", "pill", "take medication", "taking medication"
]

# Therapy/treatment actions
THERAPY_ACTION_KEYWORDS = [
    "therapy", "therapist", "counseling", "psychotherapy", "cbt",
    "cognitive behavioral therapy"
]

# General action patterns
GENERAL_ACTION_PATTERNS = [
    r"take (\w+)",  # "take medication", "take drugs"
    r"try (\w+)",   # "try therapy", "try medication"
    r"use (\w+)",   # "use medication"
    r"accept (\w+)",  # "accept treatment"
    r"pursue (\w+)",  # "pursue therapy"
]


def classify_constraint_type(sacred_value: SacredValue) -> ConstraintType:
    """
    Determine if sacred value expresses prohibition or requirement.

    Prohibition: "I cannot/must not do X" → forbids an action
    Requirement: "I must do X" → mandates an action

    Most sacred values are prohibitions (forbidding actions that violate values).
    Requirements are rarer (mandating actions that uphold values).

    Args:
        sacred_value: The detected sacred value to classify

    Returns:
        ConstraintType.PROHIBITION or ConstraintType.REQUIREMENT

    Example:
        >>> sv = SacredValue(text="I cannot take medication", ...)
        >>> classify_constraint_type(sv)
        ConstraintType.PROHIBITION

        >>> sv2 = SacredValue(text="I must pray before any decision", ...)
        >>> classify_constraint_type(sv2)
        ConstraintType.REQUIREMENT
    """
    text_lower = sacred_value.text.lower()

    # Prohibition markers: Language of rejection/refusal
    prohibition_markers = [
        "cannot", "can't", "must not", "mustn't", "will not", "won't",
        "refuse to", "never", "not", "no", "reject", "opposed to"
    ]

    # Requirement markers: Language of obligation/necessity
    requirement_markers = [
        "must", "have to", "need to", "required to", "obligated to",
        "should", "ought to", "necessary", "essential"
    ]

    # Count how many of each type of marker appears
    prohibition_count = sum(1 for m in prohibition_markers if m in text_lower)
    requirement_count = sum(1 for m in requirement_markers if m in text_lower)

    # If prohibition markers dominate, it's a prohibition
    # Otherwise assume requirement (including tie-breaks)
    if prohibition_count > requirement_count:
        return ConstraintType.PROHIBITION
    else:
        # Note: If both are 0, we default to PROHIBITION as it's more common
        # in sacred values ("I cannot" is more typical than "I must")
        if prohibition_count == 0 and requirement_count == 0:
            return ConstraintType.PROHIBITION
        return ConstraintType.REQUIREMENT


def extract_affected_actions(sacred_value: SacredValue,
                             domain_keywords: Optional[List[str]] = None) -> List[str]:
    """
    Extract which specific actions are affected by this constraint.

    For a prohibition like "I cannot take medication due to my faith",
    we need to identify: ["medication", "SSRI", "pharmaceutical", "drug"]

    This allows us to check if a consensus statement prescribes any of these
    prohibited actions.

    Algorithm:
    1. Check for domain-specific keywords (e.g., medical terms)
    2. Use regex patterns to extract action phrases
    3. Expand to related terms (e.g., "medication" → "drug", "pharmaceutical")
    4. Return list of affected action keywords

    Args:
        sacred_value: The sacred value containing the constraint
        domain_keywords: Optional list of domain-specific keywords to check
            If None, uses default medical/therapy keywords

    Returns:
        List of action keywords affected by this constraint

    Example:
        >>> sv = SacredValue(text="I cannot take medication", ...)
        >>> extract_affected_actions(sv)
        ['medication', 'medicine', 'drug', 'pharmaceutical', 'prescription']
    """
    text_lower = sacred_value.text.lower()
    affected = []

    # Use default domain keywords if none provided
    if domain_keywords is None:
        domain_keywords = MEDICAL_ACTION_KEYWORDS + THERAPY_ACTION_KEYWORDS

    # Step 1: Check for direct keyword matches
    # If the constraint text mentions "medication", add all medication-related terms
    for keyword in domain_keywords:
        if keyword in text_lower:
            affected.append(keyword)

    # Step 2: Expand based on semantic clusters
    # If "medication" is mentioned, also add related terms
    medication_cluster = ["medication", "medicine", "drug", "pharmaceutical",
                         "prescription", "ssri", "antidepressant", "pill"]
    therapy_cluster = ["therapy", "therapist", "counseling", "psychotherapy"]

    # If any medication term found, add all medication terms
    if any(term in affected for term in medication_cluster):
        for term in medication_cluster:
            if term not in affected:
                affected.append(term)

    # If any therapy term found, add all therapy terms
    if any(term in affected for term in therapy_cluster):
        for term in therapy_cluster:
            if term not in affected:
                affected.append(term)

    # Step 3: Extract action phrases using regex patterns
    # Look for "cannot X", "refuse to X", etc.
    for pattern in GENERAL_ACTION_PATTERNS:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if match not in affected:
                affected.append(match)

    # Step 4: If we found nothing, extract nouns as fallback
    # This is a crude heuristic but better than nothing
    if not affected:
        # Extract words that might be actions (heuristic: 4+ letter words after "cannot")
        words = text_lower.split()
        for i, word in enumerate(words):
            if word in ["cannot", "can't", "must", "refuse", "will"]:
                # Look at next few words
                for j in range(i+1, min(i+4, len(words))):
                    potential_action = words[j].strip(".,;:!?")
                    if len(potential_action) >= 4:  # Filter out short words
                        affected.append(potential_action)
                        break

    return affected


def create_constraint_text(sacred_value: SacredValue,
                          constraint_type: ConstraintType) -> str:
    """
    Create a clear, concise constraint statement.

    This converts the original sacred value text into a normalized constraint
    description suitable for checking and logging.

    Args:
        sacred_value: The original sacred value
        constraint_type: The classified constraint type

    Returns:
        Normalized constraint text

    Example:
        >>> sv = SacredValue(text="I cannot take medication due to my faith", ...)
        >>> create_constraint_text(sv, ConstraintType.PROHIBITION)
        "cannot take medication"
    """
    text = sacred_value.text.strip()

    # Remove trailing punctuation
    text = text.rstrip(".!?")

    # If text is very long (>100 chars), try to extract just the constraint part
    if len(text) > 100:
        # Look for the sentence with "cannot" or "must"
        constraint_markers = ["cannot", "can't", "must not", "must", "will not",
                             "refuse to", "never"]

        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            sentence_lower = sentence.lower()

            for marker in constraint_markers:
                if marker in sentence_lower:
                    text = sentence
                    break

    # Truncate if still too long
    if len(text) > 150:
        text = text[:150] + "..."

    return text


def compile_constraint(sacred_value: SacredValue,
                      domain_keywords: Optional[List[str]] = None) -> Constraint:
    """
    Compile a sacred value into a formal constraint.

    This is the main entry point for constraint compilation. It takes a detected
    sacred value and converts it into a Constraint object that can be used to
    filter consensus statements.

    Algorithm:
    1. Classify constraint type (prohibition vs requirement)
    2. Extract affected actions (what is constrained)
    3. Create normalized constraint text
    4. Build Constraint object with all metadata
    5. Validate constraint is well-formed

    Args:
        sacred_value: The detected sacred value to compile
        domain_keywords: Optional domain-specific keywords for action extraction

    Returns:
        Compiled Constraint object

    Raises:
        ValueError: If constraint cannot be compiled (e.g., no actions extracted)

    Example:
        >>> sv = SacredValue(
        ...     citizen_id=2,
        ...     text="I cannot take medication due to my faith",
        ...     confidence=0.95,
        ...     markers=['cannot', 'faith'],
        ...     justification="religious faith"
        ... )
        >>> constraint = compile_constraint(sv)
        >>> constraint.type
        ConstraintType.PROHIBITION
        >>> constraint.affected_actions
        ['medication', 'medicine', 'drug', 'pharmaceutical', ...]
        >>> constraint.is_violated_by("The patient should try SSRIs")
        True  # Violates prohibition on medication
    """
    # Step 1: Classify constraint type
    # Determine if this is a prohibition ("cannot") or requirement ("must")
    constraint_type = classify_constraint_type(sacred_value)

    # Step 2: Extract affected actions
    # Identify what specific actions this constraint applies to
    affected_actions = extract_affected_actions(sacred_value, domain_keywords)

    # Validation: Must have at least one affected action
    # Without this, we can't check for violations
    if not affected_actions:
        raise ValueError(
            f"Cannot compile constraint: no affected actions extracted from "
            f"sacred value text '{sacred_value.text}'"
        )

    # Step 3: Create normalized constraint text
    # This is a clean, concise statement of the constraint
    constraint_text = create_constraint_text(sacred_value, constraint_type)

    # Step 4: Build Constraint object
    constraint = Constraint(
        citizen_id=sacred_value.citizen_id,
        type=constraint_type,
        constraint_text=constraint_text,
        affected_actions=affected_actions,
        justification=sacred_value.justification
    )

    return constraint


class ConstraintCompiler:
    """
    Stateful constraint compiler with configurable domain knowledge.

    This class wraps the compilation logic in an object that can be configured
    with domain-specific keywords and reused across multiple sacred values.

    Attributes:
        domain_keywords: Domain-specific action keywords (e.g., medical terms)
        verbose: Whether to print compilation details

    Example:
        >>> compiler = ConstraintCompiler(
        ...     domain_keywords=MEDICAL_ACTION_KEYWORDS,
        ...     verbose=True
        ... )
        >>> sacred_values = [sv1, sv2, sv3]
        >>> constraints = compiler.compile_batch(sacred_values)
    """

    def __init__(self, domain_keywords: Optional[List[str]] = None,
                 verbose: bool = False):
        """
        Initialize the compiler with configuration.

        Args:
            domain_keywords: Domain-specific keywords for action extraction
            verbose: If True, print compilation details
        """
        self.domain_keywords = domain_keywords or (
            MEDICAL_ACTION_KEYWORDS + THERAPY_ACTION_KEYWORDS
        )
        self.verbose = verbose

    def compile(self, sacred_value: SacredValue) -> Optional[Constraint]:
        """
        Compile a single sacred value into a constraint.

        Args:
            sacred_value: The sacred value to compile

        Returns:
            Constraint object, or None if compilation fails

        Example:
            >>> compiler = ConstraintCompiler()
            >>> sv = SacredValue(text="I cannot take medication", ...)
            >>> constraint = compiler.compile(sv)
            >>> constraint.type
            ConstraintType.PROHIBITION
        """
        try:
            constraint = compile_constraint(sacred_value, self.domain_keywords)

            if self.verbose:
                print(f"✓ Compiled constraint for Citizen {sacred_value.citizen_id}")
                print(f"  Type: {constraint.type.value}")
                print(f"  Text: {constraint.constraint_text}")
                print(f"  Affected actions ({len(constraint.affected_actions)}): "
                      f"{constraint.affected_actions[:5]}...")

            return constraint

        except ValueError as e:
            if self.verbose:
                print(f"✗ Failed to compile constraint for Citizen {sacred_value.citizen_id}")
                print(f"  Error: {e}")
            return None

    def compile_batch(self, sacred_values: List[SacredValue]) -> List[Constraint]:
        """
        Compile multiple sacred values into constraints.

        Args:
            sacred_values: List of sacred values to compile

        Returns:
            List of successfully compiled constraints

        Example:
            >>> compiler = ConstraintCompiler()
            >>> sacred_values = [sv1, sv2, sv3]
            >>> constraints = compiler.compile_batch(sacred_values)
            >>> len(constraints)
            3
        """
        constraints = []

        for sv in sacred_values:
            constraint = self.compile(sv)
            if constraint:
                constraints.append(constraint)

        return constraints

    def compile_all(self, sacred_values: List[SacredValue]
                   ) -> tuple[List[Constraint], List[SacredValue]]:
        """
        Compile all sacred values and report failures.

        Args:
            sacred_values: List of sacred values to compile

        Returns:
            Tuple of (successfully_compiled_constraints, failed_sacred_values)

        Example:
            >>> constraints, failures = compiler.compile_all(sacred_values)
            >>> print(f"Compiled: {len(constraints)}, Failed: {len(failures)}")
        """
        constraints = []
        failures = []

        for sv in sacred_values:
            constraint = self.compile(sv)
            if constraint:
                constraints.append(constraint)
            else:
                failures.append(sv)

        return constraints, failures


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    from .sacred_value_detector import detect_sacred_value

    print("="*80)
    print("CONSTRAINT COMPILATION EXAMPLE")
    print("="*80)

    # Example opinion with sacred value
    opinion = """
    As a devout Christian, I believe depression is a spiritual trial that God uses
    for growth. Taking medication would be rejecting His plan and showing lack of
    faith. My pastor teaches that true healing comes through prayer, fellowship,
    and trusting God's timing. I cannot compromise on this - it's a matter of
    spiritual integrity, not a cost-benefit calculation.
    """

    print("\n" + "-"*80)
    print("Step 1: Detect Sacred Value")
    print("-"*80)
    print(opinion.strip())

    # Step 1: Detect sacred value
    sacred_value = detect_sacred_value(opinion, citizen_id=2)

    if sacred_value:
        print("\n✓ Sacred value detected")
        print(f"  Confidence: {sacred_value.confidence:.2f}")
        print(f"  Markers: {sacred_value.markers}")
        print(f"  Text: {sacred_value.text}")

        # Step 2: Compile into constraint
        print("\n" + "-"*80)
        print("Step 2: Compile Constraint")
        print("-"*80)

        constraint = compile_constraint(sacred_value)

        print("\n✓ Constraint compiled")
        print(f"  Type: {constraint.type.value.upper()}")
        print(f"  Constraint text: {constraint.constraint_text}")
        print(f"  Affected actions ({len(constraint.affected_actions)}): ")
        for action in constraint.affected_actions[:10]:
            print(f"    - {action}")
        print(f"  Justification: {constraint.justification}")

        # Step 3: Test constraint violation
        print("\n" + "-"*80)
        print("Step 3: Test Constraint Violation")
        print("-"*80)

        test_statements = [
            "The patient should try SSRIs with close monitoring.",
            "For those whose faith prohibits medication, therapy and spiritual "
            "support are valid alternatives.",
            "Patients should weigh costs and benefits carefully.",
        ]

        for i, statement in enumerate(test_statements, 1):
            violated = constraint.is_violated_by(statement)
            status = "❌ VIOLATES" if violated else "✓ SATISFIES"
            print(f"\nStatement {i}: {status}")
            print(f"  \"{statement}\"")

    else:
        print("\n✗ No sacred value detected")

    print("\n" + "="*80)
    print("BATCH COMPILATION EXAMPLE")
    print("="*80)

    opinions = [
        "I think medication is cost-effective and worth trying.",
        "I cannot take medication due to my religious beliefs.",
        "Therapy might be better than medication for some people.",
    ]

    print("\nProcessing 3 opinions:\n")

    # Detect all sacred values
    from .sacred_value_detector import SacredValueDetector
    detector = SacredValueDetector(confidence_threshold=0.7)
    sacred_values = detector.detect_batch(opinions)

    print(f"\nFound {len(sacred_values)} sacred value(s)")

    # Compile all into constraints
    compiler = ConstraintCompiler(verbose=True)
    constraints = compiler.compile_batch(sacred_values)

    print(f"\n{'='*80}")
    print(f"RESULTS: Compiled {len(constraints)} constraint(s)")
    print(f"{'='*80}")
