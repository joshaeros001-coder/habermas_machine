"""
Simple Voting Implementation

ADAPTED FROM: habermas_machine/social_choice/schulze_method.py
SIMPLIFIED: Uses basic scoring instead of full Schulze method
WHY: For prototype, we need a working voting system; can upgrade to Schulze later

This implements simplified constrained voting:
1. Citizens "vote" by scoring candidates (simulated for now)
2. Highest scoring candidate wins
3. Only feasible candidates (those satisfying constraints) are considered

Future enhancement: Replace with full Schulze method from original codebase.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class VotingResult:
    """
    Result of a voting process.

    Attributes:
        winner: The winning statement
        winner_index: Index of winner in original candidate list
        scores: Score for each candidate
        all_candidates: All candidates that were voted on
    """
    winner: str
    winner_index: int
    scores: List[float]
    all_candidates: List[str]


class SimpleVoting:
    """
    Simple voting system for selecting consensus statement.

    This is a SIMPLIFIED implementation for the prototype. It uses basic
    scoring where each candidate is scored based on a simple heuristic.

    For full implementation, this should be replaced with the Schulze method
    from habermas_machine/social_choice/schulze_method.py

    The key innovation is that this votes ONLY on the feasible set
    (constraint-satisfying statements), not all possible statements.

    Attributes:
        verbose: Whether to print voting details

    Example:
        >>> voting = SimpleVoting(verbose=True)
        >>> winner = voting.vote(feasible_candidates, opinions)
        >>> print(f"Winner: {winner.winner}")
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize the voting system.

        Args:
            verbose: If True, print voting details
        """
        self.verbose = verbose

    def vote(
        self,
        candidates: List[str],
        opinions: List[str]
    ) -> VotingResult:
        """
        Vote on candidate statements to select winner.

        SIMPLIFIED IMPLEMENTATION: For prototype, we select the candidate that
        best balances length (substance) with acknowledgment of multiple perspectives.

        Future enhancement: Implement proper Schulze method with citizen rankings.

        Args:
            candidates: List of feasible candidate statements
            opinions: Original citizen opinions (for context)

        Returns:
            VotingResult with winner and scores

        Raises:
            ValueError: If no candidates provided

        Example:
            >>> candidates = [stmt1, stmt2, stmt3]
            >>> result = voting.vote(candidates, opinions)
            >>> result.winner
            "The patient should consider multiple treatment approaches..."
        """
        if not candidates:
            raise ValueError("Cannot vote on empty candidate list")

        if len(candidates) == 1:
            # Only one candidate - it wins by default
            if self.verbose:
                print("Only one candidate - selected by default")
            return VotingResult(
                winner=candidates[0],
                winner_index=0,
                scores=[1.0],
                all_candidates=candidates
            )

        if self.verbose:
            print(f"\nVoting on {len(candidates)} candidates...")

        # SIMPLIFIED SCORING: For prototype, use basic heuristics
        # Future: Replace with proper Schulze method using citizen rankings
        scores = []

        for i, candidate in enumerate(candidates):
            # Score based on:
            # 1. Length (substance) - longer statements tend to be more comprehensive
            # 2. Acknowledgment words - shows consideration of multiple perspectives
            # 3. Conditional language - shows nuance

            length_score = min(len(candidate) / 500.0, 1.0)  # Normalize to 0-1

            # Count acknowledgment words
            acknowledgment_words = [
                'for those', 'some', 'may', 'might', 'consider', 'different',
                'individual', 'personal', 'choice', 'option', 'alternative'
            ]
            ack_count = sum(1 for word in acknowledgment_words if word in candidate.lower())
            ack_score = min(ack_count / 5.0, 1.0)  # Normalize to 0-1

            # Combined score (weighted average)
            # Favor substance (length) slightly more than acknowledgment
            score = 0.6 * length_score + 0.4 * ack_score

            scores.append(score)

            if self.verbose:
                print(f"  Candidate {i+1}: score = {score:.3f}")
                print(f"    (length={length_score:.3f}, ack={ack_score:.3f})")

        # Select winner (highest score)
        winner_index = scores.index(max(scores))
        winner = candidates[winner_index]

        if self.verbose:
            print(f"\n✓ Winner: Candidate {winner_index+1} (score: {scores[winner_index]:.3f})")

        return VotingResult(
            winner=winner,
            winner_index=winner_index,
            scores=scores,
            all_candidates=candidates
        )

    def vote_with_rankings(
        self,
        candidates: List[str],
        rankings: List[List[int]]
    ) -> VotingResult:
        """
        Vote using explicit citizen rankings.

        This is closer to the real Schulze method. Each citizen provides
        a ranking of candidates (0 = best, 1 = second best, etc.).

        Args:
            candidates: List of candidate statements
            rankings: List of rankings, one per citizen
                     Each ranking is a list of indices [0, 1, 2, 3]
                     where position indicates preference (0th position = most preferred)

        Returns:
            VotingResult with winner

        Example:
            >>> # 3 citizens ranking 3 candidates
            >>> rankings = [
            ...     [0, 1, 2],  # Citizen 0: prefers 0 > 1 > 2
            ...     [1, 0, 2],  # Citizen 1: prefers 1 > 0 > 2
            ...     [0, 1, 2],  # Citizen 2: prefers 0 > 1 > 2
            ... ]
            >>> result = voting.vote_with_rankings(candidates, rankings)
            >>> # Candidate 0 wins (2 out of 3 prefer it first)
        """
        if not candidates:
            raise ValueError("Cannot vote on empty candidate list")

        if self.verbose:
            print(f"\nVoting with {len(rankings)} citizen rankings...")

        # SIMPLIFIED: Use Borda count
        # Each candidate gets points based on ranking position
        # 1st place = n points, 2nd place = n-1 points, etc.
        n = len(candidates)
        scores = [0.0] * n

        for citizen_id, ranking in enumerate(rankings):
            for position, candidate_idx in enumerate(ranking):
                # Award points: n points for 1st, n-1 for 2nd, etc.
                points = n - position
                scores[candidate_idx] += points

        # Normalize scores
        total = sum(scores)
        if total > 0:
            scores = [s / total for s in scores]

        # Select winner
        winner_index = scores.index(max(scores))
        winner = candidates[winner_index]

        if self.verbose:
            for i, score in enumerate(scores):
                print(f"  Candidate {i+1}: {score:.3f}")
            print(f"\n✓ Winner: Candidate {winner_index+1}")

        return VotingResult(
            winner=winner,
            winner_index=winner_index,
            scores=scores,
            all_candidates=candidates
        )


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("SIMPLE VOTING EXAMPLE")
    print("="*80)

    candidates = [
        "The patient should try SSRIs as recommended by their doctor.",

        """For those whose faith prohibits pharmaceutical intervention, non-medical
approaches including therapy, spiritual support, and lifestyle changes are valid
paths. For others open to medication, SSRIs may be appropriate after consultation
with a doctor.""",

        """Multiple treatment approaches exist for depression. The choice should
reflect individual circumstances, values, and beliefs.""",
    ]

    opinions = [
        "I support SSRIs for depression.",
        "I cannot take medication due to my religious faith.",
        "Therapy might work better than medication.",
        "I think SSRIs are worth trying.",
    ]

    print("\nCandidates:")
    for i, c in enumerate(candidates, 1):
        print(f"\n{i}. {c[:80]}...")

    print("\n" + "-"*80)
    print("Voting (simple heuristic):")
    print("-"*80)

    voting = SimpleVoting(verbose=True)
    result = voting.vote(candidates, opinions)

    print("\n" + "="*80)
    print("RESULT")
    print("="*80)
    print(f"\nWinner (Candidate {result.winner_index+1}):")
    print(result.winner)

    print("\n" + "-"*80)
    print("Voting with explicit rankings:")
    print("-"*80)

    # Simulate citizen rankings
    rankings = [
        [1, 2, 0],  # Citizen 0: prefers 1 > 2 > 0
        [1, 2, 0],  # Citizen 1: prefers 1 > 2 > 0 (sacred value - favors acknowledgment)
        [0, 1, 2],  # Citizen 2: prefers 0 > 1 > 2
        [0, 1, 2],  # Citizen 3: prefers 0 > 1 > 2
    ]

    result2 = voting.vote_with_rankings(candidates, rankings)

    print("\n" + "="*80)
    print("RESULT WITH RANKINGS")
    print("="*80)
    print(f"\nWinner (Candidate {result2.winner_index+1}):")
    print(result2.winner)
