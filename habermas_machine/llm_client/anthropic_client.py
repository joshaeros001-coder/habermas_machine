# Copyright 2025 - Extended for Sacred Value Research
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

"""
Anthropic Client for Habermas Machine
=====================================

This client enables testing Claude models (Claude 3.5 Sonnet, Claude 3 Opus, etc.)
with the Habermas Machine deliberation system. Created as part of sacred value
research to compare how different LLM families handle non-negotiable positions.

Architecture:
- Inherits from base_client.LLMClient (same interface as Gemini/OpenAI clients)
- Uses Anthropic's Messages API
- Implements rate limiting to avoid quota errors
- Handles errors gracefully for long-running experiments

Usage:
    from habermas_machine.llm_client.anthropic_client import AnthropicClient

    client = AnthropicClient(
        model_name="claude-sonnet-4-20250514",
        sleep_periodically=True,  # Avoid rate limits
    )

Environment:
    Requires ANTHROPIC_API_KEY environment variable

Models to test:
    - claude-sonnet-4-20250514 (latest Sonnet 4)
    - claude-3-5-sonnet-20241022 (Claude 3.5 Sonnet)
    - claude-3-opus-20240229 (most capable, slower)
    - claude-3-haiku-20240307 (fastest, cheapest)

Research Note:
    Claude models are particularly interesting for sacred value research because
    Anthropic's Constitutional AI training explicitly addresses value conflicts.
    We hypothesize Claude may handle sacred values differently than RLHF-trained
    models like GPT.
"""

from collections.abc import Collection
import os
import time

# Anthropic's official Python client
# Install: pip install anthropic
import anthropic
from typing_extensions import override

from habermas_machine.llm_client import base_client
from habermas_machine.llm_client import utils


class AnthropicClient(base_client.LLMClient):
    """
    Language Model client for Anthropic's Claude models.

    This class wraps Anthropic's Messages API to match the LLMClient interface
    used by the Habermas Machine. The key method is sample_text(), which takes
    a prompt and returns generated text.

    Key differences from Gemini/OpenAI:
    - Uses "messages" format with explicit human/assistant turns
    - Requires max_tokens to be specified (no default)
    - Has different rate limit structure (tokens per minute, not just requests)
    - Constitutional AI training may affect sacred value handling

    Attributes:
        _client: Anthropic client instance
        _model_name: Which Claude model to use (e.g., "claude-sonnet-4-20250514")
        _sleep_periodically: Whether to pause between API calls
        _sleep_seconds: How long to pause (default 3 seconds)
        _calls_between_sleeping: Pause every N calls (default 5)
        _n_calls: Counter for rate limiting
    """

    def __init__(
        self,
        model_name: str,
        *,
        sleep_periodically: bool = False,
        sleep_seconds: float = 3.0,
        calls_between_sleeping: int = 5,
    ) -> None:
        """
        Initialize the Anthropic client.

        Args:
            model_name: Which Claude model to use. Options include:
                - "claude-sonnet-4-20250514": Latest Sonnet 4 (recommended)
                - "claude-3-5-sonnet-20241022": Claude 3.5 Sonnet
                - "claude-3-opus-20240229": Most capable, best for complex reasoning
                - "claude-3-haiku-20240307": Fastest, good for quick tests

            sleep_periodically: If True, pause between API calls to avoid
                hitting rate limits. Recommended for experiments.

            sleep_seconds: How many seconds to sleep. Anthropic rate limits
                are based on tokens/minute, so 3 seconds is conservative.

            calls_between_sleeping: Sleep after this many API calls.

        Raises:
            KeyError: If ANTHROPIC_API_KEY environment variable is not set.

        Example:
            # Basic usage
            client = AnthropicClient("claude-sonnet-4-20250514")

            # With rate limiting for long experiments
            client = AnthropicClient(
                "claude-3-opus-20240229",
                sleep_periodically=True,
                sleep_seconds=3.0,
                calls_between_sleeping=5,
            )
        """
        # =====================================================================
        # API KEY SETUP
        # =====================================================================
        # Read API key from environment variable
        # Set this before running: export ANTHROPIC_API_KEY="sk-ant-..."
        self._api_key = os.environ['ANTHROPIC_API_KEY']

        # Store model name for API calls
        self._model_name = model_name

        # =====================================================================
        # CREATE ANTHROPIC CLIENT
        # =====================================================================
        # The Anthropic() constructor can read from environment, but we pass
        # explicitly for clarity and error handling
        self._client = anthropic.Anthropic(api_key=self._api_key)

        # =====================================================================
        # RATE LIMITING CONFIGURATION
        # =====================================================================
        # Anthropic rate limits are based on:
        # - Requests per minute (RPM)
        # - Tokens per minute (TPM) - both input and output
        # - Tokens per day (TPD) for some tiers
        #
        # Free tier is very limited; paid tiers are more generous.
        # These conservative settings help avoid 429 errors.
        self._sleep_periodically = sleep_periodically
        self._sleep_seconds = sleep_seconds
        self._calls_between_sleeping = calls_between_sleeping
        self._n_calls = 0  # Counter for rate limiting

    @override
    def sample_text(
        self,
        prompt: str,
        *,
        max_tokens: int = base_client.DEFAULT_MAX_TOKENS,
        terminators: Collection[str] = base_client.DEFAULT_TERMINATORS,
        temperature: float = base_client.DEFAULT_TEMPERATURE,
        timeout: float = base_client.DEFAULT_TIMEOUT_SECONDS,
        seed: int | None = None,
    ) -> str:
        """
        Generate text from the Claude model.

        This method is called by the Habermas Machine for:
        1. Generating consensus statement candidates (StatementModel)
        2. Generating ranking explanations (RewardModel)

        The prompt contains the full context (question, opinions, instructions)
        formatted by the Habermas Machine's prompt templates.

        Args:
            prompt: The full prompt text. For the Habermas Machine, this includes
                the deliberation question, all citizen opinions, and instructions
                for generating consensus statements or rankings.

            max_tokens: Maximum tokens in the response. REQUIRED by Anthropic API.
                The Habermas Machine uses 8192 by default for chain-of-thought.

            terminators: Stop sequences. If any of these strings appear in the
                output, generation stops. Used to detect end of structured output.

            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative).
                Default 0.8 allows variation while maintaining coherence.
                Note: Anthropic recommends 0.0-1.0 range.

            timeout: Request timeout in seconds. Passed to the API client.

            seed: For reproducibility. NOTE: Anthropic does NOT support seeds
                as of 2024. This parameter is ignored but kept for interface
                compatibility. Results may vary between runs.

        Returns:
            The generated text response, truncated at any terminator string.
            Returns empty string if an error occurs.

        Note on Sacred Value Research:
            Claude's Constitutional AI training includes principles about
            respecting diverse viewpoints. We're testing whether this translates
            to better sacred value accommodation in deliberative contexts.
        """
        # Anthropic doesn't support seeds - log warning if one is provided
        if seed is not None:
            pass  # Silently ignore - don't spam logs for every call

        # =====================================================================
        # RATE LIMITING
        # =====================================================================
        self._n_calls += 1
        if self._sleep_periodically and (
            self._n_calls % self._calls_between_sleeping == 0
        ):
            print(f'Rate limit protection: sleeping for {self._sleep_seconds}s...')
            time.sleep(self._sleep_seconds)

        # =====================================================================
        # PREPARE API CALL
        # =====================================================================
        # Anthropic uses a messages format with explicit roles
        # For single-turn generation, we use one "user" message
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Convert terminators to list for API
        stop_sequences = list(terminators) if terminators else None

        # =====================================================================
        # MAKE API CALL
        # =====================================================================
        try:
            response = self._client.messages.create(
                model=self._model_name,
                max_tokens=max_tokens,  # REQUIRED for Anthropic
                messages=messages,
                temperature=temperature,
                stop_sequences=stop_sequences,
                # Note: timeout is handled at the client level in newer versions
            )

            # =================================================================
            # EXTRACT RESPONSE TEXT
            # =================================================================
            # Response structure:
            # response.content = list of content blocks
            # response.content[0].text = the generated text (for text responses)
            # response.stop_reason = why generation stopped
            #   - "end_turn": natural completion
            #   - "max_tokens": hit token limit
            #   - "stop_sequence": hit a stop sequence

            if not response.content:
                print('WARNING: No content returned by Anthropic API')
                print(f'Stop reason: {response.stop_reason}')
                return ''

            # Check stop reason for debugging
            if response.stop_reason == 'max_tokens':
                print(f'WARNING: Response truncated due to max_tokens ({max_tokens})')

            # Extract text from first content block
            # (Claude can return multiple blocks for complex responses)
            first_block = response.content[0]

            # Content blocks have a 'type' field - we want 'text' type
            if hasattr(first_block, 'text'):
                response_text = first_block.text
            else:
                print(f'WARNING: Unexpected content block type: {type(first_block)}')
                return ''

            # =================================================================
            # TRUNCATE AT TERMINATORS
            # =================================================================
            return utils.truncate(response_text, delimiters=terminators)

        except anthropic.APIConnectionError as e:
            print(f'Anthropic connection error: {e}')
            return ''

        except anthropic.RateLimitError as e:
            print(f'Anthropic rate limit hit: {e}')
            print('Consider increasing sleep_seconds or calls_between_sleeping')
            return ''

        except anthropic.APIStatusError as e:
            print(f'Anthropic API error: {e.status_code} - {e.message}')
            print(f'prompt: {prompt[:500]}...')
            return ''

        except Exception as e:
            # Catch-all for unexpected errors
            print(f'Unexpected error: {type(e).__name__}: {e}')
            print(f'prompt: {prompt[:500]}...')
            return ''
