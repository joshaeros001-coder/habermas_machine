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
OpenAI Client for Habermas Machine
==================================

This client enables testing GPT models (GPT-4o, GPT-4-turbo, etc.) with the
Habermas Machine deliberation system. Created as part of sacred value research
to compare how different LLM families handle non-negotiable religious positions.

Architecture:
- Inherits from base_client.LLMClient (same interface as Gemini client)
- Uses OpenAI's Chat Completions API
- Implements rate limiting to avoid quota errors
- Handles errors gracefully for long-running experiments

Usage:
    from habermas_machine.llm_client.openai_client import OpenAIClient

    client = OpenAIClient(
        model_name="gpt-4o",
        sleep_periodically=True,  # Avoid rate limits
    )

Environment:
    Requires OPENAI_API_KEY environment variable

Models to test:
    - gpt-4o (latest, multimodal)
    - gpt-4o-mini (faster, cheaper)
    - gpt-4-turbo (previous generation)
"""

from collections.abc import Collection, Mapping, Sequence
import os
import time

# OpenAI's official Python client
# Install: pip install openai
from openai import OpenAI
from typing_extensions import override

from habermas_machine.llm_client import base_client
from habermas_machine.llm_client import utils


# =============================================================================
# SAFETY SETTINGS
# =============================================================================
# OpenAI's safety approach differs from Gemini's explicit category thresholds.
# OpenAI uses built-in content moderation that:
#   1. Automatically filters harmful content during generation
#   2. Returns finish_reason='content_filter' if blocked
#   3. Can optionally use the Moderation API for pre/post checking
#
# For scientific consistency with the Habermas Machine's Gemini implementation
# (which uses BLOCK_ONLY_HIGH), we rely on OpenAI's default moderation which
# is roughly equivalent - it blocks clearly harmful content but allows
# discussion of sensitive topics like medical decisions and religious beliefs.
#
# The categories OpenAI monitors (similar to Gemini's):
#   - hate: Content expressing hatred toward groups
#   - harassment: Content attacking individuals
#   - self-harm: Content promoting self-injury
#   - sexual: Explicit sexual content
#   - violence: Content depicting violence
#
# Note: OpenAI's safety is not configurable per-request like Gemini's.
# This is documented for transparency in cross-model comparison.
# =============================================================================

DEFAULT_SAFETY_NOTE = """
OpenAI Safety: Using default content moderation (equivalent to BLOCK_ONLY_HIGH).
OpenAI automatically filters harmful content and returns finish_reason='content_filter'
if a response is blocked. This is comparable to Gemini's BLOCK_ONLY_HIGH threshold.
"""


class OpenAIClient(base_client.LLMClient):
    """
    Language Model client for OpenAI's GPT models.

    This class wraps OpenAI's Chat Completions API to match the LLMClient
    interface used by the Habermas Machine. The key method is sample_text(),
    which takes a prompt and returns generated text.

    Key differences from Gemini:
    - Uses "messages" format (chat-style) rather than raw prompt
    - Supports native seed parameter for reproducibility
    - Different rate limit characteristics

    Attributes:
        _client: OpenAI client instance
        _model_name: Which GPT model to use (e.g., "gpt-4o")
        _sleep_periodically: Whether to pause between API calls
        _sleep_seconds: How long to pause (default 2 seconds)
        _calls_between_sleeping: Pause every N calls (default 10)
        _n_calls: Counter for rate limiting
    """

    def __init__(
        self,
        model_name: str,
        *,
        sleep_periodically: bool = False,
        sleep_seconds: float = 2.0,
        calls_between_sleeping: int = 10,
    ) -> None:
        """
        Initialize the OpenAI client.

        Args:
            model_name: Which GPT model to use. Options include:
                - "gpt-4o": Latest GPT-4 Omni model (recommended)
                - "gpt-4o-mini": Faster/cheaper variant
                - "gpt-4-turbo": Previous generation GPT-4
                - "gpt-3.5-turbo": Older, fastest option

            sleep_periodically: If True, pause between API calls to avoid
                hitting rate limits. Recommended for free tier or heavy usage.

            sleep_seconds: How many seconds to sleep. OpenAI rate limits are
                generally more generous than Gemini, so 2 seconds is usually enough.

            calls_between_sleeping: Sleep after this many API calls.
                OpenAI allows more requests per minute than Gemini free tier.

        Raises:
            KeyError: If OPENAI_API_KEY environment variable is not set.

        Example:
            # Basic usage
            client = OpenAIClient("gpt-4o")

            # With rate limiting for long experiments
            client = OpenAIClient(
                "gpt-4o",
                sleep_periodically=True,
                sleep_seconds=2.0,
                calls_between_sleeping=10,
            )
        """
        # =====================================================================
        # API KEY SETUP
        # =====================================================================
        # Read API key from environment variable
        # Set this before running: export OPENAI_API_KEY="sk-..."
        self._api_key = os.environ['OPENAI_API_KEY']

        # Store model name for API calls
        self._model_name = model_name

        # =====================================================================
        # CREATE OPENAI CLIENT
        # =====================================================================
        # The OpenAI() constructor automatically reads OPENAI_API_KEY from
        # environment, but we pass it explicitly for clarity
        self._client = OpenAI(api_key=self._api_key)

        # =====================================================================
        # RATE LIMITING CONFIGURATION
        # =====================================================================
        # OpenAI has rate limits based on your tier:
        # - Free tier: 3 RPM (requests per minute) for GPT-4
        # - Tier 1: 500 RPM for GPT-4o
        # These settings help stay under limits during experiments
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
        Generate text from the GPT model.

        This method is called by the Habermas Machine for:
        1. Generating consensus statement candidates (StatementModel)
        2. Generating ranking explanations (RewardModel)

        The prompt contains the full context (question, opinions, instructions)
        formatted by the Habermas Machine's prompt templates.

        Args:
            prompt: The full prompt text. For the Habermas Machine, this includes
                the deliberation question, all citizen opinions, and instructions
                for generating consensus statements or rankings.

            max_tokens: Maximum tokens in the response. The Habermas Machine
                uses 8192 by default to accommodate chain-of-thought reasoning.

            terminators: Stop sequences. If any of these strings appear in the
                output, generation stops. Used to detect end of structured output.

            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative).
                Default 0.8 allows some variation while maintaining coherence.

            timeout: Not directly used by OpenAI client (handled by httpx internally).

            seed: For reproducibility. OpenAI supports this natively, unlike Gemini.
                Same seed + same prompt = same output (mostly).

        Returns:
            The generated text response, truncated at any terminator string.
            Returns empty string if an error occurs.

        Example output for sacred value test:
            "The jury acknowledges that the decision to start SSRI antidepressants
            is a deeply personal one that requires careful consideration..."
        """
        # =====================================================================
        # RATE LIMITING
        # =====================================================================
        # Increment call counter and sleep if needed
        self._n_calls += 1
        if self._sleep_periodically and (
            self._n_calls % self._calls_between_sleeping == 0
        ):
            print(f'Rate limit protection: sleeping for {self._sleep_seconds}s...')
            time.sleep(self._sleep_seconds)

        # =====================================================================
        # PREPARE API CALL
        # =====================================================================
        # OpenAI uses chat format: list of messages with roles
        # For single-turn generation, we use one "user" message with the full prompt
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Convert terminators to list (OpenAI expects list, not tuple)
        stop_sequences = list(terminators) if terminators else None

        # =====================================================================
        # MAKE API CALL
        # =====================================================================
        # Convert seed to Python int (numpy int64 is not JSON serializable)
        if seed is not None:
            seed = int(seed)

        try:
            # Newer models (o1, o3, gpt-5.x) use max_completion_tokens
            # Older models (gpt-4o, gpt-3.5) use max_tokens
            # We detect based on model name prefix
            is_new_model = any(
                self._model_name.startswith(prefix)
                for prefix in ['o1', 'o3', 'gpt-5', 'gpt-4.1']
            )

            if is_new_model:
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=messages,
                    max_completion_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop_sequences,
                    seed=seed,
                )
            else:
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop_sequences,
                    seed=seed,
                )

            # =================================================================
            # EXTRACT RESPONSE TEXT
            # =================================================================
            # Response structure:
            # response.choices[0].message.content = the generated text
            # response.choices[0].finish_reason = why generation stopped
            #   - "stop": hit a stop sequence or natural end
            #   - "length": hit max_tokens limit
            #   - "content_filter": blocked by safety filter

            if not response.choices:
                print('WARNING: No choices returned by OpenAI API')
                return ''

            choice = response.choices[0]

            # Check finish reason for debugging
            if choice.finish_reason == 'length':
                print(f'WARNING: Response truncated due to max_tokens ({max_tokens})')
            elif choice.finish_reason == 'content_filter':
                print('WARNING: Response blocked by content filter')
                return ''

            # Extract the actual text
            response_text = choice.message.content or ''

            # =================================================================
            # TRUNCATE AT TERMINATORS
            # =================================================================
            # Even though we pass stop sequences to the API, we also truncate
            # locally for consistency with the Gemini client behavior
            return utils.truncate(response_text, delimiters=terminators)

        except Exception as e:
            # =================================================================
            # ERROR HANDLING
            # =================================================================
            # Log error details but don't crash - return empty string
            # The Habermas Machine has retry logic that will try again
            print(f'OpenAI API error: {type(e).__name__}: {e}')
            print(f'prompt: {prompt[:500]}...')  # Truncate long prompts in logs
            return ''
