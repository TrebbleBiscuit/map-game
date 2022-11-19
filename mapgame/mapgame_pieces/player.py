import random
from mapgame_pieces.alive import LivingThing
from mapgame_pieces.utils import color_string


class Player(LivingThing):
    def __init__(self, gui: "GUIWrapper"):
        super().__init__()
        self.gui = gui
        self.max_hp = 50
        self.hp = self.max_hp
        self.attack_power = 5
        self.inventory = []
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
        super()._heal_over_time()
        if self.hp < self.max_hp:
            self.gui.main_out.add_line("The player heals twice as fast")
            self.hp += 1
