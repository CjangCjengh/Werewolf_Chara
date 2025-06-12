from broker.carcassonne_broker import CarcassonneGameBroker
from publisher.carcassonne_host import CarcassonneGameHost
from subscriber.carcassonne_player import CarcassonneGamePlayer
import yaml

# def game_simulation(game_host: CarcassonneGameHost, nametoplayer:dict):


def carcassonne(config):
    
    broker = CarcassonneGameBroker()
    game_host = CarcassonneGameHost(broker)

    # 初始化参与玩家
    # player1 = CarcassonneGamePlayer("Alice", "blue")
    # player2 = CarcassonneGamePlayer("Bob", "pink")
    # player3 = CarcassonneGamePlayer("Charlie", "yellow")
    # player4 = CarcassonneGamePlayer("Dave", "black")
    # player5 = CarcassonneGamePlayer("Eve", "green")
    # players = [player1, player2, player3, player4, player5]
    
    players = []
    for player_config in config['players']:
        player = CarcassonneGamePlayer(player_config)
        players.append(player)

    nametoplayer={}
    # 注册所有玩家到对应状态
    for player in players:
        game_host.register(player, "start")
        game_host.register(player, "end")
        game_host.register(player, "score_calculation")
        game_host.register(player, "final_calculation")
        nametoplayer[player.name]=player


    while game_host.state != "end":
        print("current state: " + game_host.state)

        # 流程控制
        if game_host.state == 'start':
            game_host.startgame()

        if game_host.state == 'place_tile':
            # 先注册
            game_host.register(nametoplayer.get(game_host.observation.current_player), "place_tile")
            # 进行操作
            # decision = game_host.publish('place_tile', '你要准备放置tile', game_host.observation)

            game_host.place_tile()
            # 取消注册
            game_host.unregister(nametoplayer.get(game_host.observation.current_player), "place_tile")

        if game_host.state == 'place_meeple':
            # 先注册
            game_host.register(nametoplayer.get(game_host.observation.current_player), "place_meeple")
            # 进行操作
            # decision = game_host.publish('place_meeple', '你要准备放置meeple', game_host.observation)
            game_host.place_meeple()
            # 取消注册
            game_host.unregister(nametoplayer.get(game_host.observation.current_player), "place_meeple")

        if game_host.state == 'score_calculation':
            game_host.calculate_scores()
            index = game_host.observation.playerorder.index(game_host.observation.current_player)
            game_host.observation.current_player = game_host.observation.playerorder[
                (index + 1) % len(game_host.observation.playerorder)]

        if game_host.state == 'final_calculation':
            game_host.final_scoring()

    # 输出游戏过程
    print("finally, " + game_host.state)
    for i in game_host.observation.log:
        print(i)



if __name__ == "__main__":
    
    
    # parser = argparse.ArgumentParser()
    # parser.add_argument('configs', help='game config file')

    # args = parser.parse_args()
    config_file = "configs/carcassonne.yaml"
    
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
        
    carcassonne(config)
