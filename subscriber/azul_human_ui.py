import random

from flask_socketio import SocketIO, emit

from subscriber.subscriber import Subscriber
from agent.naive_agent import NaiveAgent
import threading
from flask import Flask, render_template, request, jsonify
import base64

class AzulUI(Subscriber):
    def __init__(self, config):
        super().__init__(config["name"], role=config["role"])
        self.strategy = config["strategy"]
        self.agent = None
        self.current_observation = None  # To store the latest observation
        self.current_image_base64 = ""  # To store the latest observation image as base64

        self.human_input = ""  # To store input from the web UI
        self.input_event = threading.Event()  # To manage input waiting
        self.notify_event = threading.Event()  # To signal new observation

        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app)
        self.start_flask_app()
        

    def start_flask_app(self):
        @self.app.route('/')
        def index():
            observation_html = ''.join(
                f'<div style="background-color: {["#f0f0f0", "#ffffff"][i % 2]}; padding: 5px;">{key}: {value}</div>'
                for i, (key, value) in enumerate(self.current_observation.items())
            )
            return render_template('azul.html', name=self.name, role=self.role, observation_html=observation_html, image_base64=self.current_image_base64)

        @self.app.route('/submit_action', methods=['POST'])
        def submit_action():
            data = request.json
            self.human_input = f"{data['table']} {data['color']} {data['row']}"
            self.input_event.set()
            return jsonify(success=True)

        @self.socketio.on('connect')
        def handle_connect():
            if self.current_observation is not None:
                emit('update_observation', {
                    'observation': self.current_observation
                })

        def run_socketio():
            self.socketio.run(self.app, port=5002, debug=True, use_reloader=False)

        threading.Thread(target=run_socketio).start()
        # threading.Thread(target=app.run, kwargs={'port': 5002, 'debug': True, 'use_reloader': False}).start()

    def notify(self, topic, message, image_base64, observation):
        # self.logging(f"{self.name} ({self.role}) received message [{topic}]: {message}")
        self.current_observation = observation  # Update the current observation
        self.current_image_base64 = image_base64  # Update the current image

        # Emit the updated observation to all connected clients
        self.socketio.emit('update_observation', {
            'observation': self.current_observation
        })

        self.notify_event.set()
        self.input_event.wait()
        self.input_event.clear()
        return self.process_human_action(topic)

        
    def process_human_action(self, topic):
        try:
            table, color, row = self.human_input.split()
            table, row = int(table), int(row)
            return {
                "name": self.name,
                "role": self.role,
                "topic": topic,
                "table": table,
                "color": color,
                "row": row,
                "attempts": "1"
            }
        except ValueError:
            return None

