import sys
import random
from typing import List
import time
import math
from curses import wrapper

from loguru import logger
from colorama import Fore, Back, Style
# print(Fore.RED + 'some red text')
# print(Back.GREEN + 'and with a green background')
# print(Style.DIM + 'and in dim text')
# print(Style.RESET_ALL)
# print('back to normal now')



class Utils:
    @staticmethod
    def color_string(text, color):
        # i.e. `Fore.RED`
        # could also do `Back.RED`
        # or style: `Style.DIM`, `Style.NORMAL`, `Style.BRIGHT`, `Style.RESET_ALL`
        # Fore: BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET.
        return color + text + Style.RESET_ALL

INVALID_INPUT_MSG = Utils.color_string("Input not understood", Style.DIM)

class LivingThing:
    def __init__(self):
        self.is_dead = False
        self.max_hp = 20
        self.hp = self.max_hp
        self.x = 0
        self.y = 0
        self.tile_index = 0
        self.luck = 0
        self.attack_power = 1
    
    def _heal_over_time(self):
        if self.hp < 20:
            print("This living thing is healing over time")
            self.hp += 1

    def move(self, tile, direction):
        if not tile.check_move(self.x, self.y, direction):
            print(f"There is no path {direction}")
        elif direction == "n":
            self.y -= 1
            return True
        elif direction == "s":
            self.y += 1
            return True
        elif direction == "e":
            self.x += 1
            return True
        elif direction == "w":
            self.x -= 1
            return True
        else:
            print("Invalid direction")


class NPC(LivingThing):
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.max_hp = 30
        self.player_attitude = 0  # Attitude towards player - 0 is hostile; higher is better
        self.xp_reward = 0
        self.wander = True
    
    @classmethod
    def generate_from_level(cls, level: int):
        print(f"Generating level {level} enemy")
        name = random.choice(['slime', 'skeleton', 'reanimated corpse'])
        inst = cls(name)
        inst.max_hp = 20 + (level * 5)
        inst.hp = inst.max_hp
        inst.attack_power = 2 + level
        inst.xp_reward = ((level + 1) * 2)
        # inst.attack_type = random.choice(['ranged', 'melee'])
        return inst
    
    def _on_time_pass(self, tile):
        # TODO: not implemented
        if (self.x, self.y) in tile.chests:
            print(f"NPC {self.name} opened a chest at {(self.x, self.y)}")
            tile.chests.remove((self.x, self.y))
        elif self.wander:
            move_options = ['n', 's', 'e', 'w']
            random.shuffle(move_options)
            mv_choice = move_options.pop()
            while not self.move(tile, mv_choice):  # try to move until it works
                logger.debug("NPC tried to move to an invalid location; trying another way...")
                mv_choice = move_options.pop()
            logger.debug(f"{self.name} moved {mv_choice}")

    def take_damage(self, dmg: int):
        self.hp -= dmg
        if self.hp <= 0:
            print("It falls to the ground in a heap, then disappears in a flash of light!")
            self.is_dead = True


class Player(LivingThing):
    def __init__(self):
        super().__init__()
        self.max_hp = 50
        self.hp = self.max_hp
        self.attack_power = 5
        self.inventory = []
        self.money = 0
        self.level = 1
        self.xp = 0
        self.humanity = 100  # out of 100
    
    def grant_xp(self, xp: int):
        print(f"You gained {xp} XP!")
        self.xp += xp
        if self.xp > (50 * self.level):
            lvl_txt = Utils.color_string(f"You have leveled up!", Fore.GREEN)
            print(lvl_txt)
            self.level += 1
            print(f"You are now level {self.level}.")
            ap_txt = Utils.color_string(f"attack power", Style.BRIGHT)
            print(f"You gain 1 {ap_txt}!")
    
    def take_damage(self, dmg: int):
        ouch = random.choice(['Ouch', 'Oof', 'Owwie', 'Yikes', 'Oh no'])
        print(f"{ouch}! You take {dmg} damage!")
        self.hp -= dmg
        if self.hp <= 0:
            print("YOU DIE.")
            print("Not really implemented yet; for now you lose 25 humanity")
            self.humanity -= 25
            if self.humanity <= 0:
                print("humanity <= 0; GAME OVER")
                raise NotImplementedError('Game Over')
    
    def recover_hp(self, rec):
        hp_missing = self.max_hp - self.hp
        if hp_missing < rec:
            rec = hp_missing
        hp_txt = Utils.color_string(str(hp_missing), Fore.GREEN)
        print(f"You recover {hp_txt} HP!")
        self.hp += rec
        print(f"You are now at {self.hp}/{self.max_hp} HP!")

    
    def _heal_over_time(self):
        super()._heal_over_time()
        if self.hp < self.max_hp:
            print("The player heals twice as fast")
            self.hp += 1


class Game:
    def __init__(self):
        self.player = Player()
        self.map = Map(8, 4)
        self.current_tile = self.map.tiles[0]  # self.map.tiles[self.player.tile_index]
        self.time = 0
        # self.x = 0
        # self.y = 0
        self.debug = True
    
    def _progress_time(self):
        self.player._heal_over_time()
        self.time += 1
        self.current_tile.npc._on_time_pass(self.current_tile)
        # if random.randint(0, 9) == 0:
        #     print("Random enemy encounter!!!!")
        #     enemy = NPC.generate_from_level(self.player.tile_index)
        #     print(vars(enemy))
        #     self.combat(enemy)
        #     # uinput = ''
        #     # while uinput.lower() != 'ok':
        #     #     uinput = input("you gotta type ok to continue!")
    
    def combat(self, hostile: NPC):
        in_combat = True
        enemy_text = Utils.color_string(f"{hostile.name}", Fore.RED)
        print(f"Entered combat with a hostile {enemy_text}!")
        while in_combat:
            took_turn = False
            print(f"{enemy_text.title()}: {hostile.hp}/{hostile.max_hp} HP")
            print(f"You: {self.player.hp}/{self.player.max_hp} HP")
            print(f"You can {Utils.color_string('melee', Fore.RED)} attack, or attempt to {Utils.color_string('run', Fore.CYAN)}.")
            try:
                ui = input("> ").lower()
            except KeyboardInterrupt:
                logger.warning("caught KeyboardInterrupt to break out of combat")
                in_combat = False
                continue
            if ui in ['melee', 'm']:
                print("")
                base_dmg = self.player.attack_power
                min_dmg = int((base_dmg * 0.5) + 0.5)
                max_dmg = int(base_dmg * 1.5)
                act_dmg = random.randint(min_dmg, max_dmg)
                print(f"You take a swing at the {enemy_text}!")
                dmg_txt = Utils.color_string(f"{act_dmg} damage", Fore.RED)
                print(f"You do ({min_dmg}-{max_dmg}) {dmg_txt}!")
                hostile.take_damage(act_dmg)
                took_turn = True
            elif ui in ['run', 'r']:
                print("")
                print("You try to run but it doesn't work because it's not implemented yet!")
                took_turn = True
            else:
                print(INVALID_INPUT_MSG)
            if took_turn and in_combat:
                if hostile.hp <= 0:
                    logger.info("Ending combat because enemy is dead")
                    self.player.grant_xp(hostile.xp_reward)
                    in_combat = False
                elif hostile.player_attitude > 0:
                    logger.info("Ending combat because attitude is high")
                    in_combat = False
                else:  # enemy's turn
                    base_dmg = hostile.attack_power
                    min_dmg = int((base_dmg * 0.5) + 0.5)
                    max_dmg = int(base_dmg * 1.5)
                    act_dmg = random.randint(min_dmg, max_dmg)
                    print(f"The {enemy_text} attacks you!")
                    dmg_txt = Utils.color_string(f"{act_dmg} damage", Fore.RED)
                    print(f"It connects for ({min_dmg}-{max_dmg}) {dmg_txt}!")
                    self.player.take_damage(act_dmg)
                    print("")

    def open_chest(self):
        self.current_tile.chests.remove((self.player.x, self.player.y))
        print("You open a chest! There's nothing inside.")
        time.sleep(0.5)

    def portal_into_another_dimension(self, dim_num = None):
        if dim_num is None:
            dim_num = self.player.tile_index + 1
        else:
            pass
        self.player.tile_index = dim_num
        print(f"You portal into dimension #{dim_num}")
        try:
            self.current_tile = self.map.tiles[dim_num]
            print("This dimension already existed")
        except IndexError:
            try:
                self.map.tiles[dim_num-1]
            except IndexError as ex:
                # TODO: autogenerate several map tiles
                raise ex("Can't skip between multiple dimensions")
            Utils.color_string("This dimension needed to be generated", Style.BRIGHT)
            new_tile = Tile(self.map.default_width, self.map.default_height)
            self.map.tiles.append(new_tile)
            self.current_tile = new_tile
            self.player.grant_xp(dim_num * 2)
        finally:
            self.player.x, self.player.y = (0, 0)

    def map_turn(self):
        if (self.player.x, self.player.y) in self.current_tile.rooms:
            room_name = self.current_tile.rooms[(self.player.x, self.player.y)]['name']
        else:
            room_name = None
        ct_npc = self.current_tile.npc  # there's only 1 rn
        if ct_npc.is_dead:
            pass
        elif (ct_npc.x, ct_npc.y) == (self.player.x, self.player.y):
            if ct_npc.player_attitude <= 0:
                self.combat(ct_npc)
            else:
                print(f"There is a {ct_npc.name} in this room!")
                print("Non-hostile NPC encounters not yet implemented.")
        self.current_tile.print_map(self.player.x, self.player.y)
        print("What direction do you want to move? [n/e/s/w] ")
        # don't want any more lines so the map stays the same, use room_flavor_text instead
        # if room_name == 'portal': print("You can leave through the portal in this room.")
        command = input("> ").lower()
        if command in ['n', 'e', 's', 'w']:
            if self.player.move(self.current_tile, command):  # move successful
                print("You move in that direction.")
                print("")
                self.current_tile.explored.add((self.player.x, self.player.y))
                self.current_tile.room_flavor_text((self.player.x, self.player.y))
                if (self.player.x, self.player.y) in self.current_tile.chests:
                    print("There's a chest in this room!!!")
                self._progress_time()
                # TODO: print flavor text for room
        elif room_name == 'portal' and command in ['portal', 'leave', 'take portal', 'p']:
            print("You take the portal into the next dimension...")
            self.portal_into_another_dimension()
            return True  # don't loop
        elif (self.player.x, self.player.y) in self.current_tile.chests and command in ['open', 'chest', 'o']:
            self.open_chest()
        # beyond here lies debug commands
        elif self.debug and command[:2] == 'xp':
            self.player.grant_xp(int(command[2:].strip()))
        elif self.debug and (command[:2] == 'tp' or command[:4] == 'tele'):
            print('teleport to what coordinates? (i.e. "1, 3")')
            print('remember y is inverted')
            tc = input('> ')
            try:
                tc = tuple(int(cv.strip()) for cv in tc.split(','))
            except:
                print("invalid coordinates!")
                return
            if self.current_tile._check_valid_coords(tc):
                self.player.x, self.player.y = tc
                self.current_tile.explored.add((self.player.x, self.player.y))
                print('poof~')
            else:
                print("off-map coordinates not allowed")
        else:
            print(INVALID_INPUT_MSG)

    def play(self):
        while True:
            print("You are in the hub world. Go to 'map' or 'portal' pls.")
            command = input("> ").lower()
            if command == 'map':
                while not self.map_turn():  # loop until it returns True
                    pass # TODO: perhaps pass time here?
                        # rn it'll return if nothing happens which should change
            elif command == 'portal':
                self.portal_into_another_dimension()


class Map:
    def __init__(self, width, height):
        self.default_height = height
        self.default_width = width
        self.tiles = [Tile(width, height)]  # ordered list

# class Coordinate:
#     def __init__(self, x, y):
#         self.x = x
#         self.y = y


class Tile:
    def __init__(self, width: int, height: int):
        self.height = height
        self.width = width
        self.rooms = {
            (0, 0): {
                'name': 'entrance',
                'map_icon': '[e]',
            },  # x, y
            (self.width - 1, 0): {
                'name': 'portal',
                'map_icon': '[p]',

            }  # default for now
        }
        self.chests = set()
        self.spawn_chests()
        self.explored = set([(0, 0)])  # had to put the tuple in a list to get it to turn into a set of tuples
        self.paths = self.generate_paths(self.width * self.height)
        self.all_visible = False
        self.npc = NPC.generate_from_level(1)
        self.npc.x, self.npc.y = self.gen_random_coordinates()
        logger.debug(f"NPC spawned at {(self.npc.x, self.npc.y)}")
    
    # TODO: this should really be "Tile", just part of a larger "Map"
    # TODO: can i make a class method that generates paths? For generating ties

    def gen_random_coordinates(self):
        """ Does not select coordinates with existing rooms or chests """
        valid = False
        while not valid:
            x, y = random.randint(0, self.width), random.randint(0, self.height)
            try:
                # logger.debug(f"Checking if {(x, y)} is in rooms")
                self.rooms[(x, y)]
                continue
            except KeyError:
                # logger.debug("It isn't, let's see if there's already a chest here")
                if (x, y) not in self.chests:
                    valid = True
        return x, y


    def spawn_chests(self):
        n_chests = int(math.sqrt(self.height * self.width))
        while len(self.chests) < n_chests:
            logger.debug("Adding chest")
            self.chests.add(self.gen_random_coordinates())
        pass

    def room_flavor_text(self, room_coords):
        try:
            room_name = self.rooms[room_coords]['name']
            print(f"You stand in the {room_name} room!")
            if room_name == 'portal':
                leave_txt = Utils.color_string(f"leave", Fore.MAGENTA)
                portal_txt = Utils.color_string(f"leave", Style.BRIGHT)
                print(f"You can {leave_txt} through the portal in this room.")
                # TODO: cleared?
        except KeyError:
            # empty room
            print(f"You stand in an empty room.")


    def generate_paths(self, n_paths: int):
        paths = []
        print(f"Generating {n_paths} paths")
        n_attempts = 0
        while len(paths) < n_paths and n_attempts < (4 * n_paths):
            n_attempts += 1
            # choose starting square
            px1 = random.randint(0, self.width - 1)
            py1 = random.randint(0, self.height - 1)
            # print(f"px1, py1 is {px1, py1}")
            if (px1, py1) == (self.width - 1, self.height - 1):
                continue  # can't go anywhere from this corner
            px2 = px1
            py2 = py1
            # randomly add 1 to x or y
            if random.randint(0, 1):
                px2 = px1 + 1
            else:
                py2 = py1 + 1
            if py2 < self.height and px2 < self.width and ((px1, py1), (px2, py2)) not in paths:  # valid path
                paths.append(((px1, py1), (px2, py2)))
        # print(f"Generated {len(paths)} paths in {n_attempts} attempts")
        island_nodes = self._nodes_on_this_island(0, 0, paths)
        while len(island_nodes) < self.width * self.height:
            # print("Missing some connections")
            adj_nodes = self._nodes_with_inaccessible_adjacencies(island_nodes)
            paths.append(self._resolve_inaccessible_tile(island_nodes, adj_nodes))
            island_nodes = self._nodes_on_this_island(0, 0, paths)
        return paths

    def _nodes_on_this_island(self, start_x: int, start_y: int, paths) -> 'List(tuple)':
        coords_to_search = [(start_x, start_y)]
        found_nodes = [(start_x, start_y)]
        while len(coords_to_search) > 0:
            coord_tup = coords_to_search.pop()
            x, y = coord_tup
            for path_tup in paths:
                if (x, y) == path_tup[0]:
                    if path_tup[1] not in found_nodes:
                        # print(f'Identified connected node {path_tup[1]}')
                        found_nodes.append(path_tup[1])
                        coords_to_search.append(path_tup[1])
                elif (x, y) == path_tup[1]:
                    if path_tup[0] not in found_nodes:
                        # print(f'Identified connected node {path_tup[0]}')
                        found_nodes.append(path_tup[0])
                        coords_to_search.append(path_tup[0])
        assert coords_to_search == []
        # print(f"len(found_nodes) is {len(found_nodes)} / {self.width * self.height}")
        return found_nodes

    def _nodes_with_inaccessible_adjacencies(self, island_nodes: 'List(tuple)') -> 'List(tuple)':
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
                if self._check_valid_coords(adj) and adj not in island_nodes:  # has a valid edge canidate
                    relevant_nodes.append(coords)
                    break
        return relevant_nodes

    def _check_valid_coords(self, coords):
        # make sure coordinates don't lead off the map
        if coords[0] >= self.width or coords[1] >= self.height or coords[0] < 0 or coords[1] < 0:
            return False
        return True

    def _resolve_inaccessible_tile(self, island_nodes: list, adj_nodes: list):
        x, y = random.choice(adj_nodes)
        # print(f'Chose random adjacent node at {x}, {y} to resolve path')
        choices = [((x, y - 1), (x, y)), ((x, y), (x, y + 1)), ((x, y), (x + 1, y)), ((x - 1, y), (x, y))]
        valid_choice = False
        while not valid_choice:
            valid_choice = None
            rc = choices.pop(random.randint(0, len(choices) - 1))
            # print(f'len(choices) is {len(choices)}')
            # print(f'rc is {rc}')
            for c in rc: 
                if not self._check_valid_coords(c):
                    valid_choice = False
                    continue  # coordinates can't point off the map
            if valid_choice is False:
                continue
            elif (rc[0] not in island_nodes and rc[1] in island_nodes) or (rc[1] not in island_nodes and rc[0] in island_nodes):
                # exactly one coordinate is to an island node
                # print("this is a valid choice")
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

    def print_map(self, player_x, player_y):
        for y in range(0, self.height):
            # print the yth row of rooms
            for x in range(0, self.width):
                if player_x == x and player_y == y:
                    sys.stdout.write("[u]")  # this is the player's room
                # elif (x, y) in self.rooms:
                #     sys.stdout.write(self.rooms[(x, y)]['map_icon'])
                elif (x, y) in self.explored:
                    if (x, y) in self.rooms:
                        sys.stdout.write(self.rooms[(x, y)]['map_icon'])
                    else:
                        sys.stdout.write("[.]")  # explored, empty
                else:
                    sys.stdout.write("[ ]")  # unexplored room
                # now see whether there's a path to the next room
                c1 = (x, y)
                c2 = (x + 1, y)
                visible = self.all_visible or (c1 in self.explored or c2 in self.explored)
                if (c1, c2) in self.paths and visible:
                    sys.stdout.write("-")
                else:
                    sys.stdout.write(" ")
            # now that we've written the rooms, draw paths to next row
            print()  # newline
            for x in range(0, self.width):
                sys.stdout.write(" ")  # spaces for above room
                c1 = (x, y)
                c2 = (x, y + 1)
                visible = self.all_visible or (c1 in self.explored or c2 in self.explored)
                if (c1, c2) in self.paths and visible:
                    sys.stdout.write("|  ")
                else:
                    sys.stdout.write("   ")
            print()


game = Game()
# game._progress_time()
# game.play()
wrapper(game.play)
