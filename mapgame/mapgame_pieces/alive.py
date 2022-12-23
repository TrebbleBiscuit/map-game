import random
import logging
from mapgame_pieces.conversations import Conversation, NoConversation
from mapgame_pieces.utils import color_string

logger = logging.getLogger(__name__)


class LivingThing:
    """Base class for anything that moves around, has hp, etc"""

    def __init__(self):
        self.is_dead = False
        self.max_hp = 20
        self.hp = self.max_hp
        self.x = 0
        self.y = 0
        self.luck = 0
        self.attack_power_base = 1
        self.level = 1

    def _heal_over_time(self):
        if self.hp < self.max_hp:
            self.hp += 1

    @property
    def attack_power(self) -> int:
        return self.attack_power_base

    @property
    def coordinates(self) -> tuple[int, int]:
        return (self.x, self.y)

    def move(self, tile: "Tile", direction: str) -> str | None:
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
        self.conversation: Conversation | None = None

    @property
    def hp_flavor(self):
        ratio = self.hp / self.max_hp
        if ratio == 1:
            return "In perfect health"
        if ratio >= 0.9:
            return "In very good health"
        if ratio >= 0.7:
            return "In good health"
        if ratio >= 0.5:
            return "Slightly injured"
        if ratio >= 0.3:
            return "Significantly injured"
        if ratio >= 0.15:
            return "Critically injured"
        return "On the verge of death"

    @property
    def name_str(self):
        if self.player_attitude > 0:
            color = "friendly_name"
        else:
            color = "hostile_name"
        return color_string(self.name, color)

    @classmethod
    def hostile_from_level(cls, level: int):
        adjs = [
            "spooky",
            "scary",
            "threatening",
            "menacing",
            "dangerous",
            "fearsome",
            "angry",
            "intimidating",
            "wayward",
            "evil",
        ]
        nouns = [
            "slime",
            "skeleton",
            "bad guy",
            "zombie",
            "mugger",
            "scoundrel",
            "villain",
            "miscreant",
            "vagabond",
        ]
        name = random.choice(adjs) + " " + random.choice(nouns)
        max_level = int(level * 1.25 + 2)
        if (
            name in ("evil villain", "wayward vagabond", "spooky skeleton")
            or "dangerous" in name
        ):
            level += 1
        if random.random() < (0.04 * level):
            level += 1
        if random.random() < (0.03 * level):
            level += 1
        if random.random() < (0.02 * level):
            level += 1
        if random.random() < (0.01 * level):
            level += 1
        level = min(level, max_level)
        return cls._generate_from_level(name, level)

    @classmethod
    def friendly_from_level(cls, level: int):
        adj = random.choice(["old", "young", "bald", "spirited", "steadfast", "calm"])
        noun = random.choice(["man", "woman", "person", "human", "wanderer"])
        name = adj + " " + noun
        inst = cls._generate_from_level(name, level)
        inst.player_attitude = 1
        return inst

    @classmethod
    def _generate_from_level(cls, name: str, level: int) -> "NPC":
        logger.info(f"Generating level {level} NPC {name}")
        inst = cls(name)
        inst.level = level
        hp_base = random.randint(15, 20)
        hp_level_multi = random.uniform(4.5, 5.5)
        inst.max_hp = hp_base + int(level * hp_level_multi)
        inst.hp = inst.max_hp
        attack_modifier = random.randint(1, 3) + random.randint(
            0, random.randint(1, level)
        )
        inst.attack_power_base = level + attack_modifier
        inst.xp_reward = int(inst.attack_power_base * 0.9) + int(inst.max_hp / 8)
        # inst.attack_type = random.choice(['ranged', 'melee'])

        return inst

    def will_attack_player(self) -> bool:
        if not self.is_dead and self.player_attitude <= 0:
            return True
        return False

    def _on_time_pass(self, tile):
        # TODO: not implemented
        if (self.x, self.y) in tile.chests:
            logger.debug(f"NPC {self.name} opened a chest at {(self.x, self.y)}")
            tile.chests.remove((self.x, self.y))
            self.max_hp = int(self.max_hp * 1.09)
        elif self.wander:
            if random.random() < 0.5:
                # chance to not wander
                return
            move_options = ["n", "s", "e", "w"]
            random.shuffle(move_options)
            mv_choice = move_options.pop()
            move = None
            while not move:  # try to move until it works
                try:
                    mv_choice = move_options.pop()
                except IndexError:
                    logger.exception(
                        f"NPC at {(self.x, self.y)} could not find a location to wander to!"
                    )
                    return False
                move = self.move(tile, mv_choice)
            return move

    def take_damage(self, dmg: int) -> bool:
        """deal `dmg` damage. return True if hostile is dead"""
        self.hp -= dmg
        if self.hp <= 0:
            self.is_dead = True
        return self.is_dead
