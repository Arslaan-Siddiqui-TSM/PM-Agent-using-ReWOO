# Token Tracking Quick Start Guide

Beautiful, automatic token tracking is now built into every LLM call! 🎨✨

## Zero-Configuration Usage

Token tracking works automatically with **zero configuration needed**:

```python
from src.config.llm_config import model

# Just make your LLM calls as usual
response = model.invoke("Your prompt here")

# Beautiful token usage is automatically displayed! 🎉
```

## What You'll See

Every LLM call now displays:

```
╭─────────────── 🤖 LLM Token Usage ───────────────╮
│ Provider          OPENAI                         │
│ Model             gpt-4o-mini                    │
│ ──────────────    ──────────────                 │
│ Input Tokens      12,143                         │
│ Output Tokens     65,234                         │
│ Total Tokens      77,377                         │
│ ──────────────    ──────────────                 │
│ Duration          8.45s                          │
│ Speed             7,719 tok/s                    │
│ Est. Cost         $0.041023                      │
╰───────────────────────────────────────────────────╯
```

## Auto Session Summary

Get a summary of all calls in your session:

```python
from src.utils import enable_auto_summary

# Add this line at the start of your script
enable_auto_summary()

# Make your LLM calls...
# Session summary displays automatically when script ends!
```

Output:
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

## Manual Summary

Display summary anytime:

```python
from src.utils import print_summary

# Anytime during your script
print_summary()
```

## Silent Mode

Suppress token display for specific calls:

```python
response = model.invoke("Your prompt", show_tokens=False)
```

## Test It Out

Run the test script to see it in action:

```bash
python test_token_tracking.py
```

Or try the integration example:

```bash
python example_token_tracking_integration.py
```

## Key Features

✅ **Automatic** - Works with all existing code  
✅ **Beautiful** - Color-coded Rich formatting  
✅ **Accurate** - Uses provider metadata when available  
✅ **Cost tracking** - Real-time cost estimation  
✅ **Performance** - Shows speed and duration  
✅ **Session stats** - Cumulative tracking across calls  

## Learn More

- Full documentation: `docs/TOKEN_TRACKING.md`
- Utilities: `src/utils/token_utils.py`
- Implementation: `src/config/llm_config.py`

## That's It!

No configuration needed. Just use your existing code and enjoy beautiful token tracking! 🚀

