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

"""Utility functions for Sacred Values Architecture.

This module provides helper functions for text processing, constraint checking,
and other common operations. Many are adapted from the standard CRM utils.
"""

import numpy as np
from typing import List


def numerical_ranking_to_ordinal_text(ranking: np.ndarray) -> str:
    """Convert numerical ranking to human-readable ordinal text.

    COPIED FROM: habermas_machine.utils
    This is used for displaying rankings in a readable format.

    Args:
        ranking: Array where ranking[i] is the rank of candidate i (0=best)

    Returns:
        Human-readable string like "1st, 2nd, 3rd, ..."

    Example:
        >>> numerical_ranking_to_ordinal_text(np.array([1, 0, 2]))
        "2nd, 1st, 3rd"
    """
    def ordinal(n):
        """Convert number to ordinal string (1st, 2nd, 3rd, etc.)"""
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"

    # Convert ranks to ordinals
    ordinals = [ordinal(rank + 1) for rank in ranking]
    return ", ".join(ordinals)


def contains_any_phrase(text: str, phrases: List[str], case_sensitive: bool = False) -> bool:
    """Check if text contains any of the given phrases.

    This is used for constraint checking to see if a statement contains
    prohibited or required elements.

    Args:
        text: The text to search within
        phrases: List of phrases to search for
        case_sensitive: Whether to match case exactly

    Returns:
        True if any phrase is found in text

    Example:
        >>> contains_any_phrase("Start taking SSRI medication", ["SSRI", "medication"])
        True
        >>> contains_any_phrase("Consider therapy options", ["SSRI", "medication"])
        False
    """
    if not case_sensitive:
        text = text.lower()
        phrases = [p.lower() for p in phrases]

    for phrase in phrases:
        if phrase in text:
            return True
    return False


def extract_sentences_with_keywords(text: str, keywords: List[str]) -> List[str]:
    """Extract sentences from text that contain any of the keywords.

    Used in sacred value detection to extract relevant constraint text.

    Args:
        text: The full text to search
        keywords: List of keywords to look for

    Returns:
        List of sentences containing at least one keyword

    Example:
        >>> text = "I like therapy. I cannot take medication. It helps others."
        >>> extract_sentences_with_keywords(text, ["cannot", "must not"])
        ["I cannot take medication"]
    """
    # Split into sentences (simple split on . ! ?)
    import re
    sentences = re.split(r'[.!?]+', text)

    # Find sentences containing keywords
    matching_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence and contains_any_phrase(sentence, keywords):
            matching_sentences.append(sentence)

    return matching_sentences


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to maximum length, adding ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length (including ellipsis)

    Returns:
        Truncated text with "..." if it was cut

    Example:
        >>> truncate_text("This is a very long sentence", 20)
        "This is a very lo..."
    """
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def count_overlap(text: str, phrases: List[str]) -> int:
    """Count how many phrases appear in the text.

    Args:
        text: Text to search
        phrases: List of phrases to count

    Returns:
        Number of phrases found in text

    Example:
        >>> count_overlap("I like medication and therapy", ["medication", "therapy", "exercise"])
        2
    """
    text_lower = text.lower()
    return sum(1 for phrase in phrases if phrase.lower() in text_lower)
