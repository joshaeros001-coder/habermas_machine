"""
LLM Client Package for Sacred Values Architecture

COPIED FROM: habermas_machine/llm_client/
CHANGES: None - this is a direct copy
WHY: LLM client infrastructure works correctly and doesn't need modification

This package provides a unified interface for calling different LLM APIs.
Currently supports:
- Anthropic Claude (anthropic_client.py)

The base_client.py defines the abstract interface that all clients must implement.
"""

from .base_client import LLMClient, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
from .anthropic_client import AnthropicClient

__all__ = [
    'LLMClient',
    'AnthropicClient',
    'DEFAULT_TEMPERATURE',
    'DEFAULT_MAX_TOKENS',
]
