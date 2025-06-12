from transitions import Machine
from transitions.extensions import GraphMachine

import random
import time
from collections import Counter

import numpy as np

from broker.avalon_broker import AvalonGameBroker
from .publisher import Publisher
import pygame
import os

class AvalonGameHost(Publisher):
    def __init__(self, config):
        # super().__init__(broker)
        
        
        self.debug = False
        self.broker = AvalonGameBroker(config)
        
        self.config = config
        self.log_file = os.path.join(config['log_directory'], f"game.log")
        
        
        self.create_fsm()
        
        self.player_number = 6
        self.players_names = [player.name for player in self.broker.players]
        self.players_roles = {player.name: player.role for player in self.broker.players}
        self.total_round_number = 5
        self.team_size_each_round = [2, 3, 4, 3, 4]
        # self.current_quest_team = []
        self.current_quest_round = 1
        self.current_leader_index = random.choice(range(self.player_number))
        self.current_leader = self.players_names[self.current_leader_index]
        self.quest_success_counter = 0
        self.quest_fail_counter = 0
        self.current_team_selection_vote_round = 1
        # self.team_vote_history = [{} for _ in range(5)]  # record the team_vote history
        self.team_selection_history = [{} for _ in range(25)]  # maximum 5 selections each quest, therefore 25 in total
        self.quest_history = [{} for _ in range(5)]  # record the quest history
        self.quest_result = ["" for _ in range(5)]
        self.assassin_success = False
        self.current_selected_team = []
        self.log = []
        
    def create_fsm(self):
        
        self.finite_states = [
            'start',
            'round_start',
            'leader_assign',
            'team_selection',
            'vote',
            'quest',
            'round_end',
            'assassin',
            'assassin_end',
            'good_win',
            'evil_win',
            'end',
        ]
        
        self.machine = GraphMachine(model=self, states=self.finite_states, initial='start', show_conditions=True)
        
        self.machine.add_transition(source='start', dest='round_start', trigger='game_start') 
        self.machine.add_transition(source='round_start', dest='leader_assign', trigger='new_round')
        self.machine.add_transition(source='leader_assign', dest='team_selection', trigger='leader_assigned', after='process_assign_leader')
        
        self.machine.add_transition(source='team_selection', dest='team_selection', trigger='team_selected', conditions='team_selected_incorrect')
        self.machine.add_transition(source='team_selection', dest='vote', trigger='team_selected', after='process_team_selection')
        
        self.machine.add_transition(source='vote', dest='vote', trigger='voted', conditions='vote_format_incorrect')
        self.machine.add_transition(source='vote', dest='quest', trigger='voted', conditions='team_accepted', after='process_team_registration')
        self.machine.add_transition(source='vote', dest='leader_assign', trigger='voted', conditions='team_rejected_less_than_5_times')
        self.machine.add_transition(source='vote', dest='round_end', trigger='voted', after='process_team_selection_fail')
        
        self.machine.add_transition(source='quest', dest='quest', trigger='quest_end', conditions='quest_format_incorrect')
        self.machine.add_transition(source='quest', dest='round_end', trigger='quest_end', after='process_quest')
        
        self.machine.add_transition(source='round_end', dest='round_start', trigger='round_end', conditions='quests_over', after='process_round_end')
        self.machine.add_transition(source='round_end', dest='assassin', trigger='round_end', after='process_round_end')
        
        self.machine.add_transition(source='assassin', dest='assassin', trigger='assassinated', conditions='assassin_format_incorrect')
        self.machine.add_transition(source='assassin', dest='assassin_end', trigger='assassinated', after='process_assassin')
        
        self.machine.add_transition(source='assassin_end', dest='good_win', trigger='assassinated', conditions='good_wins')
        self.machine.add_transition(source='assassin_end', dest='evil_win', trigger='assassinated', conditions='evil_wins')
        
        self.machine.add_transition(source='good_win', dest='end', trigger='game_ends')
        self.machine.add_transition(source='evil_win', dest='end', trigger='game_ends')
    
    def process_team_selection_fail(self):
        self.current_team_selection_vote_round = 1
        self.quest_fail_counter += 1
        self.quest_result[self.current_quest_round - 1] = "fail"
        
    def assassin_format_incorrect(self):
        if 'target' not in self.current_answers[0]:
            return True
        
        if self.current_answers[0]['target'] not in self.players_names:
            return True
        
        return False
    
    def evil_wins(self):
        return self.assassin_success or self.quest_fail_counter >= 3
    
    def good_wins(self):
        return self.quest_success_counter >= 3 and not self.assassin_success
    
    def quests_over(self):
        return self.current_quest_round < 5 and self.quest_fail_counter < 3 and self.quest_success_counter < 3
    
    def team_rejected_less_than_5_times(self):
        return self.current_team_selection_vote_round < 5
    
    def team_selected_incorrect(self):
        if type(self.current_selected_team) != list:
            return True
        
        if len(self.current_selected_team) != self.team_size_each_round[self.current_quest_round - 1]:
            return True

        for p in self.current_selected_team:
            if p not in self.players_names:
                return True
        
        return False
    
    def vote_format_incorrect(self):
        for answer in self.current_answers:
            if 'vote' not in answer:
                return True
            if answer['vote'] not in ["accept", "reject"]:
                return True
        
        return False
    
    def team_accepted(self):
        vote_reject_counter = 0
        vote_accept_counter = 0
        for answer in self.current_answers:
            if answer['vote'] == "reject":
                vote_reject_counter += 1
            elif answer['vote'] == "accept":
                vote_accept_counter += 1

        if vote_reject_counter < 3:
            self.current_team_selection_vote_round = 1
            return True
        else:
            self.current_team_selection_vote_round += 1
            return False

    def quest_format_incorrect(self):   
        for answer in self.current_answers:
            if 'quest' not in answer:
                return True
            
            if answer['quest'] not in ["success", "fail"]:
                return True
        
        return False
        
    def publish(self, topic, observation):
        responses = self.broker.publish(topic, topic, None, observation)
        self.current_responses = responses
        self.current_answers = [response['answer'] for response in responses]
        
        self.logging(self.current_responses)
        if topic == "team_selection":
            self.current_selected_team = self.current_answers[0]['team']
    

    
    def process_assassin(self):
        # check if the assassin is successful
        target = self.current_answers[0]['target']
        if self.players_roles[target] == "Merlin":
            self.assassin_success = True
        else:
            self.assassin_success = False
            
    def process_quest(self):
        # record quest history here (who selects success, and who selects fail)
        # quest_result = {'team': self.current_selected_team, 'responses': self.current_responses}
        # self.quest_history[self.current_quest_round - 1] = quest_result

        for response in self.current_responses:
            self.quest_history[self.current_quest_round - 1][response['name']] = response['answer']['quest']
            
        if any( response['quest'] == "fail" for response in self.current_answers):
            self.quest_fail_counter += 1
            self.quest_result[self.current_quest_round - 1] = "fail"
        else:
            self.quest_success_counter += 1
            self.quest_result[self.current_quest_round - 1] = "success"
    
    def process_team_selection(self):
        # record team selection history here (who selects the team and the team members)
        team_selection = {'leader': self.current_leader, 'team': self.current_selected_team}
        self.team_selection_history[(self.current_quest_round-1) * 5 + self.current_team_selection_vote_round - 1] = team_selection
    
    def process_team_registration(self):
        for p in self.current_selected_team:
            for player in self.players_names:
                if player == p:
                    self.register_by_name(player, "quest")
                    
    def process_assign_leader(self):
        self.unregister_by_name(self.current_leader, "team_selection")
        self.current_leader_index = (self.current_leader_index + 1) % self.player_number
        self.current_leader = self.players_names[self.current_leader_index]
        self.register_by_name(self.current_leader, "team_selection")
    
    def register_by_name(self, name, topic):
        self.broker.register_by_name(name, topic)
    
    def unregister_by_name(self, name, topic):
        self.broker.unregister_by_name(name, topic)

    def process_round_end(self):
        self.current_quest_round += 1
        
    
    def logging(self, content):
        self.log.append(content)
        # print(content)
            
        with open(self.log_file, "w") as f:
            # save
            for i in self.log:
                # print(i)
                f.write(str(i) + "\n")
          

    
    def draw_game_gui(self):
        
        if not self.debug:
            return
        # Define colors
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        GRAY = (200, 200, 200)
        RED = (255, 0, 0)
        GREEN = (0, 255, 0)
        BLUE = (0, 0, 255)

        # Get the current game state
        game_state = self.to_dict()

        # Main game loop
                    

            # Fill the background
        self.screen.fill(WHITE)

        # Draw game information
        font = pygame.font.Font(None, 24)
        
        # Draw current round
        round_text = f"Round: {game_state['current_quest_round']}/{game_state['total_quest_round']}"
        text_surface = font.render(round_text, True, BLACK)
        self.screen.blit(text_surface, (10, 10))

        # Draw quest results
        # for i in range(5):
        #     rect_color = GRAY
        #     if i < game_state['quest_success_counter']:
        #         rect_color = GREEN
        #     elif i < game_state['quest_success_counter'] + game_state['quest_fail_counter']:
        #         rect_color = RED
        #     pygame.draw.rect(self.screen, rect_color, (10 + i * 60, 40, 50, 50))
        for i, quest in enumerate(self.quest_result):
            if quest == "success":
                pygame.draw.rect(self.screen, GREEN, (10 + i * 60, 40, 50, 50))
            elif quest == "fail":
                pygame.draw.rect(self.screen, RED, (10 + i * 60, 40, 50, 50))
            else:
                pygame.draw.rect(self.screen, GRAY, (10 + i * 60, 40, 50, 50))

        # Draw players
        for i, player in enumerate(game_state['players_names']):
            player_color = BLUE if player == game_state['current_team_leader'] else BLACK
            player_text = f"{player} ({'Leader' if player == game_state['current_team_leader'] else 'Player'})"
            text_surface = font.render(player_text, True, player_color)
            self.screen.blit(text_surface, (10, 100 + i * 30))

        # Draw current team
        team_text = "Current Team: " + ", ".join(game_state['current_selected_team'])
        text_surface = font.render(team_text, True, BLACK)
        self.screen.blit(text_surface, (10, 300))

        # Draw voting round
        vote_text = f"Team Selection Vote Round: {game_state['current_team_selection_vote_round']}/5"
        text_surface = font.render(vote_text, True, BLACK)
        self.screen.blit(text_surface, (10, 330))

        # Draw game state
        state_text = f"Current State: {game_state['current_state']}"
        text_surface = font.render(state_text, True, BLACK)
        self.screen.blit(text_surface, (10, 360))

        # Draw last log message
        if game_state['log']:
            log_text = f"Last action: {game_state['log'][-1]}"
            text_surface = font.render(log_text, True, BLACK)
            self.screen.blit(text_surface, (10, 390))

        # Update the display
        pygame.display.flip()

    
    def game_loop(self):
        
        if self.debug:
            pygame.init()
            
            # Set up the display
            width, height = 800, 600
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("Avalon Game")

        
        while self.state != "end":
            self.draw_game_gui()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.state = "end"
            print("\033[94mcurrent state: " + self.state + "\033[0m")
            if self.state == "start":
                
                self.game_start()
            
            elif self.state == "round_start":
                
                self.new_round()
            
            elif self.state == "leader_assign":
                
                self.leader_assigned()
            
            elif self.state == "team_selection":
                
                self.publish(self.state, self.to_dict())
                
                self.team_selected()
                
            
            elif self.state == "vote":
                
                self.publish(self.state, self.to_dict())
                
                self.voted()
            
            elif self.state == "quest":
                
                self.publish(self.state, self.to_dict())
                
                self.quest_end()
            
            elif self.state == "round_end":
                self.round_end()
                
            elif self.state == "assassin":
                
                self.publish(self.state, self.to_dict())
                
                self.assassinated()
                
            elif self.state == "assassin_end":
                self.assassinated()
                
            elif self.state == "good_win":
                self.game_ends()
                
            elif self.state == "evil_win":
                self.game_ends()
        
          
    def to_dict(self):
        game_state = {
            'players_names': self.players_names,
            'players_roles': self.players_roles,
            'current_quest_round': self.current_quest_round,
            'total_quest_round': self.total_round_number,
            'quest_history': self.quest_history,
            'team_selection_history': self.team_selection_history,
            # 'team_voting_history': self.team_vote_history,
            'current_vote_round': self.current_team_selection_vote_round,
            'team_size_each_round': self.team_size_each_round,
            'current_team_selection_vote_round': self.current_team_selection_vote_round,
            'current_team_leader': self.current_leader,
            # 'current_quest_team': self.current_quest_team,
            'current_selected_team': self.current_selected_team,
            'quest_success_counter': self.quest_success_counter,
            'quest_fail_counter': self.quest_fail_counter,
            # 'assassin_success': self.assassin_success,
            'log': self.log,
            'finite_states': self.finite_states,
            'current_state': self.state,
        }
        return game_state