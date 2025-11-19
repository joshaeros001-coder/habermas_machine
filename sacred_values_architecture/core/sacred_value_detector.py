"""
Sacred Value Detection Module

This module implements heuristic-based detection of sacred values in citizen opinions.
Sacred values are non-negotiable moral or religious commitments that should be treated
as hard constraints, not soft preferences.

Detection strategy:
1. Identify absolute language ("cannot", "must not", "refuse to")
2. Identify sacred justifications ("faith", "god", "conscience", "moral")
3. Identify anti-tradeoff language ("non-negotiable", "no compromise")
4. Calculate confidence score based on marker combinations
5. Extract the constraint text (what they cannot/must do)

This is a heuristic approach using keyword matching. Future versions could use
fine-tuned classifiers or LLM-based semantic understanding.
"""

from typing import Tuple, List, Optional
import re
from ..models.sacred_value import SacredValue


# ============================================================================
# DETECTION MARKERS
# ============================================================================
# These keyword lists define what linguistic patterns indicate sacred values

# Absolute language: Rejection or requirement with no room for negotiation
ABSOLUTE_MARKERS = [
    "cannot", "can't", "must not", "mustn't", "will not", "won't",
    "refuse to", "never", "under no circumstances", "not negotiable",
    "no way", "impossible", "absolutely not", "categorically",
    "without exception", "unconditionally"
]

# Sacred justifications: Religious, moral, or conscience-based reasoning
SACRED_MARKERS = [
    # Religious
    "god", "faith", "religious", "spiritual", "prayer", "church",
    "christian", "muslim", "jewish", "hindu", "buddhist", "bible",
    "scripture", "divine", "holy", "sacred", "lord", "pastor",
    "imam", "rabbi", "priest", "salvation", "soul", "sin",

    # Moral/Ethical
    "conscience", "moral", "morality", "ethics", "ethical", "integrity",
    "principle", "principled", "belief", "conviction", "values",
    "sacred value", "deeply held"
]

# Anti-tradeoff language: Explicit rejection of cost-benefit reasoning
ANTI_TRADEOFF_MARKERS = [
    "no compromise", "not a cost-benefit", "not negotiable",
    "matter of conscience", "cannot be weighed", "not up for debate",
    "beyond discussion", "non-negotiable", "inviolable",
    "unconditional", "absolute principle"
]


def count_markers(text: str, markers: List[str]) -> int:
    """
    Count how many markers from a list appear in text.

    This does case-insensitive substring matching. Each marker is counted
    at most once even if it appears multiple times (we're detecting presence,
    not frequency).

    Args:
        text: The text to search in (typically a citizen's opinion)
        markers: List of marker strings to search for

    Returns:
        Number of distinct markers found in text

    Example:
        >>> count_markers("I cannot compromise my faith", ABSOLUTE_MARKERS)
        1  # Found "cannot"
        >>> count_markers("I cannot and will not take medication", ABSOLUTE_MARKERS)
        2  # Found "cannot" and "will not"
    """
    text_lower = text.lower()
    count = 0

    for marker in markers:
        # Check if this marker appears anywhere in the text
        # We use 'in' for substring matching (e.g., "cannot" matches "I cannot do this")
        if marker.lower() in text_lower:
            count += 1

    return count


def find_markers(text: str, markers: List[str]) -> List[str]:
    """
    Find which specific markers from a list appear in text.

    Returns the actual marker strings found, not just a count.
    Useful for logging and transparency.

    Args:
        text: The text to search in
        markers: List of marker strings to search for

    Returns:
        List of markers that were found in text

    Example:
        >>> find_markers("I cannot compromise my faith", ABSOLUTE_MARKERS)
        ['cannot']
        >>> find_markers("My faith and God's will", SACRED_MARKERS)
        ['faith', 'god']
    """
    text_lower = text.lower()
    found = []

    for marker in markers:
        if marker.lower() in text_lower:
            found.append(marker)

    return found


def calculate_confidence(absolute_count: int, sacred_count: int,
                        anti_tradeoff_count: int) -> float:
    """
    Calculate confidence that an opinion contains a sacred value.

    Confidence scoring logic:
    - High (0.95): Both absolute + sacred markers present, OR anti-tradeoff language
    - Medium (0.70): Strong presence of one marker type (2+ markers)
    - Low (0.50): Weak presence (1 marker of any type)
    - Very low (0.10): No markers detected

    Rationale:
    - Anti-tradeoff language is the strongest signal (explicitly rejects compromise)
    - Combination of absolute + sacred is very strong (e.g., "I cannot due to my faith")
    - Multiple markers of one type suggests conviction
    - Single marker could be incidental, so lower confidence

    Args:
        absolute_count: Number of absolute language markers found
        sacred_count: Number of sacred justification markers found
        anti_tradeoff_count: Number of anti-tradeoff markers found

    Returns:
        Confidence score between 0.0 and 1.0

    Example:
        >>> calculate_confidence(1, 1, 0)
        0.95  # Both absolute and sacred → high confidence
        >>> calculate_confidence(3, 0, 0)
        0.70  # Multiple absolute markers → medium confidence
        >>> calculate_confidence(1, 0, 0)
        0.50  # Single marker → low confidence
    """
    # Anti-tradeoff language is the strongest signal - explicit rejection of compromise
    if anti_tradeoff_count >= 1:
        return 0.95

    # Both absolute language AND sacred justification → very likely sacred value
    # Example: "I cannot take medication because of my faith"
    if absolute_count >= 1 and sacred_count >= 1:
        return 0.95

    # Strong presence of one type (multiple markers) → likely sacred value
    # Example: "I must not, will not, and cannot compromise"
    if absolute_count >= 2 or sacred_count >= 2:
        return 0.70

    # Weak signal (single marker) → possible but uncertain
    # Could be incidental language rather than true sacred value
    if absolute_count >= 1 or sacred_count >= 1:
        return 0.50

    # No markers detected → very unlikely to be sacred value
    return 0.10


def extract_constraint_text(opinion: str, absolute_markers_found: List[str],
                           sacred_markers_found: List[str]) -> str:
    """
    Extract the actual constraint statement from the opinion.

    This attempts to find the sentence or phrase that contains the constraint.
    We look for sentences containing both absolute language and the thing being
    constrained.

    Current implementation: Simple heuristic looking for sentences with markers.
    Future improvement: Use LLM to extract constraint in structured form.

    Args:
        opinion: Full opinion text
        absolute_markers_found: Which absolute markers were detected
        sacred_markers_found: Which sacred markers were detected

    Returns:
        The extracted constraint text (sentence or phrase)

    Example:
        >>> extract_constraint_text(
        ...     "I love my doctor. I cannot take medication due to my faith. I prefer therapy.",
        ...     ["cannot"],
        ...     ["faith"]
        ... )
        "I cannot take medication due to my faith."
    """
    # Split into sentences (simple regex approach)
    # This handles periods, exclamation marks, and question marks as sentence boundaries
    sentences = re.split(r'[.!?]+', opinion)

    # Look for sentence containing absolute language
    # This is likely where the constraint is stated
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Check if this sentence contains any of the absolute markers we found
        sentence_lower = sentence.lower()
        for marker in absolute_markers_found:
            if marker.lower() in sentence_lower:
                # Found a sentence with constraint language - return it
                return sentence

    # Fallback: If no sentence with absolute marker, look for sacred marker
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        sentence_lower = sentence.lower()
        for marker in sacred_markers_found:
            if marker.lower() in sentence_lower:
                return sentence

    # Fallback: Return first non-empty sentence
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            return sentence

    # Last resort: Return full opinion (trimmed)
    return opinion.strip()[:200]  # Truncate if very long


def detect_sacred_value(opinion: str, citizen_id: int = 0,
                       confidence_threshold: float = 0.5) -> Optional[SacredValue]:
    """
    Detect whether an opinion contains a sacred value (non-negotiable constraint).

    This is the main entry point for sacred value detection. It analyzes the
    text for linguistic markers of non-negotiable commitments and returns
    a structured SacredValue object if detected.

    Algorithm:
    1. Count absolute language markers ("cannot", "must not", etc.)
    2. Count sacred justification markers ("faith", "god", "conscience", etc.)
    3. Count anti-tradeoff markers ("non-negotiable", "no compromise", etc.)
    4. Calculate confidence score based on marker combinations
    5. If confidence >= threshold, extract constraint and return SacredValue
    6. Otherwise return None (not a sacred value)

    Args:
        opinion: The citizen's opinion text to analyze
        citizen_id: ID of the citizen who provided this opinion (for tracking)
        confidence_threshold: Minimum confidence to return detection (default 0.5)

    Returns:
        SacredValue object if detected, None otherwise

    Example:
        >>> opinion = '''
        ... As a devout Christian, I believe depression is a spiritual trial.
        ... Taking medication would be rejecting God's plan and showing lack of faith.
        ... I cannot compromise on this - it's a matter of spiritual integrity.
        ... '''
        >>> sv = detect_sacred_value(opinion, citizen_id=2)
        >>> sv.confidence
        0.95
        >>> sv.markers
        ['cannot', 'christian', 'god', 'faith', 'spiritual']
        >>> sv.is_high_confidence()
        True
    """
    # Step 1: Count each type of marker
    # We count to determine strength of signal (more markers = higher confidence)
    absolute_count = count_markers(opinion, ABSOLUTE_MARKERS)
    sacred_count = count_markers(opinion, SACRED_MARKERS)
    anti_tradeoff_count = count_markers(opinion, ANTI_TRADEOFF_MARKERS)

    # Step 2: Calculate confidence score
    # This combines the counts into a single confidence value
    confidence = calculate_confidence(absolute_count, sacred_count, anti_tradeoff_count)

    # Step 3: Check if confidence meets threshold
    # If below threshold, this is likely not a sacred value
    if confidence < confidence_threshold:
        return None

    # Step 4: Find which specific markers were present
    # We need this for transparency (what triggered the detection?)
    absolute_markers_found = find_markers(opinion, ABSOLUTE_MARKERS)
    sacred_markers_found = find_markers(opinion, SACRED_MARKERS)
    anti_tradeoff_markers_found = find_markers(opinion, ANTI_TRADEOFF_MARKERS)

    # Combine all found markers for reporting
    all_markers = absolute_markers_found + sacred_markers_found + anti_tradeoff_markers_found

    # Step 5: Extract the constraint statement
    # This is the actual text that expresses what they cannot/must do
    constraint_text = extract_constraint_text(opinion, absolute_markers_found,
                                             sacred_markers_found)

    # Step 6: Determine justification category
    # This helps categorize the type of sacred value (religious, moral, etc.)
    justification_parts = []
    if sacred_markers_found:
        # Classify as religious or moral based on which markers
        religious_words = ['god', 'faith', 'religious', 'spiritual', 'prayer',
                          'church', 'christian', 'muslim', 'jewish', 'bible']
        moral_words = ['conscience', 'moral', 'ethics', 'principle', 'integrity']

        has_religious = any(m in religious_words for m in sacred_markers_found)
        has_moral = any(m in moral_words for m in sacred_markers_found)

        if has_religious:
            justification_parts.append("religious faith")
        if has_moral:
            justification_parts.append("moral conscience")

    if anti_tradeoff_markers_found:
        justification_parts.append("explicit rejection of trade-offs")

    if absolute_markers_found and not justification_parts:
        justification_parts.append("absolute language")

    justification = "; ".join(justification_parts) if justification_parts else "detected markers"

    # Step 7: Create and return SacredValue object
    return SacredValue(
        citizen_id=citizen_id,
        text=constraint_text,
        confidence=confidence,
        markers=all_markers,
        justification=justification
    )


class SacredValueDetector:
    """
    Stateful sacred value detector with configurable parameters.

    This class wraps the detection logic in an object that can be configured
    once and reused. Useful when you want to detect across multiple opinions
    with the same settings.

    Attributes:
        confidence_threshold: Minimum confidence to report detection
        verbose: Whether to print detection details

    Example:
        >>> detector = SacredValueDetector(confidence_threshold=0.7, verbose=True)
        >>> opinions = [op1, op2, op3, op4, op5]
        >>> sacred_values = detector.detect_batch(opinions)
        >>> print(f"Found {len(sacred_values)} sacred values")
    """

    def __init__(self, confidence_threshold: float = 0.5, verbose: bool = False):
        """
        Initialize the detector with configuration.

        Args:
            confidence_threshold: Minimum confidence to report detection (0.0-1.0)
            verbose: If True, print detection details for debugging
        """
        self.confidence_threshold = confidence_threshold
        self.verbose = verbose

    def detect(self, opinion: str, citizen_id: int = 0) -> Optional[SacredValue]:
        """
        Detect sacred value in a single opinion.

        This is a wrapper around the module-level detect_sacred_value function
        that uses this detector's configuration.

        Args:
            opinion: The citizen's opinion text
            citizen_id: ID of the citizen (for tracking)

        Returns:
            SacredValue object if detected, None otherwise
        """
        result = detect_sacred_value(opinion, citizen_id, self.confidence_threshold)

        if self.verbose:
            if result:
                print(f"✓ Sacred value detected for Citizen {citizen_id}")
                print(f"  Confidence: {result.confidence:.2f}")
                print(f"  Markers: {result.markers}")
                print(f"  Justification: {result.justification}")
            else:
                print(f"✗ No sacred value detected for Citizen {citizen_id}")

        return result

    def detect_batch(self, opinions: List[str]) -> List[SacredValue]:
        """
        Detect sacred values across multiple opinions.

        This processes a list of opinions and returns only those with
        detected sacred values.

        Args:
            opinions: List of opinion texts (one per citizen)

        Returns:
            List of detected SacredValue objects (may be empty)

        Example:
            >>> detector = SacredValueDetector()
            >>> opinions = [
            ...     "I think medication is cost-effective",  # Secular
            ...     "I cannot take medication due to my faith",  # Sacred!
            ...     "Therapy might work better"  # Secular
            ... ]
            >>> sacred_values = detector.detect_batch(opinions)
            >>> len(sacred_values)
            1
            >>> sacred_values[0].citizen_id
            1
        """
        detected = []

        for citizen_id, opinion in enumerate(opinions):
            result = self.detect(opinion, citizen_id)
            if result:
                detected.append(result)

        return detected

    def detect_all(self, opinions: List[str]) -> Tuple[List[SacredValue], List[int]]:
        """
        Detect sacred values and return both detected and non-detected citizens.

        This is useful when you need to know which citizens DON'T have sacred values.

        Args:
            opinions: List of opinion texts

        Returns:
            Tuple of (sacred_values_list, secular_citizen_ids)

        Example:
            >>> sacred_values, secular_ids = detector.detect_all(opinions)
            >>> print(f"Sacred values: {len(sacred_values)}")
            >>> print(f"Secular citizens: {secular_ids}")
        """
        sacred_values = []
        secular_ids = []

        for citizen_id, opinion in enumerate(opinions):
            result = self.detect(opinion, citizen_id)
            if result:
                sacred_values.append(result)
            else:
                secular_ids.append(citizen_id)

        return sacred_values, secular_ids


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    # Example: Detect sacred value in religious objection to medication

    opinion_sacred = """
    As a devout Christian, I believe depression is a spiritual trial that God uses
    for growth. Taking medication would be rejecting His plan and showing lack of
    faith. My pastor teaches that true healing comes through prayer, fellowship,
    and trusting God's timing. I cannot compromise on this - it's a matter of
    spiritual integrity, not a cost-benefit calculation.
    """

    opinion_secular = """
    I think the patient should try the SSRIs. Depression significantly impacts
    quality of life and work productivity. While side effects like nausea and
    sleep changes are possible, they're usually temporary and manageable. The
    evidence shows SSRIs help about 60% of people with moderate depression.
    The potential benefit outweighs the risk.
    """

    print("="*80)
    print("SACRED VALUE DETECTION EXAMPLE")
    print("="*80)

    print("\n" + "-"*80)
    print("Opinion 1 (Religious objection):")
    print("-"*80)
    print(opinion_sacred.strip())

    result1 = detect_sacred_value(opinion_sacred, citizen_id=1)
    if result1:
        print("\n✓ SACRED VALUE DETECTED")
        print(f"  Confidence: {result1.confidence:.2f}")
        print(f"  Markers found: {result1.markers}")
        print(f"  Justification: {result1.justification}")
        print(f"  Constraint text: {result1.text}")
        print(f"  High confidence: {result1.is_high_confidence()}")
        print(f"  Religious basis: {result1.is_religious()}")
    else:
        print("\n✗ No sacred value detected")

    print("\n" + "-"*80)
    print("Opinion 2 (Secular cost-benefit):")
    print("-"*80)
    print(opinion_secular.strip())

    result2 = detect_sacred_value(opinion_secular, citizen_id=2)
    if result2:
        print("\n✓ SACRED VALUE DETECTED")
        print(f"  Confidence: {result2.confidence:.2f}")
    else:
        print("\n✗ No sacred value detected")

    print("\n" + "="*80)
    print("BATCH DETECTION EXAMPLE")
    print("="*80)

    opinions = [opinion_secular, opinion_sacred, opinion_secular]
    detector = SacredValueDetector(confidence_threshold=0.7, verbose=True)

    print("\nProcessing 3 opinions (1 sacred, 2 secular):\n")
    sacred_values = detector.detect_batch(opinions)

    print(f"\n{'='*80}")
    print(f"RESULTS: Found {len(sacred_values)} sacred value(s) out of {len(opinions)} opinions")
    print(f"{'='*80}")
