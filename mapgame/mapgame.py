import logging
import random
from enum import Enum
from dataclasses import dataclass, field

from mapgame_pieces.player import Player
from mapgame_pieces.alive import NPC
from mapgame_pieces.map import Map
from mapgame_pieces.utils import (
    color_string,
    sanitize_input,
    get_plural_suffix,
    COLOR_SCHEME,
)
from mapgame_pieces.gui import GUIWrapper
from mapgame_pieces.items import Item

logger = logging.getLogger(__name__)

INVALID_INPUT_MSG = color_string("Input not understood", "bright_black")
MAP_WIDTH = 8
MAP_HEIGHT = 4


class GameState(Enum):
    in_map = 1
    in_combat = 2
    in_conversation = 3
    in_limbo = 4


@dataclass
class CurrentInteraction:
    in_combat_vs: list[NPC] = field(default_factory=list)
    combat_revive_count = 0
    in_conversation_with: NPC | None = None


class Game:
    def __init__(self):
        self.gui = GUIWrapper(game=self)
        self.player = Player(self.gui)
        self.map = Map(self.gui, MAP_WIDTH, MAP_HEIGHT)
        self.current_tile = self.map.get_tile(
            self.player.tile_index
        )  # self.map.tiles[self.player.tile_index]
        self.debug = False
        self.game_state = GameState.in_map
        self.interaction = CurrentInteraction()
        self.gui.run()

    def _progress_time(self):
        if random.randint(1, 6) == 1:
            self.player._heal_over_time()
        self.player.time += 1
        for npc in self.current_tile.npcs:
            npc._on_time_pass(self.current_tile)

    def enter_limbo(self):
        gui_choices = [
            "In a moment you will have an experience that will seem completely real",
            "You are in limbo",
            "A single moment stretched out to infinity",
            "You are everywhere and nowhere, a place between worlds",
            "Is there anybody out there?",
        ]
        if random.random() < 0.2:
            gui_choices.append("I N T E R D I M E N S I O N A L   L I M B O")
        self.gui.main_out.add_line("You feel yourself enter interdimensional limbo!")
        self.gui.main_in.placeholder = random.choice(gui_choices)
        self.game_state = GameState.in_limbo

    def exit_limbo(self):
        self.gui.main_in.placeholder = self.gui.default_input_placeholder
        self.game_state = GameState.in_map
        self.player.save_to_file()

    def enter_conversation(self, npc: NPC):
        # self.gui.map_out.update("")
        gui_choices = [
            "Type a response and press enter",
            "Say something interesting!",
            "One good conversation can shift the direction of change forever",
            "The best of life is conversation",
        ]
        if random.random() < 0.2:
            gui_choices.append("70 to 93 percent of all communication is nonverbal")
        self.gui.main_in.placeholder = random.choice(gui_choices)
        if self.interaction.in_conversation_with:
            raise RuntimeError(
                f"Attempted to enter conversation, but player is already speaking with: {self.interaction.in_conversation_with}"
            )
        self.game_state = GameState.in_conversation
        self.interaction.in_conversation_with = npc

    def end_conversation(self):
        self.gui.main_in.placeholder = self.gui.default_input_placeholder
        self.gui.main_out.add_line("Time to continue exploring.")
        self.game_state = GameState.in_map
        self.interaction.in_conversation_with = None

    def enter_combat(self, hostiles: list[NPC]):
        # update GUI
        gui_choices = [
            "Try not to panic",
            "Keep it cool, you've got this",
            "Show 'em what you're made of",
            "Heroism is endurance for one moment more",
            "Only the dead have seen the end of war.",
            "Aim towards the enemy.",
            "Try to look unimportant; they may be low on ammo.",
            "All warfare is based on deception.",
        ]
        if random.random() < 0.2:
            gui_choices.append("psssh...nothing personnel...kid...")
            gui_choices.append("What is this, some kind of map-game?")
            gui_choices.append("You must construct additional pylons")
        self.gui.main_in.placeholder = random.choice(gui_choices)
        if self.interaction.in_combat_vs:
            raise RuntimeError(
                f"Attempted to enter combat, but player is already fighting: {self.interaction.in_combat_vs}"
            )
        self.interaction.in_combat_vs = hostiles
        self.game_state = GameState.in_combat
        if len(hostiles) == 1:
            enemy_text = color_string(
                f"{hostiles[0].name}", COLOR_SCHEME["hostile_name"]
            )
            self.gui.main_out.add_line(f"\nEntered combat with a hostile {enemy_text}!")
        else:
            enemy_text = color_string(
                ", ".join(h.name for h in hostiles), COLOR_SCHEME["hostile_name"]
            )
            self.gui.main_out.add_line(f"\nEntered combat with hostiles: {enemy_text}!")

    def end_combat(self):
        self.gui.main_in.placeholder = self.gui.default_input_placeholder
        self.gui.main_out.add_line(
            "With combat behind you for now, it's time to keep exploring."
        )
        self.interaction.combat_revive_count = 0
        self.interaction.in_combat_vs = []
        self.game_state = GameState.in_map

    def melee_attack_hostiles(self):
        self.gui.main_out.add_line("")
        base_dmg = self.player.attack_power
        min_dmg = int((base_dmg * 0.5) + 0.5)
        max_dmg = int(base_dmg * 1.5)
        for hostile in self.interaction.in_combat_vs:
            enemy_text = color_string(f"{hostile.name}", COLOR_SCHEME["hostile_name"])
            act_dmg = random.randint(min_dmg, max_dmg)
            self.gui.main_out.add_line(f"You take a swing at the {enemy_text}!")
            dmg_txt = color_string(f"{act_dmg} damage", COLOR_SCHEME["damage_done"])
            dmg_flavor = color_string(
                self.get_dmg_flavor(act_dmg, min_dmg, base_dmg, max_dmg), "bright_black"
            )
            self.gui.main_out.add_line(f"You do {dmg_txt}! {dmg_flavor}")
            if self.debug:
                self.gui.main_out.add_line(f"DEBUG: ({min_dmg}-{max_dmg} dmg)")
            if hostile.take_damage(act_dmg):
                self.gui.main_out.add_line(
                    color_string(
                        f"It falls to the ground and disappears in a flash of light!",
                        COLOR_SCHEME["good_thing_happened"],
                    )
                )
                self.player.humanity += 1

    def get_dmg_flavor(self, act_dmg, min_dmg, base_dmg, max_dmg):
        if act_dmg == max_dmg:
            flavor_txt = "A critical hit!!"
        elif act_dmg > base_dmg:
            flavor_txt = "A good hit!"
        elif act_dmg == base_dmg:
            flavor_txt = "An average hit!"
        elif act_dmg == min_dmg:
            flavor_txt = "A very weak hit!!"
        else:
            flavor_txt = "A glancing hit!"
        return flavor_txt

    def shoot_attack_hostiles(self):
        """you know like with a gun"""
        base_dmg = 10 + self.player.level
        min_dmg = int((base_dmg * 0.5) + 0.5)
        max_dmg = int(base_dmg * 1.5)
        act_dmg = random.randint(min_dmg, max_dmg)
        hit = random.randint(0, 100) <= self.player.gun_aiming
        hostile = random.choice(self.interaction.in_combat_vs)
        enemy_text = color_string(f"{hostile.name}", COLOR_SCHEME["hostile_name"])
        self.gui.main_out.add_line(f"You aim at the {enemy_text} and pull the trigger!")
        if hit:
            dmg_flavor = color_string(
                self.get_dmg_flavor(act_dmg, min_dmg, base_dmg, max_dmg), "bright_black"
            )
            dmg_txt = color_string(f"{act_dmg} damage", COLOR_SCHEME["damage_done"])
            self.gui.main_out.add_line(f"You do {dmg_txt}! {dmg_flavor}")
            if self.debug:
                self.gui.main_out.add_line(f"DEBUG: ({min_dmg}-{max_dmg} dmg)")
            if hostile.take_damage(act_dmg):
                self.gui.main_out.add_line(
                    f"It falls to the ground and disappears in a flash of light!"
                )
                self.player.humanity += 1
        else:
            self.gui.main_out.add_line(f"You miss! ({self.player.gun_aiming}% to hit)")

    def combat(self, ui: str):
        assert len(self.interaction.in_combat_vs) > 0
        if ui in ["melee", "m"]:
            self.melee_attack_hostiles()
        elif ui in ["shoot", "s"]:
            bullet_qty = self.player.inventory.get_item_qty("Bullet")
            if bullet_qty:
                self.gui.main_out.add_line(
                    f"You decide to use one of your {bullet_qty} bullets."
                )
                self.player.inventory.remove("Bullet")
                self.shoot_attack_hostiles()
            else:
                self.gui.main_out.add_line("You don't have any ammo!")
                return
        elif ui in ["run", "r"]:
            success_chance = 0.8
            if random.random() < success_chance:
                self.gui.main_out.add_line("You run away!")
                self.end_combat()
                return
            self.gui.main_out.add_line(
                f"You try to run away ({int(success_chance*100)}%), but aren't quick enough this time!"
            )
        else:
            self.gui.main_out.add_line(INVALID_INPUT_MSG)
            return
        # if any hostiles are dead, give xp and update list of hostiles
        out_of_combat = []
        for hostile in self.interaction.in_combat_vs:
            if hostile.is_dead:
                out_of_combat.append(hostile)
                self.player.grant_xp(hostile.xp_reward)
                self.player.grant_money(random.randint(1, hostile.xp_reward))
            elif hostile.player_attitude > 0:
                out_of_combat.append(hostile)
                logger.info(f"{hostile.name} exits combat because attitude is high")
        if out_of_combat:
            self.interaction.in_combat_vs = [
                x for x in self.interaction.in_combat_vs if x not in out_of_combat
            ]
        if not self.interaction.in_combat_vs:
            logger.info("Ending combat because all enemies are dead")
            self.end_combat()
            return
        for hostile in self.interaction.in_combat_vs:
            # make sure we're still in combat each turn
            if self.game_state != GameState.in_combat:
                return
            self.hostile_combat_turn(hostile)
        self.gui.main_out.add_line("")

    def hostile_combat_turn(self, hostile: NPC):
        base_dmg = hostile.attack_power
        min_dmg = int((base_dmg * 0.7) + 0.5)
        max_dmg = int(base_dmg * 1.3)
        act_dmg = random.randint(min_dmg, max_dmg)
        dmg_flavor = color_string(
            self.get_dmg_flavor(act_dmg, min_dmg, base_dmg, max_dmg).lower(),
            "bright_black",
        )
        enemy_text = color_string(f"{hostile.name}", COLOR_SCHEME["hostile_name"])
        self.gui.main_out.add_line(
            f"The {enemy_text} attacks you, scoring {dmg_flavor}"
        )
        # dmg_txt = color_string(f"{act_dmg} damage", COLOR_SCHEME['damage'])
        # self.gui.main_out.add_line(
        #     f"It connects for ({min_dmg}-{max_dmg}) {dmg_txt}!",
        # )
        if self.debug:
            self.gui.main_out.add_line(f"DEBUG: ({min_dmg}-{max_dmg}) enemy dmg")
        if self.player.take_damage(act_dmg):
            # player 'died'
            self.interaction.combat_revive_count += 1
            if self.interaction.combat_revive_count >= 3:
                self.bail_player_out_of_combat()
            else:
                self.player.revive()

    def bail_player_out_of_combat(self):
        """player died too many times, bail them out
        they get a 'cursed' revive and no rewards from combat
        """
        for npc in self.interaction.in_combat_vs:
            npc.take_damage(npc.hp)
        self.player.revive(cursed=True)
        self.end_combat()

    def get_chest_contents(self) -> tuple[str, int]:
        choices = [
            ("Bullet", random.randint(3, int(self.player.tile_index / 2) + 3)),
            (
                "money",
                random.randint(
                    self.player.tile_index + 2, (self.player.tile_index + 2) * 2
                ),
            ),
        ]
        return random.choice(choices)

    def open_chest(self):
        # here's the real stuff
        self.current_tile.chests.remove(self.player.coordinates)
        item_in_chest, qty_in_chest = self.get_chest_contents()
        if item_in_chest == "money":
            inside_txt = color_string(f"${qty_in_chest}", COLOR_SCHEME["got_item"])
            self.gui.main_out.add_line(
                f"You open a chest - there is {inside_txt} inside!"
            )
            self.player.money += qty_in_chest
            return
        self.player.inventory.add(item_in_chest, qty_in_chest)
        # here's user feedback
        plural = get_plural_suffix(item_in_chest) if qty_in_chest > 1 else ""
        it_or_them = "it" if qty_in_chest == 1 else "them"
        are_or_is = "is" if qty_in_chest == 1 else "are"
        full_item_desc = color_string(
            f"{qty_in_chest} {item_in_chest}{plural}", COLOR_SCHEME["got_item"]
        )
        self.gui.main_out.add_line(
            f"You open a chest - there {are_or_is} {full_item_desc} inside!"
        )
        self.gui.main_out.add_line(f"You add {it_or_them} to your inventory.")
        logger.debug(f"player inventory contents: {self.player.inventory.contents}")

    def portal_into_another_dimension(self, dim_num=None):
        # heal up to ~15% health
        self.player.heal_up_to(int(self.player.max_hp / 6))
        if dim_num is None:
            self.player.tile_index += 1
            dim_num = self.player.tile_index
        else:
            self.player.tile_index = dim_num
        self.gui.main_out.add_line(f"You portal into dimension #{dim_num}")
        if self.player.humanity > 5:
            self.player.humanity -= 1
        elif self.player.humanity > 1:
            if random.random() == 0.5:
                self.player.humanity -= 1
        self.player.grant_xp(dim_num * 3 + random.randint(4, 10))
        self.current_tile = self.map.get_tile(dim_num)
        self.player.save_to_file()
        self.player.x, self.player.y = (0, 0)
        if not self.player.tile_index % 5:
            self.enter_limbo()

    def maybe_enter_combat(self):
        # Should we encounter an NPC?
        attacking_npcs = []
        other_npcs = []
        for ct_npc in self.current_tile.npcs:
            if not ct_npc.is_dead and ct_npc.coordinates == self.player.coordinates:
                if ct_npc.will_attack_player():
                    attacking_npcs.append(ct_npc)
                else:
                    other_npcs.append(ct_npc)
        if attacking_npcs:
            self.enter_combat(attacking_npcs)
        elif other_npcs:
            conversation_npcs = [x for x in other_npcs if not x.conversation.has_ended]
            if conversation_npcs:
                convo_npc = random.choice(conversation_npcs)
                self.gui.main_out.add_line(
                    f"The friendly {convo_npc.name} in this room strikes up a conversation with you!"
                )
                self.enter_conversation(convo_npc)

    def turn_prompt(self):
        """Prompt the user to enter a command"""
        # self.stdscr.clrtobot()
        self.gui.update_stats()
        if self.game_state == GameState.in_map:
            self.current_tile.room_flavor_text(self.player.coordinates)
            if self.player.coordinates in self.current_tile.chests:
                open_txt = color_string("open", COLOR_SCHEME["main_command"])
                self.gui.main_out.add_line(
                    f"There's a chest in this room! {open_txt} it to see what's inside."
                )
            for ct_npc in self.current_tile.npcs:
                if not ct_npc.is_dead and ct_npc.coordinates == self.player.coordinates:
                    if ct_npc.will_attack_player():
                        self.gui.main_out.add_line(
                            f"There is a hostile {ct_npc.name} in this room!"
                        )
                    else:
                        self.gui.main_out.add_line(
                            f"There is a friendly {ct_npc.name} in this room!"
                        )
            self.gui.main_out.add_line("What direction do you want to move? [n/e/s/w]")
        elif self.game_state == GameState.in_combat:
            for hostile in self.interaction.in_combat_vs:
                enemy_text = color_string(
                    f"{hostile.name.title()}", COLOR_SCHEME["hostile_name"]
                )
                self.gui.main_out.add_line(
                    f"{enemy_text}: {hostile.hp}/{hostile.max_hp} HP",
                )
            # self.gui.main_out.add_line(f"You: {self.player.hp}/{self.player.max_hp} HP")
            self.gui.main_out.add_line(
                f"You can {color_string('melee', COLOR_SCHEME['main_command'])} attack, or attempt to {color_string('run', COLOR_SCHEME['secondary_command'])}.",
            )
            if self.player.inventory.get_item_qty("Bullet") > 0:
                shoot_txt = color_string("shoot", COLOR_SCHEME["main_command"])
                self.gui.main_out.add_line(
                    f"You can also try to {shoot_txt} an enemy ({self.player.gun_aiming}%)"
                )
        elif self.game_state == GameState.in_conversation:
            assert self.interaction.in_conversation_with
            out = self.interaction.in_conversation_with.conversation.prompt()
            self.gui.main_out.add_line(out)
        elif self.game_state == GameState.in_limbo:
            self.gui.main_out.add_line(
                "You exist in a state of limbo; a world between worlds."
            )
            self.gui.main_out.add_line(
                f"You take a moment to reflect. Your current score is {self.player.score}"
            )
            if self.player.humanity <= 90 and self.player.money >= 10:
                self.gui.main_out.add_line(
                    "You can pay tithe to regain humanity (8c/h)"
                )
            if (
                self.player.flags.humanity_warning_level
                and self.player.humanity > 20
                and not self.player.flags.cursed_revive
            ):
                self.gui.main_out.add_line("You could pray to the dark gods...")
            self.gui.main_out.add_line("You can continue onward to exit limbo")
        else:
            raise ValueError(f"Invalid Game State '{self.game_state}'")

    def limbo_turn(self, command: str):
        if command in ["continue", "c", "down", "go", "leave", "exit"]:
            self.gui.main_out.add_line(
                "An indescribable feeling washes over you as you exit limbo!"
            )
            self.exit_limbo()
        elif (
            command in ["pay", "tithe"]
            and self.player.humanity < 80
            and self.player.money >= 10
        ):
            cost_per = 8
            max_cost = (100 - self.player.humanity) * cost_per
            pay = min(self.player.money, max_cost)
            remainder = pay % 8
            pay -= remainder
            regain = pay // cost_per
            self.gui.main_out.add_line(
                f"You exchange {pay} money for {regain} humanity!"
            )
            self.player.money -= pay
            self.player.humanity += regain
        elif (
            command in ["pray"]
            and self.player.flags.humanity_warning_level
            and self.player.humanity > 20
            and self.player.flags.cursed_revive
        ):
            self.gui.main_out.add_line(
                "Shaking off the feeling that this is a bad idea, you give in to the whispers in your head..."
            )
            self.gui.main_out.add_line(
                color_string(
                    "The whispering gets louder and louder until it is suddenly silent.",
                    COLOR_SCHEME["humanity_down"],
                )
            )
            self.gui.main_out.add_line(
                color_string(
                    "You return to awareness feeling stronger! But also distinctly...",
                    COLOR_SCHEME["good_thing_happened"],
                )
                + color_string(" unclean", COLOR_SCHEME["humanity_down"])
            )
            self.player.flags.cursed_revive += 4
            self.player.attack_power += 1

    def get_current_room_name(self) -> str | None:
        """Return the name of the room the player is currently in"""
        if self.player.coordinates in self.current_tile.rooms:
            return self.current_tile.rooms[self.player.coordinates].name

    def map_turn(self, command: str) -> bool | None:
        """Process a user's input command"""
        # don't want any more lines so the map stays the same, use room_flavor_text instead
        # if room_name == 'portal': Utils.printline(self.stdscr, "You can leave through the portal in this room.")
        if not command:
            return
        elif command in ["n", "e", "s", "w"]:
            player_move = self.player.move(self.current_tile, command)
            if player_move:  # move successful
                self.gui.main_out.add_line(
                    color_string(f"You move {player_move}.", "bright_black")
                )
                if self.player.coordinates not in self.current_tile.explored:
                    # heal when entering new rooms
                    self.player._heal_over_time()
                self.current_tile.explored.add(self.player.coordinates)
                # self.current_tile.room_flavor_text(self.player.coordinates)
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
        elif command in [
            "open",
            "chest",
            "o",
        ]:
            if self.player.coordinates in self.current_tile.chests:
                self.open_chest()
            else:
                self.gui.main_out.add_line("There's no chest here to open!")
        elif self.get_current_room_name() == "medbay" and command in [
            "medbay",
            "med",
            "heal",
            "m",
            "h",
        ]:
            if self.player.hp == self.player.max_hp:
                self.gui.main_out.add_line("You're already at full health!")
            else:
                # can only use medbay once
                self.current_tile.rooms.pop(self.player.coordinates)
                self.gui.main_out.add_line(
                    "You use the supplies in the medbay to restore some of your health!"
                )
                self.player.recover_hp(int(self.player.max_hp * 0.75))
                self._progress_time()

        elif command in ["talk", "conversation", "speak"]:
            friendly_npcs = [
                x
                for x in self.current_tile.npcs
                if not x.is_dead and x.coordinates == self.player.coordinates
            ]
            if friendly_npcs:
                for npc in friendly_npcs:
                    if npc.conversation.has_ended:
                        self.gui.main_out.add_line(
                            f"The {npc.name} doesn't have anything more to say."
                        )
                        return
                    else:
                        self.gui.main_out.add_line(
                            f"You strike up a conversation with the friendly {npc.name}."
                        )
                        self.enter_conversation(npc)
                        # return so that we don't check for combat and other conversations after this
                        return
            else:
                self.gui.main_out.add_line(INVALID_INPUT_MSG)
                return
        # beyond here lies debug commands
        # elif self.debug and command[:2] == "ff":
        #     self.combat(ct_npc)
        elif command[:5] == "debug":
            self.debug = not self.debug
            self.gui.main_out.add_line(f"Debug mode set to {self.debug}")
        elif self.debug and command[:2] == "xp":
            self.gui.main_out.add_line("DEBUG: Granting XP")
            self.player.grant_xp(int(command[2:].strip()))
        elif self.debug and command[:2] == "hp":
            self.gui.main_out.add_line("DEBUG: Setting HP")
            self.player.hp = int(command[2:].strip())
        elif self.debug and command[:5] == "tpdim":
            self.portal_into_another_dimension(
                dim_num=int(command[5:].strip() or self.player.tile_index + 1)
            )
        elif self.debug and (command[:2] == "tp" or command[:4] == "tele"):
            try:
                tc = command.split(" ")[1]
                tc = tuple(int(cv.strip()) for cv in tc.split(","))
            except (IndexError, ValueError) as err:
                self.gui.main_out.add_line(
                    'teleport to what coordinates? (i.e. "1, 3")'
                )
                self.gui.main_out.add_line("remember y is inverted")
                return
            if self.current_tile._check_valid_coords(tc):
                self.player.x, self.player.y = tc
                self.current_tile.explored.add(self.player.coordinates)
                self.gui.main_out.add_line("poof~")
            else:
                self.gui.main_out.add_line("off-map coordinates not allowed")
        elif self.debug and command == "npc":
            self.gui.main_out.add_line(
                str({x.name: x.coordinates for x in self.current_tile.npcs})
            )
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
        self.gui.main_out.add_line("")
        command = sanitize_input(command)
        match self.game_state:
            case GameState.in_map:
                return self.map_turn(command)
            case GameState.in_combat:
                return self.combat(command)
            case GameState.in_conversation:
                convo = self.interaction.in_conversation_with.conversation
                assert convo
                out = convo.respond(self.player, command)
                self.gui.main_out.add_line(out)
                if convo.has_ended:
                    self.end_conversation()
            case GameState.in_limbo:
                return self.limbo_turn(command)
            case _:
                raise ValueError(f"Invalid Game State '{self.game_state}'")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s {%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        filemode="a",
        filename="mapgame.log",
        datefmt="[%X]",
        # handlers=[RichHandler(rich_tracebacks=False)],
    )

    logger.info("\n________________\nInitialized mapgame logger; beginning game...")
    # g = Game()
    game = Game()

    logger.info("\n________________\nGame Over")
