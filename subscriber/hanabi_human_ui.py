### ./subscriber/hanabi_human_ui.py ###

import threading
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO

from subscriber.subscriber import Subscriber

class HanabiUI(Subscriber):
    def __init__(self, config):
        name = config['name']
        role = config['role']
        strategy = config['strategy']
        model = config['model'] if 'model' in config else None
        super().__init__(name, role)
        self.strategy = strategy
        self.current_observation = None  # To store the latest observation
        self.current_image_base64 = None  # To store the latest image
        self.current_topic = None  # To store the current topic
        self.human_input = {}  # To store input from the web UI
        self.input_event = threading.Event()  # To manage input waiting
        self.notify_event = threading.Event()  # To signal new observation

        self.port = config.get("port", 5004)
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app)
        self.start_flask_app()

    def start_flask_app(self):
        @self.app.route('/')
        def index():
            observation_html = ''.join(
                f'<div style="background-color: {["#f0f0f0", "#ffffff"][i % 2]}; padding: 5px;">{key}: {json.dumps(value)}</div>'
                for i, (key, value) in enumerate(self.current_observation.items())
            ) if self.current_observation else "No observation yet."
            return render_template('hanabi.html', name=self.name, role=self.role, observation_html=observation_html, image_base64=self.current_image_base64)

        @self.app.route('/current_observation', methods=['GET'])
        def current_observation():
            observation_html = ''.join(
                f'<div style="background-color: {["#f0f0f0", "#ffffff"][i % 2]}; padding: 5px;">{key}: {json.dumps(value)}</div>'
                for i, (key, value) in enumerate(self.current_observation.items())
            ) if self.current_observation else "No observation yet."
            return jsonify({"observation_html": observation_html, "topic": self.current_topic})

        @self.app.route('/submit_action', methods=['POST'])
        def submit_action():
            self.human_input = request.json
            self.input_event.set()
            return jsonify(success=True)
        def run_socketio():
            self.socketio.run(self.app, port=self.port, debug=True, use_reloader=False)

        threading.Thread(target=run_socketio).start()
        # threading.Thread(target=app.run, kwargs={'port': 5000, 'debug': True, 'use_reloader': False}).start()

    def notify(self, topic, message, image_base64, observation):
        self.current_observation = observation
        self.current_image_base64 = image_base64
        self.current_topic = topic
        self.notify_event.set()
        self.input_event.wait()
        self.input_event.clear()
        return self.process_human_action(topic)

    def process_human_action(self, topic):
        ret = {
            "name": self.name,
            "role": self.role,
            "topic": topic,
        }
        action = self.human_input.get('action')
        if action == 'give_clue':
            ret["clue"] = self.human_input.get('clue')
        elif action in ['play_card', 'discard_card']:
            ret["index"] = int(self.human_input.get('index'))

        return ret
