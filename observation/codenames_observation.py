import numpy as np
import random
from observation.observation import Observation

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gradio as gr
import random
import threading
import time 

t = time.time()


class CodenamesManager(Observation):
    def __init__(self):
        super().__init__()
        self.words_on_board = []
        self.guessed_words = []
        self.team_words = {"red": [], "blue": []}
        self.neutral_words = []
        self.assassin_word = None
        self.current_clue = None
        self.current_clue_number = None
        self.current_guess = None
        self.current_team = "red"  # Assuming the red team starts
        self.log = []
        self.current_responses = None
        self.current_guess_times = 0
        
        self.current_score = {"red": 0, "blue": 0}
        
        # self.init(config)

    def init(self, config):
        if config["mode"] == "replay" and "replay" in config:
            self.words_on_board = config["replay"]["words_on_board"]
            self.team_words = config["replay"]["team_words"]
            self.neutral_words = config["replay"]["neutral_words"]
            self.assassin_word = config["replay"]["assassin_word"]
            self.guessed_words = [] 
        else:
            # Initialize the game board with a set of words
            word_list = self.generate_word_list()
            random.shuffle(word_list)
            # print(word_list)
            # Assign words to teams and the assassin
            self.words_on_board = word_list[:25]  # Select the first 25 words for the board
            self.team_words["red"] = self.words_on_board[:8]  # Assign the first 8 words to the red team
            self.team_words["blue"] = self.words_on_board[8:17]  # Assign the next 9 words to the blue team
            self.neutral_words = self.words_on_board[17:24]  # The next 7 words are neutral
            self.assassin_word = self.words_on_board[24]  # The last word is the assassin
            
            self.guessed_words = []  # Start with no words guessed
            self.current_team = "red"  # Start with the red team
            
    def generate_word_list(self):
        # Load the word list from the specified file
        with open('resources/codenames/codenames_words.txt', 'r') as file:
            words = [line.strip() for line in file if line.strip()]
        return words

    def clue_format_incorrect(self):
        return not self.clue_format_correct()
    
    def clue_format_correct(self):
        # Check if the clue is a single word and check if clue is in the word on board
        # self.logging(f"is the clue only one word?: {len(self.current_clue.split()) == 1}")
        # self.logging(f"is the clue in the words on board?: {self.current_clue in self.words_on_board}")
        # self.logging(f"clue是否正确: {len(self.current_clue.split()) == 1 and self.current_clue not in self.words_on_board}")
        # return True
        return self.current_responses[0]['answer']['clue'] not in self.words_on_board
    
    def process_give_clue(self):
        
        self.current_team =  "red" if "red" in self.current_responses[0]["role"] else "blue"

        answer = self.current_responses[0]["answer"]
        self.current_clue = answer["clue"]
        self.current_clue_number = answer["clue_number"]
        
        self.logging({'state': 'give_clue'})
        self.logging(self.current_responses[0])
    
    def guess_format_correct(self):
        
        answer = self.current_responses[0]["answer"]
        if "guess" not in answer:
            return False
        
        guess = answer["guess"]
        if (guess not in self.words_on_board or guess in self.guessed_words) and guess != "-1":
            return False
        
        return True
    
    def guess_format_incorrect(self):
        return not self.guess_format_correct()
    
        
    def game_over(self):
        
        if self.current_responses[0]['answer']['guess'] == self.assassin_word:
            return True
        
        else:
            return False
        
        
    def game_not_over(self):
        return not self.game_over()
    
    def process_guess(self):
        
        self.current_guess = self.current_responses[0]["answer"]["guess"]
        
        self.current_guess_times += 1
        self.guessed_words.append(self.current_guess)
        
        if self.current_guess in self.team_words[self.current_team]:
            self.current_score[self.current_team] += 1
        elif self.current_guess not in self.team_words[self.current_team] and self.current_guess not in self.neutral_words:
            self.current_score[self.current_team] -= 1
        
        self.logging({'state': 'guess'})
        self.logging(self.current_responses[0]["answer"])
        # result = self.update_guessed_words(responses["guess"])
        # self.guess_result = result
        # return ret
        
        self.logging(f"current score: {self.current_score}")
        self.logging(f"current guess times: {self.current_guess_times}")
        self.logging(f"current guess: {self.current_guess}")
        self.logging(f"current team: {self.current_team}")
    
    
    def guess_not_over(self):
        return not self.guess_over()
    
    
    def guess_over(self):
        
        
        # for g in self.current_guess:
        #     if g in self.team_words["red"]:
        #         return False
            
        # self.logging(f"猜测是否正确: {self.current_guess in self.team_words['red']}")
        # if self.current_guess not in self.team_words["red"]:
        
        guess = self.current_responses[0]["answer"]["guess"]
        if guess not in self.team_words[self.current_team] or guess == "-1": # -1代表弃权
            return True
        
        if self.current_guess_times <= self.current_clue_number:
            return False
        else:
            return True
    
    
    def get_available_words(self):
        # Return a list of words that have not yet been guessed
        return [word for word in self.words_on_board if word not in self.guessed_words]

    def update_guessed_words(self, word):
        # Update the list of guessed words and check the result
        if word in self.words_on_board and word not in self.guessed_words:
            self.guessed_words.append(word)
            if word == self.assassin_word:
                return "assassin"
            elif word in self.team_words[self.current_team]:
                return "correct"
            elif word in self.team_words["red"] if self.current_team == "blue" else self.team_words["blue"]:
                return "opponent"
            else:
                return "neutral"
        return "invalid"

    # def switch_team(self, team):
    #     # Switch the turn to the other team
    #     self.current_team = team

    def is_game_over(self):
        # Check if the game is over (all words of one team or the assassin has been guessed)
        if self.assassin_word in self.guessed_words:
            return True
        
        for team in ["red", "blue"]:
            if all(word in self.guessed_words for word in self.team_words[team]):
                return True
        
        return False

    def logging(self, content):
        self.log.append(content)
        # for k, v in content_dict.items():
        #     self.logging(f"{k}: {v}")
        print(content)
            
        import os
        # save to a file named obs-<timestamp>.log
        if not os.path.exists("logs/codenames"):
            os.makedirs("logs/codenames")
        with open(f"logs/codenames/obs-{t}.log", "a") as f:
            f.write(str(content) +"\n")
        
    
    def create_image(self):
        # Initialize a subplot grid for the Codenames board
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Codenames Board", "Game Logs"),
            column_widths=[0.7, 0.3],
            specs=[[{"type": "table"}, {"type": "scatter"}]]
        )

        # Generate the data for the board table
        board_data = []
        for i, word in enumerate(self.words_on_board):
            status = "Neutral"
            if word in self.team_words["red"]:
                status = "Red"
            elif word in self.team_words["blue"]:
                status = "Blue"
            elif word == self.assassin_word:
                status = "Assassin"
            guessed = "Yes" if word in self.guessed_words else "No"
            board_data.append([word, status, guessed])

        # Add the table with the words and their status
        fig.add_trace(
            go.Table(
                header=dict(
                    values=["Word", "Team", "Guessed"],
                    fill_color='paleturquoise',
                    align='left'
                ),
                cells=dict(
                    values=[
                        [row[0] for row in board_data],  # Words
                        [row[1] for row in board_data],  # Team
                        [row[2] for row in board_data]   # Guessed
                    ],
                    fill_color=[['red' if row[1] == 'Red' else 'blue' if row[1] == 'Blue' else 'gray' if row[1] == 'Assassin' else 'white' for row in board_data],
                                ['white' for row in board_data],
                                ['lightgreen' if row[2] == 'Yes' else 'white' for row in board_data]],
                    align='left'
                )
            ),
            row=1, col=1
        )

        # Add game logs to the right side of the subplot
        # log_text = "<br>".join(self.log) if self.log else "No logs available"
        # fig.add_trace(
        #     go.Scatter(
        #         x=[0], y=[0],
        #         mode="text",
        #         text=[log_text],
        #         textposition="top left",
        #         showlegend=False
        #     ),
        #     row=1, col=2
        # )

        # Update layout for better visualization
        fig.update_layout(
            height=600, width=1200,
            title_text="Codenames Game State Visualization",
            showlegend=False
        )

        return fig
    
    
    def display_with_gradio(self):
        def render_game_state():
            # Create the Plotly figure
            fig = self.create_image()
            # Generate logs as HTML
            log_html = "\n".join([f"<p>{log_entry}</p>" for log_entry in self.log])
            return fig, log_html

        # Custom CSS to widen the plot component
        custom_css = """
        .gradio-container .js-plotly-plot {
            width: 80% !important;
            margin: auto;
        }
        """

        with gr.Blocks(css=custom_css) as demo:
            with gr.Row():
                gr.Markdown("## Codenames Game State and Logs")
            with gr.Row():
                plot = gr.Plot(label="Game State Visualization", min_width = 1200)
                log_output = gr.HTML(label="Game Logs")

            demo.load(render_game_state, inputs=None, outputs=[plot, log_output])

        # Start the Gradio app without blocking the main thread
        thread = threading.Thread(target=demo.launch, kwargs={"server_name": "127.0.0.1", "server_port": 7860})
        thread.daemon = True  # Ensure the thread does not prevent the program from exiting
        thread.start()