import random

from agent.naive_agent import NaiveAgent

from subscriber.subscriber import Subscriber


class HanabiPlayer(Subscriber):
    def __init__(self, config):
        name = config['name']
        role = config['role']
        strategy = config['strategy']
        model = config['model'] if 'model' in config else None
        
        super().__init__(name, role)
        self.strategy = strategy
        if strategy == "random":
            self.agent = None
        elif strategy == "naive":
            self.agent = NaiveAgent(model)

    def notify(self, topic, message, image, observation):
        print(f"{self.name} {self.role}收到消息[{topic}]:{message}")


        if topic == "p1_choose_action":
            return self.choose_action(observation)
        elif topic == "p1_give_clue":
            return self.give_clue(observation)
        elif topic == "p1_play_card":
            return self.play_card(observation)
        elif topic == "p1_discard_card":
            return self.discard_card(observation)
        elif topic == "p2_choose_action":
            return self.choose_action(observation)
        elif topic == "p2_give_clue":
            return self.give_clue(observation)
        elif topic == "p2_play_card":
            return self.play_card(observation)
        elif topic == "p2_discard_card":
            return self.discard_card(observation)


    def choose_action(self, observation):

        if self.strategy == "random":
            choice = random.choice(["A", "B", "C"])
            answer = {"choice": choice, "reason": "random"}
            

        elif self.strategy == "naive":

            input_data = {
                "name": self.name,
                "role": self.role,
                "record": observation["log"],
                "current_situation": str(observation),
            }

            answer = self.agent.make_decision(input_data, prompts="prompts/hanabi.prompt")


        return {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }

    def give_clue(self, observation):

        if self.strategy == "random":
            # random choose clue from RGBYW12345
            clue = random.choice(["R", "G", "B", "Y", "W", "1", "2", "3", "4", "5"])
            answer = {"clue": clue, "to": "player1" if self.role == "player2" else "player2", "reason": "random"}
            

        elif self.strategy == "naive":
            
            info = {
                "name": self.name,
                "role": self.role,
                "record": observation["log"],
                "current_situation": str(observation),
            }
            
            answer = self.agent.make_decision(info, prompts="prompts/hanabi_give_clue.prompt")
            
            
        return {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }
    
    def play_card(self, observation):
        # random choose from len of observation observation.players_hands[self.role]
        if self.strategy == "random":
            choice = random.choice(range(len(observation["players_hands"][self.role])))        
            to_where = random.choice(["red", "yellow", "blue", "green", "white"])
            answer = {"index": choice, "to": to_where, "reason": "random"}
            
        
        elif self.strategy == "naive":
            
            info = {
                "name": self.name,
                "role": self.role,
                "record": observation["log"],
                "current_situation": observation,
                "list": observation["players_hands"][self.role]
            }
            
            answer = self.agent.make_decision(info, prompts="prompts/hanabi_play_card.prompt")
                        
        return {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }
    
    def discard_card(self, observation):
        # random choose from observation self.players_hands[role]
        choice = random.choice(range(len(observation["players_hands"][self.role])))        
        if self.strategy == "random":
            answer = {"index": choice, "reason": "random"}
            
        
        elif self.strategy == "naive":
            
            info = {
                "name": self.name,
                "role": self.role,
                "record": observation["log"],
                "current_situation": observation,
                "list": observation["players_hands"][self.role]
            }
            
            answer = self.agent.make_decision(info, prompts="prompts/hanabi_play_card.prompt")
                        
        return {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }
    
        
