import random
from typing import Any
import base64
# from logger import logger
from agent.agent import Agent
from observation.carcassonne_observation import CarcassonneGameObservation
from subscriber.subscriber import Subscriber
from io import BytesIO
from PIL import Image
from agent.naive_agent import NaiveAgent
from agent.extractor import Extractor
from agent.naive_agent import NaiveAgent

class CarcassonneGamePlayer(Subscriber):
    def __init__(self, config):
        
        name = config['name']
        role = config['color']
        strategy = config['strategy']
        
        super().__init__(name, role)
        self.strategy = strategy

        if strategy == "naive":
            self.agent = NaiveAgent()
            self.extractor = Extractor()
        if strategy == "langchain":
            self.agent = NaiveAgent(model='glm-4v')

    def covert(self, image, fmt='jpeg') -> str:
        output_buffer = BytesIO()
        image.save(output_buffer, format=fmt)
        byte_data = output_buffer.getvalue()
        base64_str = base64.b64encode(byte_data).decode('utf-8')
        return base64_str

    def notify(self, topic: str, message: str, image: Any, observation: CarcassonneGameObservation):
        print(f"{self.name}{self.role}收到消息[{topic}]:{message}")

        if topic == "place_tile":
            return self.place_tile(observation, image)
        elif topic == "place_meeple":
            return self.place_meeple(observation, image)
        elif topic == 'start':
            return [self.name, self.role]

    def place_tile(self, observation: CarcassonneGameObservation, image):
        if self.strategy == 'naive':
            answer = self.agent.make_decision([
                {"role": "system",
                 "content": "You are an AI agent for the Carcassonne board game, equipped with the ability to analyze game board images. Your task is to determine the optimal position and orientation for placing a new tile based on the current game state depicted in the image. After analyzing the image, respond with the tile placement in the format 'x,y,angle', where 'x' and 'y' are the coordinates on the map where the tile should be placed, and 'angle' is the counterclockwise rotation of the tile selected from (0, 90, 180, 270) degrees. Ensure that your placement connects correctly with existing tiles and strategically positions followers to maximize scoring potential. Only communicate your decision by providing the coordinates and rotation in the specified format. Evaluate the potential moves carefully, considering both immediate scoring opportunities and strategic advantages for future turns."},
                {"role": "user",
                 "content": [
                     {
                         "type": "text",
                         "text": "The image contains the current map on the left and tile to be placed on the right. The coordinates of the places where they can be placed are given on the picture. You should only pick one of those.(instead of approximation) Please make decision only by answer me \'x,y,angle\'. x,y should be on the map and angle should be selected from(0,90,180,270) counterclockwise. e.g: 1,0,90"
                     },
                     {
                         "type": "image_url",
                         "image_url": {
                             "url": self.covert(image)  # base64 编码
                         }
                     }
                 ]}
            ])
            print(answer)
            result = self.extractor.make_decision([
                {"role": "system",
                 "content": "You are an intelligent agent extracting the specific answer from the given text. You should always answer with only three integer in the format of \"int,int,int\" e.g \"0,0,90\""},
                {"role": "user",
                 "content": "Based on the text: " + answer + " now please extract the specific answer from the given text. Answer with only three integer in the format of \"int,int,int\". if you can not identify, return 'No'."}
            ])
            print(result)
            x, y, angle = map(int, result.split(','))
            print(f"{self.name} 将tile旋转{angle}度后放置在({x},{y})")
            return {
                "player": self.name,
                "role": self.role,
                "decision": [x, y, angle],
            }
        if self.strategy == 'langchain':
            inputdata = {"image_base64": self.covert(image)}
            result = self.agent.make_decision(input_data=inputdata, prompts='prompts/carcassonne_tile.prompt', image=True)
            print(result)
            return result

    def place_meeple(self, observation: CarcassonneGameObservation, image):
        if self.strategy == 'navie':
            answer = self.agent.make_decision([
                {"role": "system",
                 "content": "You are an AI board game companion playing the board game called carcassonne, you are about to make decision of where to place the meeple and what angle should be rorate according to the current map"},
                {"role": "user",
                 "content": [
                     {
                         "type": "text",
                         "text": "The image contains the current map on the left and tile be placed just now on the right. Please make decision by answer me one capital letters from [N, E, S, W, M, X] which means you decide to put meeple onto the south/east/south/west/monastery(if have) side of the tile,X means give up putting meeples"
                     },
                     {
                         "type": "image_url",
                         "image_url": {
                             "url": self.covert(image)
                         }
                     }
                 ]}
            ])
            result = self.extractor.make_decision([
                {"role": "system",
                 "content": "You are an intelligent agent extracting the uppercase English character from the given text. You should always answer with only one character from [N, E, S, W, M, X]."},
                {"role": "user",
                 "content": "Based on the text: " + answer + " now please extract the uppercase English character from the given text. Answer with only one character from [N, E, S, W, M, X]. if you can not identify one return 'X'."}
            ])
            print(f"{self.name} meeple放置在{answer}位置")
            return {
                "player": self.name,
                "role": self.role,
                "decision": result,
            }
        if self.strategy == 'langchain':
            inputdata = {"image_base64": self.covert(image)}
            result = self.agent.make_decision(input_data=inputdata, prompts='prompts/carcassonne_meeple.prompt',
                                              image=True)
            print('1')
            print(result)
            return result