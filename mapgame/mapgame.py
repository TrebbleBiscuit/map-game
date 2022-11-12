import logging
import random
import time
from rich.logging import RichHandler
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


# TODO: REMOVE ME
class WindowManager:
    # DUMMY CLASS
    ...


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
    def add_line(self, new_content):
        old_content = self.render()
        # logger.debug("%s newlines in old content", str(old_content).count("\n"))
        if str(old_content).count("\n") + 1 >= self.content_size.height:
            # truncate content to give the appearance of scrolling
            old_content = str(old_content).split("\n", 1)[1]
        self.update(old_content + "\n" + new_content)

        # logger.debug(self.content_size.height)


class GUIWrapper(App):

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "horizontal_layout.css"

    def __init__(self):
        self.my_hello = Hello("Misc Info", classes="box")
        self.main_out = OutputWindow("Main Output", classes="box", id="tallboi")
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        # yield Welcome()
        yield Static("Map", classes="box")
        yield self.main_out
        # yield Hello("Misc Info", classes="box")
        yield self.my_hello
        # yield Static("Input", classes="box", id="longboi")
        yield Input(
            placeholder="Type a command and press enter", classes="box", id="longboi"
        )
        # yield Static("4", classes="box")

    async def on_input_submitted(self, message: Input.Submitted):
        # logger.debug("Input submitted: %s", message.value)
        self.main_out.add_line(message.value)

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


class Game:
    def __init__(self, stdscr):
        self.gui = GUIWrapper()
        self.wm = WindowManager(stdscr)
        self.player = Player(self.wm)
        self.map = Map(self.wm, 8, 4)
        self.current_tile = self.map.tiles[0]  # self.map.tiles[self.player.tile_index]
        self.time = 0
        # self.x = 0
        # self.y = 0
        self.debug = True
        self.play()

    def _progress_time(self):
        self.player._heal_over_time()
        self.time += 1
        self.current_tile.npc._on_time_pass(self.current_tile)
        # if random.randint(0, 9) == 0:
        #     print_stdscr("Random enemy encounter!!!!")
        #     enemy = NPC.generate_from_level(self.player.tile_index)
        #     print_stdscr(vars(enemy))
        #     self.combat(enemy)
        #     # uinput = ''
        #     # while uinput.lower() != 'ok':
        #     #     the input abve won't work with curses, fix that when you uncomment
        #     #     uinput = input(self.wm.stdscr, "you gotta type ok to continue!")

    def combat(self, hostile: NPC):
        in_combat = True
        enemy_text = color_string(f"{hostile.name}", "Fore.RED")
        print_stdscr(f"\nEntered combat with a hostile {enemy_text}!")
        self.wm.mapscr.clear()
        print_mapscr("COMBAT TIME >:I")
        self.wm.mapscr.refresh()
        while in_combat:
            took_turn = False
            print_stdscr(
                f"{enemy_text.title()}: {hostile.hp}/{hostile.max_hp} HP",
            )
            print_stdscr(f"You: {self.player.hp}/{self.player.max_hp} HP")
            print_stdscr(
                f"You can {color_string('melee', 'Fore.RED')} attack, or attempt to {color_string('run', 'Fore.CYAN')}.",
            )
            try:
                ui = get_input()
            except KeyboardInterrupt:
                logger.warning("caught KeyboardInterrupt to break out of combat")
                in_combat = False
                continue
            if ui in ["melee", "m"]:
                print_stdscr("")
                base_dmg = self.player.attack_power
                min_dmg = int((base_dmg * 0.5) + 0.5)
                max_dmg = int(base_dmg * 1.5)
                act_dmg = random.randint(min_dmg, max_dmg)
                print_stdscr(f"You take a swing at the {enemy_text}!")
                dmg_txt = color_string(f"{act_dmg} damage", "Fore.RED")
                print_stdscr(f"You do ({min_dmg}-{max_dmg}) {dmg_txt}!")
                hostile.take_damage(act_dmg)
                took_turn = True
            elif ui in ["run", "r"]:
                print_stdscr("")
                print_stdscr("You run away!")
                in_combat = False
                took_turn = True
            else:
                print_stdscr(INVALID_INPUT_MSG)
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
                    print_stdscr(f"The {enemy_text} attacks you!")
                    dmg_txt = color_string(f"{act_dmg} damage", "Fore.RED")
                    print_stdscr(
                        f"It connects for ({min_dmg}-{max_dmg}) {dmg_txt}!",
                    )
                    self.player.take_damage(act_dmg)
                    print_stdscr("")

    def open_chest(self):
        self.current_tile.chests.remove((self.player.x, self.player.y))
        print_stdscr("You open a chest! There's nothing inside.")
        time.sleep(0.5)

    def portal_into_another_dimension(self, dim_num=None):
        if dim_num is None:
            dim_num = self.player.tile_index + 1
        else:
            pass
        self.player.tile_index = dim_num
        print_stdscr(f"You portal into dimension #{dim_num}")
        try:
            self.current_tile = self.map.tiles[dim_num]
            logger.debug("This dimension already existed")
        except IndexError:
            print_stdscr(
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
                print_stdscr(f"There is a friendly {ct_npc.name} in this room!")
                print_stdscr("Non-hostile NPC encounters not yet implemented.")

    def turn_prompt(self):
        """Prompt the user to enter a command"""
        # self.stdscr.clrtobot()
        # self.maybe_enter_combat()
        self.current_tile.print_map(self.player.x, self.player.y)
        print_stdscr("What direction do you want to move? [n/e/s/w] ")

    def get_room_name(self) -> str:
        """Return the name of the room the player is currently in"""
        if (self.player.x, self.player.y) in self.current_tile.rooms:
            return self.current_tile.rooms[(self.player.x, self.player.y)]["name"]

    def map_turn(self, command: str) -> bool | None:
        """Process a user's input command"""
        # don't want any more lines so the map stays the same, use room_flavor_text instead
        # if room_name == 'portal': Utils.printline(self.stdscr, "You can leave through the portal in this room.")
        print_stdscr("")
        if command in ["n", "e", "s", "w"]:
            if self.player.move(self.current_tile, command):  # move successful
                print_stdscr("You move in that direction.\n")
                self.current_tile.explored.add((self.player.x, self.player.y))
                self.current_tile.room_flavor_text((self.player.x, self.player.y))
                if (self.player.x, self.player.y) in self.current_tile.chests:
                    print_stdscr(
                        "There's a chest in this room! You wonder what's inside!"
                    )
                self._progress_time()
                # TODO: print flavor text for room
        elif self.get_room_name() == "portal" and command in [
            "portal",
            "leave",
            "take portal",
            "p",
        ]:
            self.wm.mapscr.clear()
            print_stdscr("You take the portal into the next dimension...")
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
            print_stdscr('teleport to what coordinates? (i.e. "1, 3")')
            print_stdscr("remember y is inverted")
            tc = get_input()
            try:
                tc = tuple(int(cv.strip()) for cv in tc.split(","))
            except:
                print_stdscr("invalid coordinates!")
                return
            if self.current_tile._check_valid_coords(tc):
                self.player.x, self.player.y = tc
                self.current_tile.explored.add((self.player.x, self.player.y))
                print_stdscr("poof~")
            else:
                print_stdscr("off-map coordinates not allowed")
        else:
            print_stdscr(INVALID_INPUT_MSG)

    def play(self):
        print("\n" * 30)  # clear screen
        while True:
            print_stdscr("You are in the hub world. Go to 'map' or 'portal' pls.")
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
    gui = GUIWrapper()
    gui.run()

    logger.info("\n________________\nInitialized mapgame logger")
