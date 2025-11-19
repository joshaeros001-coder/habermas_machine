"""
Data class for representing detected sacred values.

A sacred value is a non-negotiable moral commitment that cannot be compromised
or traded off against other considerations.

Examples:
- Religious objections ("I cannot take medication due to my faith")
- Moral absolutes ("Abortion is murder and must be prohibited")
- Deontological duties ("I refuse to violate patient confidentiality")
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SacredValue:
    """
    Represents a detected sacred value in a citizen's opinion.

    Attributes:
        citizen_id: Index of the citizen who holds this sacred value (0-indexed)
        text: The original text containing the sacred value
        confidence: Detection confidence score (0.0-1.0)
            0.9-1.0 = high confidence (explicit absolute + sacred language)
            0.6-0.9 = medium confidence (only absolute OR only sacred language)
            0.0-0.6 = low confidence (weak or ambiguous signals)
        markers: List of specific keywords/phrases that triggered detection
            e.g., ["cannot", "faith", "God", "no compromise"]
        justification: The reason given for the sacred value
            e.g., "religious faith", "moral principle", "conscience"

    Example:
        >>> sv = SacredValue(
        ...     citizen_id=2,
        ...     text="I cannot take medication due to my Christian faith",
        ...     confidence=0.95,
        ...     markers=["cannot", "faith", "Christian"],
        ...     justification="religious faith"
        ... )
        >>> print(sv.is_high_confidence())
        True
    """

    citizen_id: int
    text: str
    confidence: float
    markers: List[str]
    justification: str

    def is_high_confidence(self) -> bool:
        """
        Check if this sacred value was detected with high confidence.

        High confidence (>= 0.9) means we should definitely treat it as a
        hard constraint. Medium/low confidence might warrant asking the
        citizen for clarification.

        Returns:
            True if confidence >= 0.9, False otherwise
        """
        return self.confidence >= 0.9

    def is_religious(self) -> bool:
        """
        Check if this sacred value has religious justification.

        Religious sacred values often require special handling as they
        invoke absolute moral authority (God, scripture, religious law).

        Returns:
            True if justification contains religious keywords
        """
        religious_keywords = [
            'religious', 'faith', 'god', 'christian', 'muslim', 'jewish',
            'hindu', 'buddhist', 'church', 'prayer', 'scripture', 'divine'
        ]
        justification_lower = self.justification.lower()
        return any(kw in justification_lower for kw in religious_keywords)

    def __str__(self) -> str:
        """
        Human-readable string representation.

        Returns:
            Formatted string showing key attributes
        """
        return (
            f"SacredValue(citizen={self.citizen_id}, "
            f"confidence={self.confidence:.2f}, "
            f"justification={self.justification})"
        )

    def __repr__(self) -> str:
        """
        Developer-friendly representation showing all fields.

        Returns:
            Complete repr string for debugging
        """
        return (
            f"SacredValue("
            f"citizen_id={self.citizen_id}, "
            f"text='{self.text[:50]}...', "
            f"confidence={self.confidence}, "
            f"markers={self.markers}, "
            f"justification='{self.justification}')"
        )
