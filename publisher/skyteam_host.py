
from transitions.extensions import GraphMachine
from broker.skyteam_broker import SkyTeamGameBroker
from publisher.publisher import Publisher
import random
import copy
import os
import time
import ast
import pygame

class SkyTeamGameHost(Publisher):

    def __init__(self, config):
        
        self.debug = False
        self.broker = SkyTeamGameBroker(config)
        
        self.create_fsm()
        
        self.log_file = os.path.join(config['log_directory'], f"game.log")
        
        self.current_round_dices =  {"pilot": [], "copilot": []}
        
        self.current_round = -1
        self.current_approach = 0
        
        self.approach_track = [0,0,1,2,1,3,2] # _airplane_numbers on rounte
        self.altitude_track = [6000, 5000, 4000, 3000, 2000, 1000, 0]
        
        self.reroll_dice_positions = [0, 4]
        self.current_round_reroll_tokens = 1
        
        self.current_brake_force = 0
        
        self.dicuss_history = {'round0': [], 'round1': [], 'round2': [], 'round3': [], 'round4': [], 'round5': [], 'round6': []}
        self.action_history = {'round0': [], 'round1': [], 'round2': [], 'round3': [], 'round4': [], 'round5': [], 'round6': []}
        self.left_axis_state = None  # Axis state starts neutral
        self.right_axis_state = None  # Axis state starts neutral
        self.axis_state = 0  # Axis state starts neutral
        
        self.left_engine_power = None  # Initial left engine power
        self.right_engine_power = None  # Initial right engine power
        self.engine_power = 0  # Initial engine power
        
        # self.brake_state = 0  # Initial brake state
        # self.landing_gear_state = [False, False, False]  # Landing gear not deployed
        
        self.coffee_tokens = 0  # No coffee tokens at start
        self.dice_rolls = {"pilot": [], "copilot": []}  # No dice rolled yet
        self.current_role = "pilot"  # Pilot goes first
        self.log = []

        self.left_aerodynamic_marker = 4.5
        self.right_aerodynamic_marker = 8.5
        self.brake_forces = [2.5, 4.5, 6.5]
        
        self.allowed_dices = {
            "use_radio": [1,2,3,4,5,6],
            "reroll_dice": [1,2,3,4,5,6],
            "correct_axis": [1,2,3,4,5,6], 
            "adjust_engine": [1,2,3,4,5,6], 
            "gear1": [1,2], 
            "gear2": [3,4], 
            "gear3": [5,6], 
            "flap1": [1,2], 
            "flap2": [2,3], 
            "flap3": [4,5], 
            "flap4": [5,6],
            'brake1': [2], 
            'brake2': [4],
            'brake3': [6],
            'coffee_add': [1,2,3,4,5,6], 
            'coffee_drink': [1,2,3,4,5,6], 
        }
        
        self.have_released_or_applied = {
            "release_landing_gear1": False,
            "release_landing_gear2": False,
            "release_landing_gear3": False,
            "release_flap1": False,
            "release_flap2": False,
            "release_flap3": False,
            "release_flap4": False,
            'apply_brake1': False,
            'apply_brake2': False,
            'apply_brake3': False,
        }
        
        self.actions_list = {
            'pilot': 
                ["pilot_use_radio", "reroll_dice", "pilot_correct_axis", "pilot_adjust_engine", "release_landing_gear1", "release_landing_gear2", "release_landing_gear3", 'apply_brake1', 'apply_brake2', 'apply_brake3', 'coffee_add', 'coffee_drink'],
            'copilot':
                ["copilot_use_radio1", "copilot_use_radio2", "reroll_dice", "copilot_correct_axis", "copilot_adjust_engine", "release_flap1", "release_flap2", "release_flap3", "release_flap4", 'coffee_add', 'coffee_drink']
            }
        
        self.current_round_allowed_actions = copy.deepcopy(self.actions_list)
        
        self.fail_case = None
        self.fail_cases = []
        
    
    def create_fsm(self):
        
        self.finite_states = [
            'start',
            'round_start',
            'discuss',
            'roll_dice',
            'pilot_action',
            'pilot_action_end',
            'copilot_action',
            'copilot_action_end',
            'reroll_dice',
            'round_end',
            'landing',
            'safe_landed',
            'crash',
            'end'
        ]
        
        self.machine = GraphMachine(model=self, states=self.finite_states, initial='start', show_conditions=True)
        
        self.machine.add_transition(source='start', dest='round_start', trigger='game_start') 
        
        self.machine.add_transition(source='round_start', dest='discuss', trigger='strategy_discuss', after = 'round_setup')  # 每回合最开始的讨论阶段

        self.machine.add_transition(source='discuss', dest='roll_dice', trigger='roll_dice', after = 'process_discuss')
        
        self.machine.add_transition(source='roll_dice', dest='pilot_action', trigger='action_time', after= 'process_roll_dice')

        # self.machine.add_transition(source='pilot_action', dest='pilot_action', trigger='next', conditions = 'action_incorrect')
        self.machine.add_transition(source='pilot_action', dest='pilot_action_end', trigger='next', after = 'process_record_action')

        self.machine.add_transition(source='pilot_action_end', dest='round_end', trigger='next', conditions = 'dices_used_up', after = 'process_action')
        self.machine.add_transition(source='pilot_action_end', dest='reroll_dice', trigger='next', conditions = 'choose_to_reroll')
        self.machine.add_transition(source='pilot_action_end', dest='copilot_action', trigger='next', after = ['process_action', 'process_round_end'])
        
        self.machine.add_transition(source='reroll_dice', dest='pilot_action', trigger='next', conditions='back_to_pilot', after = 'process_reroll_dice')
        self.machine.add_transition(source='reroll_dice', dest='copilot_action', trigger='next', conditions='back_to_copilot', after = 'process_reroll_dice')

        # self.machine.add_transition(source='copilot_action', dest='copilot_action', trigger='next', conditions = 'action_incorrect')
        self.machine.add_transition(source='copilot_action', dest='copilot_action_end', trigger='next', after = 'process_record_action')
        
        self.machine.add_transition(source='copilot_action_end', dest='round_end', trigger='next', conditions = 'dices_used_up', after = 'process_action')
        self.machine.add_transition(source='copilot_action_end', dest='reroll_dice', trigger='next', conditions = 'choose_to_reroll')
        self.machine.add_transition(source='copilot_action_end', dest='pilot_action', trigger='next', after = ['process_action', 'process_round_end'])
        
        self.machine.add_transition(source='round_end', dest='crash', trigger='game_continue', conditions=['crashed_on_air'])
        self.machine.add_transition(source='round_end', dest='round_start', trigger='game_continue', conditions=['seven_rounds_not_end'])
        self.machine.add_transition(source='round_end', dest='landing', trigger='game_continue') # , conditions=['seven_rounds_end']
        
        self.machine.add_transition(source='landing', dest='safe_landed', trigger='landing', conditions=["safe_landed"])
        self.machine.add_transition(source='landing', dest='crash', trigger='landing', conditions=["crashed_while_landing"])
        
        self.machine.add_transition(source='safe_landed', dest='end', trigger='game_end')
        self.machine.add_transition(source='crash', dest='end', trigger='game_end')
        
        
    def save_png(self):
        self.machine.get_graph().draw('resources/skyteam_fsm.png', prog='dot')

    def publish(self, topic, observation):
        
        self.current_responses = self.broker.publish(topic, topic, observation)

        if 'discuss' in topic:
            
            for response in self.current_responses:
                
                log_entry = {
                    "state": topic,
                    "log": ": ".join([response['role'], response['answer']['discuss']]),
                }
                
                self.logging(log_entry)
            
        if 'action' in topic:
                
            while self.action_incorrect():
                self.current_responses = self.broker.publish(topic, topic, observation)

            self.current_action = self.current_answer['action']
            self.current_dice = int(self.current_answer['dice'])
            
        
            log_entry = {
                "state": topic,
                "log": " ".join([self.current_role, self.current_action, str(self.current_dice)]),
            }
            self.logging(log_entry)


    def process_discuss(self):
        self.dicuss_history[f'round{self.current_round}'].append(self.current_responses)
        
    def process_round_end(self):
        
        if self.left_axis_state and self.right_axis_state: # all axis are set
            
            self.axis_state = self.left_axis_state - self.right_axis_state
        if self.left_engine_power and self.right_engine_power:
            
            self.engine_power = self.left_engine_power + self.right_engine_power
    
    def action_incorrect(self):  
        
        self.current_response = self.current_responses[0]
        self.current_answer = self.current_response['answer']
        self.current_role = self.current_response['role'] 
        
        # 这里可以放到player里面
        if 'action' not in self.current_answer or 'dice' not in self.current_answer:
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "missing action or dice in the json format"
            self.fail_cases.append(self.fail_case)
            return True
        
        self.current_action = self.current_answer['action']
        self.current_dice = int(self.current_answer['dice'])
        
        # check if this action is allowed
        if self.current_action not in self.current_round_allowed_actions[self.current_role]:
            
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "action not allowed"
            self.fail_cases.append(self.fail_case)
            return True
        
        # check if this role has this dice
        if self.current_dice not in self.current_round_dices[self.current_role]:
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "dice not in current dices"
            self.fail_cases.append(self.fail_case)
            return True
        
        # check if this dice is allowed for specific action
        for action, allowed_dice in self.allowed_dices.items():
            if action in self.current_action and self.current_dice not in allowed_dice:
                self.fail_case = self.current_answer
                self.fail_case["reason"] = "dice not allowed for this action"
                self.fail_cases.append(self.fail_case)
                # print("dice not allowed for this action")
                return True

        # flaps should realease in order
        if "flap" in self.current_action:
            flap_number = int(self.current_action[-1])
            
            for i in range(1, flap_number-1):
                
                if not self.have_released_or_applied[f"release_flap{i}"]:
                    self.fail_case = self.current_answer
                    self.fail_case["reason"] = "flap not released in order" 
                    self.fail_cases.append(self.fail_case)
                    return True
        
        # brakes should apply in order
        if "brake" in self.current_action:
            brake_number = int(self.current_action[-1])
            for i in range(1, brake_number-1):
                
                if not self.have_released_or_applied[f"apply_brake{i}"]:
                    self.fail_case = self.current_answer
                    self.fail_case["reason"] = "brake not applied in order"
                    self.fail_cases.append(self.fail_case)
                    return True
        
        # radio should call the right area
        if "radio" in self.current_action:
            area = self.current_approach + self.current_dice -1  # to clear the plane on that "area" 
            if area >= 7:
                self.fail_case = self.current_answer
                self.fail_case["reason"] = "radio call area out of range"
                self.fail_cases.append(self.fail_case)
                return True
            if self.approach_track[area] == 0: 
                self.fail_case = self.current_answer
                self.fail_case["reason"] = "radio call area already clear"
                self.fail_cases.append(self.fail_case)
                return True
        
        # coffee should be added before drink
        if "coffee" in self.current_action:
            if "drink" in self.current_action and self.coffee_tokens == 0:
                self.fail_case = self.current_answer
                self.fail_case["reason"] = "no coffee to drink"
                self.fail_cases.append(self.fail_case)
                print("no coffee to drink")
                return True
            # no more than 3 coffee tokens
            if "add" in self.current_action and self.coffee_tokens == 3:
                self.fail_case = self.current_answer
                self.fail_case["reason"] = "no more coffee to add"
                self.fail_cases.append(self.fail_case)
                # print("no more coffee to add")
                return True
                
        return False
        
    def choose_to_reroll(self):
        
        return self.current_answer['action'] == 'reroll_dice'

        
        
    def round_setup(self):
        
        if self.left_axis_state and self.right_axis_state: # all axis are set
            self.axis_state = self.left_axis_state - self.right_axis_state
            
        if self.left_engine_power and self.right_engine_power: # all engines are set
            self.engine_power = self.left_engine_power + self.right_engine_power
            
        self.current_round += 1
        if self.engine_power < self.left_aerodynamic_marker:
            self.current_approach += 0
        elif self.engine_power < self.right_aerodynamic_marker:
            self.current_approach += 1
        elif self.engine_power > self.right_aerodynamic_marker:
            self.current_approach += 2
            
        self.current_round_reroll_tokens = 1 if self.current_round in self.reroll_dice_positions else 0
        self.current_round_dices =  {"pilot": [], "copilot": []}

        self.current_round_allowed_actions = copy.deepcopy(self.actions_list)
        
        if self.current_round not in self.reroll_dice_positions:
            self.current_round_allowed_actions['pilot'].remove("reroll_dice")
            self.current_round_allowed_actions['copilot'].remove("reroll_dice")

        for action in self.have_released_or_applied:
            if self.have_released_or_applied[action]:
                if action in self.current_round_allowed_actions['pilot']:
                    self.current_round_allowed_actions['pilot'].remove(action)
                if action in self.current_round_allowed_actions['copilot']:
                    self.current_round_allowed_actions['copilot'].remove(action)
        
        
    
    def back_to_pilot(self):
        return self.current_role == "pilot"
    
    def back_to_copilot(self):
        return self.current_role == "copilot"
    
    def seven_rounds_not_end(self):
        return self.current_round < 6
    
    def seven_rounds_end(self):
        return self.current_round == 6
    
    def crashed_on_air(self):
        if not self.mandatory_actions_done():
            return True
        if self.axis_state >= 3 or self.axis_state <= -3:
            return True
        if self.current_approach > 6:
            return True
        
        return False
        # return not self.mandatory_actions_done() or self.axis_state >= 3 or self.axis_state <= -3
    
    def crashed_while_landing(self):
        
        if self.current_round != 6:
            return True
        
        if self.axis_state != 0:
            return True
        
        if self.engine_power > self.current_brake_force:
            return True
        
        if self.have_released_or_applied['release_landing_gear1'] or self.have_released_or_applied['release_landing_gear2'] or self.have_released_or_applied['release_landing_gear3']:
            return True
        
        if self.have_released_or_applied['release_flap1'] or self.have_released_or_applied['release_flap2'] or self.have_released_or_applied['release_flap3'] or self.have_released_or_applied['release_flap4']:
            return True
        
        return False
    
    def mandatory_actions_done(self):
        return self.left_axis_state and self.right_axis_state and self.left_engine_power and self.right_engine_power
    
    def safe_landed(self):
        
        return not self.crashed_while_landing()
    
    def dices_used_up(self):
        
        if self.current_round_dices['pilot'] and self.current_round_dices['copilot']:
            return False

        return True
    
    def process_roll_dice(self):
        
        self.current_round_dices['pilot'] = random.choices([1, 2, 3, 4, 5, 6], k=4)
        self.current_round_dices['copilot'] = random.choices([1, 2, 3, 4, 5, 6], k=4)
        
    
    
    def process_reroll_dice(self):
        for response in self.current_responses:

            to_be_rerolled_dices_numbers = response['answer']['dices']

            to_be_rerolled_dices_numbers = ast.literal_eval(to_be_rerolled_dices_numbers) if type(to_be_rerolled_dices_numbers) == str else to_be_rerolled_dices_numbers
            to_be_rerolled_dices_index = [self.current_round_dices[response['role']].index(i) for i in to_be_rerolled_dices_numbers]
            
            for i in to_be_rerolled_dices_index:
                
                self.current_round_dices[response['role']][i] = random.choice([1, 2, 3, 4, 5, 6])
        
    
    def process_record_action(self):
        
        self.fail_case = None
        self.fail_cases = []
        
        if self.current_action == "reroll_dice":
            self.current_round_allowed_actions['pilot'].remove("reroll_dice")
            self.current_round_allowed_actions['copilot'].remove("reroll_dice")
            return
        
        self.current_round_dices[self.current_role].remove(self.current_dice) 
        self.current_round_allowed_actions[self.current_role].remove(self.current_action)
        
        self.action_history[f'round{self.current_round}'].append(f"{self.current_role} {self.current_action} {self.current_dice}")
    
    
    def process_action(self):
        
        # if self.current_action in self.have_released_or_applied.keys():
        #     self.have_released_or_applied[self.current_action] = True
        
        if "engine" in self.current_action:
            if self.current_role == "pilot":
                self.left_engine_power = self.current_dice
            elif self.current_role == "copilot":
                self.right_engine_power = self.current_dice

        elif "axis" in self.current_action:
            if self.current_role == "pilot":
                self.left_axis_state = self.current_dice
            elif self.current_role == "copilot":
                self.right_axis_state = self.current_dice
        
        elif "radio" in self.current_action:
            radio_area = self.current_approach + self.current_dice -1  # clear the plane on that "area" 
            self.approach_track[radio_area] -= 1
        
        elif "brake" in self.current_action:
            brake_number = int(self.current_action[-1])
            self.current_brake_force = self.brake_forces[brake_number-1]
            self.have_released_or_applied[self.current_action] = True
            
        elif "coffee" in self.current_action:
            if "add" in self.current_action:
                self.coffee_tokens += 1
            elif "drink" in self.current_action:
                self.coffee_tokens -= 1
        
        elif 'gear' in self.current_action:
            self.left_aerodynamic_marker += 1
            self.have_released_or_applied[self.current_action] = True
            
        elif "flap" in self.current_action:
            self.right_aerodynamic_marker += 1
            self.have_released_or_applied[self.current_action] = True
            # wind resistance lower bound
            
            # flap_number = int(self.current_action[-1])
            # self.have_released_or_applied[f"release_flap{flap_number}"] = True
            
        
    def logging(self, content):
        self.log.append(content)
            
        with open(self.log_file, "w") as f:
            # save
            for i in self.log:
                # print(i)
                f.write(str(i) + "\n")
    
    
    def draw_game_gui(self):
        
        if not self.debug:
            return
        # Colors
        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)
        RED = (255, 0, 0)
        GREEN = (0, 255, 0)
        BLUE = (0, 0, 255)
        
        # Fonts
        font = pygame.font.Font(None, 24)
        
        # Get game data
        game_data = self.to_dict()
        width, height = 800, 600

            
        self.screen.fill(WHITE)
        
        # Draw game information
        y_offset = 10
        text_surfaces = [
            font.render(f"Current Round: {game_data['current_round']}", True, BLACK),
            font.render(f"Current Role: {game_data['current_role']}", True, BLACK),
            font.render(f"Coffee Tokens: {game_data['coffee_tokens']}", True, BLACK),
            font.render(f"Axis State: {game_data['axis_state']}", True, BLACK),
            font.render(f"Engine Power: {game_data['engine_power']}", True, BLACK),
            font.render(f"Brake Force: {game_data['current_brake_force']}", True, BLACK),
        ]
        
        for surface in text_surfaces:
            self.screen.blit(surface, (10, y_offset))
            y_offset += 30
        
        # Draw approach track
        track_width = 600
        track_height = 50
        track_x = (width - track_width) // 2
        track_y = 200
        
        pygame.draw.rect(self.screen, BLACK, (track_x, track_y, track_width, track_height), 2)
        
        for i, planes in enumerate(game_data['approach_track']):
            x = track_x + (i * track_width // 7)
            pygame.draw.rect(self.screen, BLUE, (x, track_y, track_width // 7, track_height))
            text = font.render(str(planes), True, WHITE)
            self.screen.blit(text, (x + 10, track_y + 10))
        
        # Draw dice
        dice_y = 300
        for role in ['pilot', 'copilot']:
            dice_x = 10 if role == 'pilot' else width - 210
            pygame.draw.rect(self.screen, BLACK, (dice_x, dice_y, 200, 100), 2)
            text = font.render(f"{role.capitalize()} Dice:", True, BLACK)
            self.screen.blit(text, (dice_x + 10, dice_y + 10))
            
            for i, die in enumerate(game_data['current_round_dices'][role]):
                die_text = font.render(str(die), True, RED)
                self.screen.blit(die_text, (dice_x + 30 + (i * 40), dice_y + 50))
        
        # Draw action history
        # history_y = 450
        # pygame.draw.rect(self.screen, BLACK, (10, history_y, width - 20, 140), 2)
        # text = font.render("Action History:", True, BLACK)
        # self.screen.blit(text, (20, history_y + 10))
        
        # history = game_data['log'][f"round{game_data['current_round']}"]
        # for i, action in enumerate(history[-5:]):  # Show last 5 actions
        #     action_text = font.render(action, True, BLACK)
        #     self.screen.blit(action_text, (20, history_y + 40 + (i * 20)))
        
        pygame.display.flip()
        
    
    def game_loop(self):
        
        if self.debug:
            
            pygame.init()
            
            # Set up the display
            width, height = 800, 600
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("Sky Team Game")
            
        while self.state != "end":
            self.draw_game_gui()   
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.state = "end"
                    
            print("current state: " + self.state)
            
            if self.state == "start":
                
                self.game_start()
            
            elif self.state == "round_start":

                # self.round_setup()
                self.strategy_discuss()

            elif self.state == "discuss":
                
                self.publish(self.state, self.to_dict())
                
                
                self.roll_dice()

            elif self.state == "roll_dice":
                
                # self.publish(self.state, self.to_dict())
                
                
                self.action_time()
            
            elif self.state == "reroll_dice":
                
                self.publish(self.state, self.to_dict())
                
                
                self.next()
                
            elif self.state == "pilot_action":
                
                self.publish(self.state, self.to_dict())
                
                self.next()
                            
            elif self.state == "pilot_action_end":
                
                self.next()
                
            elif self.state == "copilot_action":
                
                self.publish(self.state, self.to_dict())
                
                self.next()
            
            elif self.state == "copilot_action_end":
                
                self.next()
                
            elif self.state == "round_end":
                
                self.game_continue()
            
            elif self.state == "landing":
                    
                self.landing()
                    
            elif self.state == "safe_landed":
                self.game_end()
            elif self.state == "crash":
                self.game_end()
                
                
    
    def to_dict(self):
        # print(self.fail_case)
        game_dict = {
            'current_round': self.current_round,
            'current_approach': self.current_approach,
            'current_round_allowed_actions': self.current_round_allowed_actions,
            "discuss_history": self.dicuss_history,
            'current_round_dices': self.current_round_dices,
            'approach_track': self.approach_track,
            'altitude_track': self.altitude_track,
            'reroll_dice_positions': self.reroll_dice_positions,
            'current_round_reroll_tokens': self.current_round_reroll_tokens,
            'current_brake_force': self.current_brake_force,
            'left_axis_state': self.left_axis_state,
            'right_axis_state': self.right_axis_state,
            'axis_state': self.axis_state,
            'left_engine_power': self.left_engine_power,
            'right_engine_power': self.right_engine_power,
            'engine_power': self.engine_power,
            # 'brake_state': self.brake_state,
            'coffee_tokens': self.coffee_tokens,
            'dice_rolls': self.dice_rolls,
            'current_role': self.current_role,
            'log': self.log,
            'actions_list': self.actions_list,
            'fail_cases': self.fail_cases,
        }
        return game_dict
