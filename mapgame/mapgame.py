import logging
import random
import time
from rich.logging import RichHandler
from rich import markup
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Input
from mapgame_pieces.player import Player
from mapgame_pieces.alive import NPC
from mapgame_pieces.map import Map
from mapgame_pieces.utils import color_string, print_stdscr, get_input, print_mapscr
from textual.reactive import reactive
from itertools import cycle

logging.addLevelName(70, "MAP")
logger = logging.getLogger(__name__)

INVALID_INPUT_MSG = color_string("Input not understood", "Style.DIM")


hellos = cycle(
    [
        "Hola",
        "Bonjour",
        "Guten tag",
        "Salve",
        "Nǐn hǎo",
        "Olá",
        "Asalaam alaikum",
        "Konnichiwa",
        "Anyoung haseyo",
        "Zdravstvuyte",
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

    def __init__(self):
        super().__init__()
        self.my_hello = Hello("Misc Info", classes="box")
        self.main_out = OutputWindow("Welcome to mapgame!", classes="box", id="tallboi")
        self.map_out = Static("Map", classes="box")
        self.main_in = Input(
            placeholder="Type a command and press enter", classes="box", id="longboi"
        )
        self.game = Game(gui=self)

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

    async def on_input_submitted(self, message: Input.Submitted):
        # logger.debug("Input submitted: %s", message.value)
        self.game.map_turn(sanitize_input(message.value))
        # escape markup so that `[n]` stays that way instead of disappearing
        map_now = markup.escape(
            self.game.current_tile.get_map(self.game.player.x, self.game.player.y)
        )
        self.map_out.update(map_now)
        self.main_in.value = ""
        self.game.turn_prompt()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


def sanitize_input(in_str: str):
    return in_str.strip().lower()


class Game:
    def __init__(self, gui: GUIWrapper):
        self.gui = gui
        self.player = Player()
        self.map = Map(gui, 8, 4)
        self.current_tile = self.map.tiles[0]  # self.map.tiles[self.player.tile_index]
        self.time = 0
        # self.x = 0
        # self.y = 0
        self.debug = True

    def _progress_time(self):
        self.player._heal_over_time()
        self.time += 1
        self.current_tile.npc._on_time_pass(self.current_tile)
        # if random.randint(0, 9) == 0:
        #     self.gui.main_out.add_line("Random enemy encounter!!!!")
        #     enemy = NPC.generate_from_level(self.player.tile_index)
        #     self.gui.main_out.add_line(vars(enemy))
        #     self.combat(enemy)
        #     # uinput = ''
        #     # while uinput.lower() != 'ok':
        #     #     the input abve won't work with curses, fix that when you uncomment
        #     #     uinput = input(self.wm.stdscr, "you gotta type ok to continue!")

    def combat(self, hostile: NPC):
        in_combat = True
        enemy_text = color_string(f"{hostile.name}", "Fore.RED")
        self.gui.main_out.add_line(f"\nEntered combat with a hostile {enemy_text}!")
        # clear screen
        # clear map screen ?
        while in_combat:
            took_turn = False
            self.gui.main_out.add_line(
                f"{enemy_text.title()}: {hostile.hp}/{hostile.max_hp} HP",
            )
            self.gui.main_out.add_line(f"You: {self.player.hp}/{self.player.max_hp} HP")
            self.gui.main_out.add_line(
                f"You can {color_string('melee', 'Fore.RED')} attack, or attempt to {color_string('run', 'Fore.CYAN')}.",
            )
            try:
                raise NotImplementedError
                # can't get input this way
                ui = get_input()
            except KeyboardInterrupt:
                logger.warning("caught KeyboardInterrupt to break out of combat")
                in_combat = False
                continue
            if ui in ["melee", "m"]:
                self.gui.main_out.add_line("")
                base_dmg = self.player.attack_power
                min_dmg = int((base_dmg * 0.5) + 0.5)
                max_dmg = int(base_dmg * 1.5)
                act_dmg = random.randint(min_dmg, max_dmg)
                self.gui.main_out.add_line(f"You take a swing at the {enemy_text}!")
                dmg_txt = color_string(f"{act_dmg} damage", "Fore.RED")
                self.gui.main_out.add_line(f"You do ({min_dmg}-{max_dmg}) {dmg_txt}!")
                hostile.take_damage(act_dmg)
                took_turn = True
            elif ui in ["run", "r"]:
                self.gui.main_out.add_line("")
                self.gui.main_out.add_line("You run away!")
                in_combat = False
                took_turn = True
            else:
                self.gui.main_out.add_line(INVALID_INPUT_MSG)
            if took_turn and in_combat:
                if hostile.hp <= 0:
                    logger.info("Ending combat because enemy is dead")
                    self.player.grant_xp(hostile.xp_reward)
                    in_combat = False
                elif hostile.player_attitude > 0:
                    logger.info("Ending combat because attitude is high")
                    in_combat = False
                else:  # enemy's turn
                    base_dmg = hostile.attack_power
                    min_dmg = int((base_dmg * 0.5) + 0.5)
                    max_dmg = int(base_dmg * 1.5)
                    act_dmg = random.randint(min_dmg, max_dmg)
                    self.gui.main_out.add_line(f"The {enemy_text} attacks you!")
                    dmg_txt = color_string(f"{act_dmg} damage", "Fore.RED")
                    self.gui.main_out.add_line(
                        f"It connects for ({min_dmg}-{max_dmg}) {dmg_txt}!",
                    )
                    self.player.take_damage(act_dmg)
                    self.gui.main_out.add_line("")

    def open_chest(self):
        self.current_tile.chests.remove((self.player.x, self.player.y))
        self.gui.main_out.add_line("You open a chest! There's nothing inside.")
        time.sleep(0.5)

    def portal_into_another_dimension(self, dim_num=None):
        if dim_num is None:
            dim_num = self.player.tile_index + 1
        else:
            pass
        self.player.tile_index = dim_num
        self.gui.main_out.add_line(f"You portal into dimension #{dim_num}")
        try:
            self.current_tile = self.map.tiles[dim_num]
            self.gui.main_out.add_line("This dimension already existed")
        except IndexError:
            self.gui.main_out.add_line(
                color_string("This dimension needed to be generated", "Style.BRIGHT")
            )
            self.player.grant_xp(dim_num * 2)
            self.current_tile = self.map.get_tile(dim_num)

        finally:
            self.player.x, self.player.y = (0, 0)

    def maybe_enter_combat(self):
        # Should we encounter an NPC?
        ct_npc = self.current_tile.npc  # there's only 1 rn
        if ct_npc.is_dead:
            pass
        elif (ct_npc.x, ct_npc.y) == (self.player.x, self.player.y):
            if ct_npc.will_attack_player():
                self.combat(ct_npc)
            else:
                self.gui.main_out.add_line(
                    f"There is a friendly {ct_npc.name} in this room!"
                )
                self.gui.main_out.add_line(
                    "Non-hostile NPC encounters not yet implemented."
                )

    def turn_prompt(self):
        """Prompt the user to enter a command"""
        # self.stdscr.clrtobot()
        # self.maybe_enter_combat()
        self.gui.main_out.add_line("What direction do you want to move? [n/e/s/w] ")

    def get_room_name(self) -> str:
        """Return the name of the room the player is currently in"""
        if (self.player.x, self.player.y) in self.current_tile.rooms:
            return self.current_tile.rooms[(self.player.x, self.player.y)]["name"]

    def map_turn(self, command: str) -> bool | None:
        """Process a user's input command"""
        # don't want any more lines so the map stays the same, use room_flavor_text instead
        # if room_name == 'portal': Utils.printline(self.stdscr, "You can leave through the portal in this room.")
        logger.info("processing command %s", command)
        self.gui.main_out.add_line("")
        if not command:
            return
        elif command in ["n", "e", "s", "w"]:
            player_move = self.player.move(self.current_tile, command)
            if player_move:  # move successful
                self.gui.main_out.add_line(f"You move {player_move}.")
                self.current_tile.explored.add((self.player.x, self.player.y))
                self.current_tile.room_flavor_text((self.player.x, self.player.y))
                if (self.player.x, self.player.y) in self.current_tile.chests:
                    self.gui.main_out.add_line(
                        "There's a chest in this room! You wonder what's inside!"
                    )
                self._progress_time()
                # TODO: print flavor text for room
            else:
                self.gui.main_out.add_line("You can't move that way.")
        elif self.get_room_name() == "portal" and command in [
            "portal",
            "leave",
            "take portal",
            "p",
        ]:
            # clear screen
            self.gui.main_out.add_line("You take the portal into the next dimension...")
            self.portal_into_another_dimension()
            return True  # don't loop
        elif (self.player.x, self.player.y) in self.current_tile.chests and command in [
            "open",
            "chest",
            "o",
        ]:
            self.open_chest()
        # beyond here lies debug commands
        # elif self.debug and command[:2] == "ff":
        #     self.combat(ct_npc)
        elif self.debug and command[:2] == "xp":
            self.player.grant_xp(int(command[2:].strip()))
        elif self.debug and (command[:2] == "tp" or command[:4] == "tele"):
            self.gui.main_out.add_line('teleport to what coordinates? (i.e. "1, 3")')
            self.gui.main_out.add_line("remember y is inverted")
            tc = command.split(" ")[1]
            try:
                tc = tuple(int(cv.strip()) for cv in tc.split(","))
            except:
                self.gui.main_out.add_line("invalid coordinates!")
                return
            if self.current_tile._check_valid_coords(tc):
                self.player.x, self.player.y = tc
                self.current_tile.explored.add((self.player.x, self.player.y))
                self.gui.main_out.add_line("poof~")
            else:
                self.gui.main_out.add_line("off-map coordinates not allowed")
        else:
            self.gui.main_out.add_line(INVALID_INPUT_MSG)

    def play(self):
        print("\n" * 30)  # clear screen
        while True:
            self.gui.main_out.add_line(
                "You are in the hub world. Go to 'map' or 'portal' pls."
            )
            # input_field.getch()
            command = get_input()
            if command == "map":
                self.turn_prompt()
                while not self.map_turn(command):  # loop until it returns True
                    # TODO: perhaps pass time here?
                    self.turn_prompt()
                    command = get_input()
                    # rn it'll return if nothing happens which should change
            elif command == "portal":
                self.portal_into_another_dimension()


if __name__ == "__main__":
    from rich.console import Console
    from rich.theme import Theme

    console = Console(theme=Theme({"logging.level.custom": "green"}))
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        # filename="mapgame.log",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=False, console=console)],
    )

    # g = Game()
    wrapper = GUIWrapper()
    wrapper.run()

    logger.info("\n________________\nInitialized mapgame logger")
