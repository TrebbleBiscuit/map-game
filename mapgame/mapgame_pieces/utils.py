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
    "friendly_name": "bold white",
    "damage_done": "deep_pink4",
    "damage_taken": "bright_red",
    "got_item": "bright_cyan",
    "humanity_down": "deep_pink3",
    "level_up": "bold green1",
    "stat_up": "underline gold1",
    "good_thing_happened": "light_goldenrod1",
    "dim": "bright_black",
    "recover_hp": "green",
    "dialogue": "light_sky_blue1",
    "panel_stat_up": "medium_spring_green",
    "panel_stat_down": "hot_pink3",
    "score": "bold green1",
}


def color_string(string: str, color: str):
    """Return a string with color tags"""
    try:
        tag = COLOR_SCHEME[color]
    except KeyError:
        logger.info("Using color tag: %s", color)
        tag = color
    return f"[{tag}]{string}[/{tag}]"


def sanitize_input(in_str: str) -> str:
    """Strip input and make lowercase

    Args:
        in_str (str)

    Returns:
        str
    """
    return in_str.strip().lower()
