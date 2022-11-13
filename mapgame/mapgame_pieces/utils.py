import logging

logger = logging.getLogger(__name__)


def print_stdscr(string):
    """Print string to "standard" output"""
    print(string)


def color_string(string, color):
    """NOT IMPLEMENTED - Return a string that's been colored"""
    return string


def get_input() -> str:
    return input("> ")


def print_mapscr(string: str):
    # prepend newline
    logger.log(70, "\n" + string)
