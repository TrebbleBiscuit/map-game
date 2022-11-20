import logging

logger = logging.getLogger(__name__)


def get_plural_suffix(word: str):
    es_endings = ["s", "sh", "ch", "x", "z"]
    if any(word.endswith(x) for x in es_endings):
        return "es"
    return "s"


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
