from transitions import Machine
from transitions.extensions import GraphMachine
from publisher.publisher import Publisher
from broker.werewolf_broker import WerewolfGameBroker
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import json
import os
import pygame


class WerewolfGameHost(Publisher):
    def __init__(self, config): 
        # super().__init__(broker)
        
        self.debug = False
        self.config = config
        self.broker = WerewolfGameBroker(config, use_multi_thread=True)
        
        self.create_fsm()

        self.votes = {0: [], 1: [], 2: [], 3:[] , 4:[], 5: [], 6: [], 7: [], 8: [], 9: []} # 投票信息  视觉信息中可能需要
        self.night_victims = {0: [], 1: [], 2: [], 3:[] , 4:[], 5: [], 6: [], 7: [], 8: [], 9: []}
        self.werewolf_choices = []
        self.day_count = 0
        self.max_days = 9
        self.players_names = [player.name for player in self.broker.players]
        self.players_roles = {player.name: player.role for player in self.broker.players}
        self.players_status = {player.name: "alive" for player in self.broker.players}
        self.hunter_name = [player.name for player in self.broker.players if player.role == "hunter"][0]
        self.werewolf_victim = None 
        self.vote_exile = None 
        self.current_fail_case = []
        self.witch_used_heal = False 
        self.witch_used_poison = False
        self.previous_state = None
        self.log = [] 
        
        self.fail_case = None
        self.fail_cases = []
        

    def create_fsm(self):
        
        self.finite_states = [
            'start', 'night', 
            'wolf_action', 'wolf_action_end', 
            'hunter_action', 
            'witch_heal', 'witch_poison', 
            'seer_action', 'day', 'day_discuss', 'day_vote', 'day_last_words',
            'day_vote_end', 'wolf_win', 'good_win', 'end'
        ]

        self.machine = GraphMachine(model=self, states=self.finite_states, initial='start', show_conditions=True)
        
        self.machine.add_transition(source='start', dest='night', trigger='game_start')
        
        self.machine.add_transition(source='night', dest='wolf_action', trigger='wolf_open_eye')
        
        self.machine.add_transition(source='wolf_action', dest='hunter_action', trigger='wolf_action_done', conditions='werewolf_attack_hunter', before = "process_previous_state")
        self.machine.add_transition(source='wolf_action', dest='wolf_action_end', trigger='wolf_action_done')
        
        self.machine.add_transition(source='wolf_action_end', dest='wolf_win', trigger='wolf_action_done', conditions='no_vill')
        self.machine.add_transition(source='wolf_action_end', dest='wolf_win', trigger='wolf_action_done', conditions='no_gold')
        self.machine.add_transition(source='wolf_action_end', dest='good_win', trigger='wolf_action_done', conditions='no_wolf')
        self.machine.add_transition(source='wolf_action_end', dest='witch_heal', trigger='wolf_action_done') #, conditions= ['witch_alive','witch_1_heal'])
        # self.machine.add_transition(source='wolf_action_end', dest='witch_poison', trigger='wolf_action_done', conditions=['witch_alive','witch_0_heal','witch_1_poison'])
        # self.machine.add_transition(source='wolf_action_end', dest='seer_action', trigger='wolf_action_done', conditions=['witch_alive','witch_0_heal','witch_0_poison','seer_alive'])
        # self.machine.add_transition(source='wolf_action_end', dest='seer_action', trigger='wolf_action_done', conditions=["witch_dead", "seer_alive"])
        # self.machine.add_transition(source='wolf_action_end', dest='day', trigger='wolf_action_done', conditions=["witch_dead", "seer_dead"])
        # self.machine.add_transition(source='wolf_action_end', dest='day', trigger='wolf_action_done', conditions=["witch_0_heal", "witch_0_poison", "seer_dead"])

        # self.machine.add_transition(source='witch_heal', dest='witch_heal', trigger='witch_heal_done', conditions= ["witch_heal_format_incorrect"])
        self.machine.add_transition(source='witch_heal', dest='witch_poison', trigger='witch_heal_done') # , conditions= ["witch_1_poison"]
        # self.machine.add_transition(source='witch_heal', dest='seer_action', trigger='witch_heal_done', conditions=["seer_alive"])
        # self.machine.add_transition(source='witch_heal', dest='day', trigger='witch_heal_done', conditions=["seer_dead"])

        # self.machine.add_transition(source='witch_poison', dest='witch_poison', trigger='witch_poison_done', conditions= 'witch_poison_format_incorrect')
        self.machine.add_transition(source='witch_poison', dest='wolf_win', trigger='witch_poison_done', conditions=["no_vill"])
        self.machine.add_transition(source='witch_poison', dest='wolf_win', trigger='witch_poison_done', conditions=["no_gold"])
        self.machine.add_transition(source='witch_poison', dest='good_win', trigger='witch_poison_done', conditions=["no_wolf"])
        self.machine.add_transition(source='witch_poison', dest='seer_action', trigger='witch_poison_done')         # , conditions=["seer_alive"]
        # self.machine.add_transition(source='witch_poison', dest='day', trigger='witch_poison_done', conditions=["seer_dead"])

        # self.machine.add_transition(source='seer_action', dest='seer_action', trigger='seer_action_done', conditions = ["seer_check_format_incorrect"])
        self.machine.add_transition(source='seer_action', dest='day', trigger='seer_action_done', after = 'process_seer_check')

        self.machine.add_transition(source='day', dest='day_last_words', trigger='daytime_start')  # , conditions='someone_dead_last_night'
        # self.machine.add_transition(source='day', dest='day_discuss', trigger='daytime_start') 
        
        self.machine.add_transition(source='day_last_words', dest='day_discuss', trigger='day_last_words_done') 

        self.machine.add_transition(source='day_discuss', dest='day_vote', trigger='day_discuss_done') 
        
        # self.machine.add_transition(source='day_vote', dest='day_vote', trigger='vote_done', conditions = 'vote_format_incorrect')
        self.machine.add_transition(source='day_vote', dest='hunter_action', trigger='vote_done', conditions = 'vote_exile_hunter',before = "process_previous_state")
        self.machine.add_transition(source='day_vote', dest='day_vote_end', trigger='vote_done')
        
        self.machine.add_transition(source='day_vote_end', dest='good_win', trigger='day_vote_done', conditions="is_good_win")
        self.machine.add_transition(source='day_vote_end', dest='wolf_win', trigger='day_vote_done', conditions="is_wolf_win")
        self.machine.add_transition(source='day_vote_end', dest='night', trigger='day_vote_done', conditions='game_not_over')
        
        # self.machine.add_transition(source='hunter_action', dest='hunter_action', trigger='hunter_action_done', conditions='hunter_action_format_incorrect')
        self.machine.add_transition(source='hunter_action', dest='good_win', trigger='hunter_action_done', conditions=['no_wolf'])
        self.machine.add_transition(source='hunter_action', dest='wolf_win', trigger='hunter_action_done', conditions=['no_gold'])
        self.machine.add_transition(source='hunter_action', dest='wolf_win', trigger='hunter_action_done', conditions=['no_vill'])
        self.machine.add_transition(source='hunter_action', dest='wolf_action_end', trigger='hunter_action_done', conditions=['is_previous_state_wolf_action'])
        self.machine.add_transition(source='hunter_action', dest='day_vote_end', trigger='hunter_action_done', conditions=['is_previous_state_day_vote'])
        
        self.machine.add_transition(source='wolf_win', dest='end', trigger='game_over', before = 'process_game_over')
        self.machine.add_transition(source='good_win', dest='end', trigger='game_over', before = 'process_game_over')
        

    def save_png(self):
        self.machine.get_graph().draw('my_state_diagram.png', prog='dot')

    
    def publish(self, topic, observation):
        
        # check broker subscriber of this topic, whether it is none
        if self.broker.subscribers.get(topic) is None or len(self.broker.subscribers[topic]) == 0:
            return
        
        responses = self.broker.publish(topic, topic, self.to_dict())
        
        for response in responses:
            name = response['name']
            
            with open(os.path.join(self.config["log_directory"], f"{name}.log"), "a", encoding='utf-8') as f:
                response['answer']['topic'] = topic
                f.write(str(response['answer']) + "\n")

        self.current_responses = responses
        self.current_answer = responses[0]['answer']

        if topic == "wolf_action":
            self.werewolf_choices = responses[0]['answer']['target']
            
            while self.werewolf_action_format_incorrect():
                responses = self.broker.publish(topic, topic, self.to_dict())
                self.current_responses = responses
                self.current_answer = responses[0]['answer']
                self.werewolf_choices = responses[0]['answer']['target']
            
            self.process_werewolf_actions()

        
        elif topic == "day_vote":
            self.vote_exile = responses[0]['answer']['vote']
            
            while self.vote_format_incorrect():
                responses = self.broker.publish(topic, topic, self.to_dict())
                self.current_responses = responses
                self.current_answer = responses[0]['answer']
                self.vote_exile = responses[0]['answer']['vote']
                
            self.process_votes()
        
            
        elif topic == "hunter_action":
            self.hunter_target = responses[0]['answer']['hunt']
            
            while self.hunter_action_format_incorrect():
                responses = self.broker.publish(topic, topic, self.to_dict())
                self.current_responses = responses
                self.current_answer = responses[0]['answer']
                self.hunter_target = responses[0]['answer']['hunt']
            
            self.process_hunter_action()
                
        elif topic == "witch_poison":
            self.witch_victim = responses[0]['answer']['target']
            self.witch_name = responses[0]['name']
            while self.witch_poison_format_incorrect():
                responses = self.broker.publish(topic, topic, self.to_dict())
                self.current_responses = responses
                self.current_answer = responses[0]['answer']
                self.witch_victim = responses[0]['answer']['target']
            
            self.process_witch_poison()
            
        elif topic == "witch_heal":
            self.witch_choose_to_heal = responses[0]['answer']['heal']
            self.witch_name = responses[0]['name']

            while self.witch_heal_format_incorrect():
                responses = self.broker.publish(topic, topic, self.to_dict())
                self.current_responses = responses
                self.current_answer = responses[0]['answer']
                self.witch_choose_to_heal = responses[0]['answer']['heal']
            
            self.process_witch_heal()
            
        elif topic == "seer_action":
            self.seer_target = responses[0]['answer']['player']
            while self.seer_check_format_incorrect():
                responses = self.broker.publish(topic, topic, self.to_dict())
                self.current_responses = responses
                self.current_answer = responses[0]['answer']
                self.seer_target = responses[0]['answer']['player']

            self.process_seer_check()
            
        elif topic == "day_discuss":
            self.discuss = responses
            # while self.discuss_format_incorrect():
            #     responses = self.broker.publish(topic, topic, self.to_dict())
            #     self.current_responses = responses
            #     self.current_answer = responses[0]['answer']
            #     self.discuss = responses
            self.process_discuss()
            
        elif topic == "day_last_words":
            self.last_words = responses
            # while self.last_words_format_incorrect():
            #     responses = self.broker.publish(topic, topic, self.to_dict())
            #     self.current_responses = responses
            #     self.current_answer = responses[0]['answer']
            #     self.last_words = responses
            self.process_last_words()
        
        # log_entry = {
        #     "state": topic,
        #     "responses": responses
        # }
        
        # self.logging(log_entry)
        
    
    def unregister_all_topics_by_name(self, name):
        self.broker.unregister_all_topics_by_name(name)

    def register_one_topic_by_name(self, name, topic):
        self.broker.register_one_topic_by_name(name, topic)
    
    
    
    
    def pretty_print(self, message, message_type="info"):
        colors = {
            "info": "\033[94m",    # Blue
            "success": "\033[92m", # Green
            "warning": "\033[93m", # Yellow
            "error": "\033[91m",   # Red
            "end": "\033[0m"       # Reset to default color
        }
        color = colors.get(message_type, "\033[0m")
        print(f"{color}{message}{colors['end']}")


    def record_failure(self, response, reason):
        self.fail_case = response['answer']
        self.fail_reason = reason


    def someone_dead_last_night(self):
        result = len(self.night_victims[self.day_count]) > 0
        self.pretty_print(f"Checking if someone is dead last night: {result}", "info")
        return result
    
    def vote_format_incorrect(self):
        self.vote_counts = {}
        for response in self.current_responses:
            answer = response['answer']
            vote = answer['vote']
            if vote in self.players_names and self.players_status[vote] == "alive":
                self.votes[self.day_count].append({"name": response["name"], "vote": vote})
                if vote in self.vote_counts:
                    self.vote_counts[vote] += 1
                else:
                    self.vote_counts[vote] = 1
            else:
                self.record_failure(response, "")
                self.votes[self.day_count] = []
                self.vote_counts = {}
                return True
        
        self.vote_exile = max(self.vote_counts, key=self.vote_counts.get)

        vote_summary = {}

        for vote in self.votes[self.day_count]:
            name = vote['name']
            voted_for = vote['vote']
            if voted_for not in vote_summary:
                vote_summary[voted_for] = []
            vote_summary[voted_for].append(name)
        
        for candidate, voters in vote_summary.items():
            for player in self.broker.players:
                player.context.append(f"{', '.join(voters)} decided to vote to exile {candidate}.")
        for player in self.broker.players:
            player.context.append(f'{self.vote_exile} was exiled.')

        self.pretty_print(f"Vote format is correct. Exile vote: {self.vote_exile}", "success")
        
        log_entry = {
            "state": "vote",
            "log": f"Exile -> {self.vote_exile}"
        }
        self.logging(log_entry)
        
        return False
    
    def vote_exile_hunter(self):
        result = self.vote_exile == self.hunter_name
        # self.pretty_print(f"Checking if the vote exile is the hunter: {result}", "info")
        
        return result

    def hunter_action_format_incorrect(self):
        if self.hunter_target not in self.players_names or self.players_status[self.hunter_target] != "alive":

            self.fail_case = self.current_answer
            self.fail_case["reason"] = "Hunter target is not a valid player or is dead."
            self.fail_cases.append(self.fail_case)
            return True
        
        return False

    def seer_check_format_incorrect(self):
        if not (self.seer_target in self.players_names and self.players_status[self.seer_target] == "alive"):
            
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "Hunter target is not a valid player or is dead."
            self.fail_cases.append(self.fail_case)
            return True
            
        
        return False

    def werewolf_attack_hunter(self):
        result = self.players_roles[self.werewolf_victim] == "hunter"
        self.pretty_print(f"Checking if werewolves attacked the hunter: {result}", "info")
        return result


    def werewolf_action_format_incorrect(self):
        self.werewolf_choices = {}
        for response in self.current_responses:
            answer = response['answer']
            victim = answer['target']
            if victim in self.players_names and self.players_status[victim] == "alive":
                self.werewolf_choices[victim] = self.werewolf_choices.get(victim, 0) + 1
            else:
                # self.record_failure(response, "")
                
                self.fail_case = self.current_answer
                self.fail_case["reason"] = "Werewolf target is not a valid player or is dead."
                self.fail_cases.append(self.fail_case)
                
                self.werewolf_choices = {}
                return True
            
        self.werewolf_victim = max(self.werewolf_choices, key=self.werewolf_choices.get)

        for player in self.broker.players:
            if player.role == 'werewolf' and self.players_status[player.name] == 'alive':
                player.context.append(f'You and your werewolf teammates decide to kill {self.werewolf_victim}.')
        self.pretty_print(f"Werewolf action format is correct. Victim: {self.werewolf_victim}", "success")
        
        # self.logging(f"Werewolf action format is correct. Victim: {self.werewolf_victim}")
        return False

    def witch_poison_format_incorrect(self):
        answer = self.current_responses[0]['answer']
        # result = False
        
        if "target" not in answer:
            
            
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "Witch target is not provided."
            self.fail_cases.append(self.fail_case)
            
            return True
            
        else:
            if (answer["target"] not in self.players_names or self.players_status[answer["target"]] != "alive") and (answer["target"] != "-1"):
                
                self.fail_case = self.current_answer
                self.fail_case["reason"] = "Witch target is not a valid player or is dead."
                self.fail_cases.append(self.fail_case)
                return True
            
        # if result:
        #     # import ipdb; ipdb.set_trace()
        #     print(answer)
        #     # self.record_failure(self.current_responses[0], "")
        # self.pretty_print(f"Checking if witch poison format is incorrect: {result}", "info")
        # return result
        return False

    def witch_heal_format_incorrect(self):
        answer = self.current_responses[0]['answer']
        if "heal" not in answer:
                
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "Witch heal is not provided."
            self.fail_cases.append(self.fail_case)
            return True

        if answer["heal"] not in [True, False]:
                
            self.fail_case = self.current_answer
            self.fail_case["reason"] = "Witch heal is not a valid boolean."
            self.fail_cases.append(self.fail_case)
            return True
        
        return False
        # result = "heal" not in answer or answer["heal"] not in ["True", "False"]
        
        # if result:
        #     print(answer)
        #     self.record_failure(self.current_responses[0], "")
        # self.pretty_print(f"Checking if witch heal format is incorrect: {result}", "info")
        # return result
    
    def is_previous_state_wolf_action(self):
        result = self.previous_state == 'wolf_action'
        self.pretty_print(f"Checking if previous state was wolf action: {result}", "info")
        return result

    def is_previous_state_day_vote(self):
        result = self.previous_state == 'day_vote'
        self.pretty_print(f"Checking if previous state was day vote: {result}", "info")
        return result
    
    def no_witch(self):
        result = all(self.players_roles[p] != "witch" or self.players_status[p] != "alive" for p in self.players_names)
        self.pretty_print(f"Checking if no witch is alive: {result}", "info")
        return result
    
    def no_hunter(self):
        result = all(self.players_roles[p] != "hunter" or self.players_status[p] != "alive" for p in self.players_names)
        self.pretty_print(f"Checking if no hunter is alive: {result}", "info")
        return result
    
    def no_seer(self):
        result = all(self.players_roles[p] != "seer" or self.players_status[p] != "alive" for p in self.players_names)
        self.pretty_print(f"Checking if no seer is alive: {result}", "info")
        return result
    
    def no_gold(self):
        result = self.no_witch() and self.no_hunter() and self.no_seer()
        self.pretty_print(f"Checking if no special roles (gold) are alive: {result}", "info")
        return result
    
    def no_vill(self):
        result = all(self.players_roles[p] != "villager" or self.players_status[p] != "alive" for p in self.players_names)
        self.pretty_print(f"Checking if no villagers are alive: {result}", "info")
        return result
    
    def no_wolf(self):
        result = all(self.players_roles[p] != "werewolf" or self.players_status[p] != "alive" for p in self.players_names)
        self.pretty_print(f"Checking if no werewolves are alive: {result}", "info")
        return result
    
    def witch_1_heal(self):
        result = not self.witch_used_heal
        self.pretty_print(f"Checking if witch can use heal: {result}", "info")
        return result

    def witch_0_heal(self):
        result = self.witch_used_heal
        self.pretty_print(f"Checking if witch has used heal: {result}", "info")
        return result

    def witch_1_poison(self):
        result = not self.witch_used_poison
        self.pretty_print(f"Checking if witch can use poison: {result}", "info")
        return result

    def witch_0_poison(self):
        result = self.witch_used_poison
        self.pretty_print(f"Checking if witch has used poison: {result}", "info")
        return result

    def seer_alive(self):
        result = not self.no_seer()
        self.pretty_print(f"Checking if seer is alive: {result}", "info")
        return result

    def witch_dead(self):
        result = self.no_witch()
        self.pretty_print(f"Checking if witch is dead: {result}", "info")
        return result

    def seer_dead(self):
        result = self.no_seer()
        self.pretty_print(f"Checking if seer is dead: {result}", "info")
        return result

    def is_good_win(self):
        result = self.no_wolf()
        self.pretty_print(f"Checking if good players have won: {result}", "info")
        return result

    def is_wolf_win(self):
        result = self.no_gold() or self.no_vill()
        self.pretty_print(f"Checking if werewolves have won: {result}", "info")
        return result

    def game_not_over(self):
        result = not self.is_good_win() and not self.is_wolf_win()
        self.pretty_print(f"Checking if the game is not over: {result}", "info")
        return result

    def witch_alive(self):
        result = not self.no_witch()
        self.pretty_print(f"Checking if witch is alive: {result}", "info")
        return result
    
    
    
    def process_last_words(self):
        for player in self.night_victims[self.day_count]:
            self.unregister_all_topics_by_name(player)

        log_entry = {
            "state": "day_last_words",
            "log": f"Last words of the night victims"
        }
        self.logging(log_entry)
    
    def process_previous_state(self):
        self.previous_state = self.state

    
    def process_hunter_action(self):
        if self.hunter_target != -1:
            self.players_status[self.hunter_target] = "dead"
            self.players_status[self.hunter_name] = "dead" # hunter also dies
            self.night_victims[self.day_count].append(self.hunter_target)
            self.night_victims[self.day_count].append(self.hunter_name)
            # self.logging(f"Hunter ({self.hunter_name}) chose to kill {self.hunter_target}.")
            for player in self.broker.players:
                if player.role == 'hunter':
                    player.context.append(f'As a Hunter, you killed {self.hunter_target} before dying.')
                else:
                    player.context.append(f'Before dying, {self.hunter_name} revealed his Hunter identity and killed {self.hunter_target}.')
            
        log_entry = {
            "state": "hunter_action",
            "log": f"Hunter ({self.hunter_name}) chose to kill {self.hunter_target}."
        }
        self.logging(log_entry)


    def process_witch_poison(self):
        if self.broker.subscribers["witch_poison"] == []:
            return
        
        self.witch_victim = self.current_answer['target']
        
        if self.witch_victim != "-1":
            self.players_status[self.witch_victim] = "dead" # Victim status changed to dead
            self.witch_used_poison = True
            self.night_victims[self.day_count].append(self.witch_victim)
            self.broker.unregister_by_name(self.witch_name, "witch_poison")
            for player in self.broker.players:
                if player.role == 'witch':
                    player.context.append(f'You decide to poison {self.witch_victim}.')
                else:
                    player.context.append(f'{self.witch_victim} died.')

        log_entry = {
            "state": "witch_poison",
            "log": f"Witch poisoned {self.witch_victim}."
        }
        self.logging(log_entry)

            
    def process_witch_heal(self):
        self.witch_choose_to_heal = True if self.current_answer['heal']== True else False
        
        if self.witch_choose_to_heal:
            self.players_status[self.werewolf_victim] = "alive" # Victim status changed to alive
            self.night_victims[self.day_count].remove(self.werewolf_victim)
            self.witch_used_heal = True
            self.broker.unregister_by_name(self.witch_name, "witch_heal")
        
        for player in self.broker.players:
            if player.role == 'witch':
                player.context.append(f'You learn that {self.werewolf_victim} will be killed by the werewolves.')
                if self.witch_choose_to_heal:
                    player.context.append(f'You decide to save {self.werewolf_victim}.')
                else:
                    player.context.append(f'You decide not to save {self.werewolf_victim}.')
            elif not self.witch_choose_to_heal:
                player.context.append(f'{self.werewolf_victim} died.')

        log_entry = {
            "state": "witch_heal",
            "log": f"Witch choose to heal?: {self.witch_choose_to_heal}."
        }
        self.logging(log_entry)
        
    
    def process_seer_check(self):
        for player in self.broker.players:
            if player.role == 'seer':
                if self.players_roles[self.seer_target] == 'werewolf':
                    player.context.append(f'As the Seer, you checked {self.seer_target} and found out he is a werewolf.')
                else:
                    player.context.append(f'As the Seer, you checked {self.seer_target} and found out he is a good guy.')
        
        log_entry = {
            "state": "seer_action",
            "log": f"Seer checked {self.seer_target} and found out that they are {self.players_roles[self.seer_target]}."
        }
        self.logging(log_entry)
        
    def process_discuss(self):
        log_entry = {
            "state": "day_discuss",
            "log": f"Players are discussing."
        }
        self.logging(log_entry)
    
    
    def process_new_day(self):
        
        for victim in self.night_victims[self.day_count]:
            # unregister all topics for the victim
            self.unregister_all_topics_by_name(victim)
            self.register_one_topic_by_name(victim, "day_last_words")
            
        
        self.day_count += 1
        
        log_entry = {
            "state": "day",
            "log": f"Day {self.day_count} started."
        }
        self.logging(log_entry)
        
        
        
        
    def process_werewolf_actions(self):
        
        victim_role = self.players_roles[self.werewolf_victim]
        
        if victim_role != "hunter":
            self.players_status[ self.werewolf_victim] = "dead"
            self.night_victims[self.day_count].append(self.werewolf_victim)
        
        log_entry = {
            "state": "wolf_action",
            "log": f"Werewolves attacked {self.werewolf_victim}."
        }
        self.logging(log_entry)
        
    
    def process_votes(self):
        
        victim_role = self.players_roles[self.vote_exile]
            
        if victim_role != "hunter_action":
            self.players_status[self.vote_exile] = "dead"
        
        log_entry = {
            "state": "vote",
            "log": f"{self.vote_exile} was exiled."
        }
        self.logging(log_entry)
    
    def process_game_over(self):
        all_players = list(self.players_roles.keys())
        werewolves = [name for name, role in self.players_roles.items() if role == 'werewolf']
        non_werewolves = [name for name, role in self.players_roles.items() if role != 'werewolf']
        if self.state == 'wolf_win':
            winners = werewolves
            losers = non_werewolves
        else:
            winners = non_werewolves
            losers = werewolves
        with open(self.config['log_directory'] + '.json', 'w', encoding='utf-8') as f:
            json.dump({'players': all_players,
                       'winners': winners,
                       'losers': losers}, f, ensure_ascii=False)

        log_entry = {
            "state": "game_over",
            "log": f"winner: {self.state}"
        }
        self.logging(log_entry)

    def to_dict(self):
        game_state = {
            "players": [
                {
                    "name": name,
                    "role": self.players_roles[name],
                    "status": self.players_status[name]
                }
                for name in self.players_names
            ],
            "players_names": self.players_names,
            "today": self.day_count,
            "max_days": self.max_days,
            "who_votes_who": self.votes,
            # "werewolf_choices": self.werewolf_choices,
            "werewolf_victim": self.werewolf_victim,
            "night_victims": self.night_victims,
            "witch_used_heal": self.witch_used_heal,
            "witch_used_poison": self.witch_used_poison,
            "log": self.log,
            "current_state": self.state, 
            # "wrong_example": self.fail_case,
            # "wrong_reason": self.fail_reason
            'fail_cases': self.fail_cases
        }
        return game_state

    
    def create_image(self):
        # Initialize a subplot grid with specific titles
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                "Player Statuses", "Votes & Choices",
                "Day Count & Logs", "", 
                "", ""
            ),
            specs=[[{"type": "scatter"}, {"type": "table"}, {"type": "scatter"}], 
                [{"type": "scatter"}, None, None]]
        )

        # Player Statuses Visualization
        alive_players = [p for p in self.players_names if self.players_status[p] == "alive"]
        dead_players = [p for p in self.players_names if self.players_status[p] == "dead"]

        fig.add_trace(
            go.Scatter(
                x=[1] * len(alive_players), y=list(range(len(alive_players))),
                mode="markers+text",
                marker=dict(color="green", size=20),
                text=[f"{p} ({self.players_roles[p]})" for p in alive_players],
                textposition="middle right",
                name="Alive Players"
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=[2] * len(dead_players), y=list(range(len(dead_players))),
                mode="markers+text",
                marker=dict(color="red", size=20),
                text=[f"{p} ({self.players_roles[p]})" for p in dead_players],
                textposition="middle right",
                name="Dead Players"
            ),
            row=1, col=1
        )

        fig.update_xaxes(title_text="Player Status", row=1, col=1)
        fig.update_yaxes(title_text="Players", row=1, col=1, showticklabels=False)

        # Votes & Choices Visualization (Table)
        table_header = ["Player", "Vote"]
        # vote_rows = [[resp['name'], resp['answer']['vote']] for resp in self.votes]
        werewolf_rows = [[resp['name'], resp['answer']['vote']] for resp in self.werewolf_choices]
        
        # fig.add_trace(
        #     go.Table(
        #         header=dict(values=table_header, fill_color='paleturquoise', align='left'),
        #         cells=dict(values=[[row[0] for row in vote_rows], [row[1] for row in vote_rows]],
        #                 fill_color='lavender', align='left')
        #     ),
        #     row=1, col=2
        # )

        fig.add_trace(
            go.Table(
                header=dict(values=table_header, fill_color='paleturquoise', align='left'),
                cells=dict(values=[[row[0] for row in werewolf_rows], [row[1] for row in werewolf_rows]],
                        fill_color='lavender', align='left')
            ),
            row=1, col=2
        )

        # Day Count & Logs Visualization
        fig.add_trace(
            go.Scatter(
                x=[self.day_count], y=[1],
                mode="markers+text",
                marker=dict(color="blue", size=40, symbol="circle"),
                text=[f"Day {self.day_count}"],
                textposition="top center",
                name="Day Count"
            ),
            row=1, col=3
        )

        logs = [f"Day {log['day_count']}: {log['state']}" for log in self.log if 'day_count' in log]
        if logs:
            for i, log in enumerate(logs):
                fig.add_trace(
                    go.Scatter(
                        x=[1], y=[i],
                        mode="text",
                        text=[log],
                        textposition="middle right",
                        name="Logs"
                    ),
                    row=1, col=3
                )

        fig.update_layout(
            height=800, width=1200,
            title_text="Werewolf Game State Visualization",
            showlegend=False
        )

        # Adjust subplot layouts
        fig.update_xaxes(showticklabels=False, row=1, col=2)
        fig.update_yaxes(showticklabels=False, row=1, col=2)
        fig.update_xaxes(showticklabels=False, row=1, col=3)
        fig.update_yaxes(showticklabels=False, row=1, col=3)

        return fig
    

    def logging(self,log_entry):
        
        
        
        self.log.append(log_entry)
        # save to file
        with open(os.path.join(self.config["log_directory"], "game.log"), "w") as f:
            for entry in self.log:
                f.write(str(entry) + "\n")
                
                

    def draw_game_gui(self):
        # Colors
        BLACK = (0, 0, 0)
        WHITE = (255, 255, 255)
        GRAY = (200, 200, 200)
        RED = (255, 0, 0)
        GREEN = (0, 255, 0)
        BLUE = (0, 0, 255)
        
        width, height = 800, 600
        # Fonts
        font_small = pygame.font.Font(None, 24)
        font_medium = pygame.font.Font(None, 32)
        font_large = pygame.font.Font(None, 48)
        
        self.screen.fill(WHITE)
        
        game_state = self.to_dict()
        
        # Draw title
        title = font_large.render("Werewolf Game", True, BLACK)
        self.screen.blit(title, (width // 2 - title.get_width() // 2, 20))
        
        # Draw day count
        day_text = font_medium.render(f"Day: {game_state['today']} / {game_state['max_days']}", True, BLACK)
        self.screen.blit(day_text, (20, 80))
        
        # Draw current state
        state_text = font_medium.render(f"Current State: {game_state['current_state']}", True, BLUE)
        self.screen.blit(state_text, (20, 120))
        
        # Draw players
        player_y = 160
        for player in game_state['players']:
            color = GREEN if player['status'] == 'alive' else RED
            player_text = font_small.render(f"{player['name']} ({player['role']}): {player['status']}", True, color)
            self.screen.blit(player_text, (20, player_y))
            player_y += 30
        
        # Draw log (last 5 entries)
        # log_y = 400
        # log_text = font_medium.render("Game Log:", True, BLACK)
        # self.screen.blit(log_text, (400, log_y))
        # log_y += 40
        # for log_entry in game_state['log'][-5:]:
        #     log_entry_text = font_small.render(log_entry, True, BLACK)
        #     self.screen.blit(log_entry_text, (400, log_y))
        #     log_y += 25
        
        # Draw wrong example and reason if available
        # if game_state['wrong_example']:
        #     wrong_text = font_small.render(f"Wrong Example: {game_state['wrong_example']}", True, RED)
        #     self.screen.blit(wrong_text, (20, height - 60))
        # if game_state['wrong_reason']:
        #     reason_text = font_small.render(f"Reason: {game_state['wrong_reason']}", True, RED)
        #     self.screen.blit(reason_text, (20, height - 30))
        
        pygame.display.flip()
        
        # pygame.quit()

    def wolf_open_eye_message(self):
        werewolves = []
        for player in self.broker.players:
            if player.role == 'werewolf' and self.players_status[player.name] == 'alive':
                werewolves.append(player)
        for player in werewolves:
            other_werewolves = [wolf.name for wolf in werewolves if wolf != player]
            if len(other_werewolves) > 0:
                player.context.append(f'You open your eyes and see your werewolf teammates: {", ".join(other_werewolves)}.')
            else:
                player.context.append('You open your eyes and see that you no longer have any werewolf teammates.')

    def night_message(self):
        for player in self.broker.players:
            player.context.append(f'Night {self.day_count} begins.')

    def day_message(self):
        for player in self.broker.players:
            player.context.append(f'Day {self.day_count} begins.')

    def game_start_message(self):
        for player in self.broker.players:
            player.context.append(f'There are {len(self.players_names)} people in this game: {", ".join(self.players_names)}.')

    def game_loop(self):
        
        if self.debug:
            
            pygame.init()
            
            # Set up the display
            width, height = 800, 600
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("Werewolf Game")
            
        
        while self.state != "end":
            
            # self.draw_game_gui()
            
            # for event in pygame.event.get():
            #     if event.type == pygame.QUIT:
            #         self.state = "end"
                    
            print("current state: " + self.state)

            # Increment the counter for the current state
            # if self.state in state_counter:
            #     state_counter[self.state] += 1
            # else:
            #     state_counter[self.state] = 1

            # # Check if any state persists for over 10 times
            # if state_counter[self.state] > 15:
            #     print(f"State {self.state} persisted for over 10 times. Stopping the self.")
            #     break

            if self.state == "start":
                self.game_start_message()
                self.game_start()
            
            elif self.state == "night":
                self.night_message()
                self.wolf_open_eye()
                self.wolf_open_eye_message()
            
            elif self.state == "wolf_action":
                self.publish(self.state, self.to_dict())
                self.wolf_action_done()
            
            elif self.state == "wolf_action_end":
                self.wolf_action_done()
            
            elif self.state == "witch_heal":
                self.publish(self.state, self.to_dict())
                # self.process_witch_heal()
                self.witch_heal_done()
            
            elif self.state == "witch_poison":
                self.publish(self.state, self.to_dict())
                # self.process_witch_poison()
                self.witch_poison_done()
                
            elif self.state == "seer_action":
                self.publish(self.state, self.to_dict())
                # self.process_seer_check()
                self.seer_action_done()
            
            elif self.state == "day":
                # self.process_new_day()
                self.day_count += 1
                self.day_message()
                self.daytime_start()
            
            elif self.state == "hunter_action":
                self.publish(self.state, self.to_dict())
                
                # self.process_hunter_action()
                self.hunter_action_done()
            
            elif self.state == "day_last_words":
                self.publish(self.state, self.to_dict())
                # self.process_last_words()
                self.day_last_words_done()
                
            elif self.state == "day_discuss":
                self.publish(self.state, self.to_dict())
                # self.process_discuss()
                self.day_discuss_done()
            
            elif self.state == "day_vote":
                self.publish(self.state, self.to_dict())
                # self.process_votes()
                self.vote_done()
                    
            elif self.state == "day_vote_end":
                self.day_vote_done()
                
            elif self.state == "wolf_win" or self.state == "good_win":
                self.game_over()

            for player in self.broker.players:
                with open(os.path.join(self.config["log_directory"], f"log_{player.name}.log"), "w", encoding='utf-8') as f:
                    f.write('\n'.join(player.context))
