import anthropic
import os

# Set your API key
client = anthropic.Anthropic(
    api_key=os.environ['ANTHROPIC_API_KEY']
)

# Try to list models (Anthropic API doesn't have a direct list method)
# So we'll test common model names

models_to_test = [
    'claude-3-5-sonnet-20241022',
    'claude-3-5-sonnet-20240620',
    'claude-3-opus-20240229',
    'claude-3-sonnet-20240229',
    'claude-3-haiku-20240307',
]

print("Testing Claude models...")
print("="*50)

for model_name in models_to_test:
    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"✅ {model_name} - WORKS")
    except anthropic.NotFoundError:
        print(f"❌ {model_name} - NOT FOUND")
    except Exception as e:
        print(f"⚠️  {model_name} - ERROR: {e}")

print("="*50)