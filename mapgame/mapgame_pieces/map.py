import logging
from mapgame_pieces.alive import NPC

logger = logging.getLogger(__name__)


class Tile:
    def __init__(self, wm, width: int, height: int):
        self.wm = wm
        self.height = height
        self.width = width
        self.rooms = {
            (0, 0): {
                "name": "entrance",
                "map_icon": "[e]",
            },  # x, y
            (self.width - 1, 0): {
                "name": "portal",
                "map_icon": "[p]",
            },  # default for now
        }
        self.chests = set()
        self.spawn_chests()
        self.explored = set(
            [(0, 0)]
        )  # had to put the tuple in a list to get it to turn into a set of tuples
        self.paths = self.generate_paths(self.width * self.height)
        self.all_visible = False
        self.npc = NPC.generate_from_level(self.wm, 1)
        self.npc.x, self.npc.y = self.gen_random_coordinates()
        logger.debug(f"NPC spawned at {(self.npc.x, self.npc.y)}")

    def print_map(self, player_x, player_y):
        mapstr: str = "\n"
        for y in range(0, self.height):
            # print the yth row of rooms
            for x in range(0, self.width):
                if player_x == x and player_y == y:
                    mapstr += "[u]"  # this is the player's room
                elif (x, y) in self.explored:
                    if (x, y) in self.rooms:
                        mapstr += self.rooms[(x, y)]["map_icon"]
                    else:
                        mapstr += "[.]"  # explored, empty
                else:
                    mapstr += "[ ]"  # unexplored room
                # now see whether there's a path to the next room
                c1 = (x, y)
                c2 = (x + 1, y)
                visible = self.all_visible or (
                    c1 in self.explored or c2 in self.explored
                )
                if (c1, c2) in self.paths and visible:
                    mapstr += "-"
                else:
                    mapstr += " "
            # now that we've written the rooms, draw paths to next row
            mapstr += "\n"  # newline
            for x in range(0, self.width):
                mapstr += " "  # spaces for above room
                c1 = (x, y)
                c2 = (x, y + 1)
                visible = self.all_visible or (
                    c1 in self.explored or c2 in self.explored
                )
                if (c1, c2) in self.paths and visible:
                    mapstr += "|  "
                else:
                    # self.wm.mapscr.addstr("   ")
                    mapstr += "   "
            mapstr += "\n"
        print(mapstr)


class Map:
    def __init__(self, wm, width, height):
        self.wm = wm
        self.default_height = height
        self.default_width = width
        self.tiles = [Tile(self.wm, width, height)]  # ordered list

    def get_tile(self, tile_num: int) -> Tile:
        """Get this tile number; create it if it doesn't exist
        Note tile numbers are indexed starting from 1
        """
        try:
            return self.tiles[tile_num - 1]
        except IndexError as ex:
            # need to create one or more tiles
            num_to_create = tile_num - len(self.tiles)
            logger.debug("Creating %s new dimension(s)", num_to_create)
            for x in range(num_to_create):
                self.tiles.append(
                    Tile(self.wm, self.default_width, self.default_height)
                )
            return self.tiles[tile_num - 1]
