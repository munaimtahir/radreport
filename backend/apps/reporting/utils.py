"""
Utility functions for the reporting app.
"""


def parse_bool(value, default=None):
    """
    Parse a boolean value from various string representations.
    
    Args:
        value: The value to parse (can be string, bool, int, or None)
        default: The default value to return if parsing fails or value is None/empty
        
    Returns:
        bool or default: True for truthy values, False for falsy values, 
                        or default if value is None/empty/unrecognized
    """
    if value is None:
        return default
    raw = str(value).strip().lower()
    if raw == "":
        return default
    if raw in {"true", "1", "yes", "y"}:
        return True
    if raw in {"false", "0", "no", "n"}:
        return False
    return default
