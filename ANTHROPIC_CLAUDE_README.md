# Using Anthropic Claude with Habermas Machine

## Overview

The Habermas Machine now supports **Anthropic's Claude** as an LLM backend, in addition to Google's Gemini. This allows you to run democratic deliberation using Claude's advanced reasoning capabilities.

---

## Setup

### 1. Install the Anthropic SDK

```bash
pip install anthropic
```

### 2. Get Your API Key

1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (starts with `sk-ant-...`)

### 3. Set Environment Variable

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**For permanent setup**, add to your shell profile (`~/.bashrc` or `~/.zshrc`):
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

---

## Supported Models

The Anthropic client supports all Claude models accessible via the API:

### Recommended Models

| Model | Description | Best For |
|-------|-------------|----------|
| `claude-3-5-sonnet-20241022` | Latest Claude 3.5 Sonnet | **Recommended** - Best balance of performance and cost |
| `claude-3-opus-20240229` | Most capable model | Complex reasoning, highest quality |
| `claude-3-sonnet-20240229` | Balanced model | Good performance, lower cost |
| `claude-3-haiku-20240307` | Fastest model | Quick iterations, lower cost |

For the latest models, see [Anthropic's model documentation](https://docs.anthropic.com/en/docs/models-overview).

---

## Usage Examples

### Basic Usage (Programmatic)

```python
from habermas_machine import machine, types
from habermas_machine.social_choice import utils as sc_utils

# Initialize Claude clients
statement_client = types.LLMCLient.ANTHROPIC.get_client('claude-3-5-sonnet-20241022')
reward_client = types.LLMCLient.ANTHROPIC.get_client('claude-3-5-sonnet-20241022')

# Create other components
statement_model = types.StatementModel.CHAIN_OF_THOUGHT.get_model()
reward_model = types.RewardModel.CHAIN_OF_THOUGHT_RANKING.get_model()
social_choice_method = types.RankAggregation.SCHULZE.get_method(
    sc_utils.TieBreakingMethod.TBRC
)

# Create Habermas Machine with Claude backend
hm = machine.HabermasMachine(
    question="Your deliberation question here",
    statement_client=statement_client,
    reward_client=reward_client,
    statement_model=statement_model,
    reward_model=reward_model,
    social_choice_method=social_choice_method,
    num_candidates=4,
    num_citizens=5,
    verbose=True
)

# Run deliberation
opinions = ["Opinion 1", "Opinion 2", "Opinion 3", "Opinion 4", "Opinion 5"]
winner, candidates = hm.mediate(opinions)

print(f"Consensus: {winner}")
```

### Using the Example Script

```bash
# Set API key
export ANTHROPIC_API_KEY="your_key_here"

# Run the example
python example_anthropic_claude.py
```

This runs a complete deliberation (opinion + critique rounds) on SSRI medication decisions.

---

## Comparing Claude vs Gemini

### Use Claude When:

- ✅ You need strong **reasoning and analysis** capabilities
- ✅ You want **nuanced understanding** of complex arguments
- ✅ You prefer **longer, more detailed** consensus statements
- ✅ You have **Anthropic API credits** or prefer their pricing

### Use Gemini When:

- ✅ You want **faster response times** (Gemini Flash is very fast)
- ✅ You prefer **more concise** consensus statements
- ✅ You already have **Google Cloud** infrastructure
- ✅ You want to use the **original research configuration**

### Side-by-Side Comparison

```python
# Gemini configuration
gemini_statement_client = types.LLMCLient.AISTUDIO.get_client('gemini-2.0-flash')
gemini_reward_client = types.LLMCLient.AISTUDIO.get_client('gemini-2.0-flash')

# Claude configuration
claude_statement_client = types.LLMCLient.ANTHROPIC.get_client('claude-3-5-sonnet-20241022')
claude_reward_client = types.LLMCLient.ANTHROPIC.get_client('claude-3-5-sonnet-20241022')

# Run both deliberations with same question/opinions
# Compare final consensus statements
```

---

## Features & Capabilities

### Error Handling

The Anthropic client includes robust error handling:

- **Automatic retries** (3 attempts by default)
- **Exponential backoff** for transient errors
- **Rate limit handling** with extended backoff
- **Timeout handling** with configurable duration
- **Graceful degradation** (returns empty string on final failure)

### Rate Limiting

Built-in rate limiting options:

```python
# Enable periodic sleeping to avoid rate limits
from habermas_machine.llm_client import anthropic_client

client = anthropic_client.AnthropicClient(
    model_name='claude-3-5-sonnet-20241022',
    sleep_periodically=True,  # Sleep every 10 calls
    max_retries=5  # Increase retry attempts
)
```

### Response Truncation

Supports `terminators` parameter for stopping sequences:

```python
# Stop at specific markers
response = client.sample_text(
    prompt="Generate a statement...",
    terminators=['</answer>', '\n\n'],  # Stop at these strings
    max_tokens=2048
)
```

---

## API Differences: Claude vs Gemini

### What Works the Same

- ✅ **Chain-of-thought prompting** (both support structured templates)
- ✅ **Temperature control** (0.0-1.0 range)
- ✅ **Max tokens** (output length limits)
- ✅ **Stop sequences** (terminators)
- ✅ **Timeout configuration**

### Key Differences

| Feature | Claude | Gemini |
|---------|--------|--------|
| **Random seeds** | ❌ Not supported | ✅ Supported |
| **Safety settings** | ❌ Not configurable | ✅ Configurable |
| **System prompts** | ✅ Supported (not used here) | ❌ Not in Gemini API |
| **Context length** | ✅ 200K tokens | ✅ Varies by model |
| **Streaming** | ✅ Supported (not used) | ✅ Supported (not used) |

**Note**: The Habermas Machine doesn't currently use random seeds for reproducibility with Claude, but the framework otherwise works identically.

---

## Troubleshooting

### API Key Not Found

```
ValueError: ANTHROPIC_API_KEY environment variable is not set.
```

**Solution**:
```bash
export ANTHROPIC_API_KEY="your_key_here"
```

### Rate Limit Errors

```
anthropic.RateLimitError: rate_limit_error
```

**Solutions**:
1. Enable periodic sleeping: `sleep_periodically=True`
2. Reduce number of candidates: `num_candidates=2`
3. Reduce number of citizens: `num_citizens=3`
4. Upgrade API tier in Anthropic Console

### Timeout Errors

```
TimeoutError: API request timed out after 3 attempts
```

**Solutions**:
1. Increase timeout: `timeout=120` (in `sample_text()`)
2. Increase max retries when creating client: `max_retries=5`
3. Check internet connection
4. Verify Anthropic API status

### Import Errors

```
ModuleNotFoundError: No module named 'anthropic'
```

**Solution**:
```bash
pip install anthropic
```

---

## Cost Considerations

### Claude Pricing (as of 2024)

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Opus | $15.00 | $75.00 |
| Claude 3 Haiku | $0.25 | $1.25 |

### Estimating Costs

For a typical deliberation with 5 citizens and 4 candidates:

**Opinion Round:**
- Statement generation: ~4 prompts × ~500 tokens input = 2K input tokens
- Ranking: ~5 citizens × 4 statements × ~300 tokens = 6K input tokens
- Total output: ~4 statements × 200 tokens = 800 tokens

**Critique Round:**
- Similar volumes

**Total per deliberation**: ~10K input tokens, ~2K output tokens

**Cost with Claude 3.5 Sonnet**:
- Input: 10K tokens = $0.03
- Output: 2K tokens = $0.03
- **Total: ~$0.06 per deliberation**

**Cost with Claude 3 Haiku** (budget option):
- **Total: ~$0.005 per deliberation** (much cheaper!)

---

## Advanced Configuration

### Custom Client Initialization

```python
from habermas_machine.llm_client import anthropic_client

# Create client directly (not via types enum)
client = anthropic_client.AnthropicClient(
    model_name='claude-3-5-sonnet-20241022',
    sleep_periodically=True,  # Rate limiting
    max_retries=5  # More retries
)

# Use with Habermas Machine
hm = machine.HabermasMachine(
    question=question,
    statement_client=client,
    reward_client=client,  # Can reuse same client
    # ... other parameters
)
```

### Different Models for Different Tasks

```python
# Use Opus for statement generation (higher quality)
statement_client = types.LLMCLient.ANTHROPIC.get_client('claude-3-opus-20240229')

# Use Haiku for ranking (faster, cheaper)
reward_client = types.LLMCLient.ANTHROPIC.get_client('claude-3-haiku-20240307')

# Optimize cost while maintaining quality
```

---

## Testing

### Verify Installation

```python
import os
os.environ['ANTHROPIC_API_KEY'] = 'your_key_here'

from habermas_machine.llm_client import anthropic_client

client = anthropic_client.AnthropicClient('claude-3-5-sonnet-20241022')
response = client.sample_text("Say hello in one sentence.", max_tokens=100)
print(response)  # Should print a greeting
```

### Run Sacred Values Test with Claude

```python
# Edit example_sacred_value_test.py or compare_secular_vs_sacred.py
# Change MODEL to use Claude:

MODEL = 'claude-3-5-sonnet-20241022'

# Update client initialization:
statement_client = types.LLMCLient.ANTHROPIC.get_client(MODEL)
reward_client = types.LLMCLient.ANTHROPIC.get_client(MODEL)
```

---

## Research Comparison: Claude vs Gemini

### Hypothesis Testing

**Does the choice of LLM affect consensus quality?**

Run the same vignettes with both backends and compare:

```python
# Run with Gemini
gemini_results = run_deliberation(gemini_clients, vignettes)

# Run with Claude
claude_results = run_deliberation(claude_clients, vignettes)

# Compare:
# 1. Consensus statement length
# 2. Sacred value retention rate
# 3. Acknowledgment of diverse perspectives
# 4. Linguistic style (formal vs conversational)
```

**Expected findings**:
- Claude may produce **longer, more detailed** consensus statements
- Gemini may produce **more concise, direct** statements
- Both should **successfully build consensus** on the same questions
- **Sacred value handling** may differ slightly in linguistic framing

---

## Contributing

If you encounter issues with the Anthropic client:

1. Check Anthropic API status: https://status.anthropic.com/
2. Review error messages for API-specific guidance
3. Test with a simple prompt to isolate the issue
4. File an issue in the repository with:
   - Model name used
   - Error message
   - Minimal reproduction case

---

## Additional Resources

- **Anthropic Documentation**: https://docs.anthropic.com/
- **Claude API Reference**: https://docs.anthropic.com/en/api/
- **Anthropic Console**: https://console.anthropic.com/
- **Model Comparison**: https://docs.anthropic.com/en/docs/models-overview
- **Pricing**: https://www.anthropic.com/pricing

---

## Summary

The Anthropic Claude integration provides:

✅ **Drop-in replacement** for Gemini in Habermas Machine
✅ **Robust error handling** with retries and backoff
✅ **Multiple model options** (Opus, Sonnet, Haiku)
✅ **Cost-effective** alternatives (Haiku is very cheap)
✅ **Production-ready** with comprehensive error messages

**Quick start**:
```bash
export ANTHROPIC_API_KEY="your_key"
pip install anthropic
python example_anthropic_claude.py
```

Happy deliberating with Claude! 🎉
