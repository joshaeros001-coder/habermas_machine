#!/usr/bin/env python3
"""
Check available Google Gemini models and their status.

This script lists all Gemini models and checks which ones are available
for your API key.

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
# ALL GOOGLE GEMINI MODELS (as of November 2024)
# ============================================================================
# Listed in recommended testing order (newest/best first)

GEMINI_MODELS = [
    # --- Gemini 2.5 Series (Latest - December 2024) ---
    ("gemini-2.5-pro-preview-05-06", "2.5 Pro Preview (May 2025) - Latest flagship"),
    ("gemini-2.5-flash-preview-05-20", "2.5 Flash Preview (May 2025) - Latest fast"),
    ("gemini-2.5-pro-preview-03-25", "2.5 Pro Preview (March 2025)"),
    ("gemini-2.5-flash", "2.5 Flash - Fast & efficient"),
    ("gemini-2.5-pro", "2.5 Pro - Most capable"),

    # --- Gemini 2.0 Series ---
    ("gemini-2.0-flash", "2.0 Flash - Fast multimodal"),
    ("gemini-2.0-flash-lite", "2.0 Flash Lite - Lightweight"),
    ("gemini-2.0-flash-exp", "2.0 Flash Experimental"),

    # --- Gemini 1.5 Series ---
    ("gemini-1.5-pro", "1.5 Pro - Previous flagship"),
    ("gemini-1.5-pro-latest", "1.5 Pro Latest"),
    ("gemini-1.5-flash", "1.5 Flash - Fast"),
    ("gemini-1.5-flash-latest", "1.5 Flash Latest"),
    ("gemini-1.5-flash-8b", "1.5 Flash 8B - Smallest"),

    # --- Gemini 1.0 Series (Legacy) ---
    ("gemini-1.0-pro", "1.0 Pro - Legacy"),
    ("gemini-pro", "Pro - Alias for 1.0 Pro"),
]

# ============================================================================
# CHECK MODEL AVAILABILITY
# ============================================================================

print("=" * 70)
print("GOOGLE GEMINI MODEL AVAILABILITY CHECK")
print("=" * 70)
print()

available_models = []
unavailable_models = []

# Get list of available models from API
try:
    api_models = {m.name.replace("models/", ""): m for m in genai.list_models()}
except Exception as e:
    print(f"ERROR: Could not fetch model list: {e}")
    api_models = {}

print(f"Found {len(api_models)} models available via API\n")

# Check each model
for model_id, description in GEMINI_MODELS:
    if model_id in api_models:
        available_models.append((model_id, description))
        status = "✅ AVAILABLE"
    else:
        unavailable_models.append((model_id, description))
        status = "❌ Not available"

    print(f"{status:20} | {model_id:40} | {description}")

print()
print("=" * 70)
print(f"SUMMARY: {len(available_models)} available, {len(unavailable_models)} unavailable")
print("=" * 70)

# ============================================================================
# RECOMMENDED TESTING ORDER
# ============================================================================

print()
print("RECOMMENDED TESTING ORDER (copy these model names):")
print("-" * 70)
for i, (model_id, description) in enumerate(available_models, 1):
    print(f"  {i}. {model_id}")

print()
print("To test a model, edit example_sacred_value_test.py and change:")
print("  MODEL = 'gemini-2.5-flash'")
print("to:")
print("  MODEL = '<model-name-from-above>'")
