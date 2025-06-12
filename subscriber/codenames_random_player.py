import random
import threading
import json
from flask import Flask, render_template, request, jsonify
from subscriber.subscriber import Subscriber
from agent.naive_agent import NaiveAgent

class CodenamesRandomPlayer(Subscriber):
    def __init__(self, config):
        name = config['name']
        role = config['role']
        
        super().__init__(name, role)
            
        
        

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
            
        available_words = observation["current_available_words"]
        clue_word = random.choice(available_words)
        clue_number = random.randint(1, 3)
        answer = {"clue": clue_word, "number": clue_number}
            
        return {
            "name": self.name,
            "role": self.role,
            "topic": "give_clue",
            "answer": answer
        }

    def make_guess(self, observation):
            
        available_words = observation["current_available_words"]
        guessed_word = random.choice(available_words)
        answer = {"guess": guessed_word}
                
        return {
            "name": self.name,
            "role": self.role,
            "topic": "guess",
            "answer": answer
        }
