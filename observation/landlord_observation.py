#!/usr/bin/env python 
# encoding: utf-8 
# @author: yihuai lan
# @fileName: landlord_observation.py 
# @date: 2024/5/28 14:36 
#
# describe:
#
import random
from .observation import Observation


class Poker:
    """
    Poker 类用于创建和管理一副扑克牌，包括洗牌和发牌功能。

    Attributes:
        suits (list): 牌的花色列表，包括 ['♠', '♥', '♣', '♦']。
        ranks (list): 牌的点数列表，包括从 '3' 到 '2' 的所有牌。
        jokers (list): 牌中的大小王，包括 ['小王', '大王']。
        cards (list): 当前的一副扑克牌，初始化时会被洗牌。
    """

    suits = ['♠', '♥', '♣', '♦']
    ranks = ['3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A', '2']
    jokers = ['小王', '大王']

    def __init__(self):
        """
        初始化 Poker 类的实例，创建并洗牌一副扑克牌。

        Args:
            None

        Returns:
            None
        """
        self.cards = self.create_deck()

    def create_deck(self):
        """
        创建一副扑克牌并进行洗牌。

        生成 52 张常规扑克牌和 2 张大小王，共计 54 张牌，并将其随机打乱。

        Args:
            None

        Returns:
            list: 洗牌后的扑克牌列表。
        """
        deck = [f'{rank}{suit}' for suit in self.suits for rank in self.ranks]
        deck.extend(self.jokers)
        random.shuffle(deck)
        return deck

    def deal(self):
        """
        发牌，将一副扑克牌分发给三个玩家，并留出底牌。

        Args:
            None

        Returns:
            tuple: 三个玩家的手牌和底牌。
        """
        player1 = self.cards[:17]
        player2 = self.cards[17:34]
        player3 = self.cards[34:51]
        bottom_cards = self.cards[51:]
        return player1, player2, player3, bottom_cards

    def card_value(self, card):
        """
        获取指定牌的点数值，用于比较牌的大小。

        Args:
            card (str): 需要获取点数值的牌。

        Returns:
            int: 牌的点数值。
        """
        rank_order = Poker.ranks + Poker.jokers
        return rank_order.index(card[:-1]) if card[:-1] in rank_order else rank_order.index(card)

    def sort_cards(self, cards):
        """
        根据点数对多张牌进行排序。

        Args:
            cards (list): 需要排序的扑克牌列表。

        Returns:
            list: 按点数排序后的扑克牌列表。
        """
        return sorted(cards, key=self.card_value)


class LandlordGameObservation(Observation):
    """
    LandlordGameObservation 类用于记录和管理斗地主游戏的观察状态。

    Attributes:
        round (int): 当前的回合数。
        max_card_count (int): 扑克牌的总数量。
        hand_card_count (list): 每个玩家的手牌数量。
        table_card_count (int): 桌面上的牌数量。
        cards_in_hand (list): 每个玩家的手牌列表。
        cards_on_table (list): 桌面上的牌列表。
        past_record (list): 游戏的历史记录。
        bottom_cards (list): 底牌。
        bidding (list): 每个玩家的叫地主状态。
        landlord (int): 地主玩家的索引。
        round_order (list): 回合顺序。
        current_player (int): 当前操作的玩家索引。
        log (list): 玩家动作历史记录。
    """
    round = 0
    max_card_count = 0
    hand_card_count = [0, 0, 0]  # 每个玩家的手牌数量
    table_card_count = 0
    current_card_count = 0
    cards_in_hand = [[], [], []]  # 每个玩家的手牌
    cards_on_table = []  # 桌面上的牌
    past_record = []  # 历史记录
    bottom_cards = []
    bidding = [None, None, None, None]
    landlord_player = None
    round_order = []
    current_player = None
    last_playing = None
    log = []

    def __init__(self):
        """
        初始化 LandlordGameObservation 类的实例。

        Args:
            None

        Returns:
            None
        """
        super().__init__()

    def init(self):
        """
        初始化游戏观察状态，包括发牌、设置回合信息和初始化玩家手牌。

        Args:
            None

        Returns:
            None
        """

        poker = Poker()
        self.max_card_count = len(poker.cards)
        self.current_card_count = self.max_card_count
        self.table_card_count = 0

        # 发牌
        player1, player2, player3, bottom_cards = poker.deal()
        player1, player2, player3, bottom_cards = poker.sort_cards(player1), poker.sort_cards(player2), poker.sort_cards(player3), poker.sort_cards(bottom_cards)
        self.cards_in_hand[0] = player1
        self.cards_in_hand[1] = player2
        self.cards_in_hand[2] = player3
        self.hand_card_count[0] = len(player1)
        self.hand_card_count[1] = len(player2)
        self.hand_card_count[2] = len(player3)

        self.bottom_cards = bottom_cards  # 底牌

        # 初始化桌面上的牌和历史记录
        self.cards_on_table = []
        self.past_record = []

        self.round = 1

    def create_image(self):
        """
        创建游戏状态的图像表示。

        这是一个抽象方法，必须在子类中实现具体的图像创建逻辑。

        Args:
            None

        Returns:
            None

        Raises:
            NotImplementedError: 这是一个抽象方法，必须在子类中实现。
        """
        pass


if __name__ == '__main__':
    p = Poker()
    print(p.cards)
