#!/usr/bin/env python 
# encoding: utf-8 
# @author: yihuai lan
# @fileName: landlord_broker.py 
# @date: 2024/5/28 15:15 
#
# describe:
#
from typing import Any
from broker.broker import Broker
from observation.landlord_observation import LandlordGameObservation
from subscriber.landlord_human_ui import LandlordGameHumanUI
from subscriber.landlord_player import LandlordGamePlayer


class LandlordGameBroker(Broker):
    """
    LandlordGameBroker 是一个具体实现的发布者-订阅者模式的类，用于斗地主游戏的消息发布和订阅。

    该类继承自 BaseBroker，并实现了消息发布和观察过滤的具体逻辑。

    Methods:
        publish(topic: str, message: str, image: Any, observation: LandlordGameObservation):
            send message到指定的主题，并通知订阅者。

        filter_observation(subscriber, observation: LandlordGameObservation):
            过滤观察对象，以适应不同订阅者的需求。
    """

    def __init__(self,config, use_multi_thread=False):
        super().__init__()
        self.use_multi_thread = use_multi_thread

        players = []
        for player_config in config['players']:
            if player_config['strategy'] == 'human':
                player = LandlordGameHumanUI(player_config)
            else:
                player = LandlordGamePlayer(player_config['name'], "", strategy=player_config['strategy'],
                                            model=player_config['model'] if 'model' in player_config else None)
            players.append(player)

        for player in players:
            # states = ['start', 'deal', 'bidding', 'playing', 'game_over']
            self.register(player, "start")
            self.register(player, "deal")
            self.register(player, "bidding")
            self.register(player, "playing")
            self.register(player, "game_over")

        self.register(players[0], "first_bidding")
        self.register(players[1], "second_bidding")
        self.register(players[2], "third_bidding")
        self.register(players[0], "forth_bidding")
        self.register(players[0], "first_playing")
        self.register(players[1], "second_playing")
        self.register(players[2], "third_playing")

    def publish(self, topic: str, message: str, image: Any, observation: LandlordGameObservation):
        """
        send message到指定的主题，并通知订阅者。

        如果主题存在，遍历该主题的所有订阅者，过滤观察对象并调用订阅者的 notify 方法。

        Args:
            topic (str): send message的主题。
            message (str): 发布的消息内容。
            image (Any): 发布的图像内容。
            observation (LandlordGameObservation): 发布的观察内容，必须是 LandlordGameObservation 的实例。

        Returns:
            list: 包含所有订阅者响应的列表。如果没有订阅者响应，则返回空列表。
        """
        if topic in self.subscribers:
            print(f"send message [{topic}]: {message}")
            responses = []
            for subscriber in self.subscribers[topic]:
                filtered_observation = self.filter_observation(subscriber, observation)
                response = subscriber.notify(topic, message, image, filtered_observation)
                if response is not None:
                    responses.append(response)
            return responses
        return []

    def filter_observation(self, subscriber, observation: LandlordGameObservation):
        """
        过滤观察对象，以适应不同订阅者的需求。

        根据订阅者的名称分配玩家 ID，并创建一个过滤后的观察对象，使得订阅者只能看到他们自己的手牌信息。

        Args:
            subscriber (BaseSubscriber): 订阅者对象，包含订阅者的名称和角色。
            observation (LandlordGameObservation): 原始的观察对象。

        Returns:
            LandlordGameObservation: 过滤后的观察对象，包含订阅者可见的信息。
        """
        name = subscriber.name
        if name == "A":
            player_id = 0
        elif name == "B":
            player_id = 1
        elif name == "C":
            player_id = 2
        else:
            raise NotImplementedError()

        filtered_observation = LandlordGameObservation()
        filtered_observation.round = observation.round
        filtered_observation.max_card_count = observation.max_card_count
        filtered_observation.hand_card_count = observation.hand_card_count[:]
        filtered_observation.table_card_count = observation.table_card_count
        filtered_observation.cards_in_hand = [["未知"] for _ in range(3)]
        filtered_observation.cards_in_hand[player_id] = observation.cards_in_hand[player_id][:]
        filtered_observation.cards_on_table = observation.cards_on_table[:]
        filtered_observation.past_record = observation.past_record[:]
        filtered_observation.bottom_cards = observation.bottom_cards[:]
        filtered_observation.bidding = observation.bidding[:]
        filtered_observation.landlord_player = observation.landlord_player
        filtered_observation.round_order = observation.round_order[:]
        filtered_observation.current_player = player_id
        filtered_observation.last_playing = observation.last_playing

        return filtered_observation


# class LandlordGameBroker(Broker):
#     """
#     LandlordGameBroker 是一个具体实现的发布者-订阅者模式的类，用于斗地主游戏的消息发布和订阅。
#
#     该类继承自 BaseBroker，并实现了消息发布和观察过滤的具体逻辑。
#
#     Methods:
#         publish(topic: str, message: str, image: Any, observation: LandlordGameObservation):
#             send message到指定的主题，并通知订阅者。
#
#         filter_observation(subscriber, observation: LandlordGameObservation):
#             过滤观察对象，以适应不同订阅者的需求。
#     """
#
#     def publish(self, topic: str, message: str, image: Any, observation: LandlordGameObservation):
#         """
#         send message到指定的主题，并通知订阅者。
#
#         如果主题存在，遍历该主题的所有订阅者，过滤观察对象并调用订阅者的 notify 方法。
#
#         Args:
#             topic (str): send message的主题。
#             message (str): 发布的消息内容。
#             image (Any): 发布的图像内容。
#             observation (LandlordGameObservation): 发布的观察内容，必须是 LandlordGameObservation 的实例。
#
#         Returns:
#             list: 包含所有订阅者响应的列表。如果没有订阅者响应，则返回空列表。
#         """
#         if topic in self.subscribers:
#             print(f"send message [{topic}]: {message}")
#             responses = []
#             for subscriber in self.subscribers[topic]:
#                 filtered_observation = self.filter_observation(subscriber, observation)
#                 response = subscriber.notify(topic, message, image, filtered_observation)
#                 if response is not None:
#                     responses.append(response)
#             return responses
#         return []
#
#     def filter_observation(self, subscriber, observation: LandlordGameObservation):
#         """
#         过滤观察对象，以适应不同订阅者的需求。
#
#         根据订阅者的名称分配玩家 ID，并创建一个过滤后的观察对象，使得订阅者只能看到他们自己的手牌信息。
#
#         Args:
#             subscriber (BaseSubscriber): 订阅者对象，包含订阅者的名称和角色。
#             observation (LandlordGameObservation): 原始的观察对象。
#
#         Returns:
#             LandlordGameObservation: 过滤后的观察对象，包含订阅者可见的信息。
#         """
#         name = subscriber.name
#         if name == "A":
#             player_id = 0
#         elif name == "B":
#             player_id = 1
#         elif name == "C":
#             player_id = 2
#         else:
#             raise NotImplementedError()
#
#         filtered_observation = LandlordGameObservation()
#         filtered_observation.round = observation.round
#         filtered_observation.max_card_count = observation.max_card_count
#         filtered_observation.hand_card_count = observation.hand_card_count[:]
#         filtered_observation.table_card_count = observation.table_card_count
#         filtered_observation.cards_in_hand = [["未知"] for _ in range(3)]
#         filtered_observation.cards_in_hand[player_id] = observation.cards_in_hand[player_id][:]
#         filtered_observation.cards_on_table = observation.cards_on_table[:]
#         filtered_observation.past_record = observation.past_record[:]
#         filtered_observation.bottom_cards = observation.bottom_cards[:]
#         filtered_observation.bidding = observation.bidding[:]
#         filtered_observation.landlord_player = observation.landlord_player
#         filtered_observation.round_order = observation.round_order[:]
#         filtered_observation.current_player = player_id
#         filtered_observation.last_playing = observation.last_playing
#
#         return filtered_observation
