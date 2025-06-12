import random
import threading
import json
from flask import Flask, render_template, request, jsonify
from subscriber.subscriber import Subscriber
from agent.naive_agent import NaiveAgent

class CodenamesNaivePlayer(Subscriber):
    def __init__(self, config):
        name = config['name']
        role = config['role']
        model = config['model']
        self.agent = NaiveAgent(model)

        super().__init__(name, role)
        self.current_observation = {"game": "codenames"}
        
        
    def notify(self, topic, message, image, observation):
        print(f"{self.name} ({self.role}) received message [{topic}]: {message}")
        self.current_observation = observation
        self.current_topic = topic

        if topic.endswith("give_clue"):
            return self.give_clue(observation)
        elif topic.endswith("guess"):
            return self.make_guess(observation)
        else:
            raise ValueError(f"{self.name} ({self.role}) received an unhandled topic [{topic}]")


    def give_clue(self, observation):
            
        input_data = {
            'name': self.name,
            'role': self.role,
            'remaining_words': observation["remaining_words"],
            'fail_cases': observation["fail_cases"],
        }
        answer = self.agent.make_decision(input_data, prompts="prompts/codenames_clue.prompt")
       
        return {
            "name": self.name,
            "role": self.role,
            "topic": "give_clue",
            "answer": answer
        }

    def make_guess(self, observation):
            
            
        input_data = {
            'name': self.name,
            'role': self.role,
            'remaining_words': observation["remaining_words"],
            'clue': observation["current_clue"],
            'number': observation["current_clue_number"],
            'fail_cases': observation["fail_cases"],
        }
        answer = self.agent.make_decision(input_data, prompts="prompts/codenames_guess.prompt")
        
                
        return {
            "name": self.name,
            "role": self.role,
            "topic": "guess",
            "answer": answer
        }
