class Item:
    def __init__(self, name):
        self.name = name
        self.value = 0


class Weapon(Item):
    def __init__(self, name, attack_damage):
        super().__init__(name)
        self.attack_damage = attack_damage


class Consumable(Item):
    def __init__(self, name="consumable item"):
        super().__init__(name)
        self.consume_verb = "consume"

    def _do_consumable_effect(self, player):
        # Override this method!
        Utils.printline(self.stdscr, "It doesn't seem to have any effect...")

    def consume_item(self, player: "Player"):
        assert self in player.inventory
        Utils.printline(self.stdscr, f"You {self.consume_verb} the {self.name}")
        self._do_consumable_effect(player)
        player.inventory.remove(self)


class HealthPotion(Consumable):
    def __init__(self, name="health potion", healing_amount=10, fake=False):
        super().__init__(name)
        self.consume_verb = "drink"
        self.healing_amount = healing_amount
        self.fake = fake  # if fake = True, potion secretly has a negative effect

    def _do_consumable_effect(self, player):
        if not self.fake:
            player.recover_hp(self.healing_amount)
        else:
            player.take_damage(int(self.healing_amount / 2))


class EnergyBiscuit(Consumable):
    def __init__(self, name="energy biscuit", buff_amount=2, fake=False):
        super().__init__(name)
        self.consume_verb = "eat"
        self.buff_amount = buff_amount
        self.fake = fake  # if fake = True, potion secretly has a negative effect

    def _do_consumable_effect(self, player):
        if not self.fake:
            player.recover_hp(self.healing_amount)
        else:
            player.take_damage(int(self.healing_amount / 2))
