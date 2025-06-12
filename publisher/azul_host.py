
from transitions.extensions import GraphMachine
from publisher.publisher import Publisher
from broker.azul_broker import AzulGameBroker
import random
import pygame
import os

class AzulGameHost(Publisher):

    def __init__(self, config):
        self.debug = False
        self.broker = AzulGameBroker(config)
        
        self.config = config
        self.log_file = os.path.join(config['log_directory'], f"game.log")
        
        self.create_fsm()
        
        self.factories = {
            "tile_count": 20,
            "colors": ['green', 'purple', 'yellow', 'blue', 'red'],
            "tile_bag": random.sample(['green', 'purple', 'yellow', 'blue', 'red'] * 20, 100),
            "factory": [[] for _ in range(5)],
            "table_center": [],
        }
        self.boards = {
            'player1': {
                "score": 0,
                "pattern_lines": [[] for _ in range(5)],
                "floorline": [], 
                "num_rows": 5, 
                "floorline": [],
                "wall": [['' for _ in range(5)] for _ in range(5)],  # 5x5 grid
            }, 
            'player2': {
                "score": 0,
                "pattern_lines": [[] for _ in range(5)],
                "floorline": [], 
                "num_rows": 5, 
                "floorline": [],
                "wall": [['' for _ in range(5)] for _ in range(5)],  # 5x5 grid
            }}
        
        self.first_to_fetch = 'player1'  # First player to fetch in the first round
        self.log = []
        self.silent = False
        self.floorline_punishment = [-1, -1, -2, -2, -2, -3, -3]
        self.pattern_line_capacities = [1, 2, 3, 4, 5]
        self.wall_pattern = [
                ['green', 'yellow', 'red', 'purple', 'blue'],
                ['blue', 'green', 'yellow', 'red', 'purple'],
                ['purple', 'blue', 'green', 'yellow', 'red'],
                ['red', 'purple', 'blue', 'green', 'yellow'],
                ['yellow', 'red', 'purple', 'blue', 'green']
            ]


        # Evaluation metrics
        self.p1_total_attempts = 0
        self.p1_valid_attempts = 0
        self.p1_game_valid_attempts = 0
        self.p2_total_attempts = 0
        self.p2_valid_attempts = 0
        self.p2_game_valid_attempts = 0
        
        
        self.fail_case = None
        self.fail_cases = []
        

    def create_fsm(self):
        
        # Define the states
        self.finite_states = [
            'start',
            'p1_turn',
            'p1_turn_end',
            'p2_turn',
            'p2_turn_end',
            'round_start',
            'round_end',
            'score_count',
            'end'
        ]
        
        # Initialize the state machine
        self.machine = GraphMachine(model=self, states=self.finite_states, initial='start', show_conditions=True)
        
        self.machine.add_transition(source='start', dest='round_start', trigger='game_start') 
        
        self.machine.add_transition(source='round_start', dest='p1_turn', trigger='new_round', conditions = 'player1_first', after = 'process_distribute_tiles')
        self.machine.add_transition(source='round_start', dest='p2_turn', trigger='new_round', conditions = 'player2_first', after = 'process_distribute_tiles')
        
        self.machine.add_transition(source='p1_turn', dest='p1_turn', trigger='p1_done', conditions = 'action_format_incorrect') 
        self.machine.add_transition(source='p1_turn', dest='p1_turn_end', trigger='p1_done', after = 'process_player_action') 

        self.machine.add_transition(source='p1_turn_end', dest='score_count', trigger='p1_done', conditions= 'any_row_complete')
        self.machine.add_transition(source='p1_turn_end', dest='score_count', trigger='p1_done', conditions = 'no_tile_anywhere')
        self.machine.add_transition(source='p1_turn_end', dest='round_end', trigger='p1_done', conditions= 'no_tile_in_factories')
        self.machine.add_transition(source='p1_turn_end', dest='p2_turn', trigger='p1_done')
        
        self.machine.add_transition(source='p2_turn', dest='p2_turn', trigger='p2_done', conditions = 'action_format_incorrect')
        self.machine.add_transition(source='p2_turn', dest='p2_turn_end', trigger='p2_done', after = 'process_player_action')
        
        self.machine.add_transition(source='p2_turn_end', dest='score_count', trigger='p2_done', conditions= 'any_row_complete')
        self.machine.add_transition(source='p2_turn_end', dest='score_count', trigger='p2_done', conditions = 'no_tile_anywhere')
        self.machine.add_transition(source='p2_turn_end', dest='round_end', trigger='p2_done', conditions= 'no_tile_in_factories')
        self.machine.add_transition(source='p2_turn_end', dest='p1_turn', trigger='p2_done')
        
        self.machine.add_transition(source='round_end', dest='round_start', trigger='round_end', conditions= 'tile_in_bag', after = 'process_move_pattern')
        self.machine.add_transition(source='round_end', dest='score_count', trigger='round_end', conditions= 'any_row_complete', after = 'process_move_pattern')
        self.machine.add_transition(source='round_end', dest='score_count', trigger='round_end', conditions= 'no_tile_in_bag', after = 'process_move_pattern')
        
        self.machine.add_transition(source='score_count', dest='end', trigger='game_end', after = 'process_score_count') 
    
    def publish(self, topic, state: dict):
        image = None
        responses = self.broker.publish(topic, topic, image, state)
        
        self.current_responses = responses  
        self.logging(self.current_responses)


        self.current_player = responses[0]['name']
        self.current_topic = responses[0]['topic']  
        self.current_role = responses[0]['role']
        if topic in ['p1_turn', 'p2_turn']:
            
            
            self.current_chosen_factory_index = int(self.current_responses[0]['table'])
            self.current_topic = self.current_responses[0]['topic']
            self.current_chosen_color = self.current_responses[0]['color']
            self.current_chosen_row = int(self.current_responses[0]['row'])
            self.current_player_attempts = int(self.current_responses[0]['attempts'])


    
    def action_format_incorrect(self):
        
        if self.current_chosen_factory_index < 0 or self.current_chosen_factory_index > 5:
            
            # import ipdb; ipdb.set_trace()
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "factory_index_out_of_range"
            self.fail_cases.append(self.fail_case)
            return True
        
        if self.current_chosen_row < 1 or self.current_chosen_row > 5:
            return True
        
        if self.current_chosen_color not in self.factories['colors'] and self.current_chosen_color != "ONE":
            return True
        
        if self.current_chosen_factory_index > 0:
            if self.current_chosen_color not in self.factories['factory'][self.current_chosen_factory_index-1]:
                return True
        else:
            if self.current_chosen_color not in self.factories['table_center']:
                return True
        
        return False
            

    def any_row_complete(self):
        
        for p in ['player1', 'player2']:
            for i in range(5):
                # if the wall pattern is full
                if all(tile != '' for tile in self.boards[p]['wall'][i]):
                    return True
        
        return False

    
    def no_tile_anywhere(self):
        return self.no_tile_in_bag() and self.no_tile_in_factories()
    
    def no_tile_in_factories(self):
        
        if  all(len(factory) == 0 for factory in self.factories['factory']) and len(self.factories['table_center']) == 0:
            return True
        
        return False
        
            

    
    def player1_first(self):
        return self.first_to_fetch == 'player1'
    
    def player2_first(self):
        return self.first_to_fetch == 'player2'
    
    
    
    # def logging(self, content):
    #     if not self.silent:
    #         indented_content = "    " + content.replace("\n", "\n    ")
    #         print("\033[91m" + indented_content + "\033[0m")

    #     self.log.append(content)

    def logging(self, content):
        self.log.append(content)
        # print(content)
            
        with open(self.log_file, "w") as f:
            # save
            for i in self.log:
                # print(i)
                f.write(str(i) + "\n")
                

    def process_distribute_tiles(self):
        
        
        self.factories["table_center"] = ['ONE']  # Start with the 'ONE' tile
        for i in range(5):
            for _ in range(4):
                if self.factories['tile_bag']:
                    tile = self.factories['tile_bag'].pop()
                    self.factories['factory'][i].append(tile)
                    # log.append({"state": "round_start", "action": "add_tile", "factory": i + 1, "tile": tile, "remaining_tiles_in_bag": len(self.factory['tile_bag'])})
                else:
                    # log.append({"action": "stop_distribution", "reason": "tile_bag_empty"})
                    break  # Stop if the tile bag is empty
        
        # log.append({'state': 'round_start', "action": "end_distribution", "factory": [len(sf) for sf in self.factory['factory']]})
        
        # return log

    def tile_in_bag(self):
        """Check if there are tiles left in the tile bag."""
        return len(self.factories['tile_bag']) > 0

    def no_tile_in_bag(self):
        """Check if there are no tiles left in the tile bag."""
        return not self.tile_in_bag()

    def get_tile(self, factory_num, color):
        
        if factory_num == 0:
            retrieved_tiles = [tile for tile in self.factories['table_center'] if tile == color]
            self.factories['table_center'] = [tile for tile in self.factories['table_center'] if tile != color]
            if "ONE" in self.factories['table_center']:
                retrieved_tiles.append("ONE")
                self.factories['table_center'].remove("ONE")
                self.first_to_fetch = self.current_role
        
        else:
            factory = self.factories['factory'][factory_num - 1]
            retrieved_tiles = [tile for tile in factory if tile == color]
            remaining_tiles = [tile for tile in factory if tile != color]

            self.factories['table_center'].extend(remaining_tiles)
            self.factories['factory'][factory_num - 1] = []

        return retrieved_tiles

    def add_tile_to_pattern_lines(self, player_index, row_index, tile):
        
        
        pattern_lines = self.boards[player_index]['pattern_lines']
        current_row = pattern_lines[row_index]
        capacity = self.pattern_line_capacities[row_index]

        if current_row == []: 
            pattern_lines[row_index].append(tile)
        else:
            if current_row[0] == tile and tile not in self.boards[player_index]['wall'][row_index]:
                if len(current_row) < capacity:
                    pattern_lines[row_index].append(tile)
                else:
                    
                    self.boards[player_index]['floorline'].append(tile)
                    self.logging(f"第{row_index+1}行满了,'{tile}'放到floorline.")
            else:
                
                self.boards[player_index]['floorline'].append(tile)
                self.logging(f"'{tile}'不符合第{row_index+1}行的颜色,因此被放置在floorline.")


    def calculate_additional_points(self, wall, row, col):
        points = 0
        for c in range(col, -1, -1):
            if wall[row][c] != '':
                points += 1
            else:
                break
        for c in range(col, len(wall)):
            if wall[row][c] != '':
                points += 1
            else:
                break
        for r in range(row, -1, -1):
            if wall[r][col] != '':
                points += 1
            else:
                break
        for r in range(row, len(wall)):
            if wall[r][col] != '':
                points += 1
            else:
                break
        return points

    def process_score_count(self):
        
        for p in ['player1', 'player2']:
            for line in range(5):
                if all(tile != '' for tile in self.boards[p]['wall'][line]): # 集齐一行
                    self.boards[p]['score'] += 2
                if all(self.boards[p]['wall'][j][line] != '' for j in range(5)): # 集齐一列
                    self.boards[p]['score'] += 7
                # if all(self.boards[p]['wall'][j][line] == self.boards[p]['wall'][line][j] for j in range(5)): # 集齐某个颜色所有的tile
                #     self.boards[p]['score'] += 10
        
        # count all the tile
        self.player_tiles = {'player1': [], 'player2': []}
        for p in ['player1', 'player2']:
            for line in range(5):
                for tile in self.boards[p]['wall'][line]:
                    if tile != '':
                        self.player_tiles[p].append(tile)
        
        for player, tiles in self.player_tiles.items():
            for color in self.factories['colors']:
                if tiles.count(color) == 5: # 集齐某个颜色所有的tile
                    self.boards[player]['score'] += 10
        
        # self.log.append({"state": "score_count", "action": "process_score_count", "score": [self.players_boards['player1']['score'], self.players_boards['player2']['score']]})
        # self.log.append({"state": "end", "winner": 1 if self.players_boards['player1']['score'] > self.players_boards['player2']['score'] else 2})
        # self.log.append({"state": "end", "p1_total_attempts": self.p1_total_attempts, "p1_valid_attempts": self.p1_valid_attempts, "p1_game_valid_attempts": self.p1_game_valid_attempts})
        # self.log.append({"state": "end", "p2_total_attempts": self.p2_total_attempts, "p2_valid_attempts": self.p2_valid_attempts, "p2_game_valid_attempts": self.p2_game_valid_attempts})
        
    def process_move_pattern(self):
        # """Move tiles from pattern lines to the wall at the end of the round and apply penalties."""
        # self.log.append({"state": "round_end", "action": "movePattern2wall"})
        
        for player in ['player1', 'player2']:
            for line in range(5):
                # Check if the row in the pattern lines is full
                if len(self.boards[player]['pattern_lines'][line]) == self.pattern_line_capacities[line]:
                    
                    # move_to_wall
                    tile = self.boards[player]['pattern_lines'][line][0]
                    where_to_move = self.wall_pattern[line].index(tile)
                    if self.boards[player]['wall'][line][where_to_move] == '':
                        self.boards[player]['wall'][line][where_to_move] = tile
                        self.boards[player]['score'] += 1
                        
                        self.boards[player]['score'] += self.calculate_additional_points(self.boards[player]['wall'], line, where_to_move)
                        
                    self.boards[player]['pattern_lines'][line] = []
                    
                    self.logging(f"玩家{player}的第{line + 1}行满了, 所以移动到wall")

        # Apply penalties and clear floorline
        for player in ['player1', 'player2']:
            floorline = self.boards[player]['floorline']
            if len(floorline) > 0:
                self.logging(f"玩家{player}的floorline: {floorline}")
                self.boards[player]['score'] += sum(self.floorline_punishment[:len(floorline)])
                self.boards[player]['floorline'] = []

        # self.logging("movePattern2wall并计算分数")
        # self.logging("move2wall后玩家1的patternlines: ")
        # self.logging(str(self.boards['player1']))
        # self.logging("move2wall后玩家2的patternlines: ")
        # self.logging(str(self.boards['player2']))
  
    def process_player_action(self):
        
        self.logging(f"玩家{self.current_player}选择了第{self.current_chosen_factory_index}个工厂, 颜色为{self.current_chosen_color}, 放置在第{self.current_chosen_row}行, 尝试次数为{self.current_player_attempts}")
        
        if self.current_topic == 'p1_turn':
            self.p1_total_attempts += self.current_player_attempts
            self.p1_valid_attempts += 1
        elif self.current_topic == 'p2_turn':
            self.p2_total_attempts += self.current_player_attempts
            self.p2_valid_attempts += 1
            
        # get tile
        retrieved_tiles = self.get_tile(self.current_chosen_factory_index, self.current_chosen_color)
        
        # put tile
        for tile in retrieved_tiles:
            if tile == "ONE":
                self.boards[self.current_role]['floorline'] =  [tile] + self.boards[self.current_role]['floorline']
            else:
                # self.add_tile_to_pattern_lines(self.current_role, self.current_chosen_row-1, tile)
                
                pattern_lines = self.boards[self.current_role]['pattern_lines']
                current_row = pattern_lines[self.current_chosen_row-1]
                capacity = self.pattern_line_capacities[self.current_chosen_row-1]

                if current_row == []: 
                    pattern_lines[self.current_chosen_row-1].append(tile)
                else:
                    if current_row[0] == tile and tile not in self.boards[self.current_role]['wall'][self.current_chosen_row-1]:
                        if len(current_row) < capacity:
                            pattern_lines[self.current_chosen_row-1].append(tile)
                        else:
                            
                            self.boards[self.current_role]['floorline'].append(tile)
                            self.logging(f"第{self.current_chosen_row-1+1}行满了,'{tile}'放到floorline.")
                    else:
                        
                        self.boards[self.current_role]['floorline'].append(tile)
                        self.logging(f"'{tile}'不符合第{self.current_chosen_row}行的颜色,因此被放置在floorline.")

            # if self.boards[self.current_role]['pattern_lines'][self.current_chosen_row-1] == []:
            #     self.boards[self.current_role]['pattern_lines'][self.current_chosen_row-1].append(tile)

    def to_dict(self):
        factory_state = {
            "Factories": {f"Factory {i + 1}": factory for i, factory in enumerate(self.factories['factory'])},
            "TableCenter": self.factories['table_center'].copy()
        }

        players_boards_state = {}
        for player_name, board in self.boards.items():
            player_state = {
                "score": board['score'],
                "pattern_lines": board['pattern_lines'].copy(),
                "floorline": board['floorline'].copy(),
                "wall": board['wall'].copy()
            }
            players_boards_state[player_name] = player_state

        game_state = {
            "factory": factory_state,
            "players_boards": players_boards_state,
            "first_to_fetch": self.first_to_fetch,
            # "tile_bag": self.factories['tile_bag'].copy(),
            "table_center": self.factories['table_center'].copy(),
            "log": self.log.copy()
        }

        return game_state



    def draw_game_gui(self):
        

        # Define colors
        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)
        GRAY = (200, 200, 200)
        COLOR_MAP = {
            'green': (0, 255, 0),
            'purple': (128, 0, 128),
            'yellow': (255, 255, 0),
            'blue': (0, 0, 255),
            'red': (255, 0, 0),
            'ONE': (255, 165, 0)  # Orange for the first player marker
        }

        # Set up the display
        # width, height = 800, 600
        # self.screen = pygame.Surface((width, height))
        self.screen.fill(WHITE)

        # Draw factories
        for i, factory in enumerate(self.factories['factory']):
            x = 50 + (i * 150)
            y = 50
            pygame.draw.circle(self.screen, GRAY, (x, y), 40)
            for j, tile in enumerate(factory):
                tile_x = x - 15 + (j % 2) * 30
                tile_y = y - 15 + (j // 2) * 30
                pygame.draw.rect(self.screen, COLOR_MAP[tile], (tile_x, tile_y, 15, 15))

        # Draw table center
        x, y = 400, 150
        for i, tile in enumerate(self.factories['table_center']):
            tile_x = x - 30 + (i % 5) * 15
            tile_y = y - 15 + (i // 5) * 15
            pygame.draw.rect(self.screen, COLOR_MAP[tile], (tile_x, tile_y, 15, 15))

        # Draw player boards
        for i, (player, board) in enumerate(self.boards.items()):
            x = 50 + (i * 350)
            y = 250

            # Draw score
            font = pygame.font.Font(None, 36)
            text = font.render(f"{player}: {board['score']}", True, BLACK)
            self.screen.blit(text, (x, y - 40))

            # Draw pattern lines
            for j, line in enumerate(board['pattern_lines']):
                for k, tile in enumerate(line):
                    tile_x = x + k * 20
                    tile_y = y + j * 20
                    pygame.draw.rect(self.screen, COLOR_MAP[tile], (tile_x, tile_y, 15, 15))

            # Draw wall
            wall_x = x + 150
            for j, row in enumerate(board['wall']):
                for k, tile in enumerate(row):
                    tile_x = wall_x + k * 20
                    tile_y = y + j * 20
                    if tile:
                        pygame.draw.rect(self.screen, COLOR_MAP[tile], (tile_x, tile_y, 15, 15))
                    else:
                        pygame.draw.rect(self.screen, BLACK, (tile_x, tile_y, 15, 15), 1)

            # Draw floorline
            floor_y = y + 120
            for j, tile in enumerate(board['floorline']):
                tile_x = x + j * 20
                pygame.draw.rect(self.screen, COLOR_MAP[tile], (tile_x, floor_y, 15, 15))


        pygame.display.flip()
        # # Save the image
        # pygame.image.save(screen, save_path)
        # pygame.quit()

        # print(f"Game state image saved to {save_path}")
        
        
    def game_loop(self):
        

        if self.debug:
            
            pygame.init()
            
            # Set up the display
            self.screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption('Hanabi Game State')
            
        while self.state != "end":
            # self.draw_game_gui()
            #
            # for event in pygame.event.get():
            #     if event.type == pygame.QUIT:
            #         self.state = "end"
            print("current state: " + self.state)
            if self.state == "start":
                self.game_start()
            
            elif self.state == "round_start":
                
                self.new_round()
                
            elif self.state == "p1_turn":
                
                self.publish(self.state, self.to_dict())
                
                self.p1_done()
                
            elif self.state == "p1_turn_end":
                
                
                self.p1_done()
                
            elif self.state == "p2_turn":
                
                self.publish(self.state, self.to_dict())
                
                self.p2_done()
                
            elif self.state == "p2_turn_end":
                
                
                self.p2_done()
            
            elif self.state == "round_end":
                
                self.round_end()
                
            elif self.state == "score_count":
                
                
                self.game_end()
        