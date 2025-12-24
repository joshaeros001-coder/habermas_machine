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

"""
LLM clients for a prompted Habermas Machine.

Available Clients:
- AIStudioClient: Google Gemini/Gemma models (via AI Studio API)
- OpenAIClient: GPT models (GPT-4o, GPT-4-turbo, etc.)
- AnthropicClient: Claude models (Claude 3.5, Claude 3 Opus, etc.)

Usage:
    # Google Gemini
    from habermas_machine.llm_client.aistudio_client import AIStudioClient
    client = AIStudioClient("gemini-2.5-pro")

    # OpenAI GPT
    from habermas_machine.llm_client.openai_client import OpenAIClient
    client = OpenAIClient("gpt-4o")

    # Anthropic Claude
    from habermas_machine.llm_client.anthropic_client import AnthropicClient
    client = AnthropicClient("claude-sonnet-4-20250514")

Environment Variables Required:
    - GOOGLE_API_KEY: For AIStudioClient
    - OPENAI_API_KEY: For OpenAIClient
    - ANTHROPIC_API_KEY: For AnthropicClient
"""
