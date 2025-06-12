import random
import pyperclip
from agent.naive_agent import NaiveAgent
from subscriber.subscriber import Subscriber
import json
import threading
from flask import Flask, render_template, request, jsonify
import base64

class SkyTeamPlayer(Subscriber):
    
    def __init__(self, config):
        name = config["name"]
        role = config["role"]

        
        super().__init__(name, role)
        
      

    def notify(self, topic, message, image_base64, observation):
        
        print(f"{self.name} {self.role} get message [{topic}]:{message}")
        
        self.current_observation = observation  # Update the current observation
        self.current_image_base64 = image_base64  # Update the current image
        
        self.observation_records.append(observation)
        
        if topic == "discuss":
            return self.strategy_discuss(observation)
        
        elif topic == "reroll_dice":
            return self.reroll_dice(observation)
        
        elif topic == "pilot_action":
            return self.take_action(observation)
        
        elif topic == "copilot_action":
            return self.take_action(observation)
    
    
    def take_action(self, observation):
    
        action = random.choice(observation["current_round_allowed_actions"][self.role])
        dice = random.choice(observation["current_round_dices"][self.role])

        answer = {"action": action, "dice": dice}
        
        ret = { 
            "name": self.name,
            "role": self.role,
            "answer": answer, 
        }
        
        return ret
    
    def reroll_dice(self, observation):
        
        
        remaining_dices = observation["current_round_dices"][self.role]
        rerolled_dice_count = random.choice(range(1, len(remaining_dices)+1))
        to_be_rerolled_dices_numbers = random.sample(remaining_dices, rerolled_dice_count)
        answer = {"dices": to_be_rerolled_dices_numbers}
        
        
        ret = {
            "name": self.name,
            "role": self.role,
            "answer": answer,
        }
        
        return ret
        
    def strategy_discuss(self, observation):
        
        
        # random return 5 characters
        discuss = random.choice(["A", "B", "C", "D", "E"])
        answer = {"discuss": discuss}
        
            
        ret = {
            "name": self.name,
            "role": self.role,
            "answer": answer,
        }
        
        return ret
