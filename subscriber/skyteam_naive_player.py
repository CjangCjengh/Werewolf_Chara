import random
import pyperclip
from agent.naive_agent import NaiveAgent
from subscriber.subscriber import Subscriber
import json
import threading
from flask import Flask, render_template, request, jsonify
import base64

class SkyTeamNaivePlayer(Subscriber):
    
    def __init__(self, config):
        name = config["name"]
        role = config["role"]
        strategy = config["strategy"]
        model = config["model"]
        
        super().__init__(name, role)
        self.strategy = strategy
        self.agent = NaiveAgent(model)


    def notify(self, topic, message, image_base64, observation):
        
        # print(f"{self.name} {self.role} get message [{topic}]:{message}")
        
        # self.current_observation = observation  # Update the current observation
        # self.current_image_base64 = image_base64  # Update the current image


        
        # self.observation_records.append(observation)
        
        if topic == "discuss":
            return self.strategy_discuss(observation)
        
        elif topic == "reroll_dice":
            return self.reroll_dice(observation)
        
        elif topic == "pilot_action":
            return self.take_action(observation)
        
        elif topic == "copilot_action":
            return self.take_action(observation)
    
    def take_action(self, observation):
        info = {
            "name": self.name,
            "role": self.role,
            "record": observation["log"],
            "current_situation": observation,
            "current_dice": observation["current_round_dices"][self.role],
            "action_list": observation["current_round_allowed_actions"][self.role],
            "fail_cases": observation["fail_cases"],
        }
        
        prompt_path = "prompts/skyteam_action.prompt"
        
            
        answer = self.agent.make_decision(info, prompts=prompt_path)
        
        ret = { 
            "name": self.name,
            "role": self.role,
            "answer": answer, 
        }
        
        return ret
    
    def reroll_dice(self, observation):
        
        info = {
            "name": self.name,
            "role": self.role,
            "record": observation["log"],
            "current_situation": observation,
            "current_dice": observation["current_round_dices"][self.role],
        }
        
        prompt_path = "prompts/skyteam_reroll.prompt"
                
        
        answer = self.agent.make_decision(info, prompts=prompt_path)
        
        
        ret = {
            "name": self.name,
            "role": self.role,
            "answer": answer,
        }
        
        return ret
        
    def strategy_discuss(self, observation):
        
        info = {
            "name": self.name,
            "role": self.role,
            "record": observation["log"],
            "current_situation": observation,
        }
        prompt_path = "prompts/skyteam_discuss.prompt"
    
        answer = self.agent.make_decision(info, prompts=prompt_path)
        
        ret = {
            "name": self.name,
            "role": self.role,
            "answer": answer,
        }
        
        return ret
