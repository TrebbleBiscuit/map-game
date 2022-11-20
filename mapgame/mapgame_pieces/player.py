import random
from mapgame_pieces.alive import LivingThing
from mapgame_pieces.utils import color_string
from mapgame_pieces.items import Item
import logging

logger = logging.getLogger(__name__)

# type alias
InventoryContents = dict[str, int]
ItemMap = dict[str, Item]


class Inventory:
    def __init__(self):
        # items must have unique names!
        self._contents: InventoryContents = {}  # {Item().name: quantity}
        self._item_map: ItemMap = {  # this will be more useful when items are unique
            "Bullet": Item("Bullet"),
        }

    @property
    def contents(self) -> InventoryContents:
        # use self.add() and self.remove() to modify contents
        return self._contents

    @property
    def item_map(self) -> ItemMap:
        return self._item_map

    def get_item_qty(self, item_name: str) -> int:
        if item_name in self.contents:
            return self.contents[item_name]
        return 0

    def add(self, to_add: str, qty: int = 1):
        logger.debug(f"Adding {qty}x {to_add} to inventory")
        if to_add in self.contents:
            self._contents[to_add] += qty
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


class Player(LivingThing):
    def __init__(self, gui: "GUIWrapper"):
        super().__init__()
        self.gui = gui
        self.max_hp = 50
        self.hp = self.max_hp
        self.attack_power = 5  # base melee damage
        self.gun_aiming = 60  # base chance to hit with gun /100
        self.inventory = Inventory()
        self.money = 0
        self.level = 1
        self.xp = 0
        self.humanity = 100  # out of 100

    def grant_xp(self, xp: int):
        self.gui.main_out.add_line(f"You gained {xp} XP!")
        self.xp += xp
        if self.xp > (20 * self.level):
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
