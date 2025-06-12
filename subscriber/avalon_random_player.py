import random
import threading
import json
from flask import Flask, render_template, request, jsonify
from agent.naive_agent import NaiveAgent
from subscriber.subscriber import Subscriber
from agent.naive_agent import NaiveAgent

class AvalonRandomPlayer(Subscriber):
    def __init__(self, config):
        super().__init__(config["name"], role=config["role"])
        
        self.current_observation = None  
        


    def notify(self, topic, message, image, observation):
        self.logging(f"{self.name} ({self.role}) received message [{topic}]: {message}")
        self.current_observation = observation  # Update the current observation
        self.current_topic = topic  # Store the current topic
        if topic == "team_selection":
            return self.select_team(observation)
        elif topic == "vote":
            return self.vote(observation)
        elif topic == "quest":
            return self.quest(observation)
        elif topic == "assassin":
            return self.assassin(observation)
        else:
            print(f"{self.name} ({self.role}) received an unhandled topic [{topic}]")
            return None


    def assassin(self, observation):
        
        target = random.choice(observation['players_names'])
        
        answer = {"target": target}
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "assassin", 
            # "target": target
            "answer": answer
        }
        
        return ret

    def select_team(self, observation):
        
        team_size = observation['team_size_each_round'][observation['current_quest_round'] - 1]
        team = random.sample(observation['players_names'], team_size)
        
        answer = {"team": team}
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "team_selection", 
            # "team": team
            "answer": answer
        }
        
        return ret

    def vote(self, observation):
        
        acc_rej = random.choice(["accept", "reject"])
        answer = {"vote": acc_rej}
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "vote", 
            "answer": answer
            # "vote": acc_rej
        }
        
        return ret

    def quest(self, observation):
        
        succeed_or_fail = random.choice(["success", "fail"])
        answer = {"quest": succeed_or_fail}
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "quest", 
            # "quest": succeed_or_fail
            "answer": answer
        }
        
        return ret

    def logging(self, message):
        print(message)
