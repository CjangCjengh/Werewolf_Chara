#!/usr/bin/env python 
# encoding: utf-8 
# @author: yihuai lan
# @fileName: landlord_main.py
# @date: 2024/5/28 15:49
#
# describe:
#
import threading

from agent.naive_agent import NaiveAgent
from broker.landlord_broker import LandlordGameBroker
from publisher.landlord_host import LandlordGameHost
from subscriber.landlord_player import LandlordGamePlayer

def landlord(config):
    game = LandlordGameHost(config)

    game.game_loop()


# def landlord(config):
#     broker = LandlordGameBroker()
#     game = LandlordGameHost(broker, config)
#
#     players = []
#     for player_config in config['players']:
#         player = LandlordGamePlayer(
#             player_config['name'],
#             role=player_config.get('role', ""),
#             strategy=player_config.get('strategy', ""),
#             model=player_config.get('model', None)
#         )
#         players.append(player)
#
#     for player in players:
#         game.register(player, "start")
#         game.register(player, "deal")
#         game.register(player, "bidding")
#         game.register(player, "playing")
#         game.register(player, "game_over")
#
#     game.register(players[0], "first_bidding")
#     game.register(players[1], "second_bidding")
#     game.register(players[2], "third_bidding")
#     game.register(players[0], "forth_bidding")
#     game.register(players[0], "first_playing")
#     game.register(players[1], "second_playing")
#     game.register(players[2], "third_playing")
#
#     # 开始游戏
#     print(game.messages[game.state])
#     game.deal_cards()
#     print(game.messages[game.state])
#
#     # 启动Gradio界面
#     game.start_bidding()
#     print(game.messages[game.state])
#
#     # 在Gradio界面进行人类玩家操作后，继续游戏流程
#     game.init_gradio_interface()


# def landlord(config):
#     broker = LandlordGameBroker()
#     game = LandlordGameHost(broker, config)
#
#     # p1 = LandlordGamePlayer(NaiveAgent("glm-3-turbo"), "A", role="")
#     # p2 = LandlordGamePlayer(NaiveAgent("glm-3-turbo"), "B", role="")
#     # p3 = LandlordGamePlayer(NaiveAgent("glm-3-turbo"), "C", role="")
#     #
#     # players = [p1, p2, p3]
#     players = []
#     for player_config in config['players']:
#         player = LandlordGamePlayer(player_config['name'], "", strategy=player_config['strategy'],
#                               model=player_config['model'] if 'model' in player_config else None)
#         players.append(player)
#
#     for player in players:
#         # states = ['start', 'deal', 'bidding', 'playing', 'game_over']
#         game.register(player, "start")
#         game.register(player, "deal")
#         game.register(player, "bidding")
#         game.register(player, "playing")
#         game.register(player, "game_over")
#
#     game.register(players[0], "first_bidding")
#     game.register(players[1], "second_bidding")
#     game.register(players[2], "third_bidding")
#     game.register(players[0], "forth_bidding")
#     game.register(players[0], "first_playing")
#     game.register(players[1], "second_playing")
#     game.register(players[2], "third_playing")
#
#     # game_thread = threading.Thread(target=game.game_simulation())
#     # game_thread.start()
#     print(game.messages[game.state])
#     game.deal_cards()
#     print(game.messages[game.state])
#     # game.display_with_gradio()
#     # if self.display:
#     #     self.display_with_gradio()
#
#     game.start_bidding()
#     print(game.messages[game.state])
#
#     first_bid, second_bid, third_bid, forth_bid = game.handle_bidding()
#     game.assign_landlord()
#
#     if game.state != 'game_over':
#         # self.start_playing()
#         # print(self.messages[self.state])
#         game.handle_playing()
#     print(game.messages[game.state])


if __name__ == '__main__':
    landlord()
