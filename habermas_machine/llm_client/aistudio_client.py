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

"""Language Model that uses GDM AI Studio API."""

from collections.abc import Collection, Mapping, Sequence
import os
import time

import google.generativeai as genai
from typing_extensions import override

from habermas_machine.llm_client import base_client
from habermas_machine.llm_client import utils


DEFAULT_SAFETY_SETTINGS = (
    {
        'category': 'HARM_CATEGORY_HARASSMENT',
        'threshold': 'BLOCK_ONLY_HIGH',
    },
    {
        'category': 'HARM_CATEGORY_HATE_SPEECH',
        'threshold': 'BLOCK_ONLY_HIGH',
    },
    {
        'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT',
        'threshold': 'BLOCK_ONLY_HIGH',
    },
    {
        'category': 'HARM_CATEGORY_DANGEROUS_CONTENT',
        'threshold': 'BLOCK_ONLY_HIGH',
    },
)


class AIStudioClient(base_client.LLMClient):
  """Language Model that uses AI Studio API."""

  def __init__(
      self,
      model_name: str,
      *,
      safety_settings: Sequence[Mapping[str, str]] = DEFAULT_SAFETY_SETTINGS,
      sleep_periodically: bool = False,
      sleep_seconds: float = 5.0,
      calls_between_sleeping: int = 5,
  ) -> None:
    """Initializes the instance.

    Args:
      model_name: which language model to use. For more details, see
        https://aistudio.google.com/.
      safety_settings: Gemini safety settings. For more details, see
        https://ai.google.dev/gemini-api/docs/safety.
      sleep_periodically: sleep between API calls to avoid rate limit.
      sleep_seconds: how long to sleep (default 5 seconds).
      calls_between_sleeping: sleep after this many calls (default 5).
    """
    self._api_key = os.environ['GOOGLE_API_KEY']
    self._model_name = model_name
    self._safety_settings = safety_settings
    self._sleep_periodically = sleep_periodically
    self._sleep_seconds = sleep_seconds

    genai.configure(api_key=self._api_key)
    self._model = genai.GenerativeModel(
        model_name=self._model_name,
        safety_settings=safety_settings,
    )

    self._calls_between_sleeping = calls_between_sleeping
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
    del timeout
    del seed  # AI Studio does not support seeds.

    self._n_calls += 1
    if self._sleep_periodically and (
        self._n_calls % self._calls_between_sleeping == 0):
      print(f'Rate limit protection: sleeping for {self._sleep_seconds}s...')
      time.sleep(self._sleep_seconds)

    sample = self._model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            stop_sequences=terminators,
        ),
        safety_settings=self._safety_settings,
        stream=False,
    )
    try:
      # AI Studio returns a list of parts, but we only use the first one.
      if not sample.candidates:
        print('WARNING: No candidates returned by API')
        print(f'Prompt feedback: {sample.prompt_feedback}')
        raise ValueError('No candidates in response')

      candidate = sample.candidates[0]
      if not candidate.content.parts:
        print('WARNING: No content parts returned by API')
        print(f'Finish reason: {candidate.finish_reason}')
        print(f'Safety ratings: {candidate.safety_ratings}')
        raise ValueError('No parts in response')

      response = candidate.content.parts[0].text
    except (ValueError, IndexError) as e:
      print('An error occurred: ', e)
      print(f'prompt: {prompt[:500]}...')  # Truncate long prompts
      print(f'sample: {sample}')
      response = ''
    return utils.truncate(response, delimiters=terminators)

