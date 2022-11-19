from itertools import cycle
from rich import markup
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input


hellos = cycle(
    [
        "Howdy",
        "Sup",
        "Yo",
        "Greetings",
        "Hello",
    ]
)


class Hello(Static):
    """Display a greeting."""

    DEFAULT_CSS = """
    Hello {
        padding: 1 2;
        background: $panel;
        border: $secondary tall;
        content-align: center middle;
    }
    """

    def on_mount(self) -> None:
        self.next_word()

    # def on_click(self) -> None:
    #     self.next_word()

    def next_word(self) -> None:
        """Get a new hello and update the content area."""
        hello = next(hellos)
        self.update(f"{hello}, [b]World[/b]!")


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

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "horizontal_layout.css"

    def __init__(self, game):
        super().__init__()
        self.my_hello = Hello("Misc Info", classes="box")
        self.main_out = OutputWindow("Welcome to mapgame!", classes="box", id="tallboi")
        self.map_out = Static("Map", classes="box")
        self.main_in = Input(
            placeholder="Type a command and press enter", classes="box", id="longboi"
        )
        self.game = game

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        # yield Welcome()
        yield self.map_out
        yield self.main_out
        # yield Hello("Misc Info", classes="box")
        yield self.my_hello
        # yield Static("Input", classes="box", id="longboi")
        yield self.main_in
        # yield Static("4", classes="box")

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

    async def on_input_submitted(self, message: Input.Submitted):
        # logger.debug("Input submitted: %s", message.value)
        self.game.play(message.value)
        self.update_map()
        self.main_in.value = ""
        self.game.turn_prompt()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark
