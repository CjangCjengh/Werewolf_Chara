from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import langchain 
from agent.agent import Agent
import json
import re


class NaiveAgent(Agent):
    def __init__(self, 
                 model, 
                 temperature=0.95, 
                 debug=False,
                 ):
        
        super().__init__(model)

        langchain.debug = debug
        
        self.llm = ChatOpenAI(
            model=self.model,
            temperature=temperature,
            openai_api_base=self.base_urls[model],
            openai_api_key=self.api_keys[model]
        )
        

    def load_prompt(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    

    # def make_decision(self, input_data):
    #     attempts = 0
    #     while True:
    #         attempts += 1  # Increment attempt counter
    #         try:
    #             # Invoke the chain
    #             output = self.chain.invoke(input_data)
                
    #             output['attempts'] = attempts
                
    #             # If no exception occurs, break the loop and return the output
    #             return output
    #         except Exception as e:
    #             print(f"langchain error: {e}. Retrying...")
    #             # Optionally, add a small delay to avoid rapid consecutive retries
    #             # time.sleep(1)
                
    
    
    def make_decision(self, input_data, prompts, image=False, context=None):
        template_content = self.load_prompt(prompts)
        input_data['game_log'] = '\n'.join(context)
        alive_players = [p['name'] for p in input_data['observation']['players'] if p['status'] == 'alive']
        input_data['players_alive'] = ', '.join(alive_players)
        input_data['werewolf_victim'] = input_data['observation']['werewolf_victim']
        filled_prompt = template_content.format(**input_data)

        attempts = 0
        while True:
            attempts += 1
            try:
                system_message = SystemMessage(content="You are an expert skilled in Werewolf game. Remain objective and unbiased, but be persuaded if others' arguments make sense. Please keep this in mind.")
                human_message = HumanMessage(content=filled_prompt)

                response = self.llm.invoke([system_message, human_message])

                json_match = re.search(r'```json(.*?)```', response.content, re.DOTALL)
                if json_match:
                    json_data = json_match.group(1).strip()
                else:
                    json_match = re.search(r'\{.*?\}', response.content, re.DOTALL)
                    json_data = json_match.group()

                output = json.loads(json_data)
                output['attempts'] = attempts

                return output
            except Exception as e:
                print(f"Error: {e}. Retrying...")
                
    
    def make_prediction(self, input_data, prompts, image=False):

        # Define the prompt
        if image:
            self.prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessage(
                        "You are an AI agent for the Carcassonne board game, equipped with the ability to analyze game board images."),
                    (
                        "human",
                        [
                            {"type": "text", "text": self.load_prompt(prompts)},
                            {
                                "type": "image_url",
                                "image_url": "{image_base64}",
                            },
                        ],
                    ),
                ]
            )
        else:
            self.prompt = ChatPromptTemplate.from_template(self.load_prompt(prompts))

        # Set up the JSON output parser
        self.output_parser = JsonOutputParser()

        # Create the LLMChain
        self.chain = self.prompt | self.llm | self.output_parser
        
        attempts = 0
        while True:
            attempts += 1  # Increment attempt counter
            try:
                # Invoke the chain
                output = self.chain.invoke(input_data)
                
                output['attempts'] = attempts
                
                # If no exception occurs, break the loop and return the output
                return output
            except Exception as e:
                print(f"error: {e}. Retrying...")
                # Optionally, add a small delay to avoid rapid consecutive retries
                # time.sleep(1)
