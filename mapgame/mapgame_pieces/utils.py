import logging

logger = logging.getLogger(__name__)


def get_plural_suffix(word: str):
    es_endings = ["s", "sh", "ch", "x", "z"]
    if any(word.endswith(x) for x in es_endings):
        return "es"
    return "s"


COLOR_SCHEME = {
    "main_command": "deep_sky_blue1",
    "secondary_command": "deep_sky_blue3",
    "hostile_name": "medium_orchid",
    "damage_done": "dark_red",
    "damage_taken": "bright_red",
    "got_item": "bright_cyan",
    "humanity_down": "deep_pink3",
    "level_up": "bold green1",
    "stat_up": "gold1",
    "good_thing_happened": "gold3",
}


def color_string(string, tag):
    """Return a string with color tags"""
    return f"[{tag}]{string}[/{tag}]"


def sanitize_input(in_str: str) -> str:
    """Strip input and make lowercase

    Args:
        in_str (str)

    Returns:
        str
    """
    return in_str.strip().lower()
