"""
Feasibility V4 Configuration

Dedicated configuration for feasibility prompt v4 with enhanced capabilities:
- Higher token limits for comprehensive reports
- Optimized temperature for detailed reasoning
- Increased document context limits
- Preferred provider settings
- Improved prompt structure with examples and verification checklist
"""

import os
from pathlib import Path


# V4 Configuration Dictionary (kept as V3_CONFIG for backward compatibility)
V3_CONFIG = {
    # Prompt settings
    "prompt_file": "prompts/feasibility_promptv4.txt",
    "prompt_version": "v4",
    
    # LLM settings
    "temperature": 0.3,  # Increased from v2's 0.15 for richer output
    "max_output_tokens": 16000,  # 5x increase from v2's 3200
    "top_p": 1.0,
    
    # Document processing settings
    "max_doc_length": 150000,  # Increased from v2's 25000 characters
    "enable_truncation": False,  # Disable truncation to preserve full context
    
    # Provider preferences
    "preferred_provider": "gemini",  # Gemini handles longer outputs better
    "fallback_provider": "openai",
    
    # Timeout and retry settings
    "timeout": 240,  # 4 minutes for longer generation (vs v2's 120s)
    "retry_attempts": 3,
    "retry_delay": 5,  # Initial delay in seconds
    "exponential_backoff": True,
    
    # Output validation
    "min_thinking_summary_length": 2000,  # Minimum characters for thinking summary
    "min_feasibility_report_length": 4000,  # Minimum characters for feasibility report
    
    # Feature flags
    "use_json_input": True,  # Use structured JSON input instead of plain markdown
    "enable_detailed_logging": True,
    "save_intermediate_json": True,  # Save MD→JSON conversion for debugging
}


def get_v3_config() -> dict:
    """
    Get V4 configuration with environment variable overrides.
    (Function kept as get_v3_config for backward compatibility)
    
    Returns:
        Dictionary with V4 configuration settings
    """
    config = V3_CONFIG.copy()
    
    # Allow environment variable overrides
    if os.getenv("FEASIBILITY_TEMPERATURE"):
        config["temperature"] = float(os.getenv("FEASIBILITY_TEMPERATURE"))
    
    if os.getenv("FEASIBILITY_MAX_TOKENS"):
        config["max_output_tokens"] = int(os.getenv("FEASIBILITY_MAX_TOKENS"))
    
    if os.getenv("FEASIBILITY_PROVIDER"):
        config["preferred_provider"] = os.getenv("FEASIBILITY_PROVIDER")
    
    if os.getenv("FEASIBILITY_TIMEOUT"):
        config["timeout"] = int(os.getenv("FEASIBILITY_TIMEOUT"))
    
    return config


def get_prompt_path() -> Path:
    """
    Get the full path to the v4 prompt file.
    
    Returns:
        Path object pointing to feasibility_promptv4.txt
    """
    # Get project root (three levels up from this file)
    project_root = Path(__file__).parent.parent.parent
    prompt_path = project_root / V3_CONFIG["prompt_file"]
    
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Feasibility prompt v4 not found at: {prompt_path}\n"
            f"Please ensure prompts/feasibility_promptv4.txt exists."
        )
    
    return prompt_path


def validate_config(config: dict) -> bool:
    """
    Validate V4 configuration settings.
    
    Args:
        config: Configuration dictionary to validate
    
    Returns:
        True if valid, raises ValueError otherwise
    """
    # Check required keys
    required_keys = [
        "prompt_file", "temperature", "max_output_tokens",
        "preferred_provider", "timeout"
    ]
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    # Validate ranges
    if not 0 <= config["temperature"] <= 1:
        raise ValueError(f"Temperature must be between 0 and 1, got: {config['temperature']}")
    
    if config["max_output_tokens"] < 1000:
        raise ValueError(f"max_output_tokens must be >= 1000, got: {config['max_output_tokens']}")
    
    if config["timeout"] < 30:
        raise ValueError(f"timeout must be >= 30 seconds, got: {config['timeout']}")
    
    # Validate provider
    valid_providers = ["gemini", "google", "openai"]
    if config["preferred_provider"] not in valid_providers:
        raise ValueError(
            f"Invalid provider: {config['preferred_provider']}. "
            f"Must be one of: {valid_providers}"
        )
    
    return True


# Comparison with V2 for reference
V2_CONFIG_COMPARISON = {
    "prompt_file": "prompts/feasibility_promptv2.txt",
    "temperature": 0.15,  # V2 value
    "max_output_tokens": 3200,  # V2 value
    "max_doc_length": 25000,  # V2 value
    "timeout": 120,  # V2 value (implicit)
}


def print_config_comparison():
    """Print comparison between V2 and V4 configurations."""
    print("\n" + "="*80)
    print("FEASIBILITY CONFIGURATION COMPARISON: V2 vs V4")
    print("="*80)
    
    comparisons = [
        ("Temperature", V2_CONFIG_COMPARISON["temperature"], V3_CONFIG["temperature"]),
        ("Max Output Tokens", V2_CONFIG_COMPARISON["max_output_tokens"], V3_CONFIG["max_output_tokens"]),
        ("Max Doc Length", V2_CONFIG_COMPARISON["max_doc_length"], V3_CONFIG["max_doc_length"]),
        ("Timeout (seconds)", V2_CONFIG_COMPARISON["timeout"], V3_CONFIG["timeout"]),
    ]
    
    print(f"\n{'Setting':<25} {'V2':<15} {'V4':<15} {'Change':<20}")
    print("-"*80)
    
    for setting, v2_val, v3_val in comparisons:
        if isinstance(v2_val, (int, float)):
            change = f"+{((v3_val - v2_val) / v2_val * 100):.1f}%"
        else:
            change = "Updated"
        print(f"{setting:<25} {str(v2_val):<15} {str(v3_val):<15} {change:<20}")
    
    print("\n" + "="*80)
    print("KEY IMPROVEMENTS IN V4:")
    print("="*80)
    print("✓ 5x more output tokens → Much longer, detailed reports")
    print("✓ 6x larger document context → Less truncation, better analysis")
    print("✓ Higher temperature → More creative, thorough reasoning")
    print("✓ Structured JSON input → Better LLM comprehension")
    print("✓ Doubled timeout → Handles complex generation reliably")
    print("✓ Output quality examples → Shows LLM what good output looks like")
    print("✓ Pre-submission checklist → Enforces quality verification")
    print("✓ Edge case handling → Robust handling of unusual inputs")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Print configuration comparison
    print_config_comparison()
    
    # Validate V4 config
    config = get_v3_config()
    try:
        validate_config(config)
        print("✓ V4 Configuration is valid\n")
    except ValueError as e:
        print(f"✗ Configuration validation failed: {e}\n")
    
    # Print current V4 config
    print("Current V4 Configuration:")
    print("-" * 40)
    import json
    print(json.dumps(config, indent=2))

