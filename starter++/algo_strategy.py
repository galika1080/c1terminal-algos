import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from heapq import nsmallest


"""

SPD bot

"""

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        # attacking_from = [[0, 13], [27, 13], [1, 12], [26, 12], [2, 11], [25, 11], [3, 10], [24, 10], [4, 9], [23, 9], [5, 8], [22, 8], [6, 7], [21, 7], [7, 6], [20, 6], [8, 5], [19, 5], [9, 4], [18, 4], [10, 3], [17, 3], [11, 2], [16, 2], [12, 1], [15, 1], [13, 0], [14, 0]]

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, FACTORY, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        FACTORY = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        my_seed = random.randint(0,1)
        self.spd_strat_main(game_state, my_seed)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def spd_strat_main(self, game_state, my_seed):
        # build initial groundwork 
        if game_state.turn_number == 0:
            if my_seed == 1:
                self.build_init_defence1(game_state)
            else:
                self.build_init_defence2(game_state)

        if game_state.turn_number % 3 == 1:
            if self.attack_close_scouts_all(game_state) == 1:
                self.clear_w_demolishers(game_state)
        else:
            if game_state.turn_number % 3 == 2:
                self.clear_w_demolishers(game_state)

        if game_state.turn_number % 5 == 0:
            self.my_build_reactive_defense_w_mirror(game_state)
        else:
            self.my_build_reactive_defense(game_state)
            
        if game_state.turn_number == 2 or game_state.turn_number % 4 == 0:
            factory_locations = [[13, 0], [14, 0], [13, 1], [14, 1], [13, 2], [14, 2], [13, 3], [14, 3]]
            spawned = False
            for location in factory_locations:
                if game_state.attempt_spawn(FACTORY, location):
                    spawned = True 
                    break
            if spawned == False:
                for location in factory_locations:
                    if game_state.attempt_upgrade(location):
                        break


    # have one version then a mirrored version too
    def build_init_defence1(self, game_state):
        # Place turrets that attack enemy units
        turret_locations = [[1, 13], [26, 13], [7, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)

        # upgrade central turrets
        game_state.attempt_upgrade([[7, 11], [14, 11]])

        # build walls to divert traffic
        game_state.attempt_spawn(WALL, [[3, 13], [4, 13], [5, 13], [6, 13], [7, 13]])

        # build some Factories to generate more resources
        factory_locations = [[13, 0]]
        game_state.attempt_spawn(FACTORY, factory_locations)

        
        # place interceptors to catch others
        game_state.attempt_spawn(INTERCEPTOR, [[25, 11], [24, 10], [23, 9], [22, 8], [21, 7]])
        game_state.attempt_spawn(INTERCEPTOR,[[21, 7]])

    def build_init_defence2(self, game_state):
        # Place turrets that attack enemy units
        turret_locations = [[1, 13], [26, 13], [13, 11], [20, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)

        # upgrade central turrets
        game_state.attempt_upgrade([[13, 11], [20, 11]])

        # build walls to divert traffic
        game_state.attempt_spawn(WALL, [[20, 13], [21, 13], [22, 13], [23, 13], [24, 13]])

        # build some Factories to generate more resources
        factory_locations = [[14, 0]]
        game_state.attempt_spawn(FACTORY, factory_locations)

        
        # place interceptors to catch others
        game_state.attempt_spawn(INTERCEPTOR, [[2, 11], [3, 10], [4, 9], [5, 8], [6, 7]])
        game_state.attempt_spawn(INTERCEPTOR,[[6, 7]])

    def mirror_cord(self, cord):
        if cord[0] <= 13:
            new_x_cord = 14+(13-cord[0])
            return [new_x_cord, cord[1]]
        else:
            new_x_cord = 13-(cord[0]-14)
            return [new_x_cord, cord[1]]

    # we want to try and attack close to enemy lines when reducing points
    def attack_close_scouts_all(self, game_state):
        # we want to try and attack close to enemy lines when reducing points
        # close point
        close_target = [[4, 18], [23, 18], [3, 17], [24, 17], [2, 16], [25, 16], [1, 15], [26, 15], [0, 14], [27, 14]]
        attacking_from = [[0, 13], [27, 13], [1, 12], [26, 12], [2, 11], [25, 11], [3, 10], [24, 10], [4, 9], [23, 9], [5, 8], [22, 8], [6, 7], [21, 7], [7, 6], [20, 6], [8, 5], [19, 5], [9, 4], [18, 4], [10, 3], [17, 3], [11, 2], [16, 2], [12, 1], [15, 1], [13, 0], [14, 0]]
        best_location, options = self.pick_best_close_attack(game_state, attacking_from, close_target, 15)

        if options == 0:    
            game_state.attempt_spawn(SCOUT, best_location, 1000)
            return 0
        elif options == 2:
            for i in range(100):
                game_state.attempt_spawn(SCOUT, best_location[0])
                game_state.attempt_spawn(SCOUT, best_location[0])
            return 0
        elif options == -1:
            game_state.attempt_spawn(INTERCEPTOR, [[1, 12], [26, 12]], 3)
            return 1

    def clear_w_demolishers(self, game_state):
        # we want to try and attack close to enemy lines when reducing points
        # close point
        close_target = [[4, 18], [23, 18], [3, 17], [24, 17], [2, 16], [25, 16], [1, 15], [26, 15], [0, 14], [27, 14]]
        attacking_from = [[0, 13], [27, 13], [1, 12], [26, 12], [2, 11], [25, 11], [3, 10], [24, 10], [4, 9], [23, 9], [5, 8], [22, 8], [6, 7], [21, 7], [7, 6], [20, 6], [8, 5], [19, 5], [9, 4], [18, 4], [10, 3], [17, 3], [11, 2], [16, 2], [12, 1], [15, 1], [13, 0], [14, 0]]
        best_location, options = self.pick_best_close_attack(game_state, attacking_from, close_target, 15)
    
        game_state.attempt_spawn(DEMOLISHER, best_location, 1000)


    def my_build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        turret_built_for_scored_on_location = []
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            # build_location = [location[0], location[1]+1]

            if location in turret_built_for_scored_on_location:
                break

            added_turret = False
            for x in range(location[0] - 2, location[0]+2):
                for y in range(location[1] - 2, location[1]+2):
                    # gamelib.debug_write("attempting turrets {},{}".format(x,y))
                    if game_state.attempt_spawn(TURRET, [x,y]) == 1:
                        # gamelib.debug_write("ROHAN turrets {},{}".format(x,y))
                        added_turret = True
                        turret_built_for_scored_on_location.append(location)
                        break
                if added_turret:
                    break

            if location[0] <= 13:
                for i in range(location[0] - 2, location[0]+2):
                    if i >=3:
                        game_state.attempt_spawn(WALL, [i, location[1]])
            else:
                for i in range(location[0] - 2, location[0]+2):
                    if i >=10:
                        game_state.attempt_spawn(WALL, [i, location[1]])

    def my_build_reactive_defense_w_mirror(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """

        turret_built_for_scored_on_location = []
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            # build_location = [location[0], location[1]+1]

            if location in turret_built_for_scored_on_location:
                break

            added_turret = False
            for x in range(location[0] - 2, location[0]+2):
                for y in range(location[1] - 2, location[1]+2):
                    # gamelib.debug_write("attempting turrets {},{}".format(x,y))
                    if game_state.attempt_spawn(TURRET, [x,y]) == 1:
                        # gamelib.debug_write("ROHAN turrets {},{}".format(x,y))
                        added_turret = True
                        turret_built_for_scored_on_location.append(location)
                        game_state.attempt_spawn(TURRET, self.mirror_cord([x,y]))
                        break
                if added_turret:
                    break

            if location[0] <= 13:
                for i in range(location[0] - 3, location[0]+3):
                    if i >=3:
                        game_state.attempt_spawn(WALL, [i, location[1]])
            else:
                for i in range(location[0] - 3, location[0]+3):
                    if i >=10:
                        game_state.attempt_spawn(WALL, [i, location[1]])

    # similar to least_damage_spawn_location but with targets
    # returns best point(s) to attack from or -1
    # returns best point and another condition (0, 1, 2) 
    # 0 - Unit should take less than their health's worth of damage
    # 1- Unit could take more than their health's worth of damage
    # 2 - Multiple best paths
    def pick_best_close_attack(self, game_state, location_options, targets, unit_health):
        
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            try:
                if path[-1] in targets:
                    # gamelib.debug_write("ROHAN LOOK {}".format(path))
                    damage = 0
                    for path_location in path:
                        # Get number of enemy turrets that can attack each location and multiply by turret damage
                        damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
                    damages.append(damage)
                else:
                    damages.append(maxsize)
            except:
                damages.append(maxsize)
                continue
        
        if len(damages) == 0:
            # gamelib.debug_write("ROHAN LOOK {} {}".format([], -1))
            return [], -1
        else:
            min_damage = min(damages)
            if min_damage >= unit_health:
                # gamelib.debug_write("ROHAN LOOK {} {}".format(location_options[damages.index(min_damage)]), 1)
                return location_options[damages.index(min_damage)], 1
            else:
                # element of randomness to mess with other team
                if random.randint(0, 50) == 1:
                    # gamelib.debug_write("ROHAN LOOK {} {}".format(location_options[damages.index(nsmallest(2, damages)[-1])], 0)
                    return location_options[damages.index(nsmallest(2, damages)[-1])], 0
                else:
                    if nsmallest(2, damages)[-1] == min_damage:
                        return [location_options[damages.index(min_damage)], location_options[damages.index(nsmallest(2, damages)[-1])]], 2
                    else:
                        return location_options[damages.index(min_damage)], 1


        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]


################################################
    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                self.demolisher_line_strategy(game_state)
            else:
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time
                if game_state.turn_number % 2 == 1:
                    # To simplify we will just check sending them from back left and right
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                    game_state.attempt_spawn(SCOUT, best_location, 1000)

                # Lastly, if we have spare SP, let's build some Factories to generate more resources
                factory_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(FACTORY, factory_locations)

    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[8, 12], [19, 12]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, FACTORY]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()