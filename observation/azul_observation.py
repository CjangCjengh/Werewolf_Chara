import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import random
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class FactoryState:
    subfactories: List[List[str]]
    table_center: List[str]

@dataclass
class PlayerPatternLines:
    pattern_lines: List[List[str]]
    floorline: List[str]
    num_rows: int

@dataclass
class PlayerWall:
    grid: List[List[str]]

@dataclass
class PlayerBoardState:
    score: int
    pattern_lines: PlayerPatternLines
    floorline: List[str]
    wall: PlayerWall

@dataclass
class AzulGameState:
    factory: FactoryState
    players_boards: List[PlayerBoardState]
    first_to_fetch: int
    tile_bag: List[str]
    table_center: List[str]
    log: List[Dict[str, Any]]


class AzulStates:
    def __init__(self):
        self.init_game()

    def init_game(self):
        """Initialize the game with default values."""
        self.factory = {
            "colors": ['green', 'purple', 'yellow', 'blue', 'red'],
            "tile_count": 20,
            "tile_bag": random.sample(['green', 'purple', 'yellow', 'blue', 'red'] * 20, 100),
            "subfactories": [[] for _ in range(5)],
            "table_center": ['ONE'],
        }
        self.players_boards = [self._init_player_board(), self._init_player_board()]
        self.first_to_fetch = 0  # First player to fetch in the first round
        self.log = []
        self.silent = False
        self.floorline_punishment = [-1, -1, -2, -2, -2, -3, -3]

        # Evaluation metrics
        self.p1_total_attempts = 0
        self.p1_valid_attempts = 0
        self.p1_game_valid_attempts = 0
        self.p2_total_attempts = 0
        self.p2_valid_attempts = 0
        self.p2_game_valid_attempts = 0

    def _init_player_board(self):
        """Initialize a player board."""
        return {
            "score": 0,
            "pattern_lines": {"pattern_lines": [[] for _ in range(5)], "floorline": [], "num_rows": 5, "capacities": [1, 2, 3, 4, 5]},
            "floorline": [],
            "wall": {"grid": [['' for _ in range(5)] for _ in range(5)], 
                     "pattern": [
                        ['green', 'yellow', 'red', 'purple', 'blue'],
                        ['blue', 'green', 'yellow', 'red', 'purple'],
                        ['purple', 'blue', 'green', 'yellow', 'red'],
                        ['red', 'purple', 'blue', 'green', 'yellow'],
                        ['yellow', 'red', 'purple', 'blue', 'green']
                     ]}
        }

    def logging(self, content):
        if not self.silent:
            indented_content = "    " + content.replace("\n", "\n    ")
            print(indented_content)

    def are_subfactories_empty(self):
        return all(len(subfactory) == 0 for subfactory in self.factory['subfactories'])

    def no_tile_in_factories(self):
        """Check if all subfactories and the table center are empty."""
        if not self.are_subfactories_empty():
            return False
        return len(self.factory['table_center']) == 0 or self.factory['table_center'] == ['ONE']

    
    def player1_first(self):
        return self.first_to_fetch == 0
    
    def player2_first(self):
        return self.first_to_fetch == 1
    
    def tile_in_factories(self):
        return not self.no_tile_in_factories()
    
    def set_up_tiles_for_each_round(self):
        """Distribute tiles for each round, refill subfactories if they are empty."""
        if self.are_subfactories_empty() and self.no_tile_in_factories():
            log = self.distribute_tiles()
            self.logging("初始化工厂" + str(self.factory))
            self.log.extend(log)
    
    
    def process_round_end_move_pattern(self):
        """Move tiles from pattern lines to the wall at the end of the round and apply penalties."""
        self.log.append({"state": "round_end", "action": "movePattern2wall"})
        
        for p in range(2):
            for i in range(5):
                # Check if the row in the pattern lines is full
                if len(self.players_boards[p]['pattern_lines']['pattern_lines'][i]) == self.players_boards[p]['pattern_lines']['capacities'][i]:
                    self.move_to_wall(p, i)
                    self.logging(f"玩家{p + 1}的第{i + 1}行满了, 所以移动到wall")

        # Apply penalties and clear floorline
        for p in range(2):
            floorline = self.players_boards[p]['pattern_lines']['floorline']
            if len(floorline) > 0:
                self.logging(f"玩家{p + 1}的floorline: {floorline}")
                self.players_boards[p]['score'] += sum(self.floorline_punishment[:len(floorline)])
                self.players_boards[p]['pattern_lines']['floorline'] = []

        self.logging("movePattern2wall并计算分数")
        self.logging("move2wall后玩家1的patternlines: ")
        self.logging(str(self.players_boards[0]))
        self.logging("move2wall后玩家2的patternlines: ")
        self.logging(str(self.players_boards[1]))

    def distribute_tiles(self):
        log = []
        if not self.are_subfactories_empty():
            raise ValueError("Cannot distribute tiles: Subfactories are not empty.")
        
        log.append({"action": "start_distribution", "status": "subfactories_empty", "subfactories": [len(sf) for sf in self.factory['subfactories']]})
        
        self.factory["table_center"] = ['ONE']  # Start with the 'ONE' tile
        for i in range(5):
            for _ in range(4):
                if self.factory['tile_bag']:
                    tile = self.factory['tile_bag'].pop()
                    self.factory['subfactories'][i].append(tile)
                    log.append({"state": "round_start", "action": "add_tile", "subfactory": i + 1, "tile": tile, "remaining_tiles_in_bag": len(self.factory['tile_bag'])})
                else:
                    log.append({"action": "stop_distribution", "reason": "tile_bag_empty"})
                    break  # Stop if the tile bag is empty
        
        log.append({'state': 'round_start', "action": "end_distribution", "subfactories": [len(sf) for sf in self.factory['subfactories']]})
        
        return log

    def tile_in_bag(self):
        """Check if there are tiles left in the tile bag."""
        return len(self.factory['tile_bag']) > 0

    def no_tile_in_bag(self):
        """Check if there are no tiles left in the tile bag."""
        return not self.tile_in_bag()

    def get_tile(self, subfactory_num, color):
        if subfactory_num < 1 or subfactory_num > len(self.factory['subfactories']):
            raise ValueError("Invalid subfactory number.")
        
        subfactory = self.factory['subfactories'][subfactory_num - 1]
        retrieved_tiles = [tile for tile in subfactory if tile == color]
        remaining_tiles = [tile for tile in subfactory if tile != color]

        self.factory['table_center'].extend(remaining_tiles)
        self.factory['subfactories'][subfactory_num - 1] = []

        return retrieved_tiles

    def add_tile_to_pattern_lines(self, player_index, row_index, tile):
        pattern_lines = self.players_boards[player_index]['pattern_lines']
        current_row = pattern_lines['pattern_lines'][row_index]
        capacity = pattern_lines['capacities'][row_index]

        if not current_row:
            pattern_lines['pattern_lines'][row_index].append(tile)
        else:
            if current_row[0] == tile:
                if len(current_row) < capacity:
                    pattern_lines['pattern_lines'][row_index].append(tile)
                else:
                    self.add_to_floor_line(player_index, tile)
                    self.logging(f"第{row_index+1}行满了,'{tile}'放到floorline.")
            else:
                self.add_to_floor_line(player_index, tile)
                self.logging(f"'{tile}'不符合第{row_index+1}行的颜色,因此被放置在floorline.")

    def add_to_floor_line(self, player_index, tile):
        floorline = self.players_boards[player_index]['floorline']
        if len(floorline) < len(self.floorline_punishment):
            floorline.append(tile)

    def move_to_wall(self, player_index, row_index):
        player_board = self.players_boards[player_index]
        pattern_lines = player_board['pattern_lines']
        wall = player_board['wall']

        tiles = pattern_lines['pattern_lines'][row_index]
        if not tiles:
            raise ValueError("No tiles in the specified row.")
        
        tile = tiles[0]  # All tiles in the row should be of the same color
        col_index = wall['pattern'][row_index].index(tile)

        if wall['pattern'][row_index][col_index] == tile and wall['grid'][row_index][col_index] == '':
            wall['grid'][row_index][col_index] = tile
            self.players_boards[player_index]['score'] += 1  # Base score for placing the tile
            self.players_boards[player_index]['score'] += self._calculate_additional_points(wall['grid'], row_index, col_index)
            pattern_lines['pattern_lines'][row_index] = []
        else:
            raise ValueError(f"No valid position for the tile '{tile}' on the wall pattern in row {row_index}.")

    def _calculate_additional_points(self, grid, row, col):
        points = 0
        for c in range(col, -1, -1):
            if grid[row][c] != '':
                points += 1
            else:
                break
        for c in range(col, len(grid)):
            if grid[row][c] != '':
                points += 1
            else:
                break
        for r in range(row, -1, -1):
            if grid[r][col] != '':
                points += 1
            else:
                break
        for r in range(row, len(grid)):
            if grid[r][col] != '':
                points += 1
            else:
                break
        return points

    def process_round_end(self):
        self.log.append({"state": "round_end", "action": "movePattern2wall"})
        
        for p in range(2):
            for i in range(5):
                if len(self.players_boards[p]['pattern_lines']['pattern_lines'][i]) == self.players_boards[p]['pattern_lines']['capacities'][i]:
                    self.move_to_wall(p, i)
                    self.logging(f"玩家{p + 1}的第{i + 1}行满了, 所以移动到wall")
        
        for p in range(2):
            if len(self.players_boards[p]['pattern_lines']['floorline']) > 0:
                self.logging(f"玩家{p + 1}的floorline: {self.players_boards[p]['pattern_lines']['floorline']}")
                self.players_boards[p]['score'] += sum(self.floorline_punishment[:len(self.players_boards[p]['pattern_lines']['floorline'])])
                self.players_boards[p]['pattern_lines']['floorline'] = []
        
        self.logging("movePattern2wall并计算分数")
        self.logging("move2wall后玩家1的patternlines: ")
        self.logging(str(self.players_boards[0]))
        self.logging("move2wall后玩家2的patternlines: ")
        self.logging(str(self.players_boards[1]))

    def final_score_count(self):
        for p in range(2):
            for i in range(5):
                if all(tile != '' for tile in self.players_boards[p]['wall']['grid'][i]):
                    self.players_boards[p]['score'] += 2
                if all(self.players_boards[p]['wall']['grid'][j][i] != '' for j in range(5)):
                    self.players_boards[p]['score'] += 7
                if all(self.players_boards[p]['wall']['grid'][j][i] == self.players_boards[p]['wall']['pattern'][i][j] for j in range(5)):
                    self.players_boards[p]['score'] += 10
        
        self.log.append({"state": "score_count", "action": "final_score_count", "score": [self.players_boards[0]['score'], self.players_boards[1]['score']]})
        self.log.append({"state": "end", "winner": 1 if self.players_boards[0]['score'] > self.players_boards[1]['score'] else 2})
        self.log.append({"state": "end", "p1_total_attempts": self.p1_total_attempts, "p1_valid_attempts": self.p1_valid_attempts, "p1_game_valid_attempts": self.p1_game_valid_attempts})
        self.log.append({"state": "end", "p2_total_attempts": self.p2_total_attempts, "p2_valid_attempts": self.p2_valid_attempts, "p2_game_valid_attempts": self.p2_game_valid_attempts})
        
    def process_action(self, responses):
        topic = responses[0]['topic']
        factory_num = int(responses[0]['table'])
        color = responses[0]['color']
        row = int(responses[0]['row'])
        attempts = int(responses[0]['attempts'])
        
        if topic == 'p1_turn':
            self.p1_total_attempts += attempts
            self.p1_valid_attempts += 1
        elif topic == 'p2_turn':
            self.p2_total_attempts += attempts
            self.p2_valid_attempts += 1
        
        player_index = 0 if topic == 'p1_turn' else 1
        player_board = self.players_boards[player_index]
        
        if factory_num < 0 or factory_num > 5:
            self.logging("Invalid factory number.")
            return {'state': 'p{}_turn'.format(player_index + 1), 'is_successful': False}
        
        if row < 1 or row > 5:
            self.logging("Invalid row number.")
            return {'state': 'p{}_turn'.format(player_index + 1), 'is_successful': False}
        
        if color not in self.factory['colors'] and color != "ONE":
            self.logging("Invalid tile color.")
            return {'state': 'p{}_turn'.format(player_index + 1), 'is_successful': False}
        
        if factory_num > 0:
            if color not in self.factory['subfactories'][factory_num-1]:
                self.logging("The specified color is not in the selected factory.")
                return {'state': 'p{}_turn'.format(player_index + 1), 'is_successful': False}
        elif factory_num == 0:
            if color not in self.factory['table_center']:
                self.logging("Error: The specified color is not in the table center.")
                return {'state': 'p{}_turn'.format(player_index + 1), 'is_successful': False}
        
        if topic == 'p1_turn':
            self.p1_game_valid_attempts += 1
        elif topic == 'p2_turn':
            self.p2_game_valid_attempts += 1
            
        if factory_num == 0:
            if color == "ONE":
                self.logging(f"玩家{player_index + 1}特意取走'ONE',下一回合的先手是{player_index + 1}号玩家")
                self.first_to_fetch = player_index
                
            retrieved_tiles = [tile for tile in self.factory['table_center'] if tile == color]
            
            if "ONE" in self.factory['table_center'] and color != "ONE":
                retrieved_tiles.append("ONE")
                self.logging("取走 'ONE' 和 其他颜色 tile.下一回合的先手是{player_index + 1}号玩家")
                self.first_to_fetch = player_index

            self.factory['table_center'] = [tile for tile in self.factory['table_center'] if tile not in retrieved_tiles]
        else:
            retrieved_tiles = self.get_tile(factory_num, color)
        
        for tile in retrieved_tiles:
            try:
                self.add_tile_to_pattern_lines(player_index, row-1, tile)
            except ValueError as e:
                print(f"Error: {e}")
        
        self.logging(str(self.factory))
        self.logging(str(player_board))
        
        self.log.append({
            'state': 'p{}_turn'.format(player_index + 1),
            'is_successful': True,
            'player': player_index + 1,
            'factory_num': factory_num,
            'color': color,
            'row': row,
            'tiles_retrieved': retrieved_tiles
        })
        
        return {
            'state': 'p{}_turn'.format(player_index + 1),
            'is_successful': True,
            'player': player_index + 1,
            'factory_num': factory_num,
            'color': color,
            'row': row,
            'tiles_retrieved': retrieved_tiles
        }

    def visualize(self):
        factory_image = self.visualize_factory()
        player1_image = self.visualize_player_board(0)
        player2_image = self.visualize_player_board(1)

        combined_image = np.hstack((factory_image, player1_image, player2_image))

        plt.imshow(combined_image)
        plt.axis('off')
        plt.show()

        return combined_image
    
    def visualize_factory(self):
        fig, ax = plt.subplots(figsize=(8, 8))

        center_x, center_y = 0.5, 0.5
        ax.add_patch(plt.Circle((center_x, center_y), 0.1, color='white', ec='purple'))
        ax.text(center_x, center_y, '\n'.join(self.factory['table_center']), ha='center', va='center', fontsize=8)

        angle_step = 360 / len(self.factory['subfactories'])
        for i, subfactory in enumerate(self.factory['subfactories']):
            angle = np.deg2rad(angle_step * i)
            x = center_x + 0.3 * np.cos(angle)
            y = center_y + 0.3 * np.sin(angle)

            ax.add_patch(plt.Circle((x, y), 0.1, color='white', ec='purple'))
            ax.text(x, y, '\n'.join(subfactory), ha='center', va='center', fontsize=8)

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.axis('off')

        fig.canvas.draw()
        width, height = fig.canvas.get_width_height()
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img = img.reshape(height, width, 3)

        plt.close(fig)
        return img
    
    def visualize_player_board(self, player_index):
        player_board = self.players_boards[player_index]
        tile_colors = {
            'red': '#ED5564',
            'green': '#A0D568',
            'yellow': '#FFCE54',
            'purple': '#AC92EB',
            'blue': '#4FC1E8',
            '': '#FFFFFF',
        }

        fig, ax = plt.subplots(2, 1, figsize=(8, 8))

        pattern_lines = player_board['pattern_lines']
        for row in range(pattern_lines['num_rows']):
            capacity = pattern_lines['capacities'][row]
            tiles = pattern_lines['pattern_lines'][row]
            for col in range(capacity):
                color = tile_colors['']  # Default to white (empty)
                if col < len(tiles):
                    color = tile_colors[tiles[col]]
                rect = patches.Rectangle((col, row), 1, 1, linewidth=1, edgecolor='purple', facecolor=color)
                ax[0].add_patch(rect)
        ax[0].set_xlim(0, max(pattern_lines['capacities']))
        ax[0].set_ylim(0, pattern_lines['num_rows'])
        ax[0].set_title("Pattern Lines")
        ax[0].invert_yaxis()

        wall = player_board['wall']
        for row in range(5):
            for col in range(5):
                if wall['grid'][row][col] == '':
                    color = tile_colors[wall['pattern'][row][col]]
                else:
                    color = tile_colors[wall['grid'][row][col]]
                rect = patches.Rectangle((col, row), 1, 1, linewidth=1, edgecolor='purple', facecolor=color)
                ax[1].add_patch(rect)
                if wall['grid'][row][col] != '':
                    ax[1].plot([col, col + 1], [row, row + 1], color='purple', lw=2)
                    ax[1].plot([col + 1, col], [row, row + 1], color='purple', lw=2)
        ax[1].set_xlim(0, 5)
        ax[1].set_ylim(0, 5)
        ax[1].set_title("Wall")
        ax[1].invert_yaxis()

        fig.canvas.draw()
        width, height = fig.canvas.get_width_height()
        img = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
        img = img.reshape(height, width, 3)

        plt.close(fig)
        return img

    def to_dict(self):
        factory_state = {
            "Factories": {f"Factory {i + 1}": subfactory for i, subfactory in enumerate(self.factory['subfactories'])},
            "TableCenter": self.factory['table_center'].copy()
        }
        
        players_boards_state = []
        for player in self.players_boards:
            player_state = {
                "score": player['score'],
                "pattern_lines": player['pattern_lines']['pattern_lines'].copy(),
                "floorline": player['pattern_lines']['floorline'].copy(),
                "wall": player['wall']['grid'].copy()
            }
            players_boards_state.append(player_state)
        
        game_state = {
            "factory": factory_state,
            "players_boards": players_boards_state,
            "first_to_fetch": self.first_to_fetch,
            "tile_bag": self.factory['tile_bag'].copy(),
            "table_center": self.factory['table_center'].copy(),
            "log": self.log.copy()
        }
        
        return game_state

    def to_dataclass(self) -> AzulGameState:
        factory_state = FactoryState(
            subfactories=[subfactory.copy() for subfactory in self.factory['subfactories']],
            table_center=self.factory['table_center'].copy()
        )

        players_boards_state = [
            PlayerBoardState(
                score=player['score'],
                pattern_lines=PlayerPatternLines(
                    pattern_lines=player['pattern_lines']['pattern_lines'].copy(),
                    floorline=player['pattern_lines']['floorline'].copy(),
                    num_rows=player['pattern_lines']['num_rows']
                ),
                floorline=player['floorline'].copy(),
                wall=PlayerWall(
                    grid=player['wall']['grid'].copy()
                )
            ) for player in self.players_boards
        ]

        game_state = AzulGameState(
            factory=factory_state,
            players_boards=players_boards_state,
            first_to_fetch=self.first_to_fetch,
            tile_bag=self.factory['tile_bag'].copy(),
            table_center=self.factory['table_center'].copy(),
            log=self.log.copy()
        )

        return game_state
