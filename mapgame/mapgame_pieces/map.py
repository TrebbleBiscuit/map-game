import logging
from mapgame_pieces.alive import NPC
import math
import random
from dataclasses import dataclass

logger = logging.getLogger(__name__)
BASE_NPCS_PER_TILE = 7


@dataclass
class Room:
    x: int
    y: int
    name: str
    map_icon: str


RoomMap = dict[tuple[int, int], Room]


class Tile:
    def __init__(self, gui, width: int, height: int, level: int):
        self.gui = gui
        self.height = height
        self.width = width
        self.chests = set()
        self.rooms: RoomMap = self._starting_rooms()
        self.add_room(room_name="medbay", map_icon="[m]")
        # {
        #     (0, 0): {
        #         "name": "entrance",
        #         "map_icon": "[e]",
        #     },  # x, y
        #     (self.width - 1, 0): {
        #         "name": "portal",
        #         "map_icon": "[p]",
        #     },  # default for now
        # }
        self.spawn_chests()
        self.explored: set[tuple[int, int]] = set(
            [(0, 0)]
        )  # had to put the tuple in a list to get it to turn into a set of tuples
        self.paths = self.generate_paths(self.width * self.height)
        self.all_visible = False
        self.add_hostile_npcs_to_tile(level)
        self.add_friendly_npc_to_tile(level)

    def add_hostile_npcs_to_tile(self, level: int):
        number_of_npcs = BASE_NPCS_PER_TILE + min(int(level / 6), 3)
        self.npcs = [NPC.generate_from_level(level) for x in range(number_of_npcs)]
        for npc in self.npcs:
            npc.x, npc.y = self.gen_random_coordinates()
            logger.debug(f"NPC spawned at {(npc.x, npc.y)}")

    def add_friendly_npc_to_tile(self, level: int):
        adjs = ["old", "young", "bald", "wandering"]
        nouns = ["man", "woman", "person", "human", "adventurer"]
        f_npc = NPC.generate_from_level(level + 2)
        f_npc.name = random.choice(adjs) + " " + random.choice(nouns)
        f_npc.player_attitude = 1
        f_npc.x, f_npc.y = self.gen_random_coordinates()
        self.npcs.append(f_npc)

    def _starting_rooms(self) -> RoomMap:
        rooms = {}
        rooms[(0, 0)] = Room(x=0, y=0, name="entrance", map_icon="[e]")
        # portal always at fixed X but vary the Y
        portal_y = random.randint(0, self.height - 1)
        rooms[(self.width - 1, portal_y)] = Room(
            x=self.width - 1, y=portal_y, name="portal", map_icon="[p]"
        )
        return rooms

    def add_room(self, room_name: str, map_icon: str):
        cx, cy = self.gen_random_coordinates()
        self.rooms[(cx, cy)] = Room(x=cx, y=cy, name=room_name, map_icon=map_icon)

    def gen_random_coordinates(self) -> tuple[int, int]:
        """Does not select coordinates with existing rooms or chests"""
        while True:
            x, y = random.randint(0, self.width - 1), random.randint(0, self.height - 1)
            try:
                # logger.debug(f"Checking if {(x, y)} is in rooms")
                self.rooms[(x, y)]
                continue
            except KeyError:
                # logger.debug("It isn't, let's see if there's already a chest here")
                if (x, y) not in self.chests:
                    return x, y

    def spawn_chests(self):
        n_chests = int(math.sqrt(self.height * self.width))
        while len(self.chests) < n_chests:
            logger.debug("Adding chest")
            self.chests.add(self.gen_random_coordinates())
        pass

    def room_flavor_text(self, room_coords):
        try:
            room_name = self.rooms[room_coords].name
            self.gui.main_out.add_line(f"You stand in the {room_name} room!")
            if room_name == "portal":
                # leave_txt = Utils.color_string(f"leave", Fore.MAGENTA)
                leave_txt = "leave"
                # portal_txt = Utils.color_string(f"leave", Style.BRIGHT)
                self.gui.main_out.add_line(
                    f"You can {leave_txt} through the portal in this room.",
                )
                # TODO: cleared?
            elif room_name == "medbay":
                self.gui.main_out.add_line(
                    f"You can 'heal' in the medbay here.",
                )
        except KeyError:
            # empty room
            self.gui.main_out.add_line(f"You stand in an empty room.")

    def generate_paths(self, n_paths: int):
        paths = []
        logger.info(f"Generating {n_paths} paths")
        n_attempts = 0
        while len(paths) < n_paths and n_attempts < (4 * n_paths):
            n_attempts += 1
            # choose starting square
            px1 = random.randint(0, self.width - 1)
            py1 = random.randint(0, self.height - 1)
            # Utils.printline(self.wm.stdscr, f"px1, py1 is {px1, py1}")
            if (px1, py1) == (self.width - 1, self.height - 1):
                continue  # can't go anywhere from this corner
            px2 = px1
            py2 = py1
            # randomly add 1 to x or y
            if random.randint(0, 1):
                px2 = px1 + 1
            else:
                py2 = py1 + 1
            if (
                py2 < self.height
                and px2 < self.width
                and ((px1, py1), (px2, py2)) not in paths
            ):  # valid path
                paths.append(((px1, py1), (px2, py2)))
        # Utils.printline(self.wm.stdscr, f"Generated {len(paths)} paths in {n_attempts} attempts")
        island_nodes = self._nodes_on_this_island(0, 0, paths)
        while len(island_nodes) < self.width * self.height:
            # Utils.printline(self.wm.stdscr, "Missing some connections")
            adj_nodes = self._nodes_with_inaccessible_adjacencies(island_nodes)
            paths.append(self._resolve_inaccessible_tile(island_nodes, adj_nodes))
            island_nodes = self._nodes_on_this_island(0, 0, paths)
        return paths

    def _nodes_on_this_island(self, start_x: int, start_y: int, paths) -> list[tuple]:
        coords_to_search = [(start_x, start_y)]
        found_nodes = [(start_x, start_y)]
        while len(coords_to_search) > 0:
            coord_tup = coords_to_search.pop()
            x, y = coord_tup
            for path_tup in paths:
                if (x, y) == path_tup[0]:
                    if path_tup[1] not in found_nodes:
                        # Utils.printline(self.wm.stdscr, f'Identified connected node {path_tup[1]}')
                        found_nodes.append(path_tup[1])
                        coords_to_search.append(path_tup[1])
                elif (x, y) == path_tup[1]:
                    if path_tup[0] not in found_nodes:
                        # Utils.printline(self.wm.stdscr, f'Identified connected node {path_tup[0]}')
                        found_nodes.append(path_tup[0])
                        coords_to_search.append(path_tup[0])
        assert coords_to_search == []
        # Utils.printline(self.wm.stdscr, f"len(found_nodes) is {len(found_nodes)} / {self.width * self.height}")
        return found_nodes

    def _nodes_with_inaccessible_adjacencies(
        self, island_nodes: list[tuple]
    ) -> list[tuple]:
        # returns a list of node coordinate tuples
        relevant_nodes = []
        for coords in island_nodes:
            x, y = coords

            # for direction in ['n', 'e', 's', 'w']:
            #     path = self._path_when_moving(x, y, direction)
            #     if path in self.paths:
            #         pass

            adjs = [(x + 1, y), (x, y + 1), (x - 1, y), (x, y - 1)]
            for adj in adjs:
                # if adj[0] > self.width or adj[1] > self.height or adj[0] < 0 or adj[1] < 0:
                #     continue  # invalid coordinates
                if (
                    self._check_valid_coords(adj) and adj not in island_nodes
                ):  # has a valid edge canidate
                    relevant_nodes.append(coords)
                    break
        return relevant_nodes

    def _check_valid_coords(self, coords):
        # make sure coordinates don't lead off the map
        if (
            coords[0] >= self.width
            or coords[1] >= self.height
            or coords[0] < 0
            or coords[1] < 0
        ):
            return False
        return True

    def _resolve_inaccessible_tile(self, island_nodes: list, adj_nodes: list):
        x, y = random.choice(adj_nodes)
        # Utils.printline(self.stdscr, f'Chose random adjacent node at {x}, {y} to resolve path')
        choices = [
            ((x, y - 1), (x, y)),
            ((x, y), (x, y + 1)),
            ((x, y), (x + 1, y)),
            ((x - 1, y), (x, y)),
        ]
        valid_choice = False
        while not valid_choice:
            valid_choice = None
            rc = choices.pop(random.randint(0, len(choices) - 1))
            # Utils.printline(self.stdscr, f'len(choices) is {len(choices)}')
            # Utils.printline(self.stdscr, f'rc is {rc}')
            for c in rc:
                if not self._check_valid_coords(c):
                    valid_choice = False
                    continue  # coordinates can't point off the map
            if valid_choice is False:
                continue
            elif (rc[0] not in island_nodes and rc[1] in island_nodes) or (
                rc[1] not in island_nodes and rc[0] in island_nodes
            ):
                # exactly one coordinate is to an island node
                # Utils.printline(self.stdscr, "this is a valid choice")
                valid_choice = rc
        return valid_choice

    def _path_when_moving(self, x: int, y: int, direction):
        if direction == "n":
            return ((x, y - 1), (x, y))
        elif direction == "s":
            return ((x, y), (x, y + 1))
        elif direction == "e":
            return ((x, y), (x + 1, y))
        elif direction == "w":
            return ((x - 1, y), (x, y))

    def check_move(self, x, y, direction):
        return self._path_when_moving(x, y, direction) in self.paths

    def get_map(self, player_x, player_y):
        mapstr: str = f"You're at {player_x},{player_y}\n\n"
        for y in range(0, self.height):
            # print the yth row of rooms
            for x in range(0, self.width):
                if player_x == x and player_y == y:
                    mapstr += "[x]"  # this is the player's room
                elif (x, y) in self.explored:
                    if (x, y) in self.rooms:
                        mapstr += self.rooms[(x, y)].map_icon
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
                    mapstr += "   "
            mapstr += "\n"
        return mapstr


class Map:
    def __init__(self, gui, width, height):
        self.default_height = height
        self.default_width = width
        self.gui = gui
        self.tiles = [self.get_tile(1)]  # ordered list

    def get_tile(self, level: int) -> Tile:
        """Generate a tile with NPCs at a particular level"""
        return Tile(
            self.gui,
            self.default_width,
            self.default_height,
            level=level,
        )

    def generate_each_dimension(self, tile_num: int) -> Tile:
        """OLD get_tile() DEPRECIATED when i realized it would be a pain to save/load this
        Get this tile number; create it if it doesn't exist
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
                    Tile(
                        self.gui,
                        self.default_width,
                        self.default_height,
                        level=tile_num,
                    )
                )
            return self.tiles[tile_num - 1]
