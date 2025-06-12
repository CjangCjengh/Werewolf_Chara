import numpy as np
import random
from observation.observation import Observation

import time 
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import gradio as gr
import random
import threading

t = time.time()

class HanabiGameObservation(Observation):
    
    def __init__(self, config = None):
        super().__init__()
        
        self.init()
    
    def init(self):
        
        self.colors = ["white", "red", "blue", "yellow", "green"]
        self.values = [1, 1, 1, 2, 2, 3, 3, 4, 4, 5]
        
        self.discard_pile = []
        self.clue_tokens = 8 # can not be negative, cannot over 8
        self.error_tokens = 0  # if accumulated to 3, game over
        self.played_cards = {color: [] for color in self.colors}

        self.clue_record = {
            "player1": [],
            "player2": []
        }
        
        # Create the deck of cards
        self.deck = [(color, value) for color in self.colors for value in self.values]
        random.shuffle(self.deck)

        self.players_hands = {
            "player1": [self.deck.pop() for _ in range(5)],
            "player2": [self.deck.pop() for _ in range(5)]
        }
        
        self.log = []
    
    def logging(self, content):
        self.log.append(content)
        
        print(content)
        
        # save to a file named obs-<timestamp>.log
        if not os.path.exists("logs/hanabi"):
            os.makedirs("logs/hanabi")
        with open(f"logs/hanabi/obs-{t}.log", "a") as f:
            f.write(str(content) +"\n")
        
        
    def game_over(self):
        # game over 的三个情况
        # 1. error tokens == 3 当错误次数达到3次  
        # 2. 当完全成功
        # 3. 当牌堆用完
        return self.error_tokens == 3 or all([len(self.played_cards[color]) == 5 for color in self.colors]) or not self.deck
    
    def game_continue(self):
        return not self.game_over()
    
    def process_give_clue(self, responses):
            
        name = responses[0]['name']
        role = responses[0]['role']
        answer = responses[0]['answer']
        hint_getter = answer['to']
        
        clue = answer['clue']
        clue_list = []
        
        success = False
        # for card in :
        for i, (color, value) in enumerate(self.players_hands[hint_getter]):
            if clue in [color, str(value)]:
                clue_list.append((i+1, clue))
                success = True
                
        if success:
            self.clue_tokens -= 1
            self.clue_record[hint_getter] += (clue_list)
        
        ret = {"state": f"p{role[-1]}_give_clue", "clue": answer, "success": success}
        self.logging(ret)
        return ret
    
    def process_play_card(self, responses):
            
        name = responses[0]['name']
        role = responses[0]['role']
        answer = responses[0]['answer']
        
        choice = int(answer["index"])
        
        success = False
        if choice < 1 or choice > len(self.players_hands[role]): # 选择出现错误
            success = False
        else:
            success = True

            # remove the card from the clue list
            self.clue_record[role] = [(i, clue) for i, clue in self.clue_record[role] if i != choice]
            
            card = self.players_hands[role][choice-1]
            color, value = card
        
            if value == len(self.played_cards[color]) + 1:
                self.played_cards[color].append(value)
            else:
                self.error_tokens += 1
                self.discard_pile.append(card)
            
            if self.deck:
                self.players_hands[role][choice-1] = self.deck.pop()
            
        ret =  {"state": f"p{role[-1]}_play_card", "card": choice, "success": success}
        self.logging(ret)

        return ret
    
    def process_discard_card(self, responses):
            
        name = responses[0]['name']
        role = responses[0]['role']
        answer = responses[0]['answer']
        choice = int(answer['index'])
        
        success = False
        if choice < 1 or choice > len(self.players_hands[role]): # 选择出现错误
            success = False
        else:
            success = True

            card = self.players_hands[role][choice-1]
            self.discard_pile.append(card)
            
            self.clue_tokens = min(8, self.clue_tokens + 1)
            if self.deck:
                self.players_hands[role][choice-1] = self.deck.pop()
            
        ret = {"state": f"p{role[-1]}_discard_card", "card": choice, "success": success}
        self.logging(ret)

        return ret
    
    def process_choose_action(self, responses):
        
        name = responses[0]['name']
        role = responses[0]['role']
        answer = responses[0]['answer']
            
        if answer['choice'] == "A":
            ret = {"state": f"p{role[-1]}_choose_action", "choice": "give_clue"}
        elif answer['choice'] == "B":
            ret = {"state": f"p{role[-1]}_choose_action", "choice": "play_card"}
        elif answer['choice'] == "C":
            ret = {"state": f"p{role[-1]}_choose_action", "choice": "discard_card"}
        else:
            ret = {"state": f"p{role[-1]}_choose_action", "choice": "unkown"} # 出错
            
        self.logging(ret)
        return ret
    

    def create_image(self):
        # Create the Plotly figure for Hanabi game state
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                "Player 1's Hand", "Player 2's Hand",
                "Played Cards", "Discard Pile", 
                "Clue Tokens & Error Tokens",  "Remaining Deck Cards"
            ),
            specs=[[{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}], 
                   [{"type": "scatter"}, {"type": "scatter"}, {"type": "scatter"}]]
        )

        # Player Hands Visualization
        for i, (player, hand) in enumerate(self.players_hands.items()):
            row, col = (1, i + 1)
            x_vals = [j for j in range(len(hand))]
            y_vals = [0] * len(hand)
            colors = [color for color, _ in hand]
            text = [f"{color}-{value}" for color, value in hand]
            fig.add_trace(
                go.Scatter(
                    x=x_vals, y=y_vals, mode="markers+text",
                    marker=dict(color=colors, size=20, symbol="square"),
                    text=text, textposition="top center",
                    showlegend=False
                ),
                row=row, col=col
            )

        # Played Cards Visualization
        played_x_vals = []
        played_y_vals = []
        played_colors = []
        played_text = []

        for i, color in enumerate(self.colors):
            played_x_vals.extend([i] * len(self.played_cards[color]))
            played_y_vals.extend(list(range(len(self.played_cards[color]))))
            played_colors.extend([color] * len(self.played_cards[color]))
            played_text.extend([str(value) for value in self.played_cards[color]])

        fig.add_trace(
            go.Scatter(
                x=played_x_vals, y=played_y_vals, mode="markers+text",
                marker=dict(color=played_colors, size=20, symbol="square"),
                text=played_text, textposition="top center",
                showlegend=False
            ),
            row=1, col=3
        )

        # Discard Pile Visualization
        discard_x_vals = [i % 5 for i in range(len(self.discard_pile))]
        discard_y_vals = [i // 5 for i in range(len(self.discard_pile))]
        discard_colors = [color for color, _ in self.discard_pile]
        discard_text = [f"{color}-{value}" for color, value in self.discard_pile]
        fig.add_trace(
            go.Scatter(
                x=discard_x_vals, y=discard_y_vals, mode="markers+text",
                marker=dict(color=discard_colors, size=20, symbol="square"),
                text=discard_text, textposition="top center",
                showlegend=False
            ),
            row=2, col=1
        )

        # Clue Tokens Visualization
        clue_x = [i for i in range(self.clue_tokens)]
        clue_y = [1] * self.clue_tokens
        fig.add_trace(
            go.Scatter(
                x=clue_x, y=clue_y, mode="markers+text",
                marker=dict(color="blue", size=20, symbol="circle"),
                text=["Clue"] * self.clue_tokens, textposition="top center",
                showlegend=False
            ),
            row=2, col=2
        )

        # Error Tokens Visualization
        error_x = [i for i in range(self.error_tokens)]
        error_y = [0] * self.error_tokens
        fig.add_trace(
            go.Scatter(
                x=error_x, y=error_y, mode="markers+text",
                marker=dict(color="red", size=20, symbol="circle"),
                text=["Error"] * self.error_tokens, textposition="top center",
                showlegend=False
            ),
            row=2, col=2
        )

        # Remaining Cards in Deck Visualization
        fig.add_trace(
            go.Scatter(
                x=[4.5], y=[0.5], mode="markers+text",
                marker=dict(color="gray", size=40, symbol="square"),
                text=[f"{len(self.deck)} cards"], textposition="middle center",
                showlegend=False
            ),
            row=2, col=3
        )

        fig.update_layout(
            height=800, width=1200,
            title_text="Hanabi Game State Visualization",
            showlegend=False
        )

        # Adjust subplot layouts
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)

        return fig


    def display_with_gradio(self):
        def render_game_state():
            # Create the Plotly figure
            fig = self.create_image()
            # Generate logs as HTML
            log_html = "\n".join([f"<p>{log_entry}</p>" for log_entry in self.log])
            return fig, log_html

        with gr.Blocks() as demo:
            with gr.Row():
                gr.Markdown("## Hanabi Game State and Logs")
            with gr.Row():
                plot = gr.Plot(label="Game State Visualization")
                log_output = gr.HTML(label="Game Logs")

            demo.load(render_game_state, inputs=None, outputs=[plot, log_output])

        # Start the Gradio app without blocking the main thread
        thread = threading.Thread(target=demo.launch, kwargs={"server_name": "127.0.0.1", "server_port": 7860})
        thread.daemon = True  # Ensure the thread does not prevent the program from exiting
        thread.start()
    
    def __str__(self):
        # Formatting player hands
        hands_summary = "\n".join(
            [f"{player}: {', '.join([f'{color}-{value}' for color, value in hand])}"
            for player, hand in self.players_hands.items()]
        )
        
        # Formatting played cards
        played_summary = "\n".join(
            [f"{color}: {', '.join(map(str, values))}" for color, values in self.played_cards.items()]
        )
        
        # Formatting discard pile
        discard_summary = ", ".join([f"{color}-{value}" for color, value in self.discard_pile])
        
        # Summary string
        summary = (
            f"Hanabi Game Observation:\n"
            f"Clue Tokens: {self.clue_tokens}\n"
            f"Error Tokens: {self.error_tokens}\n"
            f"Deck Remaining: {len(self.deck)} cards\n\n"
            f"Player Hands:\n{hands_summary}\n\n"
            f"Played Cards:\n{played_summary}\n\n"
            f"Discard Pile: {discard_summary}\n"
            f"Clue Records: {self.clue_record}\n"
        )
        
        return summary
