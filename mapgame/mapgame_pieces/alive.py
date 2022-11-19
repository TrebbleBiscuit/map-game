import random
import logging

logger = logging.getLogger(__name__)


class LivingThing:
    """Base class for anything that moves around, has hp, etc"""

    def __init__(self):
        self.is_dead = False
        self.max_hp = 20
        self.hp = self.max_hp
        self.x = 0
        self.y = 0
        self.tile_index = 1
        self.luck = 0
        self.attack_power = 1

    def _heal_over_time(self):
        if self.hp < 20:
            logger.debug("This living thing is healing over time")
            self.hp += 1

    def move(self, tile: "map.Tile", direction: str) -> str | None:
        """Attempt to move a given direction

        Args:
            tile (map.Tile): Map tile
            direction (str): Direction to move ('n', 'e', 's', or 'w')

        Returns:
            str | None: Name of direction, if the move worked
        """
        if not tile.check_move(self.x, self.y, direction):
            pass  # invalid path
        elif direction == "n":
            self.y -= 1
            return "north"
        elif direction == "s":
            self.y += 1
            return "south"
        elif direction == "e":
            self.x += 1
            return "east"
        elif direction == "w":
            self.x -= 1
            return "west"
        else:
            logger.debug("Invalid direction")


class NPC(LivingThing):
    """NPC wander around, open chests, and engage the player in combat."""

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.max_hp = 30
        self.player_attitude = (
            0  # Attitude towards player - 0 is hostile; higher is better
        )
        self.xp_reward = 0
        self.wander = True
        self.is_dead = False

    @classmethod
    def generate_from_level(cls, level: int):
        logger.info(f"Generating level {level} enemy")
        name = random.choice(["slime", "skeleton", "bad guy"])
        inst = cls(name)
        inst.max_hp = 20 + (level * 5)
        inst.hp = inst.max_hp
        inst.attack_power = 2 + level
        inst.xp_reward = (level + 1) * 2
        # inst.attack_type = random.choice(['ranged', 'melee'])
        return inst

    def will_attack_player(self):
        if not self.is_dead and self.player_attitude <= 0:
            return True
        return False

    def _on_time_pass(self, tile):
        # TODO: not implemented
        if (self.x, self.y) in tile.chests:
            logger.debug(f"NPC {self.name} opened a chest at {(self.x, self.y)}")
            tile.chests.remove((self.x, self.y))
        elif self.wander:
            move_options = ["n", "s", "e", "w"]
            random.shuffle(move_options)
            mv_choice = move_options.pop()
            while not self.move(tile, mv_choice):  # try to move until it works
                try:
                    mv_choice = move_options.pop()
                except IndexError:
                    logger.exception(
                        f"NPC at {(self.x, self.y)} could not find a location to wander to!"
                    )
                    return False
            logger.debug(f"{self.name} moved {mv_choice} to {(self.x, self.y)}")

    def take_damage(self, dmg: int):
        self.hp -= dmg
        if self.hp <= 0:
            logger.debug(
                "It falls to the ground in a heap, then disappears in a flash of light!",
            )
            self.is_dead = True
