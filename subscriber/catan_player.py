import random
from subscriber.subscriber import Subscriber
from agent.naive_agent import NaiveAgent
import threading
import io
import base64

class CatanPlayer(Subscriber):
    
    def __init__(self, config):
        super().__init__(config["name"], role=config["role"])
        self.strategy = config["strategy"]
        self.agent = None
        self.current_observation = None  # To store the latest observation
        self.current_image_base64 = ""  # To store the latest observation image as base64
        

    def notify(self, topic, image_base64, observation):
        
        self.current_observation = observation  # Update the current observation
        self.current_image_base64 = image_base64  # Update the current image

        if topic == "place_initial_settlements":
            return self.place_initial_settlements(observation)
        elif topic == "place_initial_roads":
            return self.place_initial_roads(observation)
        elif topic == "production_phase":
            return self.production_phase_make_choice(observation)
        elif topic == "roll_dice":
            return self.roll_dice(observation)
        elif topic == "trade_n_build_phase":
            return self.trade_n_build_phase_make_choice(observation)
        elif topic == "move_robber":
            return self.move_robber(observation)
        elif topic == "trade":
            return self.trade(observation)
        elif topic == "response_to_trade":
            return self.response_to_trade(observation)
        
        elif topic == "maritime_trade":
            return self.maritime_trade(observation)

        elif topic == "build_road":
            return self.build_road(observation)
        elif topic == "build_settlement":
            return self.build_settlement(observation)
        elif topic == "build_city":
            return self.build_city(observation)
        elif topic == "buy_development_card":
            return self.buy_development_card(observation)
        elif topic == "play_development_card":
            return self.play_development_card(observation)
    
    def response_to_trade(self, observation):
            
        response = random.choice(['accept', 'reject'])
        answer = {
            "response": response,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "respond_to_trade",
            "answer": answer,
        }
        return ret
    
    def buy_development_card(self, observation):
              
        card = random.choice(['knight', 'road_building', 'year_of_plenty', 'monopoly', 'victory_point'])
        answer = {
            "card": card,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "play_development_card",
            "answer": answer,
        }
        return ret
    
    def build_settlement(self, observation):
                
        mouse_pos_x = random.choice(range(0, 800))
        mouse_pos_y = random.choice(range(0, 600))
        
        answer = {
            "mouse_pos_x": mouse_pos_x,
            "mouse_pos_y": mouse_pos_y,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "build_settlement",
            "answer": answer,
        }
        
        return ret
    
    def build_city(self, observation):
                
        mouse_pos_x = random.choice(range(0, 800))
        mouse_pos_y = random.choice(range(0, 600))
        
        answer = {
            "mouse_pos_x": mouse_pos_x,
            "mouse_pos_y": mouse_pos_y,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "build_city",
            "answer": answer,
        }
        
        return ret
    
    def build_city(self, observation):
                
        mouse_pos_x = random.choice(range(0, 800))
        mouse_pos_y = random.choice(range(0, 600))
        
        answer = {
            "mouse_pos_x": mouse_pos_x,
            "mouse_pos_y": mouse_pos_y,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "build_city",
            "answer": answer,
        }
        
        return ret
    def build_road(self, observation):
            
        mouse_pos_x = random.choice(range(0, 800))
        mouse_pos_y = random.choice(range(0, 600))
        
        answer = {
            "mouse_pos_x": mouse_pos_x,
            "mouse_pos_y": mouse_pos_y,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "build_road",
            "answer": answer,
        }
        
        return ret
    
    def play_development_card(self, observation):
            
        card = random.choice(['knight', 'road_building', 'year_of_plenty', 'monopoly', 'victory_point'])
        answer = {
            "card": card,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "play_development_card",
            "answer": answer,
        }
        return ret
    
    
    def maritime_trade(self, observation):
            
        color = random.choice(['wood', 'brick', 'wheat', 'ore', 'sheep'])
        give = random.choice(range(0, 4))
        get = random.choice(range(0, 4))
        
        answer = {
            "color": color,
            "give": give,
            "get": get,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "maritime_trade",
            "answer": answer,
        }
        return ret
    
    
    
    def move_robber(self, observation):
        
        mouse_pos_x = random.choice(range(0, 800))
        mouse_pos_y = random.choice(range(0, 600))
        
        answer = {
            "mouse_pos_x": mouse_pos_x,
            "mouse_pos_y": mouse_pos_y,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "robbery_phase_make_choice",
            "answer": answer,
        }
        
        return ret
    
    def trade(self, observation):
        
        give = {
            "wood": random.choice(range(0, 1)),
            "brick": random.choice(range(0, 1)),
            "wheat": random.choice(range(0, 1)),
            "ore": random.choice(range(0, 1)),
            "sheep": random.choice(range(0, 1)),
        }
        get = {
            "wood": random.choice(range(0, 1)),
            "brick": random.choice(range(0, 1)),
            "wheat": random.choice(range(0, 1)),
            "ore": random.choice(range(0, 1)),
            "sheep": random.choice(range(0, 1)),
        }
        
        answer = {
            "give": give,
            "get": get,
        }
        
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "trade",
            "answer": answer,
        }
        return ret
    
    def trade_n_build_phase_make_choice(self, observation):
            
        choice = random.choice(['trade', 'maritime_trade', 'play_development_card', 'build_road', 'build_settlement', 'build_city', 'buy_development_card', 'pass'])
        answer = {
            "choice": choice,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "trade_n_build_phase_make_choice",
            "answer": answer,
        }
        return ret
    
    def production_phase_make_choice(self, observation):
            
            choice = random.choice(['play_development_card', 'roll_dice'])
            answer = {
                "choice": choice,
            }
            ret = {
                "name": self.name,
                "role": self.role,
                "topic": "production_phase_make_choice",
                "answer": answer,
            }
            return ret
        
    def roll_dice(self, observation):
        
        # random roll two dice
        dice1 = random.choice(range(1, 7))
        dice2 = random.choice(range(1, 7))
        answer = {
            "dice": dice1 + dice2,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "roll_dice",
            "answer": answer,
        }
        return ret
    
    def place_initial_roads(self, observation):
            
        mouse_pos_x = random.choice(range(0, 800))
        mouse_pos_y = random.choice(range(0, 600))
        
        # road = random.choice(observation['available_roads'])
        answer = {
            "mouse_pos_x": mouse_pos_x,
            "mouse_pos_y": mouse_pos_y,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "place_initial_roads",
            "answer": answer,
        }
        
        return ret

    def place_initial_settlements(self, observation):
        
        
        mouse_pos_x = random.choice(range(0, 800))
        mouse_pos_y = random.choice(range(0, 600))
        
        # settlement = random.choice(observation['available_settlements'])
        answer = {
            "mouse_pos_x": mouse_pos_x,
            "mouse_pos_y": mouse_pos_y,
        }
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "place_initial_settlements",
            "answer": answer,
        }
        
        return ret