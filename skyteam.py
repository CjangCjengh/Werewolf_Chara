
import time
import os
from broker.skyteam_broker import SkyTeamGameBroker
from publisher.skyteam_host import SkyTeamGameHost


        
def skyteam(config):
    
    # game setup
    # broker = SkyTeamGameBroker(config)
    game = SkyTeamGameHost(config)

    game.game_loop()
    

    # # game loop
    # while game.state != "end":
    #     print("current state: " + game.state)
        
    #     if game.state == "start":
            
    #         game.game_start()
        
    #     elif game.state == "round_start":

    #         # game.round_setup()
    #         game.strategy_discuss()

    #     elif game.state == "discuss":
            
    #         game.publish(game.state, game.to_dict())
            
            
    #         game.roll_dice()

    #     elif game.state == "roll_dice":
            
    #         # game.publish(game.state, game.to_dict())
            
            
    #         game.action_time()
        
    #     elif game.state == "reroll_dice":
            
    #         game.publish(game.state, game.to_dict())
            
            
    #         game.next()
            
    #     elif game.state == "pilot_action":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.next()
                        
    #     elif game.state == "pilot_action_end":
            
    #         game.next()
            
    #     elif game.state == "copilot_action":
            
    #         game.publish(game.state, game.to_dict())
            
    #         game.next()
        
    #     elif game.state == "copilot_action_end":
            
    #         game.next()
            
    #     elif game.state == "round_end":
            
    #         game.game_continue()
        
    #     elif game.state == "landing":
                
    #         game.landing()
                
    #     elif game.state == "safe_landed":
    #         game.game_end()
    #     elif game.state == "crash":
    #         game.game_end()
            
    
    # log_directory = "logs/skyteam"
    # os.makedirs(log_directory, exist_ok=True)
    # t = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
    # log_file_path = os.path.join(log_directory, f"obs-{t}.log")
    # with open(log_file_path, "w") as f:
    #     # save
    #     for i in game.log:
    #         print(i)
    #         f.write(str(i) + "\n")


