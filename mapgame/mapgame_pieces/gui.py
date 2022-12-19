from rich import markup
from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Input, TextLog


def make_15_chars_long(string: str) -> str:
    n_spaces = 15 - len(string)
    if n_spaces < 0:
        raise ValueError(f"Input string is too long: '{string}'")
    return string + n_spaces * " "


class OutputWindow(TextLog):
    def add_line(self, new_content: str):
        self.write(new_content)


class GUIWrapper(App):

    CSS_PATH = "mapgui.css"

    def __init__(self, game):
        super().__init__()
        self.stats_out = Static("Stats", classes="box")
        self.main_out = OutputWindow(wrap=True, classes="box", id="tallboi")
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

        if self.game.game_state.value != 1:  # in_map
            self.map_out.update(self.game.game_state.name.replace("_", " "))
            return
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
        if self.game.debug:
            stats += "\n"
            stats += make_15_chars_long(f"Score: {self.game.player.score}")
        self.stats_out.update(stats)

    async def on_input_submitted(self, message: Input.Submitted):
        # logger.debug("Input submitted: %s", message.value)
        self.game.play(message.value)
        self.update_map()
        self.main_in.value = ""
        self.game.turn_prompt()
