from agent.agent import Agent


class NaiveAgent(Agent):
    
    
    def make_decision(self, message):
        answer = self.call_api(message)
        # print( answer)
        return answer

        
    
