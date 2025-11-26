import google.generativeai as genai
import os

# Set your API key
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

# List all available models
print("Available models:")
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")