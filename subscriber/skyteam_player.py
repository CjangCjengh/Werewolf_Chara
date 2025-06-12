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
        strategy = config["strategy"]
        model = config["model"]
        
        super().__init__(name, role)
        self.strategy = strategy
        self.agent = NaiveAgent(model) if strategy == "naive" else None

        self.observation_records = []
        self.current_observation = None  # To store the latest observation
        self.current_image_base64 = ""  # To store the latest observation image as base64

        self.human_input = ""  # To store input from the web UI
        self.input_event = threading.Event()  # To manage input waiting
        self.notify_event = threading.Event()  # To signal new observation
        
      

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
    
    
    def process_human_action(self, topic):
        
        if topic == "discuss":
            discuss = self.human_input
            answer = {"discuss": discuss}
            
            return {
                "name": self.name,
                "role": self.role,
                "topic": topic,
                "answer": answer,
            }
            
        else:
            action, dice = self.human_input.split()
            dice = int(dice)
            answer = {"action": action, "dice": dice}
            return {
                "name": self.name,
                "role": self.role,
                "topic": topic,
                "answer": answer
            }
    


    def _get_multiline_input(self, prompt):
        print(prompt)
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        return "\n".join(lines)
    
    def take_action(self, observation):
        info = {
            "name": self.name,
            "role": self.role,
            "record": observation["log"],
            "current_situation": observation,
            "current_dice": observation["current_round_dices"][self.role],
            "action_list": observation["current_round_allowed_actions"][self.role],
        }
        
        prompt_path = "prompts/skyteam_action.prompt"
        
        if self.strategy == "random":
            action = random.choice(observation["current_round_allowed_actions"][self.role])
            dice = random.choice(observation["current_round_dices"][self.role])

            answer = {"action": action, "dice": dice}
            
        elif self.strategy == "naive":
            answer = self.agent.make_decision(info, prompts=prompt_path)
        
        elif self.strategy == "copy":
            
            with open(prompt_path, "r") as prompt_file:
                prompt_content = prompt_file.read()
            
            formatted_prompt = prompt_content.format(**info)
            pyperclip.copy(formatted_prompt)
            print(f"Prompt copied to clipboard for {self.name} {self.role}")
            
            while True:
                answer_string = self._get_multiline_input("Enter action and dice (end with 'END'):")
                try:
                    answer = json.loads(answer_string)
                    break
                except json.JSONDecodeError:
                    print("Invalid input format. Please enter a valid JSON string.")
        
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
        
        remaining_dices = observation["current_round_dices"][self.role]
        
            
        if self.strategy == "random":
            
            rerolled_dice_count = random.choice(range(1, len(remaining_dices)+1))
            to_be_rerolled_dices_numbers = random.sample(remaining_dices, rerolled_dice_count)
            answer = {"dices": to_be_rerolled_dices_numbers}
        
        elif self.strategy == "naive":
            answer = self.agent.make_decision(info, prompts=prompt_path)
        
        
        elif self.strategy == "copy":
            
            with open(prompt_path, "r") as prompt_file:
                prompt_content = prompt_file.read()
            
            formatted_prompt = prompt_content.format(**info)
            pyperclip.copy(formatted_prompt)
            print(f"Prompt copied to clipboard for {self.name} {self.role}")
            
            while True:
                answer_string = self._get_multiline_input("Enter dices to reroll (end with 'END'):")
                try:
                    answer = json.loads(answer_string)
                    break
                except json.JSONDecodeError:
                    print("Invalid input format. Please enter a valid JSON string.")
        
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
        
        if self.strategy == "random":
            # random return 5 characters
            discuss = random.choice(["A", "B", "C", "D", "E"])
            answer = {"discuss": discuss}
        
        elif self.strategy == "naive":
            answer = self.agent.make_decision(info, prompts=prompt_path)
        
        elif self.strategy == "copy":
            with open(prompt_path, "r") as prompt_file:
                prompt_content = prompt_file.read()
            
            formatted_prompt = prompt_content.format(**info)
            pyperclip.copy(formatted_prompt)
            print(f"Prompt copied to clipboard for {self.name} {self.role}")
            
            while True:
                answer_string = self._get_multiline_input("Enter discuss (end with 'END'):")
                try:
                    answer = json.loads(answer_string)
                    break
                except json.JSONDecodeError:
                    print("Invalid input format. Please enter a valid JSON string.")
            
        ret = {
            "name": self.name,
            "role": self.role,
            "answer": answer,
        }
        
        return ret
