#!/usr/bin/env python3
"""
API Key Tester
==============

Tests if your API keys for OpenAI, Anthropic, and Google are working.
Run this FIRST before running any experiments.

Usage:
    python test_api_keys.py

What it does:
    - Sends a simple "Hello" prompt to each provider
    - Reports which ones work and which ones fail
    - Shows you what environment variables are needed
"""

import os

# ============================================================================
# PLAIN LANGUAGE: What are we doing?
# ============================================================================
#
# Before running experiments, we need to make sure you can actually talk to
# the AI models. Each provider (OpenAI, Anthropic, Google) requires an API key.
# This script tests each one with a simple prompt.
#
# ============================================================================


def test_openai():
    """
    Test OpenAI API (GPT models).

    TECHNICAL: Uses the openai Python package to call chat.completions.create()
    PLAIN: Sends "Say hello" to GPT and checks if it responds.
    """
    print("\n" + "="*60)
    print("Testing OPENAI (GPT models)...")
    print("="*60)

    # Check if API key exists in environment
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   To fix: export OPENAI_API_KEY='your-key-here'")
        return False

    print(f"✓ API key found (starts with: {api_key[:8]}...)")

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        # Simple test call
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cheap model for testing
            messages=[{"role": "user", "content": "Say 'Hello, API works!' and nothing else."}],
            max_tokens=20,
        )

        result = response.choices[0].message.content
        print(f"✓ OpenAI responded: {result}")
        return True

    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        return False


def test_anthropic():
    """
    Test Anthropic API (Claude models).

    TECHNICAL: Uses the anthropic Python package to call messages.create()
    PLAIN: Sends "Say hello" to Claude and checks if it responds.
    """
    print("\n" + "="*60)
    print("Testing ANTHROPIC (Claude models)...")
    print("="*60)

    # Check if API key exists in environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found in environment")
        print("   To fix: export ANTHROPIC_API_KEY='your-key-here'")
        return False

    print(f"✓ API key found (starts with: {api_key[:8]}...)")

    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)

        # Simple test call
        response = client.messages.create(
            model="claude-3-haiku-20240307",  # Cheap model for testing
            max_tokens=20,
            messages=[{"role": "user", "content": "Say 'Hello, API works!' and nothing else."}],
        )

        result = response.content[0].text
        print(f"✓ Anthropic responded: {result}")
        return True

    except Exception as e:
        print(f"❌ Anthropic error: {e}")
        return False


def test_google():
    """
    Test Google API (Gemini models).

    TECHNICAL: Uses google.generativeai package to call generate_content()
    PLAIN: Sends "Say hello" to Gemini and checks if it responds.
    """
    print("\n" + "="*60)
    print("Testing GOOGLE (Gemini models)...")
    print("="*60)

    # Check if API key exists in environment
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment")
        print("   To fix: export GOOGLE_API_KEY='your-key-here'")
        return False

    print(f"✓ API key found (starts with: {api_key[:8]}...)")

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)

        # Simple test call
        model = genai.GenerativeModel("gemini-1.5-flash")  # Cheap model for testing
        response = model.generate_content("Say 'Hello, API works!' and nothing else.")

        result = response.text
        print(f"✓ Google responded: {result}")
        return True

    except Exception as e:
        print(f"❌ Google error: {e}")
        return False


def main():
    """
    Run all API tests and summarize results.
    """
    print("\n" + "="*60)
    print("  API KEY TESTER")
    print("  Testing OpenAI, Anthropic, and Google APIs")
    print("="*60)

    results = {
        "OpenAI": test_openai(),
        "Anthropic": test_anthropic(),
        "Google": test_google(),
    }

    # Summary
    print("\n" + "="*60)
    print("  SUMMARY")
    print("="*60)

    working = []
    not_working = []

    for provider, success in results.items():
        if success:
            working.append(provider)
            print(f"  ✓ {provider}: WORKING")
        else:
            not_working.append(provider)
            print(f"  ❌ {provider}: NOT WORKING")

    print()

    if len(working) == 3:
        print("🎉 All APIs working! You can run experiments with any model.")
    elif len(working) > 0:
        print(f"⚠️  {len(working)}/3 APIs working. You can use: {', '.join(working)}")
    else:
        print("❌ No APIs working. Please check your API keys.")

    print("\n" + "="*60)
    print("  HOW TO SET API KEYS")
    print("="*60)
    print("""
    In your terminal, run:

    export OPENAI_API_KEY='sk-...'
    export ANTHROPIC_API_KEY='sk-ant-...'
    export GOOGLE_API_KEY='AI...'

    Or add them to your ~/.bashrc or ~/.zshrc file.
    """)

    return results


if __name__ == "__main__":
    main()
