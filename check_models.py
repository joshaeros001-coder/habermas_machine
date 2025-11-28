#!/usr/bin/env python3
"""
Check ALL available Google Gemini models from the API.

This script dynamically fetches and displays ALL models available
for your API key - no hardcoded lists.

Usage:
    python check_models.py
"""

import os
import google.generativeai as genai

# Configure API
api_key = os.environ.get('GOOGLE_API_KEY')
if not api_key:
    print("ERROR: GOOGLE_API_KEY environment variable not set")
    exit(1)

genai.configure(api_key=api_key)

# ============================================================================
# FETCH ALL MODELS FROM API (NO HARDCODING!)
# ============================================================================

print("=" * 80)
print("ALL GOOGLE GEMINI MODELS AVAILABLE FOR YOUR API KEY")
print("=" * 80)
print()

try:
    all_models = list(genai.list_models())
except Exception as e:
    print(f"ERROR: Could not fetch model list: {e}")
    exit(1)

print(f"Total models found: {len(all_models)}")
print()

# ============================================================================
# FILTER AND DISPLAY GEMINI MODELS (text generation capable)
# ============================================================================

# Filter for models that support text generation
gemini_models = []
for model in all_models:
    model_id = model.name.replace("models/", "")
    # Check if it supports generateContent (text generation)
    supported_methods = [m for m in model.supported_generation_methods]
    if 'generateContent' in supported_methods:
        gemini_models.append({
            'id': model_id,
            'display_name': model.display_name,
            'description': getattr(model, 'description', ''),
            'input_token_limit': getattr(model, 'input_token_limit', 'N/A'),
            'output_token_limit': getattr(model, 'output_token_limit', 'N/A'),
        })

print(f"Models supporting text generation: {len(gemini_models)}")
print()
print("-" * 80)

# Sort by model ID to group versions together
gemini_models.sort(key=lambda x: x['id'], reverse=True)

# Display all models
for i, model in enumerate(gemini_models, 1):
    print(f"\n{i:2}. {model['id']}")
    print(f"    Display name: {model['display_name']}")
    print(f"    Input tokens: {model['input_token_limit']:,} | Output tokens: {model['output_token_limit']:,}")

print()
print("=" * 80)
print("QUICK COPY LIST (model IDs only):")
print("=" * 80)
for i, model in enumerate(gemini_models, 1):
    print(f"  {i:2}. {model['id']}")

print()
print("=" * 80)
print("To test a model, edit example_sacred_value_test.py line 41:")
print("  MODEL = '<model-id-from-above>'")
print("=" * 80)
