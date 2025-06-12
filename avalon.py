
import threading
import os
import time
from broker.avalon_broker import AvalonGameBroker
from publisher.avalon_host import AvalonGameHost
from subscriber.avalon_player import AvalonPlayer
import yaml


def avalon(config):
    

    # broker = AvalonGameBroker(config)
    game = AvalonGameHost(config)
    game.game_loop()
    # game loop
    # while game.state != "end":
    #     print("\033[94mcurrent state: " + game.state + "\033[0m")
    #     if game.state == "start":
            
    #         game.game_start()
        
    #     elif game.state == "round_start":
            
    #         game.new_round()
        
    #     elif game.state == "leader_assign":
            
    #         game.leader_assigned()
        
    #     elif game.state == "team_selection":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.team_selected()
            
        
    #     elif game.state == "vote":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.voted()
        
    #     elif game.state == "quest":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.quest_end()
        
    #     elif game.state == "round_end":
    #         game.round_end()
            
    #     elif game.state == "assassin":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.assassinated()
            
    #     elif game.state == "assassin_end":
    #         game.assassinated()
            
    #     elif game.state == "good_win":
    #         game.game_ends()
            
    #     elif game.state == "evil_win":
    #         game.game_ends()
        
        
    
    # log_directory = "logs/avalon"
    # os.makedirs(log_directory, exist_ok=True)

    # t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    # log_file_path = os.path.join(log_directory, f"obs-{t}.log")

    # with open(log_file_path, "w") as f:
    #     # save
    #     for i in game.log:
    #         print(i)
    #         f.write(str(i) + "\n")



if __name__ == "__main__":
    avalon()
    
