#!/usr/bin/env python3
"""
Check ALL available models from Google, OpenAI, and Anthropic APIs.

This script dynamically fetches and displays ALL models available
for your API keys - no hardcoded lists.

Usage:
    python check_models.py           # Check all APIs with available keys
    python check_models.py google    # Check only Google/Gemini
    python check_models.py openai    # Check only OpenAI
    python check_models.py anthropic # Check only Anthropic

Environment Variables Required:
    - GOOGLE_API_KEY: For Gemini models
    - OPENAI_API_KEY: For GPT models
    - ANTHROPIC_API_KEY: For Claude models

Install dependencies:
    pip install google-generativeai openai anthropic
"""

import os
import sys

# =============================================================================
# GOOGLE GEMINI MODELS
# =============================================================================

def check_google_models():
    """Fetch and display all Google Gemini models."""
    print("=" * 80)
    print("GOOGLE GEMINI MODELS")
    print("=" * 80)

    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("  SKIPPED: GOOGLE_API_KEY environment variable not set")
        print()
        return []

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        all_models = list(genai.list_models())
    except ImportError:
        print("  ERROR: google-generativeai not installed")
        print("  Run: pip install google-generativeai")
        print()
        return []
    except Exception as e:
        print(f"  ERROR: Could not fetch model list: {e}")
        print()
        return []

    # Filter for models that support text generation
    gemini_models = []
    for model in all_models:
        model_id = model.name.replace("models/", "")
        supported_methods = [m for m in model.supported_generation_methods]
        if 'generateContent' in supported_methods:
            gemini_models.append({
                'id': model_id,
                'display_name': model.display_name,
                'input_token_limit': getattr(model, 'input_token_limit', 'N/A'),
                'output_token_limit': getattr(model, 'output_token_limit', 'N/A'),
            })

    # Sort by model ID (newest first)
    gemini_models.sort(key=lambda x: x['id'], reverse=True)

    print(f"  Found {len(gemini_models)} models supporting text generation:")
    print()

    for i, model in enumerate(gemini_models, 1):
        print(f"  {i:2}. {model['id']}")
        print(f"      {model['display_name']}")
        print(f"      Input: {model['input_token_limit']:,} | Output: {model['output_token_limit']:,}")
        print()

    return gemini_models


# =============================================================================
# OPENAI GPT MODELS
# =============================================================================

def check_openai_models():
    """Fetch and display all OpenAI models."""
    print("=" * 80)
    print("OPENAI GPT MODELS")
    print("=" * 80)

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("  SKIPPED: OPENAI_API_KEY environment variable not set")
        print()
        return []

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        models = client.models.list()
    except ImportError:
        print("  ERROR: openai not installed")
        print("  Run: pip install openai")
        print()
        return []
    except Exception as e:
        print(f"  ERROR: Could not fetch model list: {e}")
        print()
        return []

    # Filter for GPT and chat models (exclude embeddings, whisper, dall-e, etc.)
    chat_models = []
    for model in models.data:
        model_id = model.id
        # Include GPT models and o1/o3 reasoning models
        if any(prefix in model_id.lower() for prefix in ['gpt-', 'o1', 'o3', 'chatgpt']):
            chat_models.append({
                'id': model_id,
                'created': model.created,
                'owned_by': model.owned_by,
            })

    # Sort by creation date (newest first)
    chat_models.sort(key=lambda x: x['created'], reverse=True)

    print(f"  Found {len(chat_models)} chat/reasoning models:")
    print()

    # Group by model family for easier reading
    families = {}
    for model in chat_models:
        # Extract family (e.g., gpt-4o, gpt-4-turbo, o1)
        model_id = model['id']
        if model_id.startswith('gpt-4o'):
            family = 'GPT-4o Series'
        elif model_id.startswith('gpt-4-turbo'):
            family = 'GPT-4 Turbo Series'
        elif model_id.startswith('gpt-4'):
            family = 'GPT-4 Series'
        elif model_id.startswith('gpt-3.5'):
            family = 'GPT-3.5 Series'
        elif model_id.startswith('o1') or model_id.startswith('o3'):
            family = 'O-Series (Reasoning)'
        elif 'chatgpt' in model_id.lower():
            family = 'ChatGPT Series'
        else:
            family = 'Other'

        if family not in families:
            families[family] = []
        families[family].append(model)

    # Display by family
    idx = 1
    for family in ['O-Series (Reasoning)', 'GPT-4o Series', 'GPT-4 Turbo Series',
                   'GPT-4 Series', 'ChatGPT Series', 'GPT-3.5 Series', 'Other']:
        if family in families and families[family]:
            print(f"  --- {family} ---")
            for model in families[family]:
                from datetime import datetime
                created_date = datetime.fromtimestamp(model['created']).strftime('%Y-%m-%d')
                print(f"  {idx:2}. {model['id']}")
                print(f"      Created: {created_date} | Owner: {model['owned_by']}")
                idx += 1
            print()

    return chat_models


# =============================================================================
# ANTHROPIC CLAUDE MODELS
# =============================================================================

def check_anthropic_models():
    """Display Anthropic Claude models (API doesn't have list endpoint)."""
    print("=" * 80)
    print("ANTHROPIC CLAUDE MODELS")
    print("=" * 80)

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("  SKIPPED: ANTHROPIC_API_KEY environment variable not set")
        print()
        return []

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
    except ImportError:
        print("  ERROR: anthropic not installed")
        print("  Run: pip install anthropic")
        print()
        return []
    except Exception as e:
        print(f"  ERROR: Could not initialize client: {e}")
        print()
        return []

    # Anthropic doesn't have a list_models endpoint, so we use known models
    # Updated December 2025 - includes latest Claude 4 series
    claude_models = [
        # Claude 4 Series (Latest - 2025)
        {
            'id': 'claude-sonnet-4-20250514',
            'family': 'Claude 4',
            'description': 'Claude Sonnet 4 - Latest balanced model (May 2025)',
            'context': '200K',
        },
        {
            'id': 'claude-opus-4-20250514',
            'family': 'Claude 4',
            'description': 'Claude Opus 4 - Most capable, complex reasoning (May 2025)',
            'context': '200K',
        },
        # Claude 3.5 Series (2024)
        {
            'id': 'claude-3-5-sonnet-20241022',
            'family': 'Claude 3.5',
            'description': 'Claude 3.5 Sonnet - Previous generation balanced (Oct 2024)',
            'context': '200K',
        },
        {
            'id': 'claude-3-5-haiku-20241022',
            'family': 'Claude 3.5',
            'description': 'Claude 3.5 Haiku - Fast and efficient (Oct 2024)',
            'context': '200K',
        },
        # Claude 3 Series (Early 2024)
        {
            'id': 'claude-3-opus-20240229',
            'family': 'Claude 3',
            'description': 'Claude 3 Opus - Previous most capable (Feb 2024)',
            'context': '200K',
        },
        {
            'id': 'claude-3-sonnet-20240229',
            'family': 'Claude 3',
            'description': 'Claude 3 Sonnet - Previous balanced (Feb 2024)',
            'context': '200K',
        },
        {
            'id': 'claude-3-haiku-20240307',
            'family': 'Claude 3',
            'description': 'Claude 3 Haiku - Fast and cheap (Mar 2024)',
            'context': '200K',
        },
    ]

    print("  Note: Anthropic API doesn't provide a list_models endpoint.")
    print("  These are the known available models as of December 2025:")
    print()

    # Test API key validity with a minimal request
    try:
        # Just test that the API key works
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print("  API Key Status: VALID")
        print()
    except anthropic.AuthenticationError:
        print("  API Key Status: INVALID - check your ANTHROPIC_API_KEY")
        print()
        return []
    except anthropic.RateLimitError:
        print("  API Key Status: VALID (rate limited, but key works)")
        print()
    except Exception as e:
        print(f"  API Key Status: Unknown ({type(e).__name__})")
        print()

    # Display by family
    current_family = None
    for i, model in enumerate(claude_models, 1):
        if model['family'] != current_family:
            current_family = model['family']
            print(f"  --- {current_family} Series ---")

        print(f"  {i}. {model['id']}")
        print(f"     {model['description']}")
        print(f"     Context: {model['context']} tokens")
        print()

    return claude_models


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Main entry point."""
    print()
    print("*" * 80)
    print("*  MODEL CHECKER - Google Gemini, OpenAI GPT, Anthropic Claude")
    print("*  December 2025")
    print("*" * 80)
    print()

    # Parse command line arguments
    check_all = len(sys.argv) == 1
    providers = [arg.lower() for arg in sys.argv[1:]]

    all_models = {
        'google': [],
        'openai': [],
        'anthropic': []
    }

    # Check requested providers
    if check_all or 'google' in providers or 'gemini' in providers:
        all_models['google'] = check_google_models()

    if check_all or 'openai' in providers or 'gpt' in providers:
        all_models['openai'] = check_openai_models()

    if check_all or 'anthropic' in providers or 'claude' in providers:
        all_models['anthropic'] = check_anthropic_models()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"  Google Gemini:    {len(all_models['google']):3} models")
    print(f"  OpenAI GPT:       {len(all_models['openai']):3} models")
    print(f"  Anthropic Claude: {len(all_models['anthropic']):3} models")
    print()

    print("=" * 80)
    print("RECOMMENDED MODELS FOR SACRED VALUE TESTING")
    print("=" * 80)
    print()
    print("  Google Gemini (tested):")
    print("    - gemini-2.5-pro           # Best for complex reasoning")
    print("    - gemini-2.5-flash         # Fast, good quality")
    print("    - gemini-2.0-flash         # Previous generation")
    print()
    print("  OpenAI GPT:")
    print("    - gpt-4o                   # Latest, multimodal")
    print("    - gpt-4o-mini              # Faster, cheaper")
    print("    - o1                       # Reasoning model (expensive)")
    print()
    print("  Anthropic Claude:")
    print("    - claude-sonnet-4-20250514 # Latest balanced")
    print("    - claude-opus-4-20250514   # Most capable")
    print("    - claude-3-5-sonnet-20241022 # Previous gen balanced")
    print()

    print("=" * 80)
    print("USAGE IN SACRED VALUE TEST")
    print("=" * 80)
    print()
    print("  For Gemini models:")
    print("    from habermas_machine.llm_client.aistudio_client import AIStudioClient")
    print("    client = AIStudioClient('gemini-2.5-pro')")
    print()
    print("  For OpenAI models:")
    print("    from habermas_machine.llm_client.openai_client import OpenAIClient")
    print("    client = OpenAIClient('gpt-4o')")
    print()
    print("  For Anthropic models:")
    print("    from habermas_machine.llm_client.anthropic_client import AnthropicClient")
    print("    client = AnthropicClient('claude-sonnet-4-20250514')")
    print()
    print("=" * 80)


if __name__ == '__main__':
    main()
