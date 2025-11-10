"""
Token tracking utilities for LLM calls.

This module provides convenient functions for tracking and displaying
token usage across LLM calls in your scripts.
"""

from src.config.llm_config import session_tracker
import atexit


def enable_auto_summary():
    """
    Automatically display session summary when the script exits.
    
    Usage:
        from src.utils.token_utils import enable_auto_summary
        
        # Call this at the start of your script
        enable_auto_summary()
        
        # Make your LLM calls...
        # Session summary will be displayed automatically when script ends
    """
    atexit.register(session_tracker.print_summary)


def print_summary():
    """
    Manually display the current session summary.
    
    Usage:
        from src.utils.token_utils import print_summary
        
        # At any point in your script
        print_summary()
    """
    session_tracker.print_summary()


def reset_tracker():
    """
    Reset the session tracker to start fresh.
    
    Usage:
        from src.utils.token_utils import reset_tracker
        
        # After completing a workflow
        reset_tracker()
    """
    session_tracker.reset()


def get_session_stats():
    """
    Get current session statistics as a dictionary.
    
    Returns:
        dict: Session statistics including:
            - total_calls: Number of LLM calls made
            - total_input_tokens: Total input tokens used
            - total_output_tokens: Total output tokens generated
            - total_tokens: Combined token usage
            - session_duration: Time elapsed since first call
    
    Usage:
        from src.utils.token_utils import get_session_stats
        
        stats = get_session_stats()
        print(f"Used {stats['total_tokens']:,} tokens")
    """
    import time
    
    return {
        'total_calls': len(session_tracker.calls),
        'total_input_tokens': session_tracker.total_input,
        'total_output_tokens': session_tracker.total_output,
        'total_tokens': session_tracker.total_input + session_tracker.total_output,
        'session_duration': time.time() - session_tracker.session_start
    }


# Convenience alias
show_summary = print_summary

