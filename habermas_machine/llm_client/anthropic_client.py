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

"""Language Model that uses Anthropic's Claude API."""

from collections.abc import Collection
import os
import time

import anthropic
from typing_extensions import override

from habermas_machine.llm_client import base_client
from habermas_machine.llm_client import utils


class AnthropicClient(base_client.LLMClient):
  """Language Model that uses Anthropic's Claude API."""

  def __init__(
      self,
      model_name: str,
      *,
      sleep_periodically: bool = False,
      max_retries: int = 3,
  ) -> None:
    """Initializes the Anthropic client.

    Args:
      model_name: Which Claude model to use (e.g., 'claude-3-5-sonnet-20241022').
        For available models, see https://docs.anthropic.com/en/docs/models-overview.
      sleep_periodically: Sleep between API calls to avoid rate limits.
      max_retries: Maximum number of retries for API calls on failure.
    """
    self._api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not self._api_key:
      raise ValueError(
          'ANTHROPIC_API_KEY environment variable is not set. '
          'Get your API key from https://console.anthropic.com/'
      )

    self._model_name = model_name
    self._sleep_periodically = sleep_periodically
    self._max_retries = max_retries

    # Initialize Anthropic client
    self._client = anthropic.Anthropic(api_key=self._api_key)

    # Rate limiting configuration
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
      temperature: Model temperature (0.0-1.0).
      timeout: Timeout for the request in seconds.
      seed: Optional seed for sampling (not supported by Anthropic API).

    Returns:
      The sampled response (does not include the prompt).

    Raises:
      TimeoutError: If the operation times out.
      anthropic.APIError: If the API request fails after retries.
    """
    del seed  # Anthropic API does not support random seeds

    # Periodic sleeping to avoid rate limits
    self._n_calls += 1
    if self._sleep_periodically and (
        self._n_calls % self._calls_between_sleeping == 0
    ):
      print('Sleeping for 10 seconds to avoid rate limits...')
      time.sleep(10)

    # Convert terminators to stop_sequences (Anthropic format)
    stop_sequences = list(terminators) if terminators else None

    # Retry logic for API failures
    last_exception = None
    for attempt in range(self._max_retries):
      try:
        # Call Anthropic API
        message = self._client.messages.create(
            model=self._model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                }
            ],
            stop_sequences=stop_sequences,
            timeout=timeout,
        )

        # Extract text from response
        # Anthropic returns a Message object with content blocks
        if message.content and len(message.content) > 0:
          # Get the first content block (text)
          response = message.content[0].text
        else:
          response = ''

        # Truncate at terminators if needed
        return utils.truncate(response, delimiters=terminators)

      except anthropic.APITimeoutError as e:
        print(f'API timeout on attempt {attempt + 1}/{self._max_retries}: {e}')
        last_exception = e
        if attempt < self._max_retries - 1:
          time.sleep(2 ** attempt)  # Exponential backoff
        else:
          raise TimeoutError(f'API request timed out after {self._max_retries} attempts') from e

      except anthropic.RateLimitError as e:
        print(f'Rate limit hit on attempt {attempt + 1}/{self._max_retries}: {e}')
        last_exception = e
        if attempt < self._max_retries - 1:
          sleep_time = 10 * (2 ** attempt)  # Longer backoff for rate limits
          print(f'Sleeping for {sleep_time} seconds...')
          time.sleep(sleep_time)
        else:
          raise

      except anthropic.APIError as e:
        print(f'API error on attempt {attempt + 1}/{self._max_retries}: {e}')
        print(f'Error type: {type(e).__name__}')
        print(f'Prompt (first 200 chars): {prompt[:200]}...')
        last_exception = e
        if attempt < self._max_retries - 1:
          time.sleep(2 ** attempt)  # Exponential backoff
        else:
          # Return empty string on final failure (matches aistudio behavior)
          print('All retries exhausted. Returning empty string.')
          return ''

      except Exception as e:
        # Catch-all for unexpected errors
        print(f'Unexpected error on attempt {attempt + 1}/{self._max_retries}: {e}')
        print(f'Error type: {type(e).__name__}')
        last_exception = e
        if attempt < self._max_retries - 1:
          time.sleep(2 ** attempt)
        else:
          print('All retries exhausted. Returning empty string.')
          return ''

    # Should never reach here, but just in case
    print('Unexpected: exited retry loop without return. Returning empty string.')
    return ''
