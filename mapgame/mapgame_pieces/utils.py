import logging

logger = logging.getLogger(__name__)


def color_string(string, color):
    """NOT IMPLEMENTED - Return a string that's been colored"""
    return string


def sanitize_input(in_str: str) -> str:
    """Strip input and make lowercase

    Args:
        in_str (str)

    Returns:
        str
    """
    return in_str.strip().lower()
