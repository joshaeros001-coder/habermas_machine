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

"""Sacred Value Detector - Core Innovation of the Architecture.

This module detects when a citizen's opinion contains a sacred value
(non-negotiable belief) rather than a regular preference.

ARCHITECTURAL SIGNIFICANCE:
This is THE key innovation that distinguishes this architecture from standard CRM.
Standard CRM treats all opinions as weighted preferences. We detect sacred values
and treat them as lexicographic constraints instead.

DETECTION APPROACH:
Sacred values are characterized by:
1. ABSOLUTE LANGUAGE: "cannot", "must not", "refuse to", "will not"
2. MORAL/RELIGIOUS JUSTIFICATION: "faith", "conscience", "God", "beliefs"
3. REJECTION OF TRADE-OFFS: "not a cost-benefit calculation", "matter of principle"

When we detect these markers, we classify the opinion as containing a sacred
value with a confidence score.
"""

from typing import List, Tuple
from sacred_values_architecture.types import SacredValue
from sacred_values_architecture.utils import extract_sentences_with_keywords


# ==============================================================================
# LINGUISTIC MARKERS FOR SACRED VALUE DETECTION
# ==============================================================================

# These words indicate absolute rejection (not just preference)
ABSOLUTE_REJECTION_MARKERS = [
    "cannot",
    "can't",
    "must not",
    "mustn't",
    "refuse to",
    "refuse",
    "will not",
    "won't",
    "against my conscience",
    "against my beliefs",
    "never",
    "absolutely not",
    "under no circumstances",
]

# These words indicate religious or moral grounding
SACRED_GROUNDING_MARKERS = [
    "faith",
    "god",
    "religious",
    "religion",
    "conscience",
    "beliefs",
    "belief",
    "spiritual",
    "spirituality",
    "prayer",
    "pray",
    "christian",
    "muslim",
    "jewish",
    "hindu",
    "buddhist",
    "bible",
    "quran",
    "torah",
    "scripture",
    "sin",
    "sacred",
    "divine",
    "moral",
    "ethics",
    "ethical",
    "principle",
    "principled",
]

# These phrases indicate rejection of trade-off thinking
ANTI_TRADEOFF_MARKERS = [
    "not a cost-benefit",
    "not about cost",
    "matter of principle",
    "question of principle",
    "matter of faith",
    "matter of conscience",
    "spiritual integrity",
    "moral integrity",
    "non-negotiable",
    "cannot compromise",
    "will not compromise",
]


# ==============================================================================
# CORE DETECTION FUNCTION
# ==============================================================================

def detect_sacred_value(opinion: str, citizen_id: int) -> Tuple[bool, SacredValue | None]:
    """Detect whether an opinion contains a sacred value (non-negotiable constraint).

    This is the CORE INNOVATION: identifying when a preference should be treated
    as a hard constraint rather than a weighted preference.

    ALGORITHM:
    1. Look for absolute rejection language ("cannot", "must not")
    2. Look for religious/moral justifications ("faith", "conscience")
    3. Look for anti-trade-off language ("not a cost-benefit calculation")
    4. Calculate confidence based on marker presence
    5. Extract the specific constraint text
    6. Return SacredValue object if detected

    CONFIDENCE LEVELS:
    - 0.95: Absolute + Sacred/Anti-trade-off markers (very likely sacred)
    - 0.75: Absolute + (Sacred or Anti-trade-off) (likely sacred)
    - 0.60: Sacred + Anti-trade-off without Absolute (possibly sacred)
    - 0.40: Only Absolute marker (might be strong preference)
    - 0.10: No markers (regular preference)

    Args:
        opinion: The citizen's opinion text to analyze
        citizen_id: The index of this citizen (0-indexed)

    Returns:
        Tuple of:
        - is_sacred: Boolean indicating if sacred value detected
        - sacred_value: SacredValue object if detected, None otherwise

    Example:
        >>> detect_sacred_value(
        ...     "I cannot take medication due to my faith",
        ...     citizen_id=1
        ... )
        (True, SacredValue(
            citizen_id=1,
            constraint_text="I cannot take medication due to my faith",
            confidence=0.95,
            markers_found=["cannot", "faith"],
            ...
        ))

        >>> detect_sacred_value(
        ...     "I prefer therapy over medication",
        ...     citizen_id=0
        ... )
        (False, None)
    """
    opinion_lower = opinion.lower()

    # STEP 1: Look for absolute rejection language
    # These words indicate non-negotiability (not just preference)
    absolute_markers_found = [
        marker for marker in ABSOLUTE_REJECTION_MARKERS
        if marker in opinion_lower
    ]
    has_absolute = len(absolute_markers_found) > 0

    # STEP 2: Look for religious/moral justifications
    # Sacred values are often grounded in religious or moral frameworks
    sacred_markers_found = [
        marker for marker in SACRED_GROUNDING_MARKERS
        if marker in opinion_lower
    ]
    has_sacred = len(sacred_markers_found) > 0

    # STEP 3: Look for anti-trade-off language
    # Sacred values explicitly reject cost-benefit thinking
    anti_tradeoff_markers_found = [
        marker for marker in ANTI_TRADEOFF_MARKERS
        if marker in opinion_lower
    ]
    has_anti_tradeoff = len(anti_tradeoff_markers_found) > 0

    # STEP 4: Calculate confidence based on marker presence
    # More markers = higher confidence that this is a sacred value
    all_markers_found = absolute_markers_found + sacred_markers_found + anti_tradeoff_markers_found

    if has_absolute and (has_sacred or has_anti_tradeoff):
        # Strong signal: absolute language + grounding
        # Example: "I cannot take medication due to my faith"
        confidence = 0.95
        is_sacred = True
    elif has_absolute and has_sacred:
        # Strong signal: absolute + sacred
        confidence = 0.90
        is_sacred = True
    elif has_absolute and has_anti_tradeoff:
        # Strong signal: absolute + anti-trade-off
        confidence = 0.90
        is_sacred = True
    elif has_sacred and has_anti_tradeoff:
        # Medium-strong signal: sacred grounding + anti-trade-off, but no absolute
        # Example: "This is a matter of faith, not cost-benefit"
        confidence = 0.75
        is_sacred = True
    elif has_absolute:
        # Medium signal: only absolute language
        # Could be strong preference vs sacred value
        # Example: "I will not support this policy"
        confidence = 0.60
        is_sacred = True
    elif has_sacred and len(sacred_markers_found) >= 2:
        # Weak-medium signal: multiple sacred markers
        # Example: "My faith and religious beliefs guide me"
        confidence = 0.50
        is_sacred = True
    elif has_anti_tradeoff:
        # Weak signal: only anti-trade-off language
        confidence = 0.45
        is_sacred = True
    else:
        # No markers found - regular preference
        confidence = 0.10
        is_sacred = False

    # STEP 5: Extract the constraint text
    # Find sentences containing the sacred value markers
    if not is_sacred:
        return False, None

    all_keywords = ABSOLUTE_REJECTION_MARKERS + SACRED_GROUNDING_MARKERS + ANTI_TRADEOFF_MARKERS
    constraint_sentences = extract_sentences_with_keywords(opinion, all_keywords)

    if constraint_sentences:
        # Use the first matching sentence as the constraint text
        constraint_text = constraint_sentences[0]
    else:
        # Fallback: use the entire opinion
        constraint_text = opinion

    # STEP 6: Create and return SacredValue object
    sacred_value = SacredValue(
        citizen_id=citizen_id,
        constraint_text=constraint_text,
        confidence=confidence,
        markers_found=all_markers_found,
        original_opinion=opinion,
    )

    return True, sacred_value


# ==============================================================================
# BATCH DETECTION
# ==============================================================================

def detect_sacred_values_batch(opinions: List[str]) -> List[SacredValue]:
    """Detect sacred values across all citizen opinions.

    This is the entry point for the deliberation process. It analyzes all
    opinions and returns a list of detected sacred values.

    Args:
        opinions: List of citizen opinions

    Returns:
        List of SacredValue objects (may be empty if no sacred values detected)

    Example:
        >>> opinions = [
        ...     "I support SSRIs for depression",
        ...     "I cannot take medication due to my faith",
        ...     "Therapy is a good option",
        ... ]
        >>> sacred_values = detect_sacred_values_batch(opinions)
        >>> len(sacred_values)
        1
        >>> sacred_values[0].citizen_id
        1
    """
    detected_values = []

    for citizen_id, opinion in enumerate(opinions):
        is_sacred, sacred_value = detect_sacred_value(opinion, citizen_id)
        if is_sacred and sacred_value is not None:
            detected_values.append(sacred_value)

    return detected_values


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_sacred_value_summary(sacred_value: SacredValue) -> str:
    """Generate a human-readable summary of a sacred value.

    Args:
        sacred_value: The sacred value to summarize

    Returns:
        Formatted string summarizing the sacred value

    Example:
        >>> sv = SacredValue(citizen_id=1, constraint_text="cannot take medication", ...)
        >>> print(get_sacred_value_summary(sv))
        Citizen 1 (confidence: 0.95):
          "cannot take medication"
          Markers: cannot, medication, faith
    """
    return f"""Citizen {sacred_value.citizen_id} (confidence: {sacred_value.confidence:.2f}):
  "{sacred_value.constraint_text}"
  Markers: {', '.join(sacred_value.markers_found)}"""


def filter_by_confidence(
    sacred_values: List[SacredValue],
    min_confidence: float = 0.70
) -> List[SacredValue]:
    """Filter sacred values by minimum confidence threshold.

    This is useful if you want to only enforce high-confidence sacred values
    and treat low-confidence ones as strong preferences.

    Args:
        sacred_values: List of detected sacred values
        min_confidence: Minimum confidence threshold (0-1)

    Returns:
        Filtered list of sacred values above threshold

    Example:
        >>> all_values = [SacredValue(..., confidence=0.95), SacredValue(..., confidence=0.50)]
        >>> high_confidence = filter_by_confidence(all_values, min_confidence=0.70)
        >>> len(high_confidence)
        1
    """
    return [sv for sv in sacred_values if sv.confidence >= min_confidence]
