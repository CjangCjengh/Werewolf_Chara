import requests
from flask import Flask, render_template, request, jsonify
import threading
import asyncio
import json
import re

# from logger import logger
from agent.naive_agent import NaiveAgent
from subscriber.subscriber import Subscriber
from agent.extractor import Extractor

app = Flask(__name__)

def find_poker_cards(text):
    pattern = r'((?:[3-9]|10|[JQKA2])[♠♥♣♦]|小王|大王)'
    matches = re.findall(pattern, text)
    return matches

def monitor_notify_method(func):
    def wrapper(self, *args, **kwargs):
        self.monitored_notify_args = args
        self.monitored_notify_kwargs = kwargs
        return func(self, *args, **kwargs)
    return wrapper

class LandlordGamePlayer(Subscriber):
    def __init__(self, name, role, strategy, model):
        super().__init__(name, role)
        self.current_observation = None
        self.human_observation = None
        self.human_candidate_action = []
        self.human_locker = threading.Lock()
        self.human_input = None
        self.notify_event = asyncio.Event()
        self.strategy = strategy
        if strategy == "random":
            self.agent = None
        elif strategy == "langchain":
            self.agent = NaiveAgent(model)
        elif strategy == 'human':
            self.agent = None
            self.init_flask()
        self.name = name

    def init_flask(self):
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

        def run_app():
            try:
                self.app.run(host='127.0.0.1', port=7860)
            except Exception as e:
                print(f"Error running Flask app: {e}")

        self.app_thread = threading.Thread(target=run_app)
        self.app_thread.daemon = True
        self.app_thread.start()
        self.input_fn = input

    def display_with_html(self):
        if self.strategy == "human" and self.current_observation:
            new_html_content = self.create_html(self.current_observation)
            # Send the new content to the frontend
            self.html_output = new_html_content
            self.input_box_choices = self.current_observation.cards_in_hand[2]

    @monitor_notify_method
    def notify(self, topic, message, image, observation):
        self.display_with_html()
        # self.notify_event.set()
        if topic == "start":
            return None
        elif topic == "deal":
            return None
        elif topic == "first_bidding":
            return self.bidding(observation)
        elif topic == "second_bidding":
            return self.bidding(observation)
        elif topic == "third_bidding":
            return self.bidding(observation)
        elif topic == "forth_bidding":
            return self.bidding(observation)
        elif topic == "first_playing":
            return self.play_card(observation)
        elif topic == "second_playing":
            return self.play_card(observation)
        elif topic == "third_playing":
            return self.play_card(observation)
        elif topic == "game_over":
            return None
        else:
            raise NotImplementedError()

    def play_card(self, observation):
        ob = observation.to_json()
        inputs = {
            'current_player': ob.get('current_player'),
            'condition': f"大于{observation.last_playing}的牌型" if observation.last_playing else "任意",
            'current_cards': ob.get('cards_in_hand')[ob.get('current_player')],
            'landlord_player': ob.get('landlord_player'),
            'bottom_cards': ob.get('bottom_cards'),
            'past_record': ob.get('past_record'),
            'candidate_action': ob.get('cards_in_hand')[ob.get('current_player')]
        }
        if self.strategy == "human":
            self.human_candidate_action = ob.get('cards_in_hand')[ob.get('current_player')]
            self.current_observation = observation
            response = self.get_human_input("play_card", inputs)
        elif self.strategy == 'random':
            response = {}
        else:
            response = self.agent.make_decision(inputs, "prompts/landlord_play_card.prompt")
        action_list = response.get('action', [])
        return action_list

    def bidding(self, observation):
        ob = observation.to_json()
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
        if self.strategy == "human":
            self.human_candidate_action = ["True", "False"]
            self.current_observation = observation
            response = self.get_human_input("bidding", inputs)
            # response = self.human_response
        elif self.strategy == 'random':
            response = {}
        else:
            response = self.agent.make_decision(inputs, "prompts/landlord_bidding.prompt")
        action = response.get('action', 'False')
        if 'true' in action.lower():
            return True
        else:
            return False

    def get_human_input(self, topic, inputs):
        if self.strategy == "human":
            # Update the label and choices of the input box
            self.input_box_label = topic
            self.input_box_choices = inputs.get('candidate_action', [])

            # Render the updated state to the HTML output
            self.display_with_html()

            # Send updated state to the frontend
            data = {
                "topic": topic,
                "inputs": inputs,
                "html_content": self.html_output,
                "choices": self.input_box_choices
            }
            requests.post('http://127.0.0.1:7860/update', json=data)
            # self.current_observation = None

            # 等待用户提交动作
            def wait():
                while True:
                    if self.human_input is not None:
                        break

            # Wait for the human input to be set
            wait()
            # print("Wait for the human input",self.notify_event.is_set())
            # async def wait():
            #     await self.notify_event.wait()
            #
            # self.notify_event.set()
            # print("Wait for the human input", self.notify_event.is_set())
            # wait()
            # # Reset the event for the next use
            # self.notify_event.clear()

            # Return the collected human input
            user_input = self.human_input
            self.human_input = None  # Reset the human input for the next interaction

            if topic == "play_card":
                answer = {"action": user_input, "reason": "human input"}
            elif topic == "bidding":
                answer = {"action": user_input[0], "reason": "human input"}
            self.human_response = answer
            return answer
        self.human_response = {"action": [], "reason": "human input"}
        return {"action": [], "reason": "human input"}
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

#
# import asyncio
# import json
# import re
# import threading
#
# import gradio as gr
#
# from logger import logger
#
# from agent.langchain_agent import LangchainAgent
# from subscriber.subscriber import Subscriber
# from agent.extractor import Extractor
#
#
# def find_poker_cards(text):
#     """
#     使用正则表达式在给定的字符串中找出所有扑克牌。
#
#     Args:
#         text (str): 需要查找扑克牌的字符串。
#
#     Returns:
#         list: 找到的所有扑克牌。
#     """
#     pattern = r'((?:[3-9]|10|[JQKA2])[♠♥♣♦]|小王|大王)'
#     matches = re.findall(pattern, text)
#     # cards = [match[0] + match[1] if isinstance(match, tuple) else match for match in matches]
#     return matches
#
#
# def monitor_notify_method(func):
#     def wrapper(self, *args, **kwargs):
#         # Store the arguments and keyword arguments for monitoring
#         self.monitored_notify_args = args
#         self.monitored_notify_kwargs = kwargs
#         return func(self, *args, **kwargs)
#
#     return wrapper
#
#
# class LandlordGamePlayer(Subscriber):
#     def __init__(self, name, role, strategy, model):
#         super().__init__(name, role)
#         self.current_observation = None  # To store the latest observation
#         self.human_input = ""  # To store input from Gradio
#         self.input_event = threading.Event()  # To manage input waiting
#         self.notify_event = threading.Event()  # To signal new observation
#
#         self.strategy = strategy
#         if strategy == "random":
#             self.agent = None
#         elif strategy == "langchain":
#             self.agent = LangchainAgent(model)
#         elif strategy == 'human':
#             self.agent = None
#             self.init_gradio()
#
#         self.name = name
#
#     def display_with_gradio(self):
#         if self.strategy == "human" and self.current_observation:
#             # Directly set the value of the HTML component to update it
#             new_html_content = self.create_html(self.current_observation)
#             self.html_output.update(value=new_html_content)
#             # self.input_box.choices = self.current_observation.cards_in_hand[2]
#             # self.input_box.update(choices=self.input_box.choices)
#
#     @monitor_notify_method
#     def notify(self, topic, message, image, observation):
#         self.current_observation = observation
#         # Update the Gradio interface
#         self.display_with_gradio()
#
#         # Reset the input event to wait for new input
#         self.input_event.clear()
#
#         # Signal that a new observation has been received
#         self.notify_event.set()
#
#         if topic == "start":
#             return None
#         elif topic == "deal":
#             return None
#         elif topic == "first_bidding":
#             return self.bidding(observation)
#         elif topic == "second_bidding":
#             return self.bidding(observation)
#         elif topic == "third_bidding":
#             return self.bidding(observation)
#         elif topic == "forth_bidding":
#             return self.bidding(observation)
#         elif topic == "first_playing":
#             return self.play_card(observation)
#         elif topic == "second_playing":
#             return self.play_card(observation)
#         elif topic == "third_playing":
#             return self.play_card(observation)
#         elif topic == "game_over":
#             return None
#         else:
#             raise NotImplementedError()
#
#     def play_card(self, observation):
#         ob = observation.to_json()
#         inputs = {
#             'current_player': ob.get('current_player'),
#             'condition': f"大于{observation.last_playing}的牌型" if observation.last_playing else "任意",
#             'current_cards': ob.get('cards_in_hand')[ob.get('current_player')],
#             'landlord_player': ob.get('landlord_player'),
#             'bottom_cards': ob.get('bottom_cards'),
#             'past_record': ob.get('past_record'),
#             'candidate_action': ob.get('cards_in_hand')[ob.get('current_player')]
#         }
#
#         if self.strategy == "human":
#             response = self.get_human_input("play_card", inputs)
#         elif self.strategy == 'random':
#             response = {}
#         else:
#             response = self.agent.make_decision(inputs, "prompts/landlord_play_card.prompt")
#         action_list = response.get('action', [])
#         return action_list
#
#     def bidding(self, observation):
#         ob = observation.to_json()
#         bidding_record = {}
#         for i, b in enumerate(ob.get('bidding', [])):
#             if b is True:
#                 bidding_record[f"{i}号玩家"] = "叫地主"
#             if b is False:
#                 bidding_record[f"{i}号玩家"] = "不叫地主"
#             if b is None:
#                 continue
#         inputs = {
#             'current_player': ob.get('current_player'),
#             'current_cards': ob.get('cards_in_hand')[ob.get('current_player')],
#             'bidding': f"{bidding_record}",
#             'candidate_action': ["True", "False"]
#         }
#
#         if self.strategy == "human":
#             response = self.get_human_input("bidding", inputs)
#         elif self.strategy == 'random':
#             response = {}
#         else:
#             response = self.agent.make_decision(inputs, "prompts/landlord_bidding.prompt")
#         action = response.get('action', 'False')
#         if 'true' in action.lower():
#             return True
#         else:
#             return False
#
#     def get_human_input(self, topic, inputs):
#         # print(json.dumps(inputs, indent=4, ensure_ascii=False))
#         if self.strategy == "human":
#             # Update the label of the input box in Gradio UI
#             # self.input_box.label = topic
#             # self.input_box.choices = inputs.get('candidate_action', [])
#             self.input_box.update(choices=inputs.get('candidate_action', []), label=topic)
#
#             # Print the prompt in the console for debugging
#             print(topic)
#
#             # Add the prompt to the current observation
#             # if self.current_observation:
#             #     self.current_observation['prompt'] = topic
#
#             # Show the prompt in the HTML
#             self.display_with_gradio()
#
#             # Wait for the user to input through Gradio interface
#             self.input_event.wait()  # This will block until self.input_event.set() is called
#
#             # Return the collected human input
#             user_input = self.human_input
#             self.human_input = ""  # Reset the human input for the next interaction
#             if topic == "play_card":
#                 # reply = input("选择出牌: ")
#                 answer = {"action": user_input, "reason": "human input"}
#             elif topic == "bidding":
#                 # reply = input("选择叫地主（True/False）: ")
#                 answer = {"action": user_input[0], "reason": "human input"}
#             return answer
#         return {"action": [], "reason": "human input"}
#
#     def create_html(self, observation):
#         html_content = f"""<div>
#         <h3>Playing History</h3>
#         {"</br>".join(observation.past_record)}
#         </div>
#         """
#         return html_content
#
#     def init_gradio(self):
#         def render_game_state():
#             # Generate HTML content with the latest observation
#             html_content = self.create_html(self.current_observation)
#             return html_content
#
#         async def handle_user_input(user_input):
#             # Store the user input
#             self.human_input = user_input
#             # Signal that input has been received
#             self.input_event.set()
#
#             # Wait asynchronously for the next notify call
#             await asyncio.to_thread(self.notify_event.wait)
#
#             # Capture the new observation
#             monitored_observation = self.current_observation  # Get the latest observation from notify
#             self.notify_event.clear()  # Reset the event for future notifications
#
#             return self.create_html(monitored_observation)
#
#         with gr.Blocks() as demo:
#             gr.Markdown("## 斗地主游戏")
#             with gr.Row():
#                 # player3_cards = gr.Textbox(label="Player 3 Cards",
#                 #                            interactive=False)
#                 self.html_output = gr.HTML(label="Game State Visualization")
#                 self.text_box = gr.Textbox(label="Playing History")
#                 self.input_box = gr.CheckboxGroup(choices=['3♣', '4♥', '4♠', '5♦', '6♠', '7♦', '8♦', '9♠', '9♣', '10♦', '10♣', 'J♥', 'K♣', 'A♦', 'A♣', '2♥', '大王'], label="Select Cards to Play")
#                 self.submit_button = gr.Button("Play Card")
#                 self.submit_button.click(fn=handle_user_input, inputs=self.input_box,
#                                          outputs=[self.html_output])
#
#         # Start the Gradio app without blocking the main thread
#         self.gradio_thread = threading.Thread(target=demo.launch,
#                                               kwargs={"server_name": "127.0.0.1", "server_port": 7860})
#         self.gradio_thread.daemon = True  # Ensure the thread does not prevent the program from exiting
#         self.gradio_thread.start()
#
#     def __repr__(self):
#         return f'{self.name}: {self.hand}'
