from transitions import Machine
from transitions.extensions import GraphMachine

from publisher.publisher import Publisher
from observation.hanabi_observation import HanabiGameObservation
from collections import Counter
import time
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import gradio as gr
import random
import threading
import pygame
from broker.hanabi_broker import HanabiGameBroker



class HanabiGameHost(Publisher):

    def __init__(self, config = None):
        # super().__init__()
        self.debug = False
        self.broker = HanabiGameBroker(config)
        
        self.create_fsm()
        
        self.config = config
        self.log_file = os.path.join(config['log_directory'], f"game.log")
        
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
        
        self.fail_case = None
        self.fail_cases = []
        
    
    def create_fsm(self):
        
        self.finite_states = [
            'start',
            'p1_choose_action',
            'p1_give_clue',
            'p1_discard_card',
            'p1_play_card',
            'p1_done',
            'p2_choose_action',
            'p2_give_clue',
            'p2_discard_card',
            'p2_play_card',
            'p2_done',
            'end'
        ]
        
        
        self.machine = GraphMachine(model=self, states=self.finite_states, initial='start', show_conditions=True)
        # self.machine_add_transitions()
        self.machine.add_transition(source='start', dest='p1_choose_action', trigger='game_start')  # 游戏开始，进入玩家1回合
        
        
        self.machine.add_transition(source='p1_choose_action', dest='p1_choose_action', trigger='choose_done', conditions='action_choose_incorrect')
        self.machine.add_transition(source='p1_choose_action', dest='p1_give_clue', trigger='choose_done', conditions = "choose_give_clue", after = 'process_choose_action') 
        self.machine.add_transition(source='p1_choose_action', dest='p1_play_card', trigger='choose_done', conditions = "choose_play_card", after = 'process_choose_action')
        self.machine.add_transition(source='p1_choose_action', dest='p1_discard_card', trigger='choose_done', conditions = "choose_discard_card", after = 'process_choose_action')

        self.machine.add_transition(source='p1_give_clue', dest='p1_give_clue', trigger='clue_given', conditions= ['clue_incorrect']) 
        self.machine.add_transition(source='p1_give_clue', dest='p1_done', trigger='clue_given', after = "process_give_clue") 
        
        self.machine.add_transition(source='p1_play_card', dest='p1_play_card', trigger='card_played', conditions= ['card_play_incorrect']) 
        self.machine.add_transition(source='p1_play_card', dest='p1_done', trigger='card_played', after = "process_play_card") 

        self.machine.add_transition(source='p1_discard_card', dest='p1_discard_card', trigger='card_discarded', conditions= ['card_discard_incorrect'])
        self.machine.add_transition(source='p1_discard_card', dest='p1_done', trigger='card_discarded', after = 'process_discard_card') 

        self.machine.add_transition(source='p1_done', dest='p2_choose_action', trigger='p1_turn_end', conditions= ['game_continue'])
        self.machine.add_transition(source='p1_done', dest='end', trigger='p1_turn_end', conditions= ['game_over'])
        
        self.machine.add_transition(source='p2_choose_action', dest='p2_choose_action', trigger='choose_done', conditions='action_choose_incorrect')  # 玩家1选择弃牌
        self.machine.add_transition(source='p2_choose_action', dest='p2_give_clue', trigger='choose_done', conditions = "choose_give_clue", after = 'process_choose_action')  # 玩家2选择提示
        self.machine.add_transition(source='p2_choose_action', dest='p2_play_card', trigger='choose_done', conditions = "choose_play_card", after = 'process_choose_action')  # 玩家2选择打出牌
        self.machine.add_transition(source='p2_choose_action', dest='p2_discard_card', trigger='choose_done', conditions = "choose_discard_card", after = 'process_choose_action')

        self.machine.add_transition(source='p2_give_clue', dest='p2_give_clue', trigger='clue_given', conditions= ['clue_incorrect']) 
        self.machine.add_transition(source='p2_give_clue', dest='p2_done', trigger='clue_given', after = "process_give_clue")

        self.machine.add_transition(source='p2_play_card', dest='p2_play_card', trigger='card_played', conditions= ['card_play_incorrect']) 
        self.machine.add_transition(source='p2_play_card', dest='p2_done', trigger='card_played', after = "process_play_card") 
        
        self.machine.add_transition(source='p2_discard_card', dest='p2_discard_card', trigger='card_discarded', conditions= ['card_discard_incorrect']) 
        self.machine.add_transition(source='p2_discard_card', dest='p2_done', trigger='card_discarded', after = 'process_discard_card')

        self.machine.add_transition(source='p2_done', dest='p1_choose_action', trigger='p2_turn_end', conditions= ['game_continue'])  # 玩家2回合结束，轮到玩家1
        self.machine.add_transition(source='p2_done', dest='end', trigger='p2_turn_end', conditions= ['game_over'])  # 游戏结束

        
    def save_png(self):
        self.machine.get_graph().draw('hanabi_fsm.png', prog='dot')

    def publish(self, topic, observation):
        # image = observation.create_image()
        image = None
        
        responses = self.broker.publish(topic, topic, image, observation)
        
        self.current_responses = responses

        self.logging(self.current_responses)

        print(responses)
        self.current_player_name = responses[0]['name']
        self.current_player_role = responses[0]['role']
        self.current_answer = responses[0]['answer']
        
        if "choice" in self.current_answer:
            self.current_choice = self.current_answer["choice"]
        
        elif "clue" in self.current_answer:
            self.current_clue = self.current_answer["clue"]
            self.current_hint_getter = self.current_answer['to']
        
        elif "index" in self.current_answer:
            self.current_card_index = int(self.current_answer["index"])
        



    def card_discard_incorrect(self):
        
        if self.current_card_index < 1 or self.current_card_index > len(self.players_hands[self.current_role]): # 选择出现错误
            
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "card index out of range"
            self.fail_cases.append(self.fail_case)
            return True
            
        return False


    def card_play_incorrect(self):
        if self.current_card_index < 1 or self.current_card_index > len(self.players_hands[self.current_role]): # 选择出现错误
            
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "card index out of range"
            self.fail_cases.append(self.fail_case)
            return True

        return False
        
        
            
    def clue_incorrect(self):
        if self.current_clue not in self.colors + [str(i) for i in range(1, 6)]:
            
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "clue not in colors or values"
            self.fail_cases.append(self.fail_case)
            return True
        
        self.current_clue_list = []
        
        for i, (color, value) in enumerate(self.players_hands[self.current_hint_getter]):
            if self.current_clue in [color, str(value)]:
                self.current_clue_list.append((i+1, self.current_clue_list))
        
        if not self.current_clue_list: # 如果没有找到提示的牌 则为错误提示
            
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "no such card in the hint getter's hand"
            self.fail_cases.append(self.fail_case)
            return True  
        
        return False
    

    def action_choose_incorrect(self):
        
        if self.current_choice not in ["A", "B", "C"]:
                
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "choice not in A, B, C"
            self.fail_cases.append(self.fail_case)
            return True
        
        return False

    def choose_give_clue(self):
        return self.current_choice == "A"
    
    def choose_play_card(self):
        return self.current_choice == "B"
    
    def choose_discard_card(self):
        return self.current_choice == "C"
    
    # def logging(self, content):
    #     self.log.append(content)
        
    #     print(content)
        
    #     # save to a file named obs-<timestamp>.log
    #     if not os.path.exists("logs/hanabi"):
    #         os.makedirs("logs/hanabi")
    #     with open(f"logs/hanabi/game.log", "a") as f:
    #         f.write(str(content) +"\n")
    
    def logging(self, content):
        self.log.append(content)
        # print(content)
            
        with open(self.log_file, "w") as f:
            # save
            for i in self.log:
                # print(i)
                f.write(str(i) + "\n")
        
    def game_over(self):
        # game over 的三个情况
        # 1. error tokens == 3 当错误次数达到3次  
        # 2. 当完全成功
        # 3. 当牌堆用完
        return self.error_tokens == 3 or all([len(self.played_cards[color]) == 5 for color in self.colors]) or not self.deck
    
    def game_continue(self):
        return not self.game_over()
    
    def process_give_clue(self):
            
        
        # clue = self.current_clue
                # success = True
                
        # if success:
        self.clue_tokens -= 1
        self.clue_record[self.current_hint_getter] += self.current_clue_list
        
        # ret = {"state": f"p{role[-1]}_give_clue", "clue": answer, "success": success}
        # self.logging(ret)
        # return ret
    
    def process_play_card(self):
            
        # name = responses[0]['name']
        # role = responses[0]['role']
        # answer = responses[0]['answer']
        
        # choice = int(answer["index"])
        

            # remove the card from the clue list
        
        role = self.current_player_role
        choice = self.current_card_index
        
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
            
        # ret =  {"state": f"p{role[-1]}_play_card", "card": choice, "success": success}
        # self.logging(ret)

        # return ret
    
    def process_discard_card(self):
            
        # name = responses[0]['name']
        # role = responses[0]['role']
        # answer = responses[0]['answer']
        # choice = int(answer['index'])
        
        # success = True

        card = self.players_hands[self.current_player_role][self.current_card_index-1]
        self.discard_pile.append(card)
        
        self.clue_tokens = min(8, self.clue_tokens + 1)  # 增加一个提示token
        if self.deck:
            self.players_hands[self.current_player_role][self.current_card_index-1] = self.deck.pop()
            
        # ret = {"state": f"p{role[-1]}_discard_card", "card": choice, "success": success}
        # self.logging(ret)

        # return ret
    
    def process_choose_action(self):
        self.current_role = self.current_player_role
        

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

    
    def draw_game_gui(self):
        
        # Set up fonts
        font = pygame.font.SysFont(None, 24)
        
        # Colors
        COLORS = {
            "white": (255, 255, 255),
            "red": (255, 0, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "green": (0, 255, 0)
        }
        
        def draw_text(text, x, y, color=(0, 0, 0)):
            img = font.render(text, True, color)
            self.screen.blit(img, (x, y))
        
        def draw_game_state(game_dict):
            self.screen.fill((200, 200, 200))  # Clear self.screen with a light grey color
            
            # Draw clue tokens
            draw_text(f"Clue Tokens: {game_dict['clue_tokens']}", 20, 20)
            
            # Draw error tokens
            draw_text(f"Error Tokens: {game_dict['error_tokens']}", 20, 50)
            
            # Draw deck remaining
            draw_text(f"Deck Remaining: {game_dict['deck_remaining']}", 20, 80)
            
            # Draw players' hands
            y_offset = 120
            for player, hand in game_dict['players_hands'].items():
                draw_text(f"{player}'s Hand:", 20, y_offset)
                x_offset = 20
                for color, value in hand:
                    pygame.draw.rect(self.screen, COLORS[color], (x_offset, y_offset + 30, 40, 60))
                    draw_text(str(value), x_offset + 15, y_offset + 55, (0, 0, 0))
                    x_offset += 50
                y_offset += 100
            
            # Draw played cards
            y_offset = 320
            draw_text("Played Cards:", 20, y_offset)
            x_offset = 20
            for color, values in game_dict['played_cards'].items():
                draw_text(f"{color}:", x_offset, y_offset + 30)
                x = x_offset + 40
                for value in values:
                    pygame.draw.rect(self.screen, COLORS[color], (x, y_offset + 30, 40, 60))
                    draw_text(str(value), x + 15, y_offset + 55, (0, 0, 0))
                    x += 50
                x_offset += 150
            
            # Draw discard pile
            y_offset = 420
            draw_text("Discard Pile:", 20, y_offset)
            x_offset = 20
            for color, value in game_dict['discard_pile']:
                pygame.draw.rect(self.screen, COLORS[color], (x_offset, y_offset + 30, 40, 60))
                draw_text(str(value), x_offset + 15, y_offset + 55, (0, 0, 0))
                x_offset += 50
            
            # Draw logs
            y_offset = 520
            draw_text("Logs:", 20, y_offset)
            x_offset = 20
            log_lines = game_dict['log'][-5:]
            for log_entry in log_lines:
                draw_text(str(log_entry), x_offset, y_offset + 30)
                y_offset += 30
            
            pygame.display.flip()
        
        game_dict = self.to_dict()
        draw_game_state(game_dict)
        
        
    def to_dict(self):
        game_dict = {
            "clue_tokens": self.clue_tokens,
            "error_tokens": self.error_tokens,
            "deck_remaining": len(self.deck),
            "players_hands": {
                player: [(color, value) for color, value in hand]
                for player, hand in self.players_hands.items()
            },
            "played_cards": {
                color: values[:]  # Copy the list of played values for each color
                for color, values in self.played_cards.items()
            },
            "discard_pile": [(color, value) for color, value in self.discard_pile],
            "clue_record": {
                player: clues[:]
                for player, clues in self.clue_record.items()
            },
            "log": self.log[:],
            
            'fail_cases': self.fail_cases
        }
        return game_dict


    def game_loop(self):
        
        if self.debug:
            
            pygame.init()
            
            # Set up the display
            self.screen = pygame.display.set_mode((800, 600))
            pygame.display.set_caption('Hanabi Game State')
            
        
        while self.state != "end":
            # self.draw_game_gui()
            #
            # for event in pygame.event.get():
            #     if event.type == pygame.QUIT:
            #         self.state = "end"
            print("current state: " + self.state)
            if self.state == "start":
                
                self.game_start()
            
            elif self.state == "p1_choose_action":
                
                
                self.publish(self.state, self.to_dict())
                self.trigger('choose_done')
                
                    
            elif self.state == "p1_give_clue":
                
                
                self.publish(self.state, self.to_dict())
                
                self.clue_given()
                    
                
            elif self.state == "p1_discard_card":
            
                
                self.publish(self.state, self.to_dict())
                
                self.card_discarded()
                
                            
            elif self.state == "p1_play_card":
                
                self.publish(self.state, self.to_dict())
                
                self.card_played()
                
            
            elif self.state == "p1_done":
                
                self.p1_turn_end()
            
            elif self.state == "p2_choose_action":
                
                self.publish(self.state, self.to_dict())
                self.trigger('choose_done')
                
                    
            elif self.state == "p2_give_clue":
                
                self.publish(self.state, self.to_dict())
                
                self.clue_given()
                
            
            elif self.state == "p2_discard_card":
                
                self.publish(self.state, self.to_dict())
                self.card_discarded()
                
                            
            elif self.state == "p2_play_card":
                
                self.publish(self.state, self.to_dict())
                
                self.card_played()
                
            
            elif self.state == "p2_done":
                
                self.p2_turn_end()