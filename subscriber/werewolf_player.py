import random
import threading
import gradio as gr
from agent.naive_agent import NaiveAgent
from agent.character_agent import CharacterAgent
from subscriber.subscriber import Subscriber
import asyncio
import re



class WerewolfGamePlayer(Subscriber):
    
    def __init__(self, config):
        super().__init__(config["name"], role=config["role"])
        self.strategy = config["strategy"]
        self.agent = None
        self.current_observation = None  # To store the latest observation
        self.context = [f'You are {self.name}. The game begins, and you have been assigned the role: {self.role}.']

        self.human_input = ""  # To store input from Gradio
        self.input_event = threading.Event()  # To manage input waiting
        self.notify_event = threading.Event()  # To signal new observation
        
        if self.strategy == "random":
            self.agent = None
        elif self.strategy == "naive":
            self.agent = NaiveAgent(config["model"])
        elif self.strategy == "character":
            self.agent = CharacterAgent(config["model"], config["character"], "werewolf")
        elif self.strategy == "human":
            self.agent = None
            self.init_gradio()
        elif self.strategy == "replay":
            self.agent = None
            if "replay" in config:
                self.replay_actions = config["replay"]
        else:
            raise ValueError(f"Invalid strategy: {self.strategy}")
    
    def load_prompt(self, prompt_file, input_data):
        """Read and return the content of the prompt file with placeholders replaced by input_data."""
        with open(prompt_file, 'r', encoding='utf-8') as file:
            prompt = file.read()
        
        # Replace placeholders in the prompt with values from input_data
        for key, value in input_data.items():
            placeholder = '{' + key + '}'
            prompt = prompt.replace(placeholder, str(value))
        
        return prompt

    def create_html(self, observation):
        # Initialize HTML content
        html_content = """
        <html>
            <head>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                    }
                    .container {
                        margin: 20px;
                    }
                    .key {
                        font-weight: bold;
                        color: #2F4F4F;
                    }
                    .value {
                        margin-left: 10px;
                    }
                    .list {
                        list-style-type: none;
                        padding: 0;
                    }
                    .list-item {
                        margin-bottom: 5px;
                    }
                    .section-title {
                        font-size: 1.5em;
                        margin-top: 20px;
                    }
                    .section {
                        margin-bottom: 20px;
                        padding: 10px;
                        border: 1px solid #DCDCDC;
                        border-radius: 8px;
                        background-color: #F5F5F5;
                    }
                </style>
            </head>
            <body>
                <div class="container">
        """

        # Function to render a key-value pair
        def render_key_value(key, value):
            if isinstance(value, dict):
                return f'<div class="key">{key}:</div><div class="value">{render_dict(value)}</div>'
            elif isinstance(value, list):
                return f'<div class="key">{key}:</div><div class="value">{render_list(value)}</div>'
            else:
                return f'<div class="key">{key}:</div><div class="value">{value}</div>'

        # Function to render dictionaries
        def render_dict(d):
            html = '<div class="section">'
            for k, v in d.items():
                html += render_key_value(k, v)
            html += '</div>'
            return html

        # Function to render lists
        def render_list(lst):
            html = '<ul class="list">'
            for item in lst:
                if isinstance(item, dict):
                    html += f'<li class="list-item">{render_dict(item)}</li>'
                else:
                    html += f'<li class="list-item">{item}</li>'
            html += '</ul>'
            return html

        # Render each key-value pair in the observation
        for key, value in observation.items():
            html_content += f'<div class="section-title">{key}</div>'
            html_content += f'<div class="value">{value}</div>'

        # Close the HTML content
        html_content += """
                </div>
            </body>
        </html>
        """

        return html_content

    def init_gradio(self):
        def render_game_state():
            # Generate HTML content with the latest observation
            html_content = self.create_html(self.current_observation)
            return html_content

        async def handle_user_input(user_input):
            # Store the user input
            self.human_input = user_input
            # Signal that input has been received
            self.input_event.set()
            
            # Wait asynchronously for the next notify call
            await asyncio.to_thread(self.notify_event.wait)
            
            # Capture the new observation
            monitored_observation = self.current_observation  # Get the latest observation from notify
            self.notify_event.clear()  # Reset the event for future notifications
            
            return self.create_html(monitored_observation)

        with gr.Blocks(css=".submit-button {width: 150px; padding: 5px;}") as demo:
            with gr.Row():
                gr.Markdown(f"## {self.name} ({self.role})")
            with gr.Row():
                self.html_output = gr.HTML(label="Game State Visualization")
            with gr.Row():
                self.input_box = gr.Textbox(label="Your Input")
                self.submit_button = gr.Button("Submit", elem_id="submit-button")

            self.submit_button.click(fn=handle_user_input, inputs=self.input_box, outputs=self.html_output)

            demo.load(render_game_state, inputs=None, outputs=self.html_output)

        # Start the Gradio app without blocking the main thread
        self.gradio_thread = threading.Thread(target=demo.launch, kwargs={"server_name": "127.0.0.1", "server_port": 7860})
        self.gradio_thread.daemon = True  # Ensure the thread does not prevent the program from exiting
        self.gradio_thread.start()

    def display_with_gradio(self):
        if self.strategy == "human" and self.current_observation:
            # Directly set the value of the HTML component to update it
            new_html_content = self.create_html(self.current_observation)
            self.html_output.value = new_html_content

    
    def notify(self, topic, message, image, observation):
        # self.logging(f"{self.name} ({self.role}) received message [{topic}]: {message}")

        # Update the observation to be used in rendering
        self.current_observation = observation
        
        # Update the Gradio interface
        self.input_event.clear()
        self.notify_event.set()
        
        self.display_with_gradio()

        # Decision-making logic based on the topic
        if topic == "day_vote":
            return self.day_vote(observation)
        elif topic == "wolf_action" and self.role == "werewolf":
            return self.werewolf_action(observation)
        elif topic == "witch_heal" and self.role == "witch":
            return self.witch_heal(observation)
        elif topic == "witch_poison" and self.role == "witch":
            return self.witch_poison(observation)
        elif topic == "hunter_action" and self.role == "hunter":
            return self.hunter_action(observation)
        elif topic == "seer_action" and self.role == "seer":
            return self.seer_action(observation)
        elif topic == "day_last_words":
            return self.say_last_words(observation)
        elif topic == "day_discuss":
            return self.day_discuss(observation)

    def get_human_input(self, prompt_file, input_data, options=None):
        """Prompt the human player for input using the specified prompt file."""
        prompt = self.load_prompt(prompt_file, input_data)
        
        if self.strategy == "human":
            # Update the label of the input box in Gradio UI
            self.input_box.label = prompt

            # Print the prompt in the console for debugging
            # print(prompt)

            # Add the prompt to the current observation
            if self.current_observation:
                self.current_observation['prompt'] = prompt

            # Show the prompt in the HTML
            # self.display_with_gradio()

            # Wait for the user to input through Gradio interface
            self.input_event.wait()  # This will block until self.input_event.set() is called

            # Return the collected human input
            user_input = self.human_input
            self.human_input = ""  # Reset the human input for the next interaction
            return user_input

        # else:
        #     if options:
        #         prompt += f" ({', '.join(options)})"
        #     choice = input(prompt + ": ")
        #     if options and choice not in options:
        #         print(f"Invalid choice. Please choose from {options}.")
        #         return self.get_human_input(prompt_file, options)
        #     return choice

    def day_vote(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }
        prompt_file = "prompts/werewolf_vote.prompt"

        if self.strategy == "random":
            alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
            vote = random.choice(alive_players)
            answer = {"vote": vote, "reason": "随机投票"}
            
        elif self.strategy in ["naive", "character"]:
            answer = self.agent.make_decision(input_data, prompts="prompts/werewolf_vote.prompt", context=self.context)

        elif self.strategy == "human":
            alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
            vote = self.get_human_input(prompt_file, input_data, alive_players)
            answer = {"vote": vote, "reason": "human"}
            
        elif self.strategy == "replay":
            if not self.replay_actions:
                alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
                vote = self.get_human_input(f"{self.name} 请选择你要投票驱逐的玩家", input_data, alive_players)
                answer = {"vote": vote, "reason": "replay (manual)"}
            else:
                answer = self.replay_actions.pop(0)

        return {
          "name": self.name,
          "role": self.role,
        #   "prompt": self.load_prompt(prompt_file, input_data),
          "answer": answer
        }


    def werewolf_action(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }
        prompt_file = "prompts/werewolf_wolf.prompt"

        if self.strategy == "random":
            alive_players = input_data['alive_players']
            target = random.choice(alive_players)
            answer = {"target": target, "reason": "随机投票"}
            
        elif self.strategy in ["naive", "character"]:
            answer = self.agent.make_decision(input_data, prompts="prompts/werewolf_wolf.prompt", context=self.context)
            
        elif self.strategy == "human":
            alive_players = input_data['alive_players']
            target = self.get_human_input(prompt_file, input_data, alive_players)
            answer = {"target": target, "reason": "human input"}
        
        elif self.strategy == "replay":
            if not self.replay_actions:
                alive_players = input_data['alive_players']
                target = self.get_human_input(f"{self.name} 请选择你要攻击的玩家", input_data, alive_players)
                answer = {"target": target, "reason": "human input"}
            else:
                answer = self.replay_actions.pop(0)

        ret = {
            "name": self.name,
            "role": self.role,
            # "prompt": self.load_prompt(prompt_file, input_data),
            "answer": answer
        }
        # self.logging(ret)
        return ret


    def witch_heal(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }
        prompt_file = "prompts/werewolf_heal.prompt"

        if self.strategy == "random":
            choice = random.choice(["True", "False"])
            answer = {"heal": choice}
        elif self.strategy in ["naive", "character"]:
            answer = self.agent.make_decision(input_data, prompts="prompts/werewolf_heal.prompt", context=self.context)
        elif self.strategy == "human":
            choice = self.get_human_input(prompt_file, input_data, ["True", "False"])
            answer = {"heal": choice}
        elif self.strategy == "replay":
            if not self.replay_actions:
                choice = self.get_human_input(f"{self.name} 你想要使用解药吗？(Yes/No)", input_data, ["Yes", "No"]) == "Yes"
                answer = {"heal": choice}
            else:
                answer = self.replay_actions.pop(0)

        return {
            "name": self.name,
            "role": self.role,
                    #   "prompt": self.load_prompt(prompt_file, input_data),

            "answer": answer,
        }


    def witch_poison(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }
        prompt_file = "prompts/werewolf_poison.prompt"

        if self.strategy == "random":
            alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
            if random.choice([True, False]):  # 随机决定是否使用毒药
                target = random.choice(alive_players)
            else:
                target = -1
            
            answer = {"target": target}
        elif self.strategy in ["naive", "character"]:
            answer = self.agent.make_decision(input_data, prompts="prompts/werewolf_poison.prompt", context=self.context)
            
        elif self.strategy == "human":
            alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
            target = self.get_human_input(prompt_file, input_data, alive_players + ["-1"])
            answer = {"target": target}
            
        elif self.strategy == "replay":
            if not self.replay_actions:
                alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
                target = self.get_human_input(f"{self.name} 你想要使用毒药杀死哪位玩家？(输入玩家名字或-1放弃)", input_data, alive_players + ["-1"])
                target = -1 if target == "-1" else target
                answer = {"target": target}
            else:
                answer = self.replay_actions.pop(0)

        ret =  {
            "name": self.name,
            "role": self.role,
                    #   "prompt": self.load_prompt(prompt_file, input_data),

            "answer": answer,
        }
        # self.logging(ret)
        return ret


    def hunter_action(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }
        prompt_file = "prompts/werewolf_hunt.prompt"

        if self.strategy == "random":
            alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
            if random.choice([True, False]):  # 随机决定是否开枪
                target = random.choice(alive_players)
            else:
                target = -1
            
            answer = {"hunt": target}
            
        elif self.strategy in ["naive", "character"]:
            answer = self.agent.make_decision(input_data, prompts="prompts/werewolf_hunt.prompt", context=self.context)
        
        elif self.strategy == "human":
            alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive" and player != self.name]
            target = self.get_human_input(prompt_file, input_data, alive_players + ["-1"])
            target = -1 if target == "-1" else target
            answer = {"hunt": target}
        
        elif self.strategy == "replay":
            if not self.replay_actions:
                alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive" and player != self.name]
                target = self.get_human_input(f"{self.name} 你想要猎杀哪位玩家？(输入玩家名字或-1放弃)", input_data, alive_players + ["-1"])
                target = -1 if target == "-1" else target
                answer = {"hunt": target}
            else:
                answer = self.replay_actions.pop(0)

        ret = {
            "name": self.name,
            "role": self.role,
                    #   "prompt": self.load_prompt(prompt_file, input_data),

            "answer": answer,
        }
        # self.logging(ret)
        return ret


    def seer_action(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }
        prompt_file = "prompts/werewolf_seer.prompt"

        if self.strategy == "random":
            alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
            check_player = random.choice(alive_players)
            answer = {"player": check_player}
            
        elif self.strategy in ["naive", "character"]:
            answer = self.agent.make_decision(input_data, prompts="prompts/werewolf_seer.prompt", context=self.context)
        
        elif self.strategy == "human":
            alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
            check_player = self.get_human_input(prompt_file, input_data, alive_players)
            answer = {"player": check_player}
         
        elif self.strategy == "replay":
            if not self.replay_actions:
                alive_players = [player["name"] for player in observation["players"] if player["status"] == "alive"]
                check_player = self.get_human_input(f"{self.name} 请选择你要占卜的玩家", input_data, alive_players)
                answer = {"player": check_player}
            else:
                answer = self.replay_actions.pop(0)

        ret = {
            "name": self.name,
            "role": self.role,
                    #   "prompt": self.load_prompt(prompt_file, input_data),

            "answer": answer
        }
        # self.logging(ret)
        return ret

    def say_last_words(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }
        prompt_file = "prompts/werewolf_last_words.prompt"

        if self.strategy == "random":
            message = self.name + ": " + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=6))
            answer = {"last_words": message}
            
        elif self.strategy == "human":
            message = self.get_human_input(prompt_file, input_data)
            answer = {"last_words": message}
            
        elif self.strategy in ["naive", "character"]:
            answer = self.agent.make_decision(input_data, prompts="prompts/werewolf_last_words.prompt", context=self.context)
            
        elif self.strategy == "replay":
            if not self.replay_actions:
                message = self.get_human_input(f"{self.name} 请留遗言", input_data)
                answer = {"last_words": message}
            else:
                answer = self.replay_actions.pop(0)

        ret = {
            "name": self.name,
            "role": self.role,
                    #   "prompt": self.load_prompt(prompt_file, input_data),

            "answer": answer
        }
        # self.logging(ret)
        return ret
    
    
    def day_discuss(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }
        prompt_file = "prompts/werewolf_discuss.prompt"

        if self.strategy == "random":
            message = self.name + ": " + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=6))
            answer = {"discuss": message}
            
        elif self.strategy in ["naive", "character"]:
            answer = self.agent.make_decision(input_data, prompts="prompts/werewolf_discuss.prompt", context=self.context)

        elif self.strategy == "human":
            message = self.get_human_input(prompt_file, input_data)
            answer = {"discuss": message}
            
        elif self.strategy == "replay":
            if not self.replay_actions:
                message = self.get_human_input(f"{self.name} 请发表你的讨论观点", input_data)
                answer = {"discuss": message}
            else:
                answer = self.replay_actions.pop(0)

        ret = {
            "name": self.name,
            "role": self.role,
                    #   "prompt": self.load_prompt(prompt_file, input_data),

            "answer": answer
        }
        return ret
    
    
    def last_words(self, observation):
        input_data = {
            'name': self.name,
            'role': self.role,
            'state': observation["current_state"],
            'player_list': [player["name"] for player in observation["players"]],
            'alive_players': [player["name"] for player in observation["players"] if player["status"] == "alive"],
            'observation': observation,
            'fail_case': observation.get("current_fail_case", []),
        }

        if self.strategy == "random":
            message = self.name + ": " + ''.join(random.choices("abcdefghijklmnopqrstuvwxyz", k=6))
            answer = {"last_words": message}
            
        elif self.strategy == "human":
            prompt_file = "prompts/werewolf_last_words.prompt"
            message = self.get_human_input(prompt_file, input_data)
            answer = {"last_words": message}
        elif self.strategy in ["naive", "character"]:
            answer = self.agent.make_decision(input_data, prompts="prompts/werewolf_last_words.prompt", context=self.context)        
        
        ret = {
            "name": self.name,
            "role": self.role,
                    #   "prompt": self.load_prompt(prompt_file, input_data),

            "answer": answer
        }
        # self.logging(ret)
        return ret
