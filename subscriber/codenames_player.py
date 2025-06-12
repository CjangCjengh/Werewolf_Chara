import random
import threading
import json
from flask import Flask, render_template, request, jsonify
from subscriber.subscriber import Subscriber
from agent.naive_agent import NaiveAgent

class CodenamesPlayer(Subscriber):
    def __init__(self, config):
        name = config['name']
        role = config['role']
        strategy = config['strategy']
        model = config['model'] if 'model' in config else None
        
        super().__init__(name, role)
        self.strategy = strategy
        self.current_observation = {"game": "codenames"}
        self.current_topic = "unkown"
        self.human_input = ""
        self.input_event = threading.Event()
        self.notify_event = threading.Event()

        if self.strategy == "naive":
            self.agent = NaiveAgent(model)
        elif self.strategy == "replay":
            self.agent = None 
            if "replay" in config:
                self.replay_actions = config["replay"]
        elif self.strategy == "human":
            self.agent = None
            self.port = config.get("port", 5000)
            self.start_flask_app()
        else:
            self.agent = None
        
        
    def start_flask_app(self):
        app = Flask(__name__)

        @app.route('/')
        def index():
            observation_html = ''.join(
                f'<div style="background-color: {["#f0f0f0", "#ffffff"][i % 2]}; padding: 5px; word-wrap: break-word;">{key}: {json.dumps(value)}</div>'
                for i, (key, value) in enumerate(self.current_observation.items())
            )
            return render_template('codenames.html', name=self.name, role=self.role, observation_html=observation_html, topic=self.current_topic)

        @app.route('/current_observation', methods=['GET'])
        def current_observation():
            return jsonify({"observation": self.current_observation, "topic": self.current_topic})

        @app.route('/submit_action', methods=['POST'])
        def submit_action():
            self.human_input = request.json['action']
            self.input_event.set()
            return jsonify(success=True)

        threading.Thread(target=app.run, kwargs={'port': self.port, 'debug': True, 'use_reloader': False}).start()

    def notify(self, topic, message, image, observation):
        print(f"{self.name} ({self.role}) received message [{topic}]: {message}")
        self.current_observation = observation
        self.current_topic = topic

        if self.strategy == "human":
            self.notify_event.set()
            self.input_event.wait()
            self.input_event.clear()
            return self.process_human_action(topic)

        if topic.endswith("give_clue"):
            return self.give_clue(observation)
        elif topic.endswith("guess"):
            return self.make_guess(observation)
        else:
            raise ValueError(f"{self.name} ({self.role}) received an unhandled topic [{topic}]")

    def process_human_action(self, topic):
        if topic.endswith("give_clue"):
            return self.give_clue(self.current_observation)
        elif topic.endswith("guess"):
            return self.make_guess(self.current_observation)
        return None

    def get_human_input(self, prompt, options=None):
        if options:
            prompt += f" ({', '.join(options)})"
        choice = input(prompt + ": ")
        if options and choice not in options:
            print(f"Invalid choice. Please choose from {options}.")
            return self.get_human_input(prompt, options)
        return choice

    def give_clue(self, observation):
        if self.strategy == "random":
            available_words = observation["current_available_words"]
            clue_word = random.choice(available_words)
            clue_number = random.randint(1, 3)
            answer = {"clue": clue_word, "number": clue_number}
        elif self.strategy == "naive":
            input_data = {
                'name': self.name,
                'role': self.role,
                'words_on_board': observation["words_on_board"],
            }
            answer = self.agent.make_decision(input_data, prompts="prompts/codenames_clue.prompt")
        elif self.strategy == "human":
            clue = self.human_input['clue']
            clue_number = self.human_input['clueNumber']
            answer = {"clue": clue, "clue_number": clue_number}
        elif self.strategy == "replay":
            if not self.replay_actions:
                clue = self.get_human_input(f"{self.name} clue")
                clue_number = self.get_human_input(f"{self.name} clue number")
                answer = {"clue": clue, "clue_number": clue_number}
            else:
                answer = self.replay_actions.pop(0)
        return {
            "name": self.name,
            "role": self.role,
            "topic": "give_clue",
            "answer": answer
        }

    def make_guess(self, observation):
        if self.strategy == "random":
            available_words = observation["current_available_words"]
            guessed_word = random.choice(available_words)
            answer = {"guess": guessed_word}
        elif self.strategy == "naive":
            input_data = {
                'name': self.name,
                'role': self.role,
                'words_on_board': observation["words_on_board"],
                'clue': observation["current_clue"],
                'number': observation["current_clue_number"],
            }
            answer = self.agent.make_decision(input_data, prompts="prompts/codenames_guess.prompt")
        elif self.strategy == "human":
            guessed_word = self.human_input['guess']
            answer = {"guess": guessed_word}
        elif self.strategy == "replay":
            if not self.replay_actions:
                guessed_word = self.get_human_input(f"{self.name} guess")
                answer = {"guess": guessed_word}
            else:
                answer = self.replay_actions.pop(0)
        return {
            "name": self.name,
            "role": self.role,
            "topic": "guess",
            "answer": answer
        }
