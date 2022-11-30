from itertools import cycle
from rich import markup
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input


def make_15_chars_long(string: str) -> str:
    n_spaces = 15 - len(string)
    if n_spaces < 0:
        raise ValueError(f"Input string is too long: '{string}'")
    return string + n_spaces * " "


class OutputWindow(Static):
    def add_line(self, new_content: str):
        old_content = self.render()
        # logger.debug("%s newlines in old content", str(old_content).count("\n"))
        to_trunc = (
            str(old_content).count("\n")
            + new_content.count("\n")
            + 3
            - (self.content_size.height or 10)  # see following note for why 'or 10'
        )
        # 'or 10' because on_mount() height isn't set yet, so it comes across as 0
        # set it to 10 instead so that we don't try and truncate nonexistent newlines
        if to_trunc > 0:
            # truncate content to give the appearance of scrolling
            old_content = str(old_content).split("\n", to_trunc)[to_trunc]
        self.update(old_content + "\n" + new_content)

        # logger.debug(self.content_size.height)


class GUIWrapper(App):

    CSS_PATH = "mapgui.css"

    def __init__(self, game):
        super().__init__()
        self.stats_out = Static("Stats", classes="box")
        self.main_out = OutputWindow("Welcome to mapgame!", classes="box", id="tallboi")
        self.map_out = Static("Map", classes="box")
        self.default_input_placeholder = "Type a command and press enter"
        self.main_in = Input(
            placeholder=self.default_input_placeholder, classes="box", id="longboi"
        )
        self.game = game

    def compose(self) -> ComposeResult:
        yield Header()
        # yield Footer()
        yield self.map_out
        yield self.main_out
        yield self.stats_out
        yield self.main_in

    def on_mount(self):
        map_now = markup.escape(
            self.game.current_tile.get_map(self.game.player.x, self.game.player.y)
        )
        self.map_out.update(map_now)
        self.game.turn_prompt()

    def update_map(self):
        # escape markup so that `[n]` stays that way instead of disappearing
        map_now = markup.escape(
            self.game.current_tile.get_map(self.game.player.x, self.game.player.y)
        )
        self.map_out.update(map_now)

    def update_stats(self):
        stats = make_15_chars_long(
            f"HP: {self.game.player.hp}/{self.game.player.max_hp}"
        )
        stats += make_15_chars_long(f"Humanity: {self.game.player.humanity}")
        stats += "\n"
        stats += make_15_chars_long(f"XP: {self.game.player.xp}")
        stats += make_15_chars_long(f"Money: {self.game.player.money}")
        stats += "\n"
        stats += make_15_chars_long(f"Level: {self.game.player.level}")
        stats += make_15_chars_long(f"Depth: {self.game.player.tile_index}")
        stats += "\n"
        stats += f"Inv: {self.game.player.inventory.contents}"
        self.stats_out.update(stats)

    async def on_input_submitted(self, message: Input.Submitted):
        # logger.debug("Input submitted: %s", message.value)
        self.game.play(message.value)
        self.update_map()
        self.main_in.value = ""
        self.game.turn_prompt()
