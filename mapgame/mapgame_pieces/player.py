import random
from mapgame_pieces.alive import LivingThing
from mapgame_pieces.utils import color_string
from mapgame_pieces.items import Item
import logging

logger = logging.getLogger(__name__)


class Inventory:
    def __init__(self):
        # items must have unique names!
        self._contents: dict[str, int] = {}  # {Item().name: quantity}
        self._item_map: dict[str, Item] = {}

    @property
    def contents(self):
        # use self.add() and self.remove() to modify contents
        return self._contents

    @property
    def item_map(self):
        return self._item_map

    def add(self, to_add: Item, qty: int = 1):
        if to_add.name in self.contents:
            self._contents[to_add.name] += qty
        self._contents[to_add.name] = qty
        self._item_map[to_add.name] = to_add
        logger.info(self._item_map)

    def remove(self, to_remove: Item, qty: int = 1):
        if to_remove.name not in self.contents:
            raise ValueError(
                f"Tried to remove {to_remove.name} from player inventory, but it's not in here"
            )
        self._contents[to_remove.name] -= qty
        if self.contents[to_remove.name] < 0:
            raise ValueError(
                "Tried to remove more {to_remove.name} from player inventory than exists here"
            )
        elif self.contents[to_remove.name] == 0:
            self._contents.pop(to_remove.name)
            self._item_map.pop(to_remove.name)


class Player(LivingThing):
    def __init__(self, gui: "GUIWrapper"):
        super().__init__()
        self.gui = gui
        self.max_hp = 50
        self.hp = self.max_hp
        self.attack_power = 5
        self.inventory = Inventory()
        self.money = 0
        self.level = 1
        self.xp = 0
        self.humanity = 100  # out of 100

    def grant_xp(self, xp: int):
        self.gui.main_out.add_line(f"You gained {xp} XP!")
        self.xp += xp
        if self.xp > (50 * self.level):
            lvl_txt = color_string(f"You have leveled up!", Fore.GREEN)
            self.gui.main_out.add_line(lvl_txt)
            self.level += 1
            self.gui.main_out.add_line(f"You are now level {self.level}.")
            ap_txt = color_string(f"attack power", Style.BRIGHT)
            self.gui.main_out.add_line(f"You gain 1 {ap_txt}!")

    def take_damage(self, dmg: int):
        ouch = random.choice(["Ouch", "Oof", "Owwie", "Yikes", "Oh no"])
        self.gui.main_out.add_line(f"{ouch}! You take {dmg} damage!")
        self.hp -= dmg
        if self.hp <= 0:
            self.gui.main_out.add_line("YOU DIE.")
            self.gui.main_out.add_line(
                "Not really implemented yet; for now you lose 25 humanity",
            )
            self.humanity -= 25
            if self.humanity <= 0:
                self.gui.main_out.add_line("humanity <= 0; GAME OVER")
                raise NotImplementedError("Game Over")

    def recover_hp(self, rec):
        hp_missing = self.max_hp - self.hp
        if hp_missing < rec:
            rec = hp_missing
        hp_txt = color_string(str(hp_missing), Fore.GREEN)
        self.gui.main_out.add_line(f"You recover {hp_txt} HP!")
        self.hp += rec
        self.gui.main_out.add_line(f"You are now at {self.hp}/{self.max_hp} HP!")

    def _heal_over_time(self):
        if self.hp < self.max_hp:
            self.gui.main_out.add_line("You regain some HP")
        super()._heal_over_time()
        if self.hp < self.max_hp:
            # player heals twice as fast
            self.hp += 1
