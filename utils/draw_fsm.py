
# from publisher.werewolf_game_host import WerewolfGameHost
# from broker.werewolf_broker import WerewolfGameBroker

# if __name__ == '__main__':
#     broker = WerewolfGameBroker()
#     game = WerewolfGameHost(broker)
#     game.save_png()


# from publisher.hanabi_host import HanabiGameHost
# from broker.hanabi_broker import HanabiGameBroker

# if __name__ == '__main__':
#     broker = HanabiGameBroker()
#     game = HanabiGameHost(broker)
#     game.save_png()




from publisher.skyteam_host import SkyTeamGameHost
from broker.skyteam_broker import SkyTeamGameBroker

if __name__ == '__main__':
    broker = SkyTeamGameBroker()
    game = SkyTeamGameHost(broker)
    game.save_png()