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

"""Language Model client for Anthropic's Claude API.

NEW CLIENT: Created for Sacred Values Architecture
This client interfaces with Anthropic's Claude API (Claude 3.5 Sonnet, etc.)
"""

from collections.abc import Collection
import os
import time

from typing_extensions import override

from sacred_values_architecture.llm_client import base_client
from sacred_values_architecture.llm_client import utils


class AnthropicClient(base_client.LLMClient):
    """Language Model that uses Anthropic's Claude API.

    This client requires the anthropic package:
        pip install anthropic

    And an API key set in the environment:
        export ANTHROPIC_API_KEY='your_key_here'
    """

    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        *,
        sleep_periodically: bool = False,
    ) -> None:
        """Initializes the Anthropic client.

        Args:
            model_name: Which Claude model to use. Options:
                - claude-3-5-sonnet-20241022 (recommended, most capable)
                - claude-3-opus-20240229 (very capable, slower)
                - claude-3-sonnet-20240229 (balanced)
                - claude-3-haiku-20240307 (fast, less capable)
            sleep_periodically: Sleep between API calls to avoid rate limits.
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

        # Get API key from environment
        self._api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not self._api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Set it with: export ANTHROPIC_API_KEY='your_key_here'"
            )

        self._model_name = model_name
        self._sleep_periodically = sleep_periodically

        # Initialize Anthropic client
        self._client = anthropic.Anthropic(api_key=self._api_key)

        # Rate limiting
        self._calls_between_sleeping = 10
        self._n_calls = 0

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
        """Samples text from Claude.

        Args:
            prompt: The input text that the model conditions on.
            max_tokens: The maximum number of tokens in the response.
            terminators: The response will be terminated before any of these strings.
            temperature: Model temperature (0-1).
            timeout: Timeout for the request (currently not used by Anthropic SDK).
            seed: Optional seed for sampling (not supported by Anthropic API).

        Returns:
            The sampled response (does not include the prompt).

        Raises:
            TimeoutError: if the operation times out.
        """
        # Note: Anthropic API doesn't support deterministic seeds currently
        if seed is not None:
            print("Warning: Anthropic API does not support seeds. Ignoring seed parameter.")

        # Rate limiting
        self._n_calls += 1
        if self._sleep_periodically and (self._n_calls % self._calls_between_sleeping == 0):
            print('Sleeping for 10 seconds to avoid rate limits...')
            time.sleep(10)

        try:
            # Call Claude API
            # Anthropic uses a messages format
            message = self._client.messages.create(
                model=self._model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # Anthropic uses stop_sequences instead of terminators
                stop_sequences=list(terminators) if terminators else None,
            )

            # Extract text from response
            response = message.content[0].text

        except Exception as e:
            print(f'An error occurred calling Anthropic API: {e}')
            print(f'Prompt: {prompt[:200]}...')
            response = ''

        # Truncate at terminators if needed (double-check, API should handle this)
        return utils.truncate(response, delimiters=terminators)
