import random
import threading
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from subscriber.subscriber import Subscriber
import multiprocessing
import gevent
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler


def run_socketio(app):
    # self.socketio.run(self.app, port=5005, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
    http_server = WSGIServer(('127.0.0.1', 5005), app, handler_class=WebSocketHandler)
    http_server.serve_forever()
class SkyTeamUI(Subscriber):
    def __init__(self, config):
        super().__init__(config["name"], role=config["role"])
        
        self.strategy = config["strategy"]
        self.port = config.get("port",5005)
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
            return render_template('skyteam.html', name=self.name, role=self.role, observation_html=observation_html, image_base64=self.current_image_base64)

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
            self.reroll_dices = request.json['reroll_dices']
            self.input_event.set()
            return jsonify(success=True)

        @self.app.route('/submit_discussion', methods=['POST'])
        def submit_discussion():
            self.human_input = request.json['discussion']
            self.input_event.set()
            return jsonify(success=True)

        # def run_socketio():
        #     #self.socketio.run(self.app, port=5005, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
        #     http_server = WSGIServer(('127.0.0.1', 5005), self.app, handler_class=WebSocketHandler)
        #     http_server.serve_forever()

        # p = multiprocessing.Process(target=run_socketio,args=([self.app]))
        # p.start()
        def run_socketio():
            self.socketio.run(self.app, port=self.port, debug=True, use_reloader=False)

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
        if topic == "discuss":
            answer = {"discuss": self.human_input}
        elif "reroll" in topic:
            answer = {"dices": [self.current_observation["current_round_dices"][self.role][int(dice)-1] for dice in self.reroll_dices]}
        else:
            action, dice = self.human_input.split()
            dice = int(dice)
            answer = {"action": action, "dice": dice}

        return {
            "name": self.name,
            "role": self.role,
            "topic": topic,
            "answer": answer,
        }