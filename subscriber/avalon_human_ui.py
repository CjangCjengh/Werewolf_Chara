import random
import threading
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from subscriber.subscriber import Subscriber

class AvalonUI(Subscriber):
    def __init__(self, config):
        super().__init__(config["name"], role=config["role"])
        self.strategy = config["strategy"]
        self.current_observation = None
        self.current_image_base64 = None
        self.human_input = ""
        self.input_event = threading.Event()
        self.notify_event = threading.Event()
        self.current_topic = None
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app)
        self.start_flask_app()

    def start_flask_app(self):
        @self.app.route('/')
        def index():
            if self.current_observation is None:
                observation_html = ""
            else:
                observation_html = self.generate_observation_html()
            return render_template('avalon.html', name=self.name, role=self.role, observation_html=observation_html, image_base64=self.current_image_base64)

        @self.socketio.on('connect')
        def handle_connect():
            if self.current_observation is not None:
                emit('update_observation', {
                    'observation_html': self.generate_observation_html(),
                    'topic': self.current_topic,
                    'observation': self.current_observation
                })

        @self.app.route('/submit_action', methods=['POST'])
        def submit_action():
            self.human_input = request.json['action']
            self.input_event.set()
            return jsonify(success=True)

        def run_socketio():
            self.socketio.run(self.app, port=5001, debug=True, use_reloader=False)

        threading.Thread(target=run_socketio).start()

    def generate_observation_html(self):
        return ''.join(
            f'<div style="background-color: {["#f0f0f0", "#ffffff"][i % 2]}; padding: 5px;">{key}: {json.dumps(value)}</div>'
            for i, (key, value) in enumerate(self.current_observation.items())
        )

    def notify(self, topic, message, image_base64, observation):
        print(f"{self.name} {self.role} get message [{topic}]:{message}")
        self.current_observation = observation
        self.current_image_base64 = image_base64
        self.current_topic = topic

        self.socketio.emit('update_observation', {
            'observation_html': self.generate_observation_html(),
            'topic': self.current_topic,
            'observation': self.current_observation
        })

        self.notify_event.set()
        self.input_event.wait()
        self.input_event.clear()
        return self.process_human_action(topic)

    def process_human_action(self, topic):
        if topic == 'team_selection':
            answer = {"team": self.human_input.split()}
        elif topic == 'vote':
            answer = {"vote": self.human_input}
        elif topic == 'quest':
            answer = {"quest": self.human_input}
        elif topic == 'assassin':
            answer = {"target": self.human_input}
        else:
            answer = {"action": self.human_input}

        return {
            "name": self.name,
            "role": self.role,
            "topic": topic,
            "answer": answer,
        }
