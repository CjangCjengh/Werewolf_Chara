import random
from subscriber.subscriber import Subscriber
from agent.naive_agent import NaiveAgent
import threading

class AzulPlayer(Subscriber):
    def __init__(self, config):
        super().__init__(config["name"], role=config["role"])
        self.strategy = config["strategy"]
        self.agent = None
        self.current_observation = None  # To store the latest observation
        self.current_image_base64 = ""  # To store the latest observation image as base64

        if self.strategy == "random":
            self.agent = None
        elif self.strategy == "naive":
            self.agent = NaiveAgent(config["model"])
        elif self.strategy == "heuristic":
            self.agent = None
        elif self.strategy == "replay":
            self.agent = None
            if "replay" in config:
                self.replay_actions = config["replay"]


    def notify(self, topic, message, image_base64, observation):
        self.logging(f"{self.name} ({self.role}) received message [{topic}]: {message}")
        self.current_observation = observation  # Update the current observation
        self.current_image_base64 = image_base64  # Update the current image

        if topic == "p1_turn":
            return self.get_tiles(observation, player_key='player1')
        elif topic == "p2_turn":
            return self.get_tiles(observation, player_key='player2')
        else:
            print(f"{self.name} ({self.role}) received an unhandled topic [{topic}]")
            return None


    def get_tiles(self, observation, player_key):
        if self.strategy == "random":
            table = random.randint(0, 5)
            color = random.choice(observation["factory"]["colors"])
            row = random.randint(1, 5)
        elif self.strategy == "naive":
            input_data = {
                'name': self.name,
                'role': self.role,
                # 'observation': observation,
                'factory': observation['factory'],
                'players_boards': observation['players_boards']
            }
            answer = self.agent.make_decision(input_data, prompts="prompts/azul.prompt")
            table, color, row = answer['location'], answer['color'], answer['line']
            attempts = answer['attempts']   
        elif self.strategy == "heuristic":
            return self.heuristic_strategy(observation, player_key)
        return {
            "name": self.name,
            "role": self.role,
            "topic": player_key + "_turn",
            "table": table,
            "color": color,
            "row": row,
            "attempts": attempts
        }

    def heuristic_strategy(self, obs, player_key):
        player_board = obs["players_boards"][player_key]
        best_score = float('-inf')
        best_move = None
        valid_moves = []

        
        def is_valid_move(player_board, color, row):
            pattern_line = player_board["pattern_lines"][row]
            return (not pattern_line or pattern_line[0] == color) and color not in player_board["wall"][row]

        def evaluate_move(obs, player_key, factory_num, color, row):
            player_board = obs["players_boards"][player_key]
            pattern_line = player_board["pattern_lines"][row]
            if color in player_board["wall"][row]:
                return float('-inf')
            score = len(pattern_line) + 1

            if len(pattern_line) + 1 == row + 1:
                score += 10

            return score
        
        for factory_num, factory in enumerate(obs["factory"]["Factories"].values(), start=1):
            for color in set(factory):
                for row in range(5):
                    if is_valid_move(player_board, color, row):
                        score = evaluate_move(obs, player_key, factory_num, color, row)
                        valid_moves.append((score, factory_num, color, row))
                        if score > best_score:
                            best_score = score
                            best_move = (factory_num, color, row)

        if not valid_moves:
            # Select from non-empty factories and the table center
            non_empty_sources = [
                (0, obs["factory"]["TableCenter"]) 
                if obs["factory"]["TableCenter"] 
                else None
            ] + [
                (i + 1, factory) 
                for i, factory in enumerate(obs["factory"]["Factories"].values()) 
                if factory
            ]
            non_empty_sources = [source for source in non_empty_sources if source]

            factory_num, tiles = random.choice(non_empty_sources)
            color = random.choice(tiles)
            row = random.choice(range(5))
            best_move = (factory_num, color, row)
        else:
            factory_num, color, row = best_move

        return {
            "name": self.name,
            "role": self.role,
            "topic": "p1_turn" if player_key == 'player1' else "p2_turn",
            "table": factory_num,
            "color": color,
            "row": row + 1,
            "attempts": "1"
        }


    def logging(self, message):
        print(message)
