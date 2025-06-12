import random
import threading
import gradio as gr
from agent.naive_agent import NaiveAgent
from subscriber.subscriber import Subscriber
import asyncio
import re



class WerewolfRandomPlayer(Subscriber):
    
    def __init__(self, config):
        super().__init__(config["name"], role=config["role"])
        
        self.current_observation = None  # To store the latest observation
        self.context = [f'The game begins, and you have been assigned the role: {self.role}.']


    
    def notify(self, topic, message, image, observation):
        
        self.current_observation = observation
        

        # Decision-making logic based on the topic
        if topic == "day_vote":
            return self.day_vote(observation)
        elif topic == "wolf_action" and self.role == "werewolf":
            return self.werewolf_action(observation)
        elif topic == "witch_heal" and self.role == "witch":
            return self.witch_heal(observation)
        elif topic == "witch_poison" and self.role == "witch":
            return self.witch_poison(observation)
        elif topic == "hunter_action" and self.role == "hunter":
            return self.hunter_action(observation)
        elif topic == "seer_action" and self.role == "seer":
            return self.seer_action(observation)
        elif topic == "day_last_words":
            return self.say_last_words(observation)
        elif topic == "day_discuss":
            return self.day_discuss(observation)


    def day_vote(self, observation):
        
        
        alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
        vote = random.choice(alive_players)
        answer = {"vote": vote, "reason": "random"}
            
        return {
          "name": self.name,
          "role": self.role,
          "answer": answer
        }


    def werewolf_action(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }
        
        alive_players = input_data['alive_players']
        target = random.choice(alive_players)
        answer = {"target": target, "reason": "随机投票"}
            
        ret = {
            "name": self.name,
            "role": self.role,
            # "prompt": self.load_prompt(prompt_file, input_data),
            "answer": answer
        }
        # self.logging(ret)
        return ret


    def witch_heal(self, observation):

        
        choice = random.choice([True, False])
        answer = {"heal": choice}
                

        return {
            "name": self.name,
            "role": self.role,
            "answer": answer,
        }


    def witch_poison(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }

        
        alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
        if random.choice([True, False]):  # 随机决定是否使用毒药
            target = random.choice(alive_players)
        else:
            target = -1
            
        answer = {"target": target}

        ret =  {
            "name": self.name,
            "role": self.role,
                    #   "prompt": self.load_prompt(prompt_file, input_data),

            "answer": answer,
        }
        # self.logging(ret)
        return ret


    def hunter_action(self, observation):
        
        
        alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
        if random.choice([True, False]):  # 随机决定是否开枪
            target = random.choice(alive_players)
        else:
            target = -1
        
        answer = {"hunt": target}
            

        ret = {
            "name": self.name,
            "role": self.role,
            "answer": answer,
        }
        
        return ret


    def seer_action(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }

        
        alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
        check_player = random.choice(alive_players)
        answer = {"player": check_player}
            

        ret = {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }
        # self.logging(ret)
        return ret

    def say_last_words(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }

        
        message = self.name + ": " + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=6))
        answer = {"last_words": message}
            

        ret = {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }
        # self.logging(ret)
        return ret
    
    
    def day_discuss(self, observation):
        
        message = self.name + ": " + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=6))
        answer = {"discuss": message}
            

        ret = {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }
        return ret
    
    
    def last_words(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }

        
        message = self.name + ": " + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=6))
        answer = {"last_words": message}
            
        
        ret = {
            "name": self.name,
            "role": self.role,

            "answer": answer
        }
        # self.logging(ret)
        return ret
