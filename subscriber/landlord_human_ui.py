#!/usr/bin/env python 
# encoding: utf-8 
# @author: yihuai lan
# @fileName: landlord_human_ui.py 
# @date: 2024/8/1 14:17 
#
# describe:
#
import asyncio
import multiprocessing
import threading
from flask import Flask, render_template, request, jsonify
from flask_socketio import emit, SocketIO
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler

from subscriber.subscriber import Subscriber

class LandlordGameHumanUI(Subscriber):
    def __init__(self, config):
        print(config)
        super().__init__(config['name'], role=config['role'])
        self.strategy = config["strategy"]
        # self.port = config["port"]
        self.current_observation = None
        self.current_image_base64 = None
        self.human_input = ""
        self.input_event = threading.Event()
        self.notify_event = threading.Event()
        self.human_locker = threading.Lock()
        self.current_topic = None
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'secret!'
        self.socketio = SocketIO(self.app)
        self.start_flask_app()

    def start_flask_app(self):
        self.app = Flask(__name__)

        @self.app.route('/')
        def index():
            try:
                return render_template('landlord.html')
            except Exception as e:
                print(f"Error rendering template: {e}")
                return "Error rendering template", 500

        @self.app.route('/update', methods=['POST'])
        def update():
            try:
                data = request.json
                self.notify(data['topic'], data['message'], data['image'], data['observation'])
                return jsonify(success=True)
            except Exception as e:
                print(f"Error in update route: {e}")
                return jsonify(success=False, error=str(e)), 500

        @self.app.route('/input', methods=['POST'])
        def input():
            try:
                user_input = request.json.get('input')
                self.human_input = user_input
                self.notify_event.set()
                return jsonify(success=True)
            except Exception as e:
                print(f"Error in input route: {e}")
                return jsonify(success=False, error=str(e)), 500

        @self.app.route('/check_condition', methods=['GET'])
        def check_condition():
            self.human_locker.acquire()
            condition_met = self.current_observation is not None
            if condition_met:
                self.human_observation = self.current_observation
            self.current_observation = None
            self.human_locker.release()
            return jsonify(condition_met=condition_met)

        @self.app.route('/get_update', methods=['GET'])
        def get_update():
            if self.human_observation:
                playing_history_html = self.create_html(self.human_observation)
                candidate_action = self.human_candidate_action
                self.human_observation = None
                return jsonify(playing_history=playing_history_html, candidate_action=candidate_action)
            return jsonify(playing_history="", candidate_action=[])

        @self.socketio.on('connect')
        def handle_connect():
            if self.current_observation is not None:
                # data = {
                #     "topic": self.current_topic,
                #     "inputs": self.current_inputs,
                #     "html_content": self.html_output,
                #     "choices": self.input_box_choices
                # }
                emit('update_observation', {
                    "topic": self.current_topic,
                    "inputs": self.current_inputs,
                    "html_content": self.html_output,
                    "choices": self.input_box_choices
                })

        def run_app():
            try:
                self.app.run(host='127.0.0.1', port=7860)
            except Exception as e:
                print(f"Error running Flask app: {e}")
        def run_socketio():
            self.socketio.run(self.app, port=5007, debug=True, use_reloader=False)

        threading.Thread(target=run_socketio).start()
        # def run_socketio():
        #     # self.socketio.run(self.app, port=5005, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
        #     http_server = WSGIServer(('127.0.0.1', 5007), self.app, handler_class=WebSocketHandler)
        #     http_server.serve_forever()
        #
        # p = multiprocessing.Process(target=run_socketio)
        # p.start()

    def display_with_html(self):
        if self.strategy == "human" and self.current_observation:
            new_html_content = self.create_html(self.current_observation)
            # Send the new content to the frontend
            self.html_output = new_html_content
            self.input_box_choices = self.current_observation.cards_in_hand[2]

    def generate_observation_html(self):
        self.display_with_html()

    def notify(self, topic, message, image, observation):
        ob = observation.to_json()
        if topic in ["first_bidding","second_bidding","third_bidding","forth_bidding"]:
            bidding_record = {}
            for i, b in enumerate(ob.get('bidding', [])):
                if b is True:
                    bidding_record[f"{i}号玩家"] = "叫地主"
                if b is False:
                    bidding_record[f"{i}号玩家"] = "不叫地主"
                if b is None:
                    continue
            inputs = {
                'current_player': ob.get('current_player'),
                'current_cards': ob.get('cards_in_hand')[ob.get('current_player')],
                'bidding': f"{bidding_record}",
                'candidate_action': ["True", "False"]
            }
        elif topic in ["first_playing","second_playing","third_playing"]:
            inputs = {
                'current_player': ob.get('current_player'),
                'condition': f"大于{observation.last_playing}的牌型" if observation.last_playing else "任意",
                'current_cards': ob.get('cards_in_hand')[ob.get('current_player')],
                'landlord_player': ob.get('landlord_player'),
                'bottom_cards': ob.get('bottom_cards'),
                'past_record': ob.get('past_record'),
                'candidate_action': ob.get('cards_in_hand')[ob.get('current_player')]
            }
        else:
            inputs = {}
        print(f"{self.name} {self.role} get message [{topic}]:{message}")
        self.current_observation = observation
        self.display_with_html()
        self.current_inputs = inputs

        self.socketio.emit('update_observation',{
                    "topic": self.current_topic,
                    "inputs": self.current_inputs,
                    "html_content": self.html_output,
                    "choices": self.input_box_choices
                })

        self.notify_event.set()
        self.input_event.wait()
        self.input_event.clear()
        return self.process_human_action(topic)

    def process_human_action(self, topic):
        if topic in ["first_bidding","second_bidding","third_bidding","forth_bidding"]:
            answer = {"action": self.human_input, "reason": "human input"}
        elif topic in ["first_playing","second_playing","third_playing"]:
            answer = {"action": self.human_input, "reason": "human input"}
        else:
            answer = {"action": [], "reason": ""}

        return {
            "name": self.name,
            "role": self.role,
            "topic": topic,
            "answer": answer,
        }

    def create_html(self, observation):
        html_content = f"""<div>
        <h3>Playing History</h3>
        {"</br>".join(observation.past_record)}
        </div>
        <h3>Your Cards</h3>
        {"</br>".join(observation.cards_in_hand[2])}
        </div>
        <h3>Bidding History</h3>
        {observation.bidding}
        <h3>Landlord Player</h3>
        {observation.landlord_player+1 if observation.landlord_player else observation.landlord_player}
        """
        return html_content
