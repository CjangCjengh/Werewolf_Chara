import copy
import random

from transitions import Machine
from transitions.extensions import GraphMachine
from publisher.publisher import Publisher
from observation.carcassonne_observation import CarcassonneGameObservation, Meeple, Tile
import observation.carcassonne_setting as carcassonne_setting
from PIL import Image, ImageDraw, ImageFont


class CarcassonneGameHost(Publisher):
    """
    CarcassonneGameHost 类继承自 Publisher, 用于管理卡卡颂游戏的状态和send message。

    该类包含游戏状态的状态机、状态转换逻辑以及消息的发布和处理方法。

    Attributes:
        observation (CarcassonneGameObservation): 游戏的观察对象，包含游戏状态信息。
        machine (Machine): 状态机，用于管理游戏状态和状态转换。
        previous_state (str): 存储上一个状态的名称。
        messages (dict): 包含不同状态对应的消息内容。
    """

    def __init__(self, broker):
        """
        初始化 CarcassonneGameHost 类的实例。

        Args:
            broker (BaseBroker): 用于管理订阅者和send message的 broker 对象。

        Returns:
            None
        """
        super().__init__(broker)
        self.observation = CarcassonneGameObservation()

        # Define the states
        states = ['start', 'end', 'place_tile', 'place_meeple', 'score_calculation', 'final_calculation']

        # Initialize the state machine
        self.machine = GraphMachine(model=self, states=states, initial='start', show_conditions=True)
        self.machine_add_transitions()
        self.previous_state = None

    def machine_add_transitions(self):
        """
        为状态机添加状态转换规则。

        Args:
            None

        Returns:
            None
        """
        self.machine.add_transition(source='start', dest='place_tile', trigger='game_start', before='store_previous')
        self.machine.add_transition(source='place_tile', dest='place_meeple', trigger='place_tile_done',
                                    before='store_previous', conditions='have_enough_meeple')
        self.machine.add_transition(source='place_tile', dest='place_tile', trigger='place_tile_fail_done',
                                    before='store_previous')
        self.machine.add_transition(source='place_tile', dest='score_calculation', trigger='place_tile_done',
                                    before='store_previous', conditions='not_enough_meeple')
        self.machine.add_transition(source='place_meeple', dest='score_calculation', trigger='place_meeple_done',
                                    before='store_previous')
        self.machine.add_transition(source='score_calculation', dest='place_tile', trigger='score_calculation_done',
                                    before='store_previous', conditions='is_game_end')
        self.machine.add_transition(source='score_calculation', dest='final_calculation',
                                    trigger='score_calculation_done',
                                    before='store_previous', conditions='is_deck_empty')
        self.machine.add_transition(source='final_calculation', dest='end', trigger='final_calculation_done', before='store_previous')

    def store_previous(self):
        """
        存储上一个状态。

        Args:
            None

        Returns:
            None
        """
        self.previous_state = self.state

    def on_enter(self, event):
        """
        状态转换时的回调函数，打印状态转换信息。

        Args:
            event (EventData): 包含状态转换信息的事件数据对象。

        Returns:
            None
        """
        print(f'Transitioned from {self.previous_state} to {self.state}')

    # Conditions for transitions
    def have_enough_meeple(self):
        """
        检查玩家的meeple是否有余量

        Args:
            None

        Returns:
            bool: 如果有则返回 True，否则返回 False。
        """
        for meeple in self.observation.playersinfo[self.observation.current_player]['meeples']:
            if meeple.isplaced == False:
                return True
        return False

    def not_enough_meeple(self):
        """
        检查玩家的meeple是否有余量

        Args:
            None

        Returns:
            bool: 如果有则返回 True，否则返回 False。
        """
        return not self.have_enough_meeple()

    def is_deck_empty(self):
        """
        检查牌堆是否为空（游戏结束）

        Args:
            None

        Returns:
            bool: 如果为空则返回 True，否则返回 False。
        """
        return not self.is_game_end()

    def is_game_end(self):
        """
        检查游戏是否结束（牌堆是否空）

        Args:
            None

        Returns:
            bool: 如果游戏尚未结束则返回 True，否则返回 False。
        """
        return len(self.observation.deck)>0

    def save_png(self):
        """
        保存状态机的状态图到 PNG 文件。

        Args:
            None

        Returns:
            None
        """
        self.machine.get_graph().draw('my_state_diagram.png', prog='dot')

    def publish(self, topic, message, observation):
        """
        send message到指定的主题，并附带观察对象的图像。

        Args:
            topic (str): send message的主题。
            message (str): 发布的消息内容。
            observation (CarcassonneGameObservation): 发布的观察内容。

        Returns:
            list: 包含所有订阅者响应的列表。
        """
        image = self.display_with_tile()
        responses = self.broker.publish(topic, message, image, observation)
        return responses

    def startgame(self):
        # 收集全部信息
        playerinfo = self.publish('start', '开始游戏，请提供你们的信息给我', self.observation)

        for info in playerinfo:
            name, color = info
            self.observation.playerorder.append(name)
            self.observation.playersinfo[name] = {
                'color': color,
                'score': 0,  # 初始分数设置为0
                'meeples': [Meeple(color, name) for _ in range(7)]  # 每个玩家开始时有7个Meeple
            }
        self.observation.deck = self.generate_deck()
        self.observation.current_player = self.observation.playerorder[0]
        self.game_start()


    def generate_deck(self):
        # 生成牌堆
        deck = []
        for tile_letter, info in carcassonne_setting.tiles_info.items():
            # 使用deepcopy来确保每个Tile都有其独立的edge对象
            for _ in range(info[0]):
                deck.append(Tile(tile_letter, copy.deepcopy(info[1]), info[2], info[3]))
        # 乱序
        random.shuffle(deck)
        return deck


    def display_with_tile(self):
        map_image = self.observation.board.display()
        tile_image = self.observation.t_tile.make_image()

        map_width, map_height = map_image.size
        tile_width, tile_height = tile_image.size

        # 创建足够大的新画布，以容纳地图和tile图像
        total_width = map_width + tile_width + 20  # 添加一些间隔
        max_height = max(map_height, tile_height)

        # 创建一个新的白色背景图片
        new_image = Image.new('RGB', (total_width, max_height), 'white')

        # 粘贴地图图像和tile图像到新的画布
        new_image.paste(map_image, (0, 0))
        new_image.paste(tile_image, (map_width, int(max_height / 2) - 60))  # 将tile图像放在地图右侧10像素的位置

        # 返回拼接好的图片对象
        return new_image


    def place_tile(self):
        self.observation.t_tile = self.observation.deck.pop()
        print(f"{self.observation.current_player} draws a tile: {self.observation.t_tile.type}")
        self.display_with_tile().save("resources/carcassonne/map/Test.jpg")  # Save initial state
        decison = self.publish('place_tile','你要决定把tile放哪里了',self.observation)
        x, y = decison[0].get('coordinate')
        degrees = decison[0].get('angle')
        self.observation.t_tile.rotate(degrees)
        if self.observation.board.place_tile(self.observation.t_tile, x, y):
            print("成功放置tile")
            self.place_tile_done()
        else:
            print("放置tile无效,跳过")
            self.place_tile_fail_done()


    def place_meeple(self):
        self.display_with_tile().save("resources/carcassonne/map/Test.jpg")
        decison = self.publish('place_meeple', '你要决定把meeple放哪里了', self.observation)
        position_key = decison[0].get('decision')
        if position_key == 'X':
            print("它选择不放置")
            self.place_meeple_done()
            return
        selected_meeple=None
        for meeple in self.observation.playersinfo[self.observation.current_player]['meeples']:
            if not meeple.isplaced:
                selected_meeple=meeple
        success, msg = self.observation.board.place_meeple(self.observation.t_tile, position_key, selected_meeple)
        if success:
            print("Meeple placed successfully.")
            selected_meeple.place(self.observation.t_tile, position_key)  # Mark meeple as placed
        else:
            print(f"Failed to place meeple: {msg}")
        self.place_meeple_done()
        return

    def calculate_scores(self):
        round_scores = self.observation.board.calculate_scores(self.observation.t_tile)  # 使用 Board 类的得分计算方法
        for player_name, score in round_scores.items():
            self.observation.playersinfo[player_name]['score'] += score
        print(f'本轮得分：{round_scores}')
        self.score_calculation_done()
        return

    def final_scoring(self):
        final_scores = self.observation.board.final_scoring()  # 使用 Board 类的游戏结束得分计算方法
        for player_name, score in final_scores.items():
            self.observation.playersinfo[player_name]['score'] += score
        print(f'最后清算：{final_scores}')
        self.final_calculation_done()
        return
