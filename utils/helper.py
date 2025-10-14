from states.rewoo_state import ReWOO


def load_prompt_template(path: str) -> str:
    """
    Load a prompt template from a file.

    Args:
        path (str): The path to the prompt template file.
    Returns:
        str: The content of the prompt template file.
    """
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def get_current_task(state: ReWOO):
    """Get the current task number for the given state.

    Args:
        state (ReWOO): The current state of the ReWOO agent.

    Returns:
        int | None: The current task number, or None if all tasks are completed.
    """
    if not hasattr(state, "results") or state.results is None:
        return 1
    if state.steps is not None and len(state.results) == len(state.steps):
        return None
    else:
        return len(state.results) + 1


def route(state):
    """Determine the next node to route to based on the current task state.

    Args:
        state (ReWOO): The current state of the ReWOO agent.

    Returns:
        str: The name of the next node to route to ("solve" or "tool").
    """
    _step = get_current_task(state)
    if _step is None:
        # We have executed all tasks
        return "solve"
    else:
        # We are still executing tasks, loop back to the "tool" node
        return "tool"
    
def truncate_query(query: str, max_length: int = 400) -> str:
    """Truncate a search query to fit within the maximum length while preserving meaning."""
    if len(query) <= max_length:
        return query

    # If query is too long, try to find a good breaking point
    # Look for sentence endings or common separators
    separators = ['. ', '! ', '? ', '; ', ', ', ' - ']

    for separator in separators:
        parts = query.split(separator)
        if len(parts) > 1:
            # Try to fit as much as possible
            result = ""
            for part in parts[:-1]:  # All parts except the last
                if len(result + part + separator.strip()) <= max_length - 50:  # Leave room for closing
                    result += part + separator.strip() + ' '
                else:
                    break

            # Add a shortened version of the last part if there's room
            remaining = max_length - len(result) - 10
            if remaining > 50:  # Only add if we have reasonable space
                last_part = parts[-1][:remaining] + "..."
                result += last_part
            else:
                result = result.rstrip() + "..."

            return result[:max_length]

    # If no good separators found, just truncate with ellipsis
    return query[:max_length-3] + "..."