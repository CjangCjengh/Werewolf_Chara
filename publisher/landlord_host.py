import copy
import os
import random
import threading
from collections import Counter
import gradio as gr
from transitions.extensions import GraphMachine

from broker.landlord_broker import LandlordGameBroker
# from logger import logger

from observation.landlord_observation import LandlordGameObservation, Poker
from publisher.publisher import Publisher

# Existing functions here: identify_hand_type, compare_hands, is_valid_move
def identify_hand_type(hand):
    """Identify the type of hand, e.g., single, pair, etc."""
    if not hand:
        return None

    # Check for duplicates
    if len(hand) != len(set(hand)):
        return 'invalid'

    hand.sort(key=lambda x: (Poker.ranks + Poker.jokers).index(x[:-1]) if x[:-1] in Poker.ranks else (
            Poker.ranks + Poker.jokers).index(x))
    counts = Counter([card[:-1] for card in hand])
    values = sorted(set(hand))
    num_values = len(values)
    if len(hand) == 1:
        return 'single'
    elif len(hand) == 2:
        if hand[0][:-1] == hand[1][:-1]:
            return 'pair'
        elif set(hand) == set(Poker.jokers):
            return 'joker_bomb'
    elif len(hand) == 3 and hand[0][:-1] == hand[2][:-1]:
        return 'triple'
    elif len(hand) == 4 and hand[0][:-1] == hand[3][:-1]:
        return 'bomb'
    elif len(hand) == 4 and sorted(counts.values()) == [1, 3]:
        return 'three_with_one'
    elif len(hand) == 5 and sorted(counts.values()) == [2, 3]:
        return 'three_with_pair'
    if num_values >= 3 and all(counts[value] == 3 for value in values[:-2]):
        return 'plane'

        # Check for consecutive pairs (连对)
    if num_values >= 3 and all(counts[value] == 2 for value in values[:-2]) and all(
            Poker.card_value(values[i]) + 1 == Poker.card_value(values[i + 1]) for i in range(num_values - 1)):
        return 'consecutive_pairs'
    elif len(hand) >= 5 and all(counts[card[:-1]] == 1 for card in hand):
        sorted_ranks = sorted([Poker().card_value(card) for card in hand])
        if sorted_ranks == list(range(sorted_ranks[0], sorted_ranks[0] + len(hand))):
            return 'straight'
    # Add more hand types as needed
    return 'invalid'


def compare_hands(current_hand, previous_hand):
    """Compare two hands to see if the current hand can beat the previous hand."""
    if not previous_hand:
        return True

    current_type = identify_hand_type(current_hand)
    previous_type = identify_hand_type(previous_hand)

    if current_type == 'invalid' or previous_type == 'invalid':
        return False

    # Joker bomb beats any hand
    if current_type == 'joker_bomb':
        return True

    # Bombs can beat any other hand type except for another bomb or joker bomb
    if current_type == 'bomb' and previous_type != 'bomb' and previous_type != 'joker_bomb':
        return True

    if current_type != previous_type:
        return False

    current_value = max(Poker().card_value(card) for card in current_hand)
    previous_value = max(Poker().card_value(card) for card in previous_hand)

    return current_value > previous_value


def is_valid_move(current_hand, previous_hand, cards_in_hand):
    """Check if the current move is valid according to the rules."""

    for card in current_hand:
        if card not in cards_in_hand:
            # 如果要打的牌手牌中没有，则不符合规则
            return False

    current_type = identify_hand_type(current_hand)

    if current_type == 'invalid':
        return False  # Current hand is invalid

    if not previous_hand:
        return True  # Any valid hand is allowed if there's no previous hand

    previous_type = identify_hand_type(previous_hand)

    if current_type != previous_type and current_type not in ['bomb', 'joker_bomb']:
        return False  # Different types of hands

    if len(current_hand) != len(previous_hand) and current_type not in ['bomb', 'joker_bomb', 'straight']:
        return False  # Different lengths

    return compare_hands(current_hand, previous_hand)



class LandlordGameHost(Publisher):
    def publish(self, topic, message, observation):

        image = None
        
        responses = self.broker.publish(topic, message, image, observation)
        return responses

    def __init__(self, config):
        self.debug = False
        self.broker = LandlordGameBroker(config)
        self.create_fsm()
        self.log_file = os.path.join(config['log_directory'], f"game.log")

        self.display = True
        self.observation: LandlordGameObservation = LandlordGameObservation()
        self.bottom_cards = []
        self.landlord = None


    def create_fsm(self):
        states = ['start', 'deal', 'bidding', 'first_bidding', 'second_bidding', 'third_bidding', 'forth_bidding',
                  'first_playing', 'second_playing', 'third_playing', 'game_over']
        self.machine = GraphMachine(model=self, states=states, initial='start', show_conditions=True)
        self.machine.add_transition(trigger='deal_cards', source='start', dest='deal', before='deal')
        self.machine.add_transition(trigger='start_bidding', source='deal', dest='bidding')
        self.machine.add_transition(trigger='first_bidding', source='bidding', dest='bidding', before='handle_bidding')
        self.machine.add_transition(trigger='second_bidding', source='bidding', dest='bidding', before='handle_bidding')
        self.machine.add_transition(trigger='third_bidding', source='bidding', dest='bidding', before='handle_bidding')
        self.machine.add_transition(trigger='forth_bidding', source='bidding', dest='bidding', before='handle_bidding')
        self.machine.add_transition(trigger='start_playing', source='bidding', dest='first_playing')
        self.machine.add_transition(trigger='first_playing', source='first_playing', dest='second_playing')
        self.machine.add_transition(trigger='second_playing', source='second_playing', dest='third_playing')
        self.machine.add_transition(trigger='third_playing', source='third_playing', dest='game_over',
                                    conditions='is_game_over')

        self.messages = {
            "start": "游戏开始",
            "deal": "发牌中...",
            "bidding": "开始叫地主",
            "first_playing": "第一位玩家出牌",
            "second_playing": "第二位玩家出牌",
            "third_playing": "第三位玩家出牌",
            "game_over": "游戏结束",
            "first_bidding": "第一位玩家叫地主",
            "second_bidding": "第二位玩家叫地主",
            "third_bidding": "第三位玩家叫地主",
            "forth_bidding": "第一位玩家第二次叫地主"
        }

    def deal(self):
        self.observation = LandlordGameObservation()
        self.observation.init()
        return

    def handle_playing(self):
        # 修改为通过Gradio界面处理游戏进程
        round_order = copy.deepcopy(self.observation.round_order)
        played_record = [False, False]  # 记录前是否出牌
        while not self.is_game_over():
            for player in round_order:
                if played_record.count(True) == 0:
                    self.observation.last_playing = None
                if player == 0:
                    play = self.player_playing(player)
                    if self.is_game_over():
                        self.machine.set_state('game_over')
                        break
                elif player == 1:
                    play = self.player_playing(player)
                    if self.is_game_over():
                        self.machine.set_state('game_over')
                        break
                elif player == 2:
                    play = self.player_playing(player)
                    if self.is_game_over():
                        self.machine.set_state('game_over')
                        break
                played_record.pop(0)
                played_record.append(play)

            print(self.messages[self.state])

    def player_playing(self, player_index):
        if player_index==0:
            order = "first"
        if player_index==1:
            order = "second"
        if player_index==2:
            order = "third"
        # 玩家出牌处理函数
        responses = self.publish(f'{order}_playing', self.messages[f'{order}_playing'],
                                 self.observation)
        response = responses[0]
        if not response:
            self.logging("不出牌")
            record = f"Player {player_index + 1}: {response if response else 'pass'}"
            self.observation.past_record.append(record)
            return False
        valid_playing = is_valid_move(response, self.observation.last_playing,
                                      self.observation.cards_in_hand[player_index])
        if not valid_playing:
            self.logging(f"出牌不符合规范：{response}。则视为不出牌")
            record = f"Player {player_index + 1}: pass"
            self.observation.past_record.append(record)
            return False
        for card in response:
            self.observation.cards_in_hand[player_index].remove(card)
            self.observation.cards_on_table.append(card)
            self.observation.hand_card_count[player_index] -= 1
            self.observation.current_card_count -= 1
            self.observation.table_card_count += 1
        self.observation.last_playing = copy.deepcopy(response)
        # {player_index: copy.deepcopy(response)}
        record = f"Player {player_index+1}: {response if response else 'pass'}"
        self.observation.past_record.append(record)
        self.logging(f"出牌：{response}。")
        return True

    def show_player_hand(self, player_index):
        return self.observation.cards_in_hand[player_index]

    def play_card(self, player_index, cards):
        if not isinstance(cards, list):
            cards = [cards]
        for card in cards:
            if card in self.observation.cards_in_hand[player_index]:
                self.observation.cards_in_hand[player_index].remove(card)
            else:
                return (
                    f"Invalid move. {card} not in player {player_index + 1}'s hand.",
                    ", ".join(self.show_player_hand(player_index)),
                    gr.CheckboxGroup.update(choices=self.show_player_hand(player_index))
                )
        self.observation.current_player = (self.observation.current_player + 1) % 3
        self.update_gradio_display()
        return (
            f"Player {player_index + 1} played {' '.join(cards)}",
            ", ".join(self.show_player_hand(player_index)),
            gr.CheckboxGroup.update(choices=self.show_player_hand(player_index))
        )

    def display_with_gradio(self):
        with gr.Blocks() as demo:
            gr.Markdown("## 斗地主游戏")

            # with gr.Row():
            #     player1_cards = gr.Textbox(label="Player 1 Cards", value=", ".join(self.show_player_hand(0)),
            #                                interactive=False)
            #     player1_play_card = gr.CheckboxGroup(choices=self.show_player_hand(0), label="Select Cards to Play")
            #     play_button1 = gr.Button("Play Card")
            #     play_button1.click(lambda cards: self.play_card(0, cards), inputs=player1_play_card,
            #                        outputs=[player1_play_card, player1_cards])
            #
            # with gr.Row():
            #     player2_cards = gr.Textbox(label="Player 2 Cards", value=", ".join(self.show_player_hand(1)),
            #                                interactive=False)
            #     player2_play_card = gr.CheckboxGroup(choices=self.show_player_hand(1), label="Select Cards to Play")
            #     play_button2 = gr.Button("Play Card")
            #     play_button2.click(lambda cards: self.play_card(1, cards), inputs=player2_play_card,
            #                        outputs=[player2_play_card, player2_cards])

            with gr.Row():
                player3_cards = gr.Textbox(label="Player 3 Cards", value=", ".join(self.show_player_hand(2)),
                                           interactive=False)
                player3_play_card = gr.CheckboxGroup(choices=self.show_player_hand(2), label="Select Cards to Play")
                play_button3 = gr.Button("Play Card")
                play_button3.click(lambda cards: self.play_card(2, cards), inputs=player3_play_card,
                                   outputs=[player3_play_card, player3_cards])

        # Start the Gradio app without blocking the main thread
        thread = threading.Thread(target=demo.launch, kwargs={"server_name": "0.0.0.0", "server_port": 7860})
        thread.daemon = True  # Ensure the thread does not prevent the program from exiting
        thread.start()
        # demo.launch()

    def update_gradio_display(self):
        # 更新Gradio显示的内容
        self.player1_cards.update(value=", ".join(self.show_player_hand(0)))
        self.player1_play_card.update(choices=self.show_player_hand(0))

        self.player2_cards.update(value=", ".join(self.show_player_hand(1)))
        self.player2_play_card.update(choices=self.show_player_hand(1))

        self.player3_cards.update(value=", ".join(self.show_player_hand(2)))
        self.player3_play_card.update(choices=self.show_player_hand(2))
    def logging(self, s):
        print(s)
    def game_simulation(self):
        print(self.messages[self.state])
        self.deal_cards()
        print(self.messages[self.state])
        # if self.display:
        #     self.display_with_gradio()

        self.start_bidding()
        print(self.messages[self.state])

        first_bid, second_bid, third_bid, forth_bid = self.handle_bidding()
        self.assign_landlord()

        if self.state != 'game_over':
            # self.start_playing()
            # print(self.messages[self.state])
            self.handle_playing()
        print(self.messages[self.state])

    def game_loop(self):
        print(self.messages[self.state])
        self.deal_cards()
        print(self.messages[self.state])
        # if self.display:
        #     self.display_with_gradio()

        self.start_bidding()
        print(self.messages[self.state])

        first_bid, second_bid, third_bid, forth_bid = self.handle_bidding()
        self.assign_landlord()

        if self.state != 'game_over':
            # self.start_playing()
            # print(self.messages[self.state])
            self.handle_playing()
        print(self.messages[self.state])

    def handle_bidding(self):
        # 实现叫地主的逻辑
        first_bid = self.first_player_bids()
        second_bid = self.second_player_bids()
        third_bid = self.third_player_bids()
        if not (first_bid or second_bid or third_bid):
            self.machine.set_state('game_over')
            self.observation.bidding = [False, False, False, False]
            return False, False, False, False
        if first_bid and (second_bid or third_bid):
            forth_bid = self.first_player_bids_again()
        else:
            forth_bid = False
        self.machine.set_state('first_playing')
        self.observation.bidding = [first_bid, second_bid, third_bid, forth_bid]
        return first_bid, second_bid, third_bid, forth_bid

    def first_player_bids(self):
        # 实现第一个玩家叫地主的逻辑
        responses = self.publish('first_bidding', self.messages['first_bidding'], self.observation)
        response = responses[0]
        self.logging(f"抢地主：{response}")
        return response

    def first_player_bids_again(self):
        # 实现第一个玩家第二次叫地主的逻辑
        responses = self.publish('forth_bidding', self.messages['forth_bidding'], self.observation)
        response = responses[0]
        self.logging(f"抢地主：{response}")
        return response

    def second_player_bids(self):
        # 实现第二个玩家叫地主的逻辑
        responses = self.publish('second_bidding', self.messages['second_bidding'], self.observation)
        response = responses[0]
        self.logging(f"抢地主：{response}")
        return response

    def third_player_bids(self):
        # 实现第三个玩家叫地主的逻辑
        responses = self.publish('third_bidding', self.messages['third_bidding'], self.observation)
        response = responses[0]
        self.logging(f"抢地主：{response}")
        return response

    def assign_landlord(self):
        # 实现指定地主逻辑
        first_bid, second_bid, third_bid, forth_bid = self.observation.bidding
        if forth_bid:
            self.landlord = self.broker.subscribers['start'][0].name
            self.observation.landlord_player = 0
            self.observation.round_order = [0, 1, 2]
            return
        elif third_bid:
            self.landlord = self.broker.subscribers['start'][2].name
            self.observation.landlord_player = 2
            self.observation.round_order = [2, 0, 1]
            return
        elif second_bid:
            self.landlord = self.broker.subscribers['start'][1].name
            self.observation.landlord_player = 1
            self.observation.round_order = [1, 2, 0]
            return
        elif first_bid:
            self.landlord = self.broker.subscribers['start'][0].name
            self.observation.landlord_player = 0
            self.observation.round_order = [0, 1, 2]
            return
        self.observation.cards_in_hand[self.observation.landlord_player].extend(self.observation.bottom_cards)
        self.observation.hand_card_count[self.observation.landlord_player] += len(self.observation.bottom_cards)
