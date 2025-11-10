# Token Tracking Documentation

## Overview

The PM-Agent system now includes **beautiful, automatic token tracking** for all LLM calls. Every time you invoke an LLM, you'll see detailed metrics including token usage, cost estimation, and performance statistics.

## Features

### 🎨 Beautiful Display
- Color-coded metrics using Rich library
- Provider and model information
- Input/Output/Total token counts
- Request duration and generation speed (tokens/second)
- Cost estimation (when pricing is available)

### 📊 Session Tracking
- Cumulative token usage across multiple calls
- Total cost tracking
- Session duration
- Call count statistics

### 💰 Cost Estimation
Built-in pricing for popular models:
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo, GPT-3.5-turbo
- **Google Gemini**: Gemini 2.5 Pro, Gemini 1.5 Pro, Gemini 1.5 Flash
- **NVIDIA**: (pricing can be updated as needed)

## Usage

### Basic Usage

Token tracking is **enabled by default** for all LLM calls:

```python
from src.config.llm_config import model

# Make any LLM call - token usage is automatically displayed
response = model.invoke("What is the capital of France?")
print(response.content)
```

### Output Example

```
╭─────────────── 🤖 LLM Token Usage ───────────────╮
│ Provider          OPENAI                         │
│ Model             gpt-4o-mini                    │
│ ──────────────    ──────────────                 │
│ Input Tokens      12                             │
│ Output Tokens     45                             │
│ Total Tokens      57                             │
│ ──────────────    ──────────────                 │
│ Duration          1.23s                          │
│ Speed             37 tok/s                       │
│ Est. Cost         $0.000029                      │
╰───────────────────────────────────────────────────╯
```

### Disable Token Display

To suppress token display for specific calls:

```python
response = model.invoke("Query text", show_tokens=False)
```

### Session Summary

View cumulative token usage for your session:

```python
from src.config.llm_config import session_tracker

# At the end of your script
session_tracker.print_summary()
```

**Output:**
```
╭─────────── 📊 Session Token Summary ────────────╮
│ Metric                     Value                │
│ Total Calls                5                    │
│ Total Input Tokens         1,234                │
│ Total Output Tokens        5,678                │
│ Total Tokens               6,912                │
│ Total Cost                 $0.004156            │
│ Session Duration           45.3s                │
╰──────────────────────────────────────────────────╯
```

### Reset Session Tracker

```python
session_tracker.reset()
```

## Token Extraction

The system automatically extracts **actual token counts** from LLM provider responses:

1. **LangChain 0.2+ format** (`usage_metadata`)
2. **OpenAI format** (`response_metadata.token_usage`)
3. **Google Gemini format** (`response_metadata.usage_metadata`)
4. **NVIDIA format** (`response_metadata.usage`)
5. **Fallback estimation** (if metadata unavailable)

When metadata is available, you'll see accurate token counts. If estimation is used, the display shows "(estimated)".

## Cost Estimation

### Update Pricing

To update or add pricing for models, edit `src/config/llm_config.py`:

```python
def _estimate_cost(self, token_usage: dict, model: str) -> Optional[float]:
    pricing = {
        'openai': {
            'gpt-4o': {'input': 2.50, 'output': 10.00},  # $ per 1M tokens
            'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
            # Add more models...
        },
        'gemini': {
            'gemini-2.5-pro': {'input': 1.25, 'output': 5.00},
            # Add more models...
        },
        'nvidia': {
            'qwen': {'input': 0.00, 'output': 0.00},  # Update with actual
            # Add more models...
        }
    }
```

### Current Pricing (as of implementation)

| Provider | Model | Input ($/1M tokens) | Output ($/1M tokens) |
|----------|-------|---------------------|----------------------|
| OpenAI | gpt-4o | $2.50 | $10.00 |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| OpenAI | gpt-4-turbo | $10.00 | $30.00 |
| OpenAI | gpt-3.5-turbo | $0.50 | $1.50 |
| Gemini | gemini-2.5-pro | $1.25 | $5.00 |
| Gemini | gemini-1.5-pro | $3.50 | $10.50 |
| Gemini | gemini-1.5-flash | $0.075 | $0.30 |

## Integration with Existing Code

Token tracking is **automatically integrated** with existing code using the `model` instance:

### Feasibility Agent
```python
# src/app/feasibility_agent.py
from src.config.llm_config import model

# Token tracking happens automatically
result = model.invoke(full_prompt)
```

### Project Planner
```python
# Any script using the model
from src.config.llm_config import model, session_tracker

# Make multiple calls
for prompt in prompts:
    response = model.invoke(prompt)
    # Process response...

# Show session summary at the end
session_tracker.print_summary()
```

## Advanced Usage

### Access Token Data Programmatically

If you need to access token counts programmatically:

```python
from src.config.llm_config import model

# Make a call
result = model.chat_model.invoke(messages)

# Extract token usage
if hasattr(result, 'usage_metadata'):
    usage = result.usage_metadata
    print(f"Input tokens: {usage.input_tokens}")
    print(f"Output tokens: {usage.output_tokens}")
    print(f"Total tokens: {usage.total_tokens}")
```

### Custom Session Tracking

Create your own tracker for specific workflows:

```python
from src.config.llm_config import TokenSessionTracker

# Create custom tracker
workflow_tracker = TokenSessionTracker()

# Your calls here...

# Display custom summary
workflow_tracker.print_summary()
```

## Testing

Run the test script to see token tracking in action:

```bash
python test_token_tracking.py
```

This will demonstrate:
- Multiple LLM calls with varying sizes
- Token usage display for each call
- Session summary at the end
- Silent calls (without token display)

## Benefits

1. **🔍 Transparency**: See exactly how many tokens each call uses
2. **💰 Cost Control**: Real-time cost estimation helps manage budgets
3. **⚡ Performance**: Track response times and generation speeds
4. **📈 Analytics**: Session summaries for workflow optimization
5. **🎨 Beautiful**: Color-coded, easy-to-read display

## Notes

- Token tracking adds negligible overhead (~0.001s per call)
- Token display is printed to console via Rich library
- Session tracker persists until process ends or manual reset
- Estimated costs are approximate; check provider documentation for exact pricing
- All existing code continues to work without modification

## Troubleshooting

### No token usage displayed
- Check if `show_tokens=True` (default)
- Verify Rich library is installed: `pip install rich`
- Check console output isn't being redirected

### Inaccurate token counts
- If showing "(estimated)", the provider didn't return metadata
- Update LangChain to latest version for better metadata support
- Check provider documentation for token counting details

### Missing cost estimates
- Add pricing for your model in `_estimate_cost()` method
- Ensure model name matches pricing dictionary keys
- Set pricing to 0.00 if not available or free tier

## Future Enhancements

Potential improvements:
- Export session data to JSON/CSV
- Token usage graphs and visualizations
- Budget alerts and warnings
- Per-provider detailed statistics
- Integration with monitoring services

