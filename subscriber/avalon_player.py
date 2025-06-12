import random
import threading
import json
from flask import Flask, render_template, request, jsonify
from agent.naive_agent import NaiveAgent
from agent.character_agent import CharacterAgent
from subscriber.subscriber import Subscriber

class AvalonPlayer(Subscriber):
    def __init__(self, config):
        super().__init__(config["name"], role=config["role"])
        self.strategy = config["strategy"]
        self.agent = None
        self.current_observation = None  # To store the latest observation

        self.human_input = ""  # To store input from the web UI
        self.input_event = threading.Event()  # To manage input waiting
        self.notify_event = threading.Event()  # To signal new observation

        if self.strategy == "random":
            self.agent = None
        elif self.strategy == "naive":
            self.agent = NaiveAgent(config["model"])
        elif self.strategy == "character":
            self.agent = CharacterAgent(config["model"])
        elif self.strategy == "replay":
            self.agent = None
            if "replay" in config:
                self.replay_actions = config["replay"]
        else:
            raise ValueError(f"Invalid strategy: {self.strategy}")


    def notify(self, topic, message, image, observation):
        self.logging(f"{self.name} ({self.role}) received message [{topic}]: {message}")
        self.current_observation = observation  # Update the current observation
        self.current_topic = topic  # Store the current topic

        if self.strategy == "human":
            self.notify_event.set()
            self.input_event.wait()
            self.input_event.clear()
            return self.process_human_action(topic)

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
        if self.strategy == "random":
            target = random.choice(observation['players_names'])
        elif self.strategy in ["naive", "character"]:
            input_data = {
                'name': self.name,
                'role': self.role,
                'player_list': observation['players_names'],
            }
            answer = self.agent.make_decision(input_data, prompts="prompts/avalon_assassin.prompt")
            target = answer['target']
            
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "assassin", 
            "target": target
        }
        
        return ret

    def select_team(self, observation):
        if self.strategy == "random":
            team_size = observation['team_size_each_round'][observation['current_quest_round'] - 1]
            team = random.sample(observation['players_names'], team_size)
        elif self.strategy in ["naive", "character"]:
            input_data = {
                'name': self.name,
                'role': self.role,
                'team_size': observation['team_size_each_round'][observation['current_quest_round'] - 1],
                'current_quest_round': observation['current_quest_round'],
                'player_list': observation['players_names'],
            }
            answer = self.agent.make_decision(input_data, prompts="prompts/avalon_team_selection.prompt")
            team = answer['team']
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "team_selection", 
            "team": team
        }
        
        return ret

    def vote(self, observation):
        if self.strategy == "random":
            acc_rej = random.choice(["accept", "reject"])
        elif self.strategy in ["naive", "character"]:
            input_data = {
                'name': self.name,
                'role': self.role,
                'current_quest_round': observation['current_quest_round'],
                'vote_round': observation['current_vote_round'],
                'player_list': observation['players_names'],
            }
            answer = self.agent.make_decision(input_data, prompts="prompts/avalon_vote.prompt")
            acc_rej = answer['vote']
            
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "vote", 
            
            "vote": acc_rej
        }
        
        return ret

    def quest(self, observation):
        if self.strategy == "random":
            succeed_or_fail = random.choice(["success", "fail"])
        elif self.strategy in ["naive", "character"]:
            input_data = {
                'name': self.name,
                'role': self.role,
                'current_quest_round': observation['current_quest_round'],
            }
            answer = self.agent.make_decision(input_data, prompts="prompts/avalon_quest.prompt")
            succeed_or_fail = answer['quest']
            
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": "quest", 
            "quest": succeed_or_fail
        }
        
        return ret

    def logging(self, message):
        print(message)
