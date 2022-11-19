import logging
import random
import time
from rich.logging import RichHandler
from mapgame_pieces.player import Player
from mapgame_pieces.alive import NPC
from mapgame_pieces.map import Map
from mapgame_pieces.utils import color_string, sanitize_input
from enum import Enum
from mapgame_pieces.gui import GUIWrapper

logger = logging.getLogger(__name__)

INVALID_INPUT_MSG = color_string("Input not understood", "Style.DIM")


class GameState(Enum):
    in_map = 1
    in_combat = 2


class Game:
    def __init__(self):
        self.gui = GUIWrapper(game=self)
        self.player = Player(self.gui)
        self.map = Map(self.gui, 8, 4)
        self.current_tile = self.map.tiles[0]  # self.map.tiles[self.player.tile_index]
        self.time: int = 0
        # self.x = 0
        # self.y = 0
        self.debug = True
        self.game_state = GameState.in_map
        self.in_combat_vs: list[NPC] = []
        self.gui.run()

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

    def enter_combat(self, hostile: NPC):
        if self.in_combat_vs:
            raise RuntimeError(
                f"Attempted to enter combat, but player is already fighting: {self.in_combat_vs}"
            )
        # only support 1v1 combat rn but eventually want multiple hostiles
        self.in_combat_vs = [hostile]
        self.game_state = GameState.in_combat
        enemy_text = color_string(f"{hostile.name}", "Fore.RED")
        self.gui.main_out.add_line(f"\nEntered combat with a hostile {enemy_text}!")

    def end_combat(self):
        self.in_combat_vs = []
        self.game_state = GameState.in_map

    def combat(self, ui: str):
        assert len(self.in_combat_vs) == 1
        hostile = self.in_combat_vs[0]
        enemy_text = color_string(f"{hostile.name}", "Fore.RED")
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
        elif ui in ["run", "r"]:
            self.gui.main_out.add_line("")
            self.gui.main_out.add_line("You run away!")
            self.end_combat()
            return
        else:
            self.gui.main_out.add_line()
            self.gui.main_out.add_line(INVALID_INPUT_MSG)
            return

        if hostile.hp <= 0:
            logger.info("Ending combat because enemy is dead")
            self.player.grant_xp(hostile.xp_reward)
            self.end_combat()
            return
        elif hostile.player_attitude > 0:
            logger.info("Ending combat because attitude is high")
            self.end_combat()
            return
        else:
            self.hostile_combat_turn(hostile)

    def hostile_combat_turn(self, hostile: NPC):
        base_dmg = hostile.attack_power
        min_dmg = int((base_dmg * 0.5) + 0.5)
        max_dmg = int(base_dmg * 1.5)
        act_dmg = random.randint(min_dmg, max_dmg)
        enemy_text = color_string(f"{hostile.name}", "Fore.RED")
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
                self.enter_combat(ct_npc)
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
        if self.game_state == GameState.in_map:
            self.gui.main_out.add_line("What direction do you want to move? [n/e/s/w] ")
        elif self.game_state == GameState.in_combat:
            assert len(self.in_combat_vs) == 1
            hostile = self.in_combat_vs[0]
            enemy_text = color_string(f"{hostile.name}", "Fore.RED")
            self.gui.main_out.add_line(
                f"{enemy_text.title()}: {hostile.hp}/{hostile.max_hp} HP",
            )
            self.gui.main_out.add_line(f"You: {self.player.hp}/{self.player.max_hp} HP")
            self.gui.main_out.add_line(
                f"You can {color_string('melee', 'Fore.RED')} attack, or attempt to {color_string('run', 'Fore.CYAN')}.",
            )
        else:
            raise ValueError(f"Invalid Game State '{self.game_state}'")

    def get_current_room_name(self) -> str:
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
        elif self.get_current_room_name() == "portal" and command in [
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
        # after that, check to see if we're in combat
        self.maybe_enter_combat()

    def play(self, command: str) -> bool | None:
        """Route input to where it needs to go depending on current game state

        Args:
            command (str)

        Returns:
            bool | None: True iff you portal into another dimension
        """
        command = sanitize_input(command)
        if self.game_state == GameState.in_map:
            return self.map_turn(command)
        elif self.game_state == GameState.in_combat:
            return self.combat(command)
        else:
            raise ValueError(f"Invalid Game State '{self.game_state}'")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        # filename="mapgame.log",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=False)],
    )

    # g = Game()
    game = Game()

    logger.info("\n________________\nInitialized mapgame logger")
