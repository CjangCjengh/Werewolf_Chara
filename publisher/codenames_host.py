from transitions import Machine
from transitions.extensions import GraphMachine
from broker.codenames_broker import CodenamesGameBroker
from publisher.publisher import Publisher
from observation.codenames_observation import CodenamesManager
from collections import Counter
import time
import random
import os
import pygame

from subscriber.subscriber import Subscriber
class CodenamesGameHost(Publisher):

    def __init__(self, config):
        
        self.debug = False
        self.broker = CodenamesGameBroker(config)
        # super().__init__(broker)
        self.create_fsm()
        
        self.config = config
        self.log_file = os.path.join(config['log_directory'], f"game.log")

        # game infos
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
        self.clues = []
        
        self.fail_case = None
        self.fail_cases = []

        
    def create_fsm(self):
        
        # Define the states
        self.finite_states = [
            'start',
            'red_spymaster_give_clue',
            'red_operative_guess',
            'red_operative_guess_made',
            'blue_spymaster_give_clue',
            'blue_operative_guess',
            'blue_operative_guess_made',
            'game_over',
            'blue_win',
            'red_win',
            'end'
        ]
        
        self.machine = GraphMachine(model=self, states=self.finite_states, initial='start', show_conditions=True)
        self.machine.add_transition(source='start', dest='red_spymaster_give_clue', trigger='game_start', after = 'process_game_initialization')
        
        self.machine.add_transition(source='red_spymaster_give_clue', dest='red_spymaster_give_clue', trigger='clue_given',conditions = ['clue_format_incorrect'])
        self.machine.add_transition(source='red_spymaster_give_clue', dest='red_operative_guess', trigger='clue_given', after = "process_give_clue")
        
        self.machine.add_transition(source='red_operative_guess', dest='red_operative_guess', trigger='guess_made', conditions=['guess_format_incorrect'])
        self.machine.add_transition(source='red_operative_guess', dest='red_operative_guess_made', trigger='guess_made', after = 'process_guess')
        
        self.machine.add_transition(source='red_operative_guess_made', dest='blue_win', trigger='guess_made', conditions='blue_wins')
        self.machine.add_transition(source='red_operative_guess_made', dest='red_win', trigger='guess_made', conditions='red_wins')
        self.machine.add_transition(source='red_operative_guess_made', dest='blue_spymaster_give_clue', trigger='guess_made', conditions=['guess_finished'])
        self.machine.add_transition(source='red_operative_guess_made', dest='red_operative_guess', trigger='guess_made')
        
        self.machine.add_transition(source='blue_spymaster_give_clue', dest='blue_spymaster_give_clue', trigger='clue_given', conditions = ['clue_format_incorrect'])
        self.machine.add_transition(source='blue_spymaster_give_clue', dest='blue_operative_guess', trigger='clue_given', after = "process_give_clue")
        
        self.machine.add_transition(source='blue_operative_guess', dest='blue_operative_guess', trigger='guess_made',  conditions=['guess_format_incorrect'])
        self.machine.add_transition(source='blue_operative_guess', dest='blue_operative_guess_made', trigger='guess_made', after = 'process_guess')
        
        self.machine.add_transition(source='blue_operative_guess_made', dest='red_win', trigger='guess_made',  conditions='red_wins')
        self.machine.add_transition(source='blue_operative_guess_made', dest='blue_win', trigger='guess_made',  conditions='blue_wins')
        self.machine.add_transition(source='blue_operative_guess_made', dest='red_spymaster_give_clue', trigger='guess_made', after= 'process_guess', conditions='guess_finished')
        self.machine.add_transition(source='blue_operative_guess_made', dest='blue_operative_guess', trigger='guess_made', after= 'process_guess')
        
        self.machine.add_transition(source='game_over', dest='red_win', trigger='game_over', conditions='red_wins')
        self.machine.add_transition(source='game_over', dest='blue_win', trigger='game_over', conditions='blue_wins')
        

    def save_png(self):
        self.machine.get_graph().draw('codenames_fsm.png', prog='dot')

    def publish(self, topic, observation):
        
        responses = self.broker.publish(topic, topic, observation)
        self.current_responses = responses
        
        self.logging(self.current_responses)

        if len(responses) == 1:
            self.current_role = responses[0]['role']
            self.current_answer = responses[0]['answer']
        


    def process_game_initialization(self):
        
        if self.config["mode"] == "replay" and "replay" in self.config:
            self.words_on_board = self.config["replay"]["words_on_board"]
            self.team_words = self.config["replay"]["team_words"]
            self.neutral_words = self.config["replay"]["neutral_words"]
            self.assassin_word = self.config["replay"]["assassin_word"]
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
        
        if len(self.current_responses[0]['answer']['clue'].split()) > 1:
            
            self.fail_case = self.current_answer
            self.fail_case['reason'] = "clue has more than one word"
            self.fail_cases.append(self.fail_case)
            
            return True
        
        if self.current_responses[0]['answer']['clue'].upper() in self.words_on_board:
            
            self.fail_case = self.current_answer
            self.fail_case['reason'] = "clue is a word on the board"
            self.fail_cases.append(self.fail_case)
            
            return True
        
        for clue in self.clues:
            if self.current_responses[0]['answer']['clue'] == clue['clue']:
                
                self.fail_case = self.current_answer
                self.fail_case['reason'] = "clue has been used, try another one"
                self.fail_cases.append(self.fail_case)
                
                return True
        
        return False
    
    def process_give_clue(self):
        
        self.fail_cases = []
        self.fail_case = None
        
        self.current_team =  "red" if "red" in self.current_responses[0]["role"] else "blue"

        answer = self.current_responses[0]["answer"]
        self.current_clue = answer["clue"]
        self.current_clue_number = answer["number"]
        
        self.clues.append({
            'team': self.current_team,
            'clue': self.current_clue,
            'number': self.current_clue_number,
        })
        
        self.logging({'state': 'give_clue'})
        self.logging(self.current_responses[0])
    
        
    def guess_format_incorrect(self):
    
        
        if "guess" not in self.current_answer:
            self.fail_case = self.current_answer
            self.fail_case['reason'] = "guess entry is not provided"
            self.fail_cases.append(self.fail_case)
            
            return True
        
        for guess in self.current_answer['guess']:
            if guess not in self.words_on_board and guess != "-1":
                
                self.fail_case = self.current_answer
                self.fail_case['reason'] = f"{guess}, this word is not on the board, never ever guess it again!!!!"
                self.fail_cases.append(self.fail_case)
                return True
        
        for guess in self.current_answer['guess']:
            if guess in self.guessed_words and guess != "-1":
                self.fail_case = self.current_answer
                self.fail_case['reason'] = f"{guess}, this word has been guessed, never ever guess it again!!!!"
                self.fail_cases.append(self.fail_case)
                return True
        

        return False
    
    
    
    def process_guess(self):
        
        self.fail_cases = []
        self.fail_case = None
        
        self.current_guess = self.current_responses[0]["answer"]["guess"]
        
        self.current_guess_times += 1
        
        
        for guess in self.current_guess:
            
            if guess in self.team_words[self.current_team]:
                self.guessed_words.append(guess)
                self.current_score[self.current_team] += 1
            elif guess in self.neutral_words:
                self.guessed_words.append(guess)
                break
            elif guess not in self.team_words[self.current_team] and guess not in self.neutral_words:
                self.guessed_words.append(guess)
                self.current_score[self.current_team] -= 1
                break
        
        # self.logging({'state': 'guess'})
        # self.logging(self.current_responses[0]["answer"])
        # result = self.update_guessed_words(responses["guess"])
        # self.guess_result = result
        # return ret
        
        # self.logging(f"current score: {self.current_score}")
        # self.logging(f"current guess times: {self.current_guess_times}")
        # self.logging(f"current guess: {self.current_guess}")
        # self.logging(f"current team: {self.current_team}")
        # print("red team words length:" + str(len(self.team_words["red"])))
        # print("blue team words length:" + str(len(self.team_words["blue"])))
        # print("neutral words length:" + str(len(self.neutral_words)))
    

    
    
    def guess_finished(self):
        
        return True
        # guess = self.current_responses[0]["answer"]["guess"]
        # if guess not in self.team_words[self.current_team] or guess == "-1": # -1 means give up and pass the turn
        #     return True
        
        # if self.current_guess_times <= int(self.current_clue_number):
        #     return False
        # else:
        #     return True
    
    
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


    def red_wins(self):
        # Check if the game is over (all words of one team or the assassin has been guessed)
        
        
        if self.current_role == "blue_operative" and self.current_guess == self.assassin_word: # if the blue operative guesses the assassin word
            return True
        
        if all(word in self.guessed_words for word in self.team_words["red"]): # if all red team words are guessed
            return True
        
        return False

    def blue_wins(self):
        # Check if the game is over (all words of one team or the assassin has been guessed)
        
        
        if self.current_role == "red_operative" and self.current_guess == self.assassin_word: # if the red operative guesses the assassin word
            return True
        
        if all(word in self.guessed_words for word in self.team_words["blue"]): # if all blue team words are guessed
            return True
        
        return False
    
    
    def logging(self, content):
        self.log.append(content)
        # print(content)
            
        with open(self.log_file, "w") as f:
            # save
            for i in self.log:
                # print(i)
                f.write(str(i) + "\n")
                
    # def logging(self, content):
    #     self.log.append(content)
    #     # for k, v in content_dict.items():
    #     #     self.logging(f"{k}: {v}")
    #     print(content)
            
        # import os
        # # save to a file named obs-<timestamp>.log
        # if not os.path.exists("logs/codenames"):
        #     os.makedirs("logs/codenames")
        # with open(f"logs/codenames/obs-{t}.log", "a") as f:
        #     f.write(str(content) +"\n")
        
    
    def to_dict(self):
        self.remaining_words = [word for word in self.words_on_board if word not in self.guessed_words]
        game_dict = {
            "remaining_words": self.remaining_words,
            "words_on_board": self.words_on_board,
            "guessed_words": self.guessed_words,
            "blue_team_words": self.team_words["blue"],
            "red_team_words": self.team_words["red"],
            "neutral_words": self.neutral_words,
            "assassin_word": self.assassin_word,
            "current_clue": self.current_clue,
            "current_clue_number": self.current_clue_number,
            "current_guess": self.current_guess,
            "current_team": self.current_team,
            # "log": self.log,
            # "current_responses": self.current_responses,
            "current_guess_times": self.current_guess_times,
            "current_score": self.current_score,
            "current_available_words": self.get_available_words(),
            "clues_given": self.clues,
            'fail_cases': self.fail_cases,
        }
        return game_dict

    def draw_game_gui(self):
        
        if not self.debug:
            return
        game_dict = self.to_dict()
        
        self.screen.fill((255, 255, 255))  # Fill the screen with white

        font = pygame.font.Font(None, 36)
        word_font = pygame.font.Font(None, 24)
        box_color = {
            "red": (255, 0, 0),
            "blue": (0, 0, 255),
            "neutral": (192, 192, 192),
            "assassin": (0, 0, 0)
        }

        for idx, word in enumerate(game_dict["words_on_board"]):
            if word in game_dict["guessed_words"]:
                color = (128, 128, 128)  # Guessed words are gray
            elif word in game_dict["red_team_words"]:
                color = box_color["red"]
            elif word in game_dict["blue_team_words"]:
                color = box_color["blue"]
            elif word in game_dict["neutral_words"]:
                color = box_color["neutral"]
            elif word == game_dict["assassin_word"]:
                color = box_color["assassin"]
            else:
                color = (255, 255, 255)  # Shouldn't happen

            x = (idx % 5) * 160 + 10
            y = (idx // 5) * 120 + 10
            pygame.draw.rect(self.screen, color, (x, y, 150, 110))
            text = word_font.render(word, True, (255, 255, 255))
            self.screen.blit(text, (x + 10, y + 40))

        # Draw some game state info to the right of the board
        info_x = 820  # Starting x position for info
        info_y = 10   # Starting y position for info

        clue_text = font.render(f"Clue: {game_dict['current_clue']} ({game_dict['current_clue_number']})", True, (0, 0, 0))
        self.screen.blit(clue_text, (info_x, info_y))
        
        score_text = font.render(f"Red: {game_dict['current_score']['red']} Blue: {game_dict['current_score']['blue']}", True, (0, 0, 0))
        self.screen.blit(score_text, (info_x, info_y + 40))

        pygame.display.flip()  # Update the full display Surface to the screen

        # pygame.image.save(self.screen, "codenames_board.png")  # Save the current screen as an image 
        
    def game_loop(self):
        
        if self.debug:
            pygame.init()
            self.screen = pygame.display.set_mode((1000, 600))
            pygame.display.set_caption("Codenames Board")
        
        
        while self.state != "end":
            
            # self.draw_game_gui()
            #
            # for event in pygame.event.get():
            #     if event.type == pygame.QUIT:
            #         self.state = "end"
            print("current state: " + self.state)
            self.logging("current state: " + self.state)
            if self.state == "start":

                self.game_start()
            
            elif self.state == "red_spymaster_give_clue":
                
                self.publish(self.state, self.to_dict())
                
                self.clue_given()
                
            
            elif self.state == "red_operative_guess":
                
                self.publish(self.state, self.to_dict())
                    
                self.guess_made()
            
            elif self.state == "red_operative_guess_made":
                self.guess_made()
                
            elif self.state == "blue_spymaster_give_clue":
                
                self.publish(self.state, self.to_dict())
                
                
                self.clue_given()
            
            elif self.state == "blue_operative_guess":
                
                self.publish(self.state, self.to_dict())
                
                self.guess_made()
        
            elif self.state == "blue_operative_guess_made":
                self.guess_made()
                
                