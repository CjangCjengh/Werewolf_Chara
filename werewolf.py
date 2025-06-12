import threading
import os
import time
import yaml
from broker.werewolf_broker import WerewolfGameBroker
from publisher.werewolf_host import WerewolfGameHost
# from subscriber.werewolf_player import WerewolfGamePlayer

def werewolf(config):

    # broker = WerewolfGameBroker(config)
    game = WerewolfGameHost(config)

    game.game_loop()
    # Initialize state counter
    # state_counter = {}
    
    # # game loop
    # while game.state != "end":
    #     print("current state: " + game.state)

    #     # Increment the counter for the current state
    #     if game.state in state_counter:
    #         state_counter[game.state] += 1
    #     else:
    #         state_counter[game.state] = 1

    #     # Check if any state persists for over 10 times
    #     if state_counter[game.state] > 15:
    #         print(f"State {game.state} persisted for over 10 times. Stopping the game.")
    #         break

    #     if game.state == "start":
    #         game.game_start()
        
    #     elif game.state == "night":
    #         game.wolf_open_eye()
        
    #     elif game.state == "wolf_action":
    #         game.publish(game.state, game.to_dict())
    #         game.wolf_action_done()
        
    #     elif game.state == "wolf_action_end":
    #         game.wolf_action_done()
        
    #     elif game.state == "witch_heal":
    #         game.publish(game.state, game.to_dict())
    #         game.witch_heal_done()
        
    #     elif game.state == "witch_poison":
    #         game.publish(game.state, game.to_dict())
    #         game.witch_poison_done()
            
    #     elif game.state == "seer_action":
    #         game.publish(game.state, game.to_dict())
    #         game.seer_action_done()
        
    #     elif game.state == "day":
    #         game.daytime_start()
        
    #     elif game.state == "hunter_action":
    #         game.publish(game.state, game.to_dict())
    #         game.hunter_action_done()
        
    #     elif game.state == "day_last_words":
    #         game.publish(game.state, game.to_dict())
    #         game.day_last_words_done()
            
    #     elif game.state == "day_discuss":
    #         game.publish(game.state, game.to_dict())
    #         game.day_discuss_done()
        
    #     elif game.state == "day_vote":
    #         game.publish(game.state, game.to_dict())
    #         game.vote_done()
                
    #     elif game.state == "day_vote_end":
    #         game.day_vote_done()
            
    #     elif game.state == "wolf_win" or game.state == "good_win":
    #         game.game_over()

    # # Create log directory with timestamp

    # # Save game log
    # # log_file_path = os.path.join(config["log_directory"], "game.log")
    # # with open(log_file_path, "w") as log_file:
    # #     for entry in game.log:
    # #         log_file.write(str(entry) + "\n")

    # # Save config
    # config_file_path = os.path.join(config["log_directory"], config["config_file_path"].split("/")[-1])
    # with open(config_file_path, "w") as config_file:
    #     yaml.dump(config, config_file)

    # print(f"Logs and config saved in {config["log_directory"]}")

# if __name__ == "__main__":
#     werewolf()