import random
import threading
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

from subscriber.subscriber import Subscriber
from agent.naive_agent import NaiveAgent

class CodenamesUI(Subscriber):
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

        self.port = config.get("port", 5003)
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app)
        self.start_flask_app()
            
        
        
    def start_flask_app(self):
        @self.app.route('/')
        def index():
            observation_html = ''.join(
                f'<div style="background-color: {["#f0f0f0", "#ffffff"][i % 2]}; padding: 5px; word-wrap: break-word;">{key}: {json.dumps(value)}</div>'
                for i, (key, value) in enumerate(self.current_observation.items())
            )
            return render_template('codenames.html', name=self.name, role=self.role, observation_html=observation_html, topic=self.current_topic)

        @self.app.route('/current_observation', methods=['GET'])
        def current_observation():
            return jsonify({"observation": self.current_observation, "topic": self.current_topic})

        @self.app.route('/submit_action', methods=['POST'])
        def submit_action():
            self.human_input = request.json['action']
            self.input_event.set()
            return jsonify(success=True)

        @self.socketio.on('connect')
        def handle_connect():
            if self.current_observation is not None:
                emit('update_observation', {
                    'topic': self.current_topic,
                    'observation': self.current_observation
                })
        def run_socketio():
            self.socketio.run(self.app, port=self.port, debug=True, use_reloader=False)

        threading.Thread(target=run_socketio).start()
        #threading.Thread(target=app.run, kwargs={'port': self.port, 'debug': True, 'use_reloader': False}).start()

    def notify(self, topic, message, image, observation):
        print(f"{self.name} ({self.role}) received message [{topic}]: {message}")
        self.current_observation = observation
        self.current_topic = topic

        # Emit the updated observation to all connected clients
        self.socketio.emit('update_observation', {
            'topic': self.current_topic,
            'observation': self.current_observation
        })

        self.notify_event.set()
        self.input_event.wait()
        self.input_event.clear()
        return self.process_human_action(topic)

    def process_human_action(self, topic):
        if topic.endswith("give_clue"):
            return self.give_clue(self.current_observation)
        elif topic.endswith("guess"):
            return self.make_guess(self.current_observation)
        return None


    def give_clue(self, observation):
            
        clue = self.human_input['clue']
        clue_number = self.human_input['clueNumber']
        answer = {"clue": clue, "number": clue_number}
        return {
            "name": self.name,
            "role": self.role,
            "topic": "give_clue",
            "answer": answer
        }

    def make_guess(self, observation):
            
        
        guessed_word = self.human_input['guess']
        answer = {"guess": guessed_word}
            
        return {
            "name": self.name,
            "role": self.role,
            "topic": "guess",
            "answer": answer
        }
