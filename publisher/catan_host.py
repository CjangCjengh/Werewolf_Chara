import random
import math
from publisher.publisher import Publisher
from broker.catan_broker import CatanBroker
from transitions import Machine, State
from transitions.extensions import GraphMachine
from utils.catan_utils import Hexagon, HEX_WIDTH, HEX_HEIGHT, WHITE, FOREST_COLOR, PASTURE_COLOR, GRAIN_COLOR, CLAY_COLOR, HILL_COLOR, DESERT_COLOR, CENTER_X, CENTER_Y, HEX_RADIUS

class CatanHost(Publisher):
    def __init__(self, broker: CatanBroker):
        super().__init__(broker)
        
        self.create_fsm()
        self.settlements = []
        self.roads = []
        self.temp_road_start = None
        self.current_observation = {
            "hexagons": {},
            "settlements": {},
            "roads": {}
        }

        self.correct_click_radius = 800
        
        self.terrains_resources = {
            "Forest": "wood",
            "Pasture": "sheep",
            "Grain": "wheat",
            "Clay": "brick",
            "Hill": "ore",
        }
        self.players = ["red", "blue", "green"]
        self.players_resources = {
            "red": {"wood": 0, "brick": 0, "wheat": 0, "ore": 0, "sheep": 0},
            "blue": {"wood": 0, "brick": 0, "wheat": 0, "ore": 0, "sheep": 0},
            "green": {"wood": 0, "brick": 0, "wheat": 0, "ore": 0, "sheep": 0},
            # "yellow": {"wood": 0, "brick": 0, "wheat": 0, "ore": 0, "sheep": 0}
        }
        self.victory_points = {
            "red": 0,
            "blue": 0,
            "green": 0,
            # "yellow": 0
        }
        
        self.players_development_cards = {
            "red": [],
            "blue": [],
            "green": [],
            # "yellow": []
        }
        
        self.development_cards = ["knight", "victory_point", "road_building", "year_of_plenty", "monopoly"]
        
        
        self.hexes = self.generate_hexagonal_grid(2)
        
        # Store initial hexagon information in the observation dictionary
        for hex in self.hexes:
            self.current_observation["hexagons"][(hex.q, hex.r, hex.s)] = {
                "color": hex.color,
                "position": hex.pixel_coordinates(),
                "number": hex.number
            }
        # self.ports = [
        #     {"position": (2, 0, -2), "resource": "wood"},
        #     {"position": (0, 2, -2), "resource": "brick"},
        #     {"position": (-2, 2, 0), "resource": "wheat"},
        #     {"position": (-2, 0, 2), "resource": "ore"},
        #     {"position": (0, -2, 2), "resource": "sheep"}
        # ]
        
        self.current_player = "red"
        # self.board = [random.choice(["wood", "brick", "wheat", "ore", "sheep", "desert"]) for _ in range(19)]

    
    def create_fsm(self):
        # Define states
        self.states = [
            
            'game_start',
            'initial_phase',
            'place_initial_settlements',
            'place_initial_roads',
            
            'initial_phase_end',
            
            'production_phase',
            'roll_dice',
            
            'production_phase_end',
            
            'trade_n_build_phase',
            'trade',
            'response_to_trade',
            'maritime_trade',
            'build_road',
            'build_settlement',
            'build_city',
            'buy_development_card',
            'play_development_card',
            'trade_n_build_phase_end',
            
            'robbery_phase',
            'move_robber',
            'robbery_phase_end',
            
            'game_end',
            'end'
        ]

        # Initialize the state machine
        self.machine = GraphMachine(model=self, states=self.states, initial='game_start', auto_transitions=False)
        
        self.machine.add_transition(source='game_start', dest='initial_phase', trigger='next')
        
        self.machine.add_transition(source='initial_phase', dest='place_initial_settlements', trigger='next')  
        
        self.machine.add_transition(source='place_initial_settlements', dest='initial_phase_end', trigger='next',conditions= 'initial_phase_end' )
        self.machine.add_transition(source='place_initial_settlements', dest='place_initial_settlements', trigger='next', conditions='settlement_place_incorrect')
        self.machine.add_transition(source='place_initial_settlements', dest='place_initial_roads', trigger='next', after = 'process_settlement_placement')
        
        self.machine.add_transition(source='place_initial_roads', dest='initial_phase_end', trigger='next',conditions= 'initial_phase_end' )
        self.machine.add_transition(source='place_initial_roads', dest='place_initial_roads', trigger='next', conditions = 'road_placement_incorrect')
        self.machine.add_transition(source='place_initial_roads', dest='place_initial_settlements', trigger='next', after = 'process_road_placement')
        
        self.machine.add_transition(source='initial_phase_end', dest='production_phase', trigger='next')
        
        self.machine.add_transition(source='production_phase', dest = 'production_phase', trigger='next', conditions='production_phase_choice_incorrect')
        self.machine.add_transition(source='production_phase', dest='roll_dice', trigger='next', conditions='choose_to_roll_dice')
        self.machine.add_transition(source='production_phase', dest='play_development_card', trigger='next', conditions='choose_to_play_development_card_production_phase')
        
        self.machine.add_transition(source='roll_dice', dest='production_phase_end', trigger='next', after = 'process_roll_dice')
        
        self.machine.add_transition(source='production_phase_end', dest='robbery_phase', trigger='next', conditions='dice_is_7')
        self.machine.add_transition(source='production_phase_end', dest='trade_n_build_phase', trigger='next')
        
        self.machine.add_transition(source='trade_n_build_phase', dest='trade_n_build_phase', trigger='next', conditions='trade_n_build_phase_choice_incorrect')
        self.machine.add_transition(source='trade_n_build_phase', dest='trade', trigger='next', conditions='choose_to_trade')
        self.machine.add_transition(source='trade_n_build_phase', dest='maritime_trade', trigger='next', conditions='choose_to_maritime_trade')
        self.machine.add_transition(source='trade_n_build_phase', dest='build_road', trigger='next', conditions='choose_to_build_road')
        self.machine.add_transition(source='trade_n_build_phase', dest='build_settlement', trigger='next', conditions='choose_to_build_settlement')
        self.machine.add_transition(source='trade_n_build_phase', dest='build_city', trigger='next', conditions='choose_to_build_city')
        self.machine.add_transition(source='trade_n_build_phase', dest='buy_development_card', trigger='next', conditions='choose_to_buy_development_card')
        self.machine.add_transition(source='trade_n_build_phase', dest='play_development_card', trigger='next', conditions='choose_to_play_development_card_tb_phase')
        self.machine.add_transition(source='trade_n_build_phase', dest='trade_n_build_phase_end', trigger='next')
        
        self.machine.add_transition(source='robbery_phase', dest='move_robber', trigger='next')
        
        self.machine.add_transition(source='move_robber', dest='robbery_phase_end', trigger='next')
        
        self.machine.add_transition(source='robbery_phase_end', dest='production_phase', trigger='next')
        
        self.machine.add_transition(source='trade', dest='trade', trigger='next', conditions='trade_format_incorrect')
        
        self.machine.add_transition(source='trade', dest='response_to_trade', trigger='next')
        
        self.machine.add_transition(source='response_to_trade', dest='trade_n_build_phase', trigger='next')
        
        self.machine.add_transition(source='maritime_trade', dest='trade_n_build_phase', trigger='next')
        
        self.machine.add_transition(source='build_road', dest='trade_n_build_phase', trigger='next')
        
        self.machine.add_transition(source='build_settlement', dest='trade_n_build_phase', trigger='next')
        
        self.machine.add_transition(source='build_city', dest='trade_n_build_phase', trigger='next')
        
        self.machine.add_transition(source='buy_development_card', dest='trade_n_build_phase', trigger='next')
        
        self.machine.add_transition(source='play_development_card', dest='play_year_of_plenty', trigger='next')
        self.machine.add_transition(source='play_development_card', dest='play_monopoly', trigger='next')
        self.machine.add_transition(source='play_development_card', dest='play_knight', trigger='next')
        self.machine.add_transition(source='play_development_card', dest='play_victory_point', trigger='next')
        self.machine.add_transition(source='play_development_card', dest='play_road_building', trigger='next')
        
        self.machine.add_transition(source='play_year_of_plenty', dest='trade_n_build_phase', trigger='next')
        self.machine.add_transition(source='play_monopoly', dest='trade_n_build_phase', trigger='next')
        self.machine.add_transition(source='play_knight', dest='trade_n_build_phase', trigger='next')
        self.machine.add_transition(source='play_knight', dest='robbery_phase', trigger='next')
        self.machine.add_transition(source='play_victory_point', dest='trade_n_build_phase', trigger='next')
        self.machine.add_transition(source='play_road_building', dest='trade_n_build_phase', trigger='next')
        
        self.machine.add_transition(source='trade_n_build_phase_end', dest='production_phase', trigger='next')
        self.machine.add_transition(source='trade_n_build_phase_end', dest='game_end', trigger='next')
        
        self.machine.add_transition(source='game_end', dest='end', trigger='next')
        
    
    def publish(self, topic, state: dict):
        image = None
        responses = self.broker.publish(topic, image, state)
        
        self.current_responses = responses  

        self.current_name = responses[0]['name']
        self.current_role = responses[0]['role']
        self.current_topic = responses[0]['topic']
        self.current_answer = responses[0]['answer']
        
        if topic == 'place_initial_settlements' or topic == 'place_initial_roads':
            self.current_chosen_mouse_pos_x = self.current_answer['mouse_pos_x']
            self.current_chosen_mouse_pos_y = self.current_answer['mouse_pos_y']
            self.current_mouse_pos = [self.current_chosen_mouse_pos_x, self.current_chosen_mouse_pos_y]

        elif topic == "production_phase":
            self.current_production_phase_choice = self.current_answer['choice']
            
        elif topic == 'roll_dice':
            
            self.current_dice = self.current_answer['dice']

        elif topic == 'trade_n_build_phase':
            self.current_trade_n_build_phase_choice = self.current_answer['choice']
        
        elif topic == 'trade':
            self.current_trade_give = self.current_answer['give']
            self.current_trade_get = self.current_answer['get']
        
    
    def trade_format_incorrect(self):
        if any(self.current_trade_give[resource] < 0 for resource in self.current_trade_give):
            return True
        
        if any(self.current_trade_get[resource] < 0 for resource in self.current_trade_get):
            return True
        
        # check current player's resources
        for resource in self.current_trade_give:
            if self.players_resources[self.current_player][resource] < self.current_trade_give[resource]:
                return True
        
        return False
        
    def dice_is_7(self):
        return self.current_dice == 7
    
    def choose_to_trade(self):
        return self.current_trade_n_build_phase_choice == "trade"
    
    def choose_to_maritime_trade(self):
        return self.current_trade_n_build_phase_choice == "maritime_trade"
    
    def choose_to_build_road(self):
        return self.current_trade_n_build_phase_choice == "build_road"
    
    def choose_to_build_settlement(self):
        return self.current_trade_n_build_phase_choice == "build_settlement"
    
    def choose_to_build_city(self):
        return self.current_trade_n_build_phase_choice == "build_city"
    
    def choose_to_buy_development_card(self):
        return self.current_trade_n_build_phase_choice == "buy_development_card"
    
    def production_phase_choice_incorrect(self):
        if self.current_production_phase_choice not in ["roll_dice", "play_development_card"]:
            return True
        
        if self.players_development_cards[self.current_player] == []:
            if self.current_production_phase_choice == "play_development_card":
                return True
        
        return False
    
    def trade_n_build_phase_choice_incorrect(self):
        if self.current_trade_n_build_phase_choice not in ["trade", "maritime_trade", "play_development_card", "build_road", "build_settlement", "build_city", "buy_development_card", "pass"]:
            return True
        
        if self.current_trade_n_build_phase_choice == "play_development_card":
            if self.players_development_cards[self.current_player] == []:
                return True
        
        if self.current_trade_n_build_phase_choice == "trade":
            return False
        
        if self.current_trade_n_build_phase_choice == "maritime_trade":
            if all(self.players_resources[self.current_player][resource] < 4 for resource in self.players_resources[self.current_player]):
                return True
        
        if self.current_trade_n_build_phase_choice == "build_road":
            if self.players_resources[self.current_player]["brick"] < 1 or self.players_resources[self.current_player]["wood"] < 1:
                return True
            
        if self.current_trade_n_build_phase_choice == "build_settlement":
            if self.players_resources[self.current_player]["brick"] < 1 or self.players_resources[self.current_player]["wood"] < 1 or self.players_resources[self.current_player]["wheat"] < 1 or self.players_resources[self.current_player]["sheep"] < 1:
                return True
        
        if self.current_trade_n_build_phase_choice == "build_city":
            if self.players_resources[self.current_player]["ore"] < 3 or self.players_resources[self.current_player]["wheat"] < 2:
                return True
        
        if self.current_trade_n_build_phase_choice == "buy_development_card":
            if self.players_resources[self.current_player]["ore"] < 1 or self.players_resources[self.current_player]["wheat"] < 1 or self.players_resources[self.current_player]["sheep"] < 1:
                return True
        
        return False
    

    def generate_hexagonal_grid(self, radius):
        hexes = []
        for q in range(-radius, radius + 1):
            for r in range(-radius, radius + 1):
                s = -q - r
                if abs(s) <= radius:
                    hexes.append(Hexagon(q, r, s))
        
        # Prepare terrains with the appropriate counts
        terrain_counts = {
            "Forest": 4,
            "Pasture": 4,
            "Grain": 4,
            "Clay": 3,
            "Hill": 3,
            "Desert": 1
        }

        terrains = []
        for terrain, count in terrain_counts.items():
            terrains.extend([terrain] * count)
            
        numbers = [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        
        random.shuffle(terrains)
        # self.assign_terrains_to_hexes(hexes, terrains, numbers)
        
        # assign_terrains and number to_hexes
        for hex in hexes:
                
            hex.terrain = terrains.pop()
            hex.color = {
                "Forest": FOREST_COLOR,
                "Pasture": PASTURE_COLOR,
                "Grain": GRAIN_COLOR,
                "Clay": CLAY_COLOR,
                "Hill": HILL_COLOR,
                "Desert": DESERT_COLOR
            }[hex.terrain]
            if hex.terrain != "Desert":
                hex.number = numbers.pop()
            else:
                hex.number = 0
        

        
        return hexes
    
    def closest_edge(self, point):
        nearest_edge = None
        nearest_edge_midpoint = None
        nearest_distance = float('inf')

        for hexagon in self.hexes:
            for edge in hexagon.get_edges():
                midpoint = ((edge[0][0] + edge[1][0]) / 2, (edge[0][1] + edge[1][1]) / 2)
                distance = math.dist(point, midpoint)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_edge = edge
                    nearest_edge_midpoint = midpoint

        return nearest_edge, nearest_edge_midpoint

    def closest_corner(self, point):
        nearest_corner = None
        nearest_distance = float('inf')

        for hexagon in self.hexes:
            for corner in hexagon.get_corners():
                distance = math.dist(point, corner)
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_corner = corner

        return nearest_corner

    
    def initial_phase_end(self):
        print("number of settlements: ", len(self.settlements))
        print("number of roads: ", len(self.roads))
        return len(self.settlements) == 6 and len(self.roads) == 6
    
    
    def choose_to_roll_dice(self):
        return self.current_production_phase_choice == "roll_dice"
    
    def choose_to_play_development_card_production_phase(self):
        return self.current_production_phase_choice == "play_development_card"
    
    def choose_to_play_development_card_tb_phase(self):
        return self.current_trade_n_build_phase_choice == "play_development_card"
    
    
    def process_roll_dice(self):
        
        for hex in self.hexes:
            if hex.number == self.current_dice:
                for settlement in self.settlements:
                    if math.dist(hex.pixel_coordinates(), settlement[0]) < HEX_WIDTH:
                        player = settlement[1]
                        self.players_resources[player][self.terrains_resources[hex.terrain]] += 1
                        
        
    def process_road_placement(self):
        start = self.current_edge[0]
        end = self.current_edge[1]
        self.roads.append((start, end , self.current_player))
        self.current_observation["roads"][(start, end)] = {
            "color": self.current_player,
            "start": start,
            "end": end
        }
        
        # next player turn: sequence 123 321 123 321
        self.broker.unregister_by_name(self.current_player, "place_initial_roads")
        if len(self.roads) < 3:
            self.current_player = self.players[(self.players.index(self.current_player) + 1) % len(self.players)]
        else:
            self.current_player = self.players[(self.players.index(self.current_player) - 1) % len(self.players)]
            
        self.broker.register_by_name(self.current_player, "place_initial_roads")
 
    
    def get_highlight(self, mouse_pos):
        nearest_corner = self.closest_corner(mouse_pos)
        nearest_edge, nearest_edge_midpoint = self.closest_edge(mouse_pos)

        if nearest_corner and nearest_edge:
            corner_distance = math.dist(mouse_pos, nearest_corner)
            edge_distance = math.dist(mouse_pos, nearest_edge_midpoint)

            if corner_distance < edge_distance:
                return nearest_corner, None
            else:
                return None, nearest_edge
        else:
            return nearest_corner, nearest_edge
  
    def calculate_scores(self):
        scores = {player: 0 for player in self.players}
        
        # Points for settlements
        for settlement in self.settlements:
            position, color = settlement
            scores[color] += 1
        
        # Points for roads
        connected_roads = {}
        for road in self.roads:
            start, end, color = road
            # Check if this road connects two settlements
            if any(math.dist(start, s[0]) < self.correct_click_radius for s in self.settlements if s[1] == color) and \
               any(math.dist(end, s[0]) < self.correct_click_radius for s in self.settlements if s[1] == color):
                road_length = math.dist(start, end)
                if color not in connected_roads:
                    connected_roads[color] = []
                connected_roads[color].append(road_length)
        
        # Add road lengths to scores
        for color, roads in connected_roads.items():
            for length in roads:
                scores[color] += int(length // HEX_WIDTH)  # Convert pixel distance to "hex steps"

        return scores
    
    def to_dict(self):
        return {
            "hexagons": self.current_observation["hexagons"],
            "settlements": self.current_observation["settlements"],
            "roads": self.current_observation["roads"],
            "temp_road_start": self.temp_road_start,
            "scores": self.calculate_scores()
        }
    
    def to_dict_flask(self):
        # Convert hexagons
        hexagons_dict = {
            str(key): {
                'position': list(value["position"]),
                'color': value["color"],
                'number': value["number"]
            } for key, value in self.current_observation["hexagons"].items()
        }

        # Convert settlements
        settlements_dict = {
            str(key): {
                'position': list(value["position"]),
                'color': value["color"]
            } for key, value in self.current_observation["settlements"].items()
        }

        # Convert roads
        roads_dict = {
            str(key): {
                'start': list(value["start"]),
                'end': list(value["end"]),
                'color': value["color"]
            } for key, value in self.current_observation["roads"].items()
        }

        return {
            'hexagons': hexagons_dict,
            'settlements': settlements_dict,
            'roads': roads_dict
        }
    
    def get_all_available_corners(self):
        corners = set()
        for hex in self.hexes:
            for corner in hex.get_corners():
                corners.add(corner)
        
        # Remove corners that are already occupied by settlements
        occupied_corners = set(settlement[0] for settlement in self.settlements)
        available_corners = corners - occupied_corners
        
        return list(available_corners)
    
    def settlement_place_incorrect(self):
        self.current_available_corners = self.get_all_available_corners()
        
        # check if the current mouse pos is enough close to any available corner (10 in radius)
        
        self.current_chosen_corner = self.closest_corner(self.current_mouse_pos)
        if math.dist(self.current_mouse_pos, self.current_chosen_corner) > self.correct_click_radius:
            return True
        
        # check if the current chosen corner is enough far from any other settlements, two roads away
        for settlement in self.settlements:
            if math.dist(self.current_chosen_corner, settlement[0]) < int(HEX_WIDTH):
                return True
            
        return False

    
    def road_placement_incorrect(self):
        
        self.current_edge, nearest_edge_midpoint = self.closest_edge(self.current_mouse_pos)
        
        if math.dist(self.current_mouse_pos, nearest_edge_midpoint) > self.correct_click_radius:
            return True
        
        # Check if the road is connected to any settlements of the same color
        for settlement in self.settlements:
            if settlement[1] == self.current_player:
                if math.dist(nearest_edge_midpoint, settlement[0]) < HEX_WIDTH / 2 :
                    return False
        
        # Check if the road is connected to another road of the same color
        
        if "initial" not in self.state: 
            for road in self.roads:
                if road[2] == self.current_player:
                    if (math.dist(nearest_edge_midpoint, road[0]) < HEX_WIDTH / 2 or math.dist(nearest_edge_midpoint, road[1]) < HEX_WIDTH / 2):
                        return False
        
        return True
    
    
    def handle_mouse_click(self, mouse_pos, button, player_color, placing_settlement):
        nearest_corner = self.closest_corner(mouse_pos)
        nearest_edge, nearest_edge_midpoint = self.closest_edge(mouse_pos)

        if nearest_corner and nearest_edge:
            corner_distance = math.dist(mouse_pos, nearest_corner)
            edge_distance = math.dist(mouse_pos, nearest_edge_midpoint)

            if corner_distance < edge_distance:
                # Closer to a corner, consider placing a settlement
                if button == 1 and placing_settlement:  # Left click for settlements
                    # Convert corner position to hex for distance comparison
                    # corner_hex = self.pixel_to_hex(nearest_corner)
                    for settlement in self.settlements:
                        if math.dist(nearest_corner, settlement[0]) < int(HEX_WIDTH):
                            return False
                    # if all(self.hex_distance(corner_hex, self.pixel_to_hex(s[0])) >= 1 for s in self.settlements):
                    self.place_settlement(nearest_corner, player_color)
                    
                    return True
            else:
                # Closer to an edge, consider placing a road
                if button == 1 and not placing_settlement:  # Left click for roads
                    if self.is_connected_road(nearest_edge_midpoint, player_color):
                        # if self.temp_road_start is None:
                        #     self.temp_road_start = nearest_edge
                        # else:
                        self.place_road(nearest_edge[0], nearest_edge[1], player_color)
                        self.temp_road_start = None
                        
                        return True

        return False

    def process_settlement_placement(self):
        
        self.settlements.append((self.current_chosen_corner, self.current_player))
        self.current_observation["settlements"][self.current_chosen_corner] = {
            
            "position": self.current_chosen_corner,
            "color": self.current_player,
            # "color": self.players_colors[self.current_player]
        }
