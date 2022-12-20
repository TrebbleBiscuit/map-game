import random
from mapgame_pieces.alive import LivingThing
from mapgame_pieces.utils import color_string, COLOR_SCHEME
from mapgame_pieces.items import Item
import logging
from dataclasses import dataclass
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# type alias
InventoryContents = dict[str, int]
ItemMap = dict[str, Item]
EquippedMap = dict[str, Item | None]


SAVE_PATH = Path("mapgame.mapsave")
logger = logging.getLogger(__name__)


class Inventory:
    def __init__(self, contents=None):
        if contents is None:
            contents = {}
        # items must have unique names!
        self._contents: InventoryContents = contents  # {Item().name: quantity}
        self._item_map: ItemMap = {  # this will be more useful when items are unique
            "Bullet": Item("Bullet"),
        }
        self._equipped: EquippedMap = {"melee": None, "ranged": None, "armor": None}

    @property
    def contents(self) -> InventoryContents:
        # use self.add() and self.remove() to modify contents
        return self._contents

    @property
    def item_map(self) -> ItemMap:
        return self._item_map

    @property
    def equipped(self) -> EquippedMap:
        return self._equipped

    def get_item_qty(self, item_name: str) -> int:
        if item_name in self.contents:
            return self.contents[item_name]
        return 0

    def add(self, to_add: str, qty: int = 1):
        logger.debug(f"Adding {qty}x {to_add} to inventory")
        if to_add in self.contents:
            self._contents[to_add] += qty
        else:
            self._contents[to_add] = qty

    def remove(self, to_remove: str, qty: int = 1):
        logger.debug(f"Removing {qty}x {to_remove} from inventory")
        if to_remove not in self.contents:
            raise ValueError(
                f"Tried to remove {to_remove} from inventory, but it's not in here"
            )
        self._contents[to_remove] -= qty
        if self.contents[to_remove] < 0:
            raise ValueError(
                "Tried to remove more {to_remove.name} from inventory than exists here"
            )
        elif self.contents[to_remove] == 0:
            self._contents.pop(to_remove)


@dataclass
class Abilities:
    def __init__(self, saved: dict | None = None):
        self.passive_heal_double = False
        self.reduced_humanity_loss = False
        if saved:
            self.from_saved(saved)

    def to_save(self):
        return {key: val for key, val in self.__dict__.items() if val}

    def from_saved(self, saved):
        for key, val in saved.items():
            setattr(self, key, val)


@dataclass
class Flags:
    def __init__(self, saved: dict | None = None):
        self.humanity_warning_level = 0
        self.blessed_revive = 0
        self.cursed_revive = 0

        if saved:
            self.from_saved(saved)

    def to_save(self):
        return {key: val for key, val in self.__dict__.items() if val}

    def from_saved(self, saved):
        for key, val in saved.items():
            setattr(self, key, val)


class Player(LivingThing):
    def __init__(self, gui: "GUIWrapper"):
        super().__init__()
        self.gui = gui
        self.max_hp = 30
        self.hp = self.max_hp
        self.attack_power = 4  # base melee damage
        self.inventory = Inventory()
        self.abilities = Abilities()
        self.flags = Flags()
        self.money = 0
        self.level = 1
        self.xp = 0
        self._humanity = 100  # out of 100
        self.time = 0
        if SAVE_PATH.exists():
            self.load_from_file()

    @property
    def humanity(self) -> int:
        return self._humanity

    @humanity.setter
    def humanity(self, val: int):
        if val > 100:
            val = 100

        diff = val - self._humanity
        if diff < -1 and (val <= 0 or self.abilities.reduced_humanity_loss):
            val += 1
            if diff < -9:
                val += 1

        warn_lvl = self.flags.humanity_warning_level
        if val < 80 and warn_lvl == 0:
            self.flags.humanity_warning_level = 1
            warn_msg = "As you lose another part of your humanity, you begin to feel a benign sense of unease..."
            self.gui.main_out.add_line(warn_msg)
        elif val < 60 and warn_lvl == 1:
            self.flags.humanity_warning_level = 2
            warn_msg = "As you lose more of your humanity, you begin to hear dark whispers at the edge of your focus..."
            self.gui.main_out.add_line(warn_msg)
        elif val < 40 and warn_lvl == 2:
            self.flags.humanity_warning_level = 3
            warn_msg = "It is getting harder to ignore the whispers. To fight away the sense of hopeless despair..."
            self.gui.main_out.add_line(warn_msg)
        elif val < 20 and warn_lvl == 3:
            self.flags.humanity_warning_level = 4
            warn_msg = "There is less and less human about you all the time... How much longer can you remain in control?"
            self.gui.main_out.add_line(warn_msg)
            self.gui.main_out.add_line("Right?")

        self._humanity = val

    @property
    def gun_aiming(self) -> int:
        base_chance = 60
        return min(base_chance + self.level, 100)

    def save_to_file(self):
        logger.debug("Saving to %s", SAVE_PATH)
        save_data = {
            "max_hp": self.max_hp,
            "hp": self.hp,
            "attack_power": self.attack_power,
            "money": self.money,
            "level": self.level,
            "tile_index": self.tile_index,
            "xp": self.xp,
            "humanity": self.humanity,
            "inventory_contents": self.inventory.contents,
            "abilities": self.abilities.to_save(),
            "flags": self.flags.to_save(),
        }
        with open(SAVE_PATH, "w") as savefile:
            json.dump(save_data, savefile)

    @property
    def score(self):
        return (
            self.max_hp
            + self.xp
            + (self.level * 10)
            + (self.tile_index * 20)
            + (len(self.abilities.to_save()) * 20)
            + self.humanity
        )

    def load_from_file(self):
        logger.debug("Loading save from %s", SAVE_PATH)
        with open(SAVE_PATH) as savefile:
            try:
                save_data = json.load(savefile)
            except json.decoder.JSONDecodeError as exc:
                logger.error("Error decoding savefile; starting new game")
                logger.exception(exc)
                return
        for entry, value in save_data.items():
            if entry == "inventory_contents":
                self.inventory = Inventory(contents=value)
            elif entry == "abilities":
                self.abilities = Abilities(saved=value)
            elif entry == "flags":
                self.flags = Flags(saved=value)
            elif entry == "humanity":
                self._humanity = value
            else:
                setattr(self, entry, value)

    def grant_xp(self, xp: int):
        xp_txt = color_string(f"{xp} XP!", COLOR_SCHEME["stat_up"])
        self.gui.main_out.add_line(f"You gained {xp_txt}")
        self.xp += xp
        if self.xp > (25 * pow(self.level, 1.3)):
            lvl_txt = color_string(f"You have leveled up!", COLOR_SCHEME["level_up"])
            self.gui.main_out.add_line(lvl_txt)
            self.level += 1
            self.attack_power += 1
            self.max_hp += 5
            self.hp += 5
            buffs_txt = color_string("(+1 ATK, +5 Max HP)", COLOR_SCHEME["stat_up"])
            self.gui.main_out.add_line(f"You are now level {self.level}. {buffs_txt}")

            # heal up to ~15% health
            self.heal_up_to(int(self.max_hp / 6))

            # invisible buffs
            self.humanity += 1

    def grant_money(self, money: int):
        money_txt = color_string(f"${money}!", COLOR_SCHEME["got_item"])
        self.gui.main_out.add_line(f"You gained {money_txt}")
        self.money += money

    def game_over(self):
        logger.info(f"GAME OVER - Score: {self.score}")
        self.gui.main_out.add_line("Your humanity drops to zero!")
        self.gui.main_out.add_line(
            "No longer will you rise to fight the endless hoard of monsters."
        )
        self.gui.main_out.add_line("Instead you are doomed to wander among them.")
        self.gui.main_out.add_line("    GAME OVER    ")
        self.gui.main_out.add_line(f"Your final score is {self.score}")
        self.gui.main_out.add_line(
            "delete your save file if you want, or just keep playing"
        )

    def revive(self, cursed=False, blessed=False):
        if not blessed and self.flags.blessed_revive:
            self.flags.blessed_revive -= 1
            blessed = True
        elif not cursed and self.flags.cursed_revive:
            self.flags.cursed_revive -= 1
            cursed = True
        if blessed:
            humanity_loss = 0
            recover_ratio = 1
        elif cursed:
            humanity_loss = 13
            recover_ratio = 0.7
        else:
            humanity_loss = 10
            recover_ratio = 0.9
        self.humanity -= humanity_loss
        if self.humanity <= 0:
            self.game_over()
        if blessed:
            self.gui.main_out.add_line(
                "Suddenly a feeling of holy power overwhelms you! You feel refreshed and recovered!"
            )
        elif cursed:
            self.gui.main_out.add_line(
                "Suddenly an unholy feeling of cursed power overwhelms you!"
            )
            self.gui.main_out.add_line(
                "You scream out in rage, and then everything goes black..."
            )
            self.gui.main_out.add_line("")
            self.gui.main_out.add_line(
                "When you come to, there is nothing left of the hostiles but mutilated corpses. Was this your doing..?"
            )
        else:
            malicious_power_txt = color_string(
                "Suddenly a feeling of malicious power overwhelms you!",
                COLOR_SCHEME["humanity_down"],
            )
            self.gui.main_out.add_line(
                malicious_power_txt + " You feel refreshed, but at what cost?"
            )
        self.recover_hp(int(self.max_hp * recover_ratio))

    def take_damage(self, dmg: int) -> bool:
        """return True if you died"""
        ouch = random.choice(["Ouch", "Oof", "Owwie", "Yikes", "Oh no"])
        dmg_txt = color_string(f"You take {dmg} damage!", COLOR_SCHEME["damage_taken"])
        self.gui.main_out.add_line(f"{ouch}! {dmg_txt}")
        self.hp -= dmg
        if self.hp >= 0:
            return False
        self.hp = (
            0  # maybe rm this? the idea of overkill affecting your next hp pool is cool
        )
        self.gui.main_out.add_line(
            "Your HP drops to zero! You collapse to your knees, feeling weak..."
        )
        return True

    def recover_hp(self, rec: int):
        hp_missing = self.max_hp - self.hp
        if hp_missing < rec:
            rec = hp_missing
        hp_txt = color_string(str(rec) + " HP", "green")
        self.gui.main_out.add_line(f"You recover {hp_txt}!")
        self.hp += rec

    def heal_up_to(self, up_to: int):
        hp_missing = up_to - self.hp
        if hp_missing > 0:
            self.recover_hp(hp_missing)

    def _heal_over_time(self):
        # if self.hp < self.max_hp:
        #     self.gui.main_out.add_line("You regain some HP")
        super()._heal_over_time()
        if self.abilities.passive_heal_double:
            super()._heal_over_time()
        # if self.hp < self.max_hp:
        #     # player heals twice as fast
        #     self.hp += 1

    def grant_ability(self, ability_name: str):
        if not getattr(self.abilities, ability_name):
            self.gui.main_out.add_line("You have learned a new ability!")
            setattr(self.abilities, ability_name, True)
