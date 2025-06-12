import openai
from time import sleep
from abc import ABC, abstractmethod


class Agent(ABC):
    def __init__(self, model = "glm-3-turbo"):
        
        self.api_keys = {
            "deepseek-chat": "",
            "glm-3-turbo": "",
            "glm-4": "",
            "gpt-4": "",
            "mistralai/Mistral-7B-Instruct-v0.2": "",
            "Qwen/Qwen2-72B-Instruct": "",
            "Qwen/Qwen2-57B-A14B-Instruct": "",
            "Qwen/Qwen1.5-110B-Chat": "",
            "Qwen/Qwen1.5-32B-Chat": "",
            "Qwen/Qwen1.5-14B-Chat": "",
            "deepseek-ai/DeepSeek-V2-Chat": "",
            "deepseek-ai/deepseek-llm-67b-chat": "",
            "01-ai/Yi-1.5-34B-Chat-16K": "",
            "gpt-4o-mini": ""
        }
        
        self.model = model
        
        self.base_urls = {
            "deepseek-chat": "",
            "glm-3-turbo": "",
            "glm-4": "",
            "gpt-4": "",
            "mistralai/Mistral-7B-Instruct-v0.2": "",
            "Qwen/Qwen2-72B-Instruct": "",
            "Qwen/Qwen2-57B-A14B-Instruct": "",
            "Qwen/Qwen1.5-110B-Chat": "",
            "Qwen/Qwen1.5-32B-Chat": "",
            "Qwen/Qwen1.5-14B-Chat": "",
            "deepseek-ai/DeepSeek-V2-Chat": "",
            "deepseek-ai/deepseek-llm-67b-chat": "",
            "01-ai/Yi-1.5-34B-Chat-16K": "",
            "gpt-4o-mini": ""
        }
        
        self.client = openai.OpenAI(api_key=self.api_keys[model], base_url=self.base_urls[model])

        

    def call_api(self, message):
        while True:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=message
                )
                assistant_message = response.choices[0].message.content
            except Exception as e:
                # print("e", end="")
                print(f"Error: {e}")
                # print(f"Error: {e}")
                sleep(1.5)
            else:
                break
        return assistant_message

    @abstractmethod
    def make_decision(self, input_data):
        pass



if __name__ == '__main__':
    class TestAgent(Agent):
        def make_decision(self, message):
            return self.call_api(message)


    test_message = [
        {"role": "system", "content": "You are a smart and creative novelist"},
        {"role": "user",
         "content": "As the king of fairy tales, write a short fairy tale, the theme of which is to always maintain a kind heart, to stimulate children's interest in learning and imagination, while also helping children better understand and accept the principles and values contained in the story."}
    ],
    agent = TestAgent("client_glm")
    response = agent.make_decision(test_message)
    print(response)
