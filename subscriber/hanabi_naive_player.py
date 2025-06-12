import random

from agent.naive_agent import NaiveAgent

from subscriber.subscriber import Subscriber


class HanabiNaivePlayer(Subscriber):
    def __init__(self, config):
        name = config['name']
        role = config['role']
        super().__init__(name, role)

        model = config['model'] 
        self.agent = NaiveAgent(model)

        

    def notify(self, topic, message, image, observation):
        print(f"{self.name} {self.role}收到消息[{topic}]:{message}")

        self.info = {
            "name": self.name,
            "role": self.role,
            "record": observation["log"],
            "current_situation": observation,
            # "list": observation["players_hands"][self.role],
            "fail_cases":  observation["fail_cases"]
        }
        
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

        # info = {
        #     "name": self.name,
        #     "role": self.role,
        #     "record": observation["log"],
        #     "current_situation": str(observation),
        # }

        answer = self.agent.make_decision(self.info, prompts="prompts/hanabi.prompt")

        return {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }

    def give_clue(self, observation):

        # info = {
        #     "name": self.name,
        #     "role": self.role,
        #     "record": observation["log"],
        #     "current_situation": str(observation),
        # }
        
        answer = self.agent.make_decision(self.info, prompts="prompts/hanabi_give_clue.prompt")
            
            
        return {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }
    
    def play_card(self, observation):
        
        # self.info = {
        #     "name": self.name,
        #     "role": self.role,
        #     "record": observation["log"],
        #     "current_situation": observation,
        #     # "list": observation["players_hands"][self.role]
        # }
        
        answer = self.agent.make_decision(self.info, prompts="prompts/hanabi_play_card.prompt")
                        
        return {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }
    
    def discard_card(self, observation):
        
        # self.info = {
        #     "name": self.name,
        #     "role": self.role,
        #     "record": observation["log"],
        #     "current_situation": observation,
        #     # "list": observation["players_hands"][self.role]
        # }
        
        answer = self.agent.make_decision(self.info, prompts="prompts/hanabi_play_card.prompt")
                        
        return {
            "name": self.name,
            "role": self.role,
            "answer": answer
        }
    
        
