import random
from mapgame_pieces.alive import LivingThing
from mapgame_pieces.utils import color_string, COLOR_SCHEME
from mapgame_pieces.items import Item
import logging
from dataclasses import dataclass
import json
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

# type alias
InventoryContents = dict[str, int]
ItemMap = dict[str, Item]
EquippedMap = dict[str, Item | None]


SAVE_PATH = Path("mapgame.mapsave")
logger = logging.getLogger(__name__)


class ArmorSlot(str, Enum):
    head = "head"
    chest = "chest"
    legs = "legs"
    feet = "feet"


class ArmorModifier(str, Enum):
    blessed = "blessed"
    cursed = "cursed"


class ArmorPiece:
    def __init__(
        self,
        name: str | None = None,
        armor_slot: ArmorSlot = ArmorSlot.head,
        armor_amount: int = 1,
        modifier: ArmorModifier | None = None,
        saved: dict | None = None,
    ):
        self.name: str = name if name else self.generate_name(armor_slot)
        self.armor_slot = armor_slot
        self.armor_amount = armor_amount
        self.modifier = modifier

        if saved:
            self.from_saved(saved)

    def to_save(self) -> dict:
        return {k: val for k, val in self.__dict__.items() if val is not None}

    @property
    def name_str(self):
        if self.modifier is None:
            modifier_str = ""
        else:
            modifier_str = self.modifier.name + " "
        flavor_adj_map = {
            0: color_string("useless ", "grey39"),
            1: color_string("damaged ", "grey50"),
            2: color_string("tattered ", "grey62"),
            3: color_string("worn ", "grey78"),
            4: "",
            5: color_string("solid ", "cornsilk1"),
            6: color_string("strong ", "wheat1"),
            7: color_string("powerful ", "khaki1"),
        }
        flavor_adj = flavor_adj_map[min(7, self.armor_amount)]
        return color_string(
            modifier_str
            + flavor_adj
            + color_string(self.name, "armor_name")
            + " "
            + f"(+{self.armor_amount})",
            "entire_armor_str",
        )

    @staticmethod
    def generate_name(armor_slot: ArmorSlot) -> str:
        match armor_slot:
            case ArmorSlot.head:
                return random.choice(["helmet", "helm", "headgear"])
            case ArmorSlot.chest:
                return random.choice(["chestplate", "chestpiece"])
            case ArmorSlot.legs:
                return random.choice(["leggings", "pants"])
            case ArmorSlot.feet:
                return random.choice(["boots", "shoes"])
            case _:
                raise ValueError(f"armor_slot is not valid: {armor_slot}")

    @classmethod
    def random_from_level(cls, level: int):
        armor_slot = random.choice([x for x in ArmorSlot])
        armor_amount = random.randint(max(1, level // 5), max(1, level // 2))
        inst = cls(armor_slot=armor_slot, armor_amount=armor_amount)
        return inst

    def from_saved(self, saved):
        for key, val in saved.items():
            if key == "armor_slot":
                setattr(self, key, ArmorSlot(val))
            elif key == "modifier":
                setattr(self, key, ArmorModifier(val))
            else:
                setattr(self, key, val)


class EquippedArmor:
    def __init__(self, saved=None):
        for slot in ArmorSlot:
            setattr(self, slot.name, None)
        if saved:
            self.from_saved(saved)

    def unequip(self, armor_slot: ArmorSlot, gui):
        gui.main_out.add_line(
            f"You remove the {getattr(self, armor_slot.name).name_str} from your {armor_slot.name}."
        )
        setattr(self, armor_slot.name, None)

    def equip(self, to_equip: ArmorPiece, gui):
        armor_slot = to_equip.armor_slot
        already_equipped = getattr(self, armor_slot)
        if already_equipped:
            self.unequip(to_equip.armor_slot, gui)
        setattr(self, armor_slot.name, to_equip)
        gui.main_out.add_line(
            f"You cover your {armor_slot.name} with the {getattr(self, armor_slot.name).name_str}."
        )
        # TODO: 'you equip the x'

    @property
    def armor_score(self) -> int:
        total = 0
        for slot in ArmorSlot:
            this_slot = getattr(self, slot.name)
            if this_slot:
                total += this_slot.armor_amount
        return total

    def to_save(self) -> dict:
        return {k: val.to_save() for k, val in self.__dict__.items() if val is not None}

    def from_saved(self, saved):
        for key, val in saved.items():
            setattr(self, key, ArmorPiece(saved=val))


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

    def to_save(self):
        return self.contents

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

    def to_save(self) -> dict:
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
        self.cursed_power = 0

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
        self.attack_power_base = 4  # base melee damage
        self.inventory = Inventory()
        self.abilities = Abilities()
        self.flags = Flags()
        self.armor = EquippedArmor()
        self.money = 0
        self.level = 1
        self.xp = 0
        self._humanity = 100  # out of 100
        self.time = 0
        self.tile_index = 1
        if SAVE_PATH.exists():
            self.load_from_file()

    @property
    def attack_power(self):
        power = (self.level * 0.8) + 4
        if self.flags.cursed_power:
            power *= 1.1**self.flags.cursed_power
        return int(power)

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
            self.gui.main_out.add_line(color_string(warn_msg, "humanity_down"))
        elif val < 60 and warn_lvl == 1:
            self.flags.humanity_warning_level = 2
            warn_msg = "As you lose more of your humanity, you begin to hear dark whispers at the edge of your focus..."
            self.gui.main_out.add_line(color_string(warn_msg, "humanity_down"))
        elif val < 40 and warn_lvl == 2:
            self.flags.humanity_warning_level = 3
            warn_msg = "It is getting harder to ignore the whispers. To fight away the sense of hopeless despair..."
            self.gui.main_out.add_line(color_string(warn_msg, "humanity_down"))
        elif val < 20 and warn_lvl == 3:
            self.flags.humanity_warning_level = 4
            warn_msg = "There is less and less human about you all the time... How much longer can you remain in control?"
            self.gui.main_out.add_line(color_string(warn_msg, "humanity_down"))

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
            "money": self.money,
            "level": self.level,
            "tile_index": self.tile_index,
            "xp": self.xp,
            "humanity": self.humanity,
            "time": self.time,
        }
        for object_to_save in ["abilities", "flags", "armor", "inventory"]:
            save_value = getattr(self, object_to_save).to_save()
            if save_value:
                save_data[object_to_save] = save_value
        with open(SAVE_PATH, "w") as savefile:
            json.dump(save_data, savefile)

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
            if entry == "inventory":
                self.inventory = Inventory(contents=value)
            elif entry == "abilities":
                self.abilities = Abilities(saved=value)
            elif entry == "flags":
                self.flags = Flags(saved=value)
            elif entry == "armor":
                self.armor = EquippedArmor(saved=value)
            elif entry == "humanity":
                self._humanity = value
            else:
                setattr(self, entry, value)

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

    def grant_xp(self, xp: int):
        xp_txt = color_string(f"{xp} XP", "stat_up")
        self.gui.main_out.add_line(f"You gained {xp_txt}!")
        self.xp += xp
        if self.xp > (25 * pow(self.level, 1.3)):
            lvl_txt = color_string(f"You have leveled up!", "level_up")
            self.gui.main_out.add_line(lvl_txt)
            self.level += 1
            self.max_hp += 5
            self.hp += 5

            # buff_txt = color_string("+5 Max HP", "stat_up")
            # if self.level % 3 == 0:
            #     # 1/3 of the time
            #     buff_txt += ", " color_string("some other buff", "stat_up")
            # else:
            #     # 2/3 of the time
            #     buff_txt += ", " + color_string("+1 ATK", "stat_up")
            #     self.attack_power += 1

            self.gui.main_out.add_line(f"You are now level {self.level}.")

            # heal up to ~15% health
            self.heal_up_to(int(self.max_hp / 6))

            # invisible buffs
            self.humanity += 1

    def grant_money(self, money: int):
        money_txt = color_string(f"${money}!", "got_item")
        self.gui.main_out.add_line(f"You gained {money_txt}")
        self.money += money

    def game_over(self):
        logger.info(f"GAME OVER - Score: {self.score}")
        self.gui.main_out.add_line("\nYour humanity drops to zero!")
        self.gui.main_out.add_line(
            "No longer will you rise to fight the endless hoard of monsters."
        )
        self.gui.main_out.add_line("Instead you are doomed to wander among them.")
        self.gui.main_out.add_line("\n" + color_string("GAME OVER", "cursed"))
        self.gui.main_out.add_line(f"Your final score is {self.score}")
        self.gui.main_out.add_line(
            "delete your save file if you want, or just keep playing"
        )
        self.gui.main_out.add_line("")

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
                color_string(
                    "Suddenly a feeling of holy power overwhelms you! You feel refreshed and recovered!",
                    "good_thing_happened",
                )
            )
        elif cursed:
            malicious_power_txt = color_string(
                f"Suddenly an unholy feeling of {color_string('cursed', 'cursed')} power overwhelms you!",
                "humanity_down",
            )
            self.gui.main_out.add_line(
                malicious_power_txt + " You feel refreshed, but at a great cost..."
            )
        else:
            malicious_power_txt = color_string(
                "Suddenly a feeling of malicious power overwhelms you!",
                "humanity_down",
            )
            self.gui.main_out.add_line(
                malicious_power_txt + " You feel refreshed, but at what cost?"
            )
        self.recover_hp(int(self.max_hp * recover_ratio))

    def take_damage(self, dmg: int) -> bool:
        """return True if you died"""
        # each armor point has a 50% chance to mitigate dmg
        for x in range(self.armor.armor_score):
            if random.random() >= 0.5:
                dmg -= 1
        if dmg < 1:
            dmg = 1
        ouch = random.choice(["Ouch", "Oof", "Owwie", "Yikes", "Oh no"])
        dmg_txt = color_string(f"You take {dmg} damage!", "damage_taken")
        self.gui.main_out.add_line(f"{ouch}! {dmg_txt}")
        self.hp -= dmg
        if self.hp > 0:
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
        hp_txt = color_string(str(rec) + " HP", "recover_hp")
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
