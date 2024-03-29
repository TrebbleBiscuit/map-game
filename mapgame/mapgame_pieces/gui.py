from textual.app import App, ComposeResult
from textual.widgets import Header, Static, Input, TextLog
from rich.text import Text
from mapgame_pieces.utils import color_string


def make_15_chars_long(string: str) -> str:
    n_spaces = 15 - len(string)
    if n_spaces < 0:
        raise ValueError(f"Input string is too long: '{string}'")
    return string + n_spaces * " "


class OutputWindow(TextLog):
    def add_line(self, new_content: str):
        self.write(Text.from_markup(new_content))


class GUIWrapper(App):

    CSS_PATH = "mapgui.css"

    def __init__(self, game):
        super().__init__()
        self.stats_out = Static("Stats", classes="box")
        self.main_out = OutputWindow(
            wrap=True, markup=True, classes="box", id="tallboi"
        )
        self.map_out = Static("Map", classes="box")
        self.default_input_placeholder = "Type a command and press enter"
        self.main_in = Input(
            placeholder=self.default_input_placeholder, classes="box", id="longboi"
        )
        self.game = game

    def compose(self) -> ComposeResult:
        # yield Header()
        # yield Footer()
        yield self.map_out
        yield self.main_out
        yield self.stats_out
        yield self.main_in

    def on_mount(self):
        self.main_out.add_line(
            color_string("Welcome to mapgame!", "bold medium_spring_green")
        )
        map_now = self.game.current_tile.get_map(self.game.player.x, self.game.player.y)
        colored_map = color_string(map_now, self.map_color_from_level())
        self.map_out.update(colored_map)
        self.update_stats()
        self.game.turn_prompt()

    def map_color_from_level(self) -> str:
        # range: 160 to 195
        red = min(250, self.game.player.tile_index * 10)
        blue = 250 - red
        green = 250 - red
        return f"rgb({red},{green},{blue})"

    def update_map(self):
        if self.game.game_state.value != 1:  # in_map
            self.map_out.update(self.game.game_state.name.replace("_", " "))
            return
        map_now = self.game.current_tile.get_map(self.game.player.x, self.game.player.y)
        colored_map = color_string(map_now, self.map_color_from_level())
        self.map_out.update(colored_map)

    def color_stat_up_or_down(self, text: str, diff: int):
        if diff > 0:
            return color_string(text, "panel_stat_up")
        elif diff < 0:
            return color_string(text, "panel_stat_down")
        else:
            return text

    def get_stat_diff(self, stat_name: str):
        old_stat_prefix = "_old_"
        current_stat = getattr(self.game.player, stat_name)
        try:
            old_stat = getattr(self, old_stat_prefix + stat_name)
        except AttributeError:
            old_stat = 0
        setattr(self, old_stat_prefix + stat_name, current_stat)
        return current_stat - old_stat

    def get_stat_line(self, text: str, stat_name: str):
        return self.color_stat_up_or_down(
            make_15_chars_long(text), self.get_stat_diff(stat_name)
        )

    def update_stats(self):
        # hp_diff = self.game.player.hp - self.old_hp
        # self.old_hp = self.game.player.hp
        stats = self.get_stat_line(
            f"HP: {self.game.player.hp}/{self.game.player.max_hp}", "hp"
        )
        stats += self.get_stat_line(
            f"Humanity: {self.game.player.humanity}", "humanity"
        )
        stats += "\n"
        stats += self.get_stat_line(f"XP: {self.game.player.xp}", "xp")
        stats += self.get_stat_line(f"Money: {self.game.player.money}", "money")
        stats += "\n"
        stats += self.get_stat_line(f"Level: {self.game.player.level}", "level")
        stats += self.get_stat_line(
            f"Depth: {self.game.player.tile_index}", "tile_index"
        )
        stats += "\n"
        stats += f"Inv: {self.game.player.inventory.contents}"
        if self.game.debug:
            stats += "\n"
            stats += make_15_chars_long(f"Score: {self.game.player.score}")
            stats += make_15_chars_long(f"Time: {self.game.player.time}")
        self.stats_out.update(stats)

    async def on_input_submitted(self, message: Input.Submitted):
        # logger.debug("Input submitted: %s", message.value)
        self.game.play(message.value)
        self.update_map()
        self.main_in.value = ""
        self.game.turn_prompt()
