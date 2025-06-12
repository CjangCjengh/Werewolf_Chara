import numpy as np
import random
from observation.observation import Observation


class SkyTeamGameObservation(Observation):
    
    def __init__(self):
        super().__init__()
        self.init()
        
    def init(self):
        
        self.current_round_dices =  {"pilot": [], "copilot": []}
        # self.current_round_copilot_dices = []
        
        self.current_round = -1
        
        self.approach_track = [0,0,1,2,1,3,2] # _airplane_numbers on rounte
        self.altitude_track = [6000, 5000, 4000, 3000, 2000, 1000, 0]
        
        self.reroll_dice_positions = [0, 4]
        self.current_round_reroll_tokens = 1
        
        self.flaps_deployment_state = [False, False, False, False]  # Flaps not deployed
        self.flaps_allowed_dice =[[1,2], [2,3], [4,5], [5,6]]
        
        self.brake_dice_numbers = [2,4,6]
        self.brake_applied = [False, False, False]
        self.current_brake_force = 0
        
        self.left_axis_state = None  # Axis state starts neutral
        self.right_axis_state = None  # Axis state starts neutral
        self.axis_state = 0  # Axis state starts neutral
        
        self.left_engine_power = None  # Initial left engine power
        self.right_engine_power = None  # Initial right engine power
        self.engine_power = 0  # Initial engine power
        
        self.brake_state = 0  # Initial brake state
        self.landing_gear_state = [False, False, False]  # Landing gear not deployed
        
        self.traffic = [2, 1, 2, 1, 2, 1, 2]  # Traffic on the approach track
        self.coffee_tokens = 0  # No coffee tokens at start
        self.dice_rolls = {"pilot": [], "copilot": []}  # No dice rolled yet
        self.turn_order = "pilot"  # Pilot goes first
        self.log = []

        self.gear1_allowed_dice = [1,2]
        self.gear2_allowed_dice = [3,4]
        self.gear3_allowed_dice = [5,6]
        
        self.pilot_radio_allowed_dice = [1,2,3,4,5,6]
        self.copilot_radio1_allowed_dice = [1,2,3,4,5,6]
        
        self.pilot_axis_state_allowed_dice = [1,2,3,4,5,6]
        self.copilot_axis_state_allowed_dice = [1,2,3,4,5,6]
        
        self.copilot_flap1_allowed_dice = [1,2]
        self.copilot_flap2_allowed_dice = [2,3]
        self.copilot_flap3_allowed_dice = [4,5]
        self.copilot_flap4_allowed_dice = [5,6]
        
        self.actions_list = {
            'pilot': 
                ["pilot_use_radio", "reroll_dice", "pilot_correct_axis", "pilot_adjust_engine", "release_landing_gear1", "release_landing_gear2", "release_landing_gear3", 'apply_brake', 'coffee_add', 'coffee_drink'],
            'copilot':
                ["copilot_use_radio1", "copilot_use_radio2", "reroll_dice", "copilot_correct_axis", "copilot_adjust_engine", "release_flap1", "release_flap2", "release_flap3", "release_flap4", 'coffee_add', 'coffee_drink']
            }
        # self.pilot_actions_list = 
        # self.copilot_actions_list = 
    

    def round_setup(self):
        
        if self.left_axis_state and self.right_axis_state: # 如果所有的轴都被设置了
            self.axis_state = self.left_axis_state - self.right_axis_state
            
        if self.left_engine_power and self.right_engine_power: # 如果所有的引擎都被设置了
            self.engine_power = self.left_engine_power + self.right_engine_power
            
        self.current_round += 1
        self.current_round_reroll_tokens = 1 if self.current_round in self.reroll_dice_positions else 0
        self.current_round_dices =  {"pilot": [], "copilot": []}
        # self.current_round_pilot_dices = []
        # self.current_round_copilot_dices = []
    
    def back_to_pilot(self):
        return self.turn_order == "pilot"
    
    def seven_rounds_not_end(self):
        return self.current_round < 6
    
    def seven_rounds_end(self):
        return self.current_round == 6
    
    def crashed_on_air(self):
        return not self.mandatory_actions_done() or self.axis_state >= 3 or self.axis_state <= -3
    
    def crashed_while_landing(self):
        return self.axis_state != 0 or self.engine_power > self.current_brake_force or not all(self.landing_gear_state) or not all(self.flaps_deployment_state)
    
    def mandatory_actions_done(self):
        return self.left_axis_state and self.right_axis_state and self.left_engine_power and self.right_engine_power
    
    def safe_landed(self):
        if self.current_round == 6 and self.axis_state == 0 and self.engine_power < self.current_brake_force and all(self.landing_gear_state) and all(self.flaps_deployment_state):
            return True
    
    def round_end(self):
        
        return not self.round_not_end()
    
    def round_not_end(self):
        
        if self.current_round_dices['pilot'] and self.current_round_dices['copilot']:
            return True
    
    
    def process_roll_dice(self, responses):
        for response in responses:
            
            self.current_round_dices[response['role']] = response['answer']['dice_rolls']
            # if response['role'] == "pilot":
            #     self.current_round_pilot_dices = response['answer']['dice_rolls']
            # elif response['role'] == "copilot":
            #     self.current_round_copilot_dices = response['answer']['dice_rolls']
        
        ret = {"state": "roll_dice", "success": True}
        return  ret
    
    
    def process_reroll_dice(self, responses):
        for response in responses:

            to_be_rerolled_dices_numbers = response['answer']['dices']
            to_be_rerolled_dices_index = [self.current_round_dices[response['role']].index(i) for i in to_be_rerolled_dices_numbers]
            
            # random choose a new dice
            for i in to_be_rerolled_dices_index:
                # if response['role'] == "pilot":
                self.current_round_dices[response['role']][i] = random.choice([1, 2, 3, 4, 5, 6])
                # elif response['role'] == "copilot":
                #     self.current_round_copilot_dices[i] = random.choice([1, 2, 3, 4, 5, 6])
        
        ret = {"state": "reroll_dice", "success": True}
        return  ret
        
    
    
    def process_flap(self, dice):
        
        # find the first dice number where it is not applied
        for i in range(4):
            if not self.flaps_deployment_state[i] and dice in self.flaps_allowed_dice[i]:
                self.flaps_deployment_state[i] = True
                return True
        
        return False
            
            
    def process_brake(self, dice):
        
        # find the first dice number where it is not applied
        for i in range(3):
            if not self.brake_applied[i] and dice == self.brake_dice_numbers[i]:
                self.brake_applied[i] = True
                if i == 0:
                    self.current_brake_force = 2.5
                elif i == 1:
                    self.current_brake_force = 4.5
                elif i== 2:
                    self.current_brake_force = 6.5
                    
                return True
        
        return False
            
        
    def process_radio_call(self, dice):
        area = self.current_round + dice -1  # clear the plane on that "area" 
        
        if area < 7 and self.approach_track[area] > 0: 
            self.approach_track[area] -= 1
            self.log.append("radio call success")
            return True
        else:
            self.log.append("radio call failed")
            return False
            
    def process_axis_state(self, is_pilot, dice):
            
        if is_pilot:
            self.left_axis_state = dice
        else:
            self.right_axis_state = dice
        
        return True
        # self.axis_state = self.left_axis_state - self.right_axis_state
        
    def process_landing_gear(self, gear_index, dice):
        
        if gear_index == 0 and dice+1 in self.gear1_allowed_dice:
            self.landing_gear_state[gear_index] = True
            return True
        elif gear_index == 1 and dice+1 in self.gear2_allowed_dice:
            self.landing_gear_state[gear_index] = True
            return True
        elif gear_index == 2 and dice+1 in self.gear3_allowed_dice:
            self.landing_gear_state[gear_index] = True
            return True
        else:
            return False
        
    def process_engine(self, is_pilot, dice):
        
        if is_pilot:
            self.left_engine_power = dice
        else:
            self.right_engine_power = dice
        
        return True
        # self.engine_power = self.left_engine_power + self.right_engine_power
        
        
    # def process_copilot_action(self, responses):
        
    #     self.turn_order = "copilot"
    #     answer = responses[0]['answer']
    #     self.logging(answer)

    #     action = answer['action']
        
    #     if action == "reroll_dice":
    #         return {"state": "copilot_action", "action": "reroll_dice"}
            
    #     dice = answer['dice']
        
    #     if action == "copilot_use_radio1":
            
    #         successed = self.process_radio_call(dice)
            

    #     elif action == "copilot_use_radio2":
    #         successed = self.process_radio_call(dice)
            
            
    #     elif action == "copilot_correct_axis":
    #         successed = self.process_axis_state(is_pilot= False, dice = dice)
            
    #     elif action == "copilot_adjust_engine":
            
    #         successed = self.process_engine(is_pilot=False, dice = dice)
            
    #     elif action == "release_flap1":
            
    #         successed = self.process_flap(dice)
            
            
    #     elif action == "release_flap2":
        
    #         successed = self.process_flap(dice)
            
    #     elif action == "release_flap3":
        
    #         successed = self.process_flap(dice)
            
    #     elif action == "release_flap4":
        
    #         successed = self.process_flap(dice)
            
    #     elif action == "coffee_add":
    #         successed = self.process_add_coffee(dice)
            
    #     elif action == "coffee_drink":
    #         successed = self.process_drink_coffee()
    #     else:
    #         raise ValueError(f"Invalid action {action}")
        
        
    #     if successed:
    #         self.current_round_copilot_dices.remove(dice) # remove the dice
    #         ret = {"state": "copilot_action", "action": answer, "success": True}
    #         self.logging(ret)
    #         return ret
    #     else:
    #         ret = {"state": "pilot_action", "action": answer, "success": False}
    #         self.logging(ret)
    #         return ret
        
    # def process_pilot_action(self, responses):
        
    #     self.turn_order = "pilot"

    #     answer = responses[0]['answer']
    #     self.logging(answer)

    #     action = answer['action']
        
    #     if action == "reroll_dice":
    #         return {"state": "pilot_action", "action": "reroll_dice"}
            
    #     dice = int(answer['dice'])
        
    #     if action == "release_landing_gear1":
            
    #         successed = self.process_landing_gear(0, dice)
            
    #     elif action == "release_landing_gear2":
            
    #         successed = self.process_landing_gear(1, dice)
            
    #     elif action == "release_landing_gear3":
            
    #         successed = self.process_landing_gear(2, dice)
        
    #     elif action == "pilot_adjust_engine":
            
    #         successed = self.process_engine(is_pilot=True, dice = dice)
        
    #     elif action == "pilot_correct_axis":
    #         successed = self.process_axis_state(is_pilot= True, dice = dice)
            
    #     elif action == "pilot_use_radio":
            
    #         successed = self.process_radio_call(dice)
            
    #     elif action == "apply_brake":
            
    #         successed = self.process_brake(dice)
            
    #     elif action == "coffee_add":
    #         successed = self.process_add_coffee()
            
    #     elif action == "coffee_drink":
            
    #         successed = self.process_drink_coffee()
            
    
    #     else:
    #         raise ValueError(f"Invalid action {action}")
        
    #     if successed:
    #         self.current_round_pilot_dices.remove(dice) # remove the dice
    #         ret = {"state": "copilot_action", "action": answer, "success": True}
    #         self.logging(ret)
    #         return ret
    #     else:
    #         ret = {"state": "pilot_action", "action": answer, "success": False}
    #         self.logging(ret)
    #         return ret
        
    def process_choose_action(self, responses):
        answer = responses[0]['answer']
        self.logging(answer)

        role = responses[0]['role']  # Get the role (pilot or copilot)
        action = answer['action']
        dice = int(answer['dice']) if 'dice' in answer else None

        # Define action mappings for both pilot and copilot
        common_action_mapping = {
            "coffee_add": lambda: self.process_add_coffee(),
            "coffee_drink": lambda: self.process_drink_coffee(),
            "reroll_dice": lambda: {"state": f"{role}_choose_action", "action": "reroll_dice"}
        }

        pilot_action_mapping = {
            "release_landing_gear1": lambda: self.process_landing_gear(0, dice),
            "release_landing_gear2": lambda: self.process_landing_gear(1, dice),
            "release_landing_gear3": lambda: self.process_landing_gear(2, dice),
            "pilot_adjust_engine": lambda: self.process_engine(is_pilot=True, dice=dice),
            "pilot_correct_axis": lambda: self.process_axis_state(is_pilot=True, dice=dice),
            "pilot_use_radio": lambda: self.process_radio_call(dice),
            "apply_brake": lambda: self.process_brake(dice)
        }

        copilot_action_mapping = {
            "copilot_use_radio1": lambda: self.process_radio_call(dice),
            "copilot_use_radio2": lambda: self.process_radio_call(dice),
            "copilot_correct_axis": lambda: self.process_axis_state(is_pilot=False, dice=dice),
            "copilot_adjust_engine": lambda: self.process_engine(is_pilot=False, dice=dice),
            "release_flap1": lambda: self.process_flap(dice),
            "release_flap2": lambda: self.process_flap(dice),
            "release_flap3": lambda: self.process_flap(dice),
            "release_flap4": lambda: self.process_flap(dice)
        }

        # Combine common and role-specific actions
        action_mapping = common_action_mapping.copy()
        if role == "pilot":
            action_mapping.update(pilot_action_mapping)
            self.turn_order = "pilot"
        elif role == "copilot":
            action_mapping.update(copilot_action_mapping)
            self.turn_order = "copilot"
        else:
            raise ValueError(f"Invalid role {role}")

        # Process the action
        if action in action_mapping:
            result = action_mapping[action]()
            if isinstance(result, dict):  # For reroll_dice or any immediate returns
                return result
            successed = result
        else:
            raise ValueError(f"Invalid action {action}")

        if successed:
            self.current_round_dices[role].remove(dice)  # Remove the dice from the respective role's list
            ret = {"state": f"{role}_choose_action" if role == "pilot" else "pilot_action", "action": answer, "success": True}
        else:
            ret = {"state": f"{role}_choose_action", "action": answer, "success": False}

        self.logging(ret)
        return ret

    def process_add_coffee(self):
        
        if self.coffee_tokens < 3:
            self.coffee_tokens += 1
            return True
        else:
            return False
    
    def process_drink_coffee(self):
        
        if self.coffee_tokens > 0:
            self.coffee_tokens -= 1
            return True
        else:
            return False
    
    def logging(self, content):
        self.log.append(content)
        # for k, v in content_dict.items():
        #     self.logging(f"{k}: {v}")
        print(content)
            
            
    def create_image(self):
        image = np.ones((100, 100, 3), dtype=np.uint8) * 255  # 全白图像
        return image
